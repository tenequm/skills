# macOS Audio Recording Pipeline

Recording system audio plus microphone to disk on macOS: the dual pipeline (SCStream + AVAudioEngine), AVAssetWriter crash safety, PCM buffer conversion and layout traps, AVAudioFile, on-device transcription with SpeechAnalyzer, and the signing/TCC failures that make recordings silent.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: Swift blocks compiled through SIL (`swiftc -emit-sil -target arm64-apple-macos15.0 -swift-version 6`, with and without `-default-isolation MainActor`; SpeechAnalyzer also typechecked against `arm64-apple-ios26.0`); an output-only `AVAudioEngine` was run to confirm the MainActor tap-closure trap; the ObjC wrapper built with `swift build`; the macOS 27 throwing `installTap` run on an `AVAudioPlayerNode` (no mic); APIs read from the macOS 27.0 SDK.

## Contents
- AVAudioEngine mic tap and its traps
- AVAssetWriter (and the macOS 26+ receiver API)
- AVAssetWriter crash safety and track integrity
- Buffer conversion and layout traps
- AVAudioFile and format settings
- Transcription with SpeechAnalyzer
- Microphone permission and entitlements
- TCC after rebuilds, reinstalls and identity changes

Default architecture for system audio + mic: two independent pipelines writing two tracks. System audio comes from an `SCStream` `.audio` output appended straight to an AAC `AVAssetWriterInput`; the mic comes from an `AVAudioEngine` tap, resampled to a fixed format, converted to `CMSampleBuffer` and appended to a second input. SCStream setup and Screen Recording TCC are in `macos-screencapturekit.md`; process taps in `macos-core-audio-tap.md`.

## AVAudioEngine mic tap and its traps

```swift
func startMicCapture() throws {
    let inputNode = engine.inputNode
    let format = inputNode.inputFormat(forBus: 0)
    // Explicit @Sendable closure: see the isolation trap below.
    let tapHandler: @Sendable (AVAudioPCMBuffer, AVAudioTime) -> Void = { [weak self] buffer, time in
        guard let self else { return }
        nonisolated(unsafe) let buffer = buffer
        audioQueue.async { self.handleMicBuffer(buffer, time: time) }
    }
    inputNode.installTap(onBus: 0, bufferSize: 4800, format: format, block: tapHandler)
    engine.prepare()
    try engine.start()
}
```

`bufferSize` is a request; the header gives the supported range as 100-400 ms.

**Isolation trap: the tap block is `NS_SWIFT_NONSENDABLE`.** An inline closure written inside a MainActor-isolated type - which every type is under `-default-isolation MainActor` - inherits MainActor isolation, compiles with no diagnostic in Swift 6 mode, and then traps (`EXC_BREAKPOINT`, exit 133 in a test run) on the first buffer, because CoreAudio calls it on its render thread. Always pass a closure typed `@Sendable (AVAudioPCMBuffer, AVAudioTime) -> Void` as above, and declare capture classes `nonisolated final class ...: @unchecked Sendable` with state confined to one queue.

Sendability in the macOS 27 SDK: `AVAudioFormat` and `AVAudioTime` are Sendable; `AVAudioPCMBuffer` is not (hence the `nonisolated(unsafe)` hop above - the tap hands you a fresh buffer you do not touch again); `CMSampleBuffer`, `AVAssetWriter` and `AVAssetWriterInput` mark Sendable unavailable, so keep the writer, its inputs and in-flight buffers on one serial queue. On a 27+ target, `AVReadOnlyAudioPCMBuffer` is a Sendable buffer you can pass across tasks.

**`installTap` raises an ObjC `NSException`, not a Swift error** (incompatible format, tap already on the bus). Swift `do/catch` cannot catch it, and a generic "ObjC try block" helper fails in release builds because the compiler removes the ObjC trampoline for `NS_NOESCAPE` blocks. `engine.start()` can raise too.

- **macOS 27+ / iOS 27+:** the SDK adds a throwing variant and deprecates the old one. Swift imports it under a refined name with a vestigial `error: ()` argument (there is no Swift overlay wrapper):

  ```swift
  try engine.inputNode.__installTap(onBus: 0, bufferSize: 4800, format: nil, error: (), block: handler)
  ```

  Verified: a second tap on the same bus throws `com.apple.coreaudio.avfaudio` code -10863 (`nullptr == Tap()`) where the old call terminates the process. `connectNode(_:to:format:)` is the matching throwing replacement for `connect(_:to:format:)`.
- **Earlier deployment targets:** wrap the calls in ObjC so the whole throw-to-catch chain is ObjC.

```objc
// Sources/ObjCExceptionCatcher/include/ObjCExceptionCatcher.h
#import <AVFAudio/AVFAudio.h>
NS_ASSUME_NONNULL_BEGIN
BOOL ObjCInstallTap(AVAudioNode *node, AVAudioNodeBus bus, AVAudioFrameCount bufferSize,
                    AVAudioFormat * _Nullable format, AVAudioNodeTapBlock block,
                    NSError * _Nullable * _Nullable outError);
BOOL ObjCStartEngine(AVAudioEngine *engine, NSError * _Nullable * _Nullable outError);
NS_ASSUME_NONNULL_END

// Sources/ObjCExceptionCatcher/ObjCExceptionCatcher.m
#import "ObjCExceptionCatcher.h"

static NSError *ErrorFromException(NSException *e) {
    return [NSError errorWithDomain:@"ObjCException" code:-1
                           userInfo:@{NSLocalizedDescriptionKey: e.reason ?: e.name}];
}

BOOL ObjCInstallTap(AVAudioNode *node, AVAudioNodeBus bus, AVAudioFrameCount bufferSize,
                    AVAudioFormat *format, AVAudioNodeTapBlock block, NSError **outError) {
    @try {
        [node installTapOnBus:bus bufferSize:bufferSize format:format block:block];
        return YES;
    } @catch (NSException *e) {
        if (outError) *outError = ErrorFromException(e);
        return NO;
    }
}

BOOL ObjCStartEngine(AVAudioEngine *engine, NSError **outError) {
    @try {
        return [engine startAndReturnError:outError];
    } @catch (NSException *e) {
        if (outError) *outError = ErrorFromException(e);
        return NO;
    }
}
```

```swift
// Package.swift target
.target(name: "ObjCExceptionCatcher", publicHeadersPath: "include",
        linkerSettings: [.linkedFramework("AVFAudio")]),

// Swift call site (C functions do not import as throws)
var error: NSError?
guard ObjCInstallTap(node, 0, 4800, format, block, &error) else { throw TapError(underlying: error) }
```

**Device changes.** Handle `AVAudioEngineConfigurationChange` on `.main`, read the new device's native format (never the stored one), reinstall the tap. Debounce 200-500 ms: virtual devices like Krisp fire bursts.

```swift
NotificationCenter.default.addObserver(forName: .AVAudioEngineConfigurationChange, object: engine,
                                       queue: .main) { [weak self] _ in self?.handleConfigChange() }

func handleConfigChange() {
    let newFormat = engine.inputNode.inputFormat(forBus: 0)
    guard newFormat.sampleRate > 0, newFormat.channelCount > 0 else { return }
    engine.inputNode.removeTap(onBus: 0)
    // reinstall with newFormat via the safe install path above
}
```

**The mic tap can die on an output-device switch with no notification.** Switching the output device can rebuild the capture graph without `AVAudioEngineConfigurationChange` firing for input; the tap stays on a dead graph and delivers nothing for the rest of the recording - no error, no log. After any rebuild, check that buffers resumed, and if not, recreate the engine (reattaching to the stale engine reproduces the dead state):

```swift
func verifyMicAlive(after rebuild: Date) async {
    try? await Task.sleep(for: .milliseconds(400))
    if lastMicBufferAt < rebuild {
        teardownEngine()            // stop, remove tap, replace with a new AVAudioEngine
        try? buildEngine()
    }
}
```

**Voice processing (VPIO) traps.**
- `setVoiceProcessingEnabled(true)` reports input+output channels combined (for example 9). Pass `format: nil` to `installTap` and let VPIO negotiate.
- Enabling VPIO makes macOS treat you as a VoIP app and duck every other source by about 20 dB - including the system audio you record - and it silences SCStream system audio outright. Measure before shipping it, and keep a raw-mode path working (enabling can fail and leave the input node unusable).
- Another app's VPIO reshapes *your* mic tap: during a call in a communications app your raw tap can receive more than two channels, and naive stereo handling yields a nearly inaudible track. With more than two channels take channel 0 (plus a makeup gain) instead of downmixing an unknown layout, and log per-session RMS so "it is quiet" becomes a number:

```swift
nonisolated func micMono(_ buffer: AVAudioPCMBuffer, makeupGainDB: Float) -> [Float] {
    let channels = Int(buffer.format.channelCount)
    guard channels > 2, let data = buffer.floatChannelData else { return downmixToMono(buffer) }
    let gain = powf(10, makeupGainDB / 20)
    let frames = Int(buffer.frameLength)
    if buffer.format.isInterleaved {
        return (0..<frames).map { data[0][$0 * channels] * gain }
    }
    return (0..<frames).map { data[0][$0] * gain }
}
```

## AVAssetWriter (and the macOS 26+ receiver API)

AVAssetWriter is the default sink for SCStream audio: it takes `CMSampleBuffer` directly and encodes AAC.

```swift
let writer = try AVAssetWriter(url: url, fileType: .m4a)
writer.movieFragmentInterval = CMTime(seconds: 10, preferredTimescale: 600)
let input = AVAssetWriterInput(mediaType: .audio, outputSettings: [
    AVFormatIDKey: kAudioFormatMPEG4AAC,
    AVSampleRateKey: 48_000.0,
    AVNumberOfChannelsKey: 2,
    AVEncoderBitRateKey: 128_000,
])
input.expectsMediaDataInRealTime = true
writer.add(input)
guard writer.startWriting() else { throw writer.error ?? CocoaError(.fileWriteUnknown) }
```

```swift
// SCStreamOutput callback on audioQueue; writer state is touched only on that queue.
func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer,
            of type: SCStreamOutputType) {
    guard type == .audio, sampleBuffer.isValid,
          let writer, let input, writer.status == .writing else { return }
    if !sessionStarted {
        writer.startSession(atSourceTime: sampleBuffer.presentationTimeStamp)
        sessionStarted = true
    }
    if input.isReadyForMoreMediaData { input.append(sampleBuffer) }
}
```

Stop with the bounded teardown from `macos-screencapturekit.md`: `stopCapture()` under a timeout, then `input.markAsFinished()` on the audio queue, then `await writer.finishWriting()` under a timeout. Pair this with the audio-only SCStream configuration there (2x2, 1 fps, ignored `.screen` output).

File types: `.m4a` (AAC/ALAC), `.mov` (PCM/AAC/ALAC), `.mp4` (AAC), `.wav` (PCM), `.caf` (any). `outputSettings: nil` is pass-through (no re-encode).

**macOS 27 SDK deprecation.** In Swift, `add(_:)`, `startWriting()`, `isReadyForMoreMediaData`, `expectsMediaDataInRealTime`, `requestMediaDataWhenReady` and `append(_:)` are deprecated as of macOS/iOS 27 in favor of a receiver API available since macOS/iOS 26. The classic calls still work and only warn when the deployment target is 27. With a 26+ target:

```swift
@available(macOS 26, *)
func writeWithReceiver(url: URL, firstBuffer: sending CMSampleBuffer) async throws {
    let writer = try AVAssetWriter(url: url, fileType: .m4a)
    let input = AVAssetWriterInput(mediaType: .audio, outputSettings: [
        AVFormatIDKey: kAudioFormatMPEG4AAC, AVSampleRateKey: 48_000.0,
        AVNumberOfChannelsKey: 2, AVEncoderBitRateKey: 128_000,
    ])
    let receiver = writer.inputReceiver(for: input)   // attaches the input
    try writer.start()
    writer.startSession(atSourceTime: firstBuffer.presentationTimeStamp)
    // Real-time sources: appendImmediately returns false when not ready (drop), throws if the writer failed.
    // Pull sources: `try await receiver.append(_:)` suspends until ready.
    if try !receiver.appendImmediately(CMReadySampleBuffer(unsafeBuffer: firstBuffer)) { /* dropped */ }
    receiver.finish()
    await writer.finishWriting()
}
```

`CMReadySampleBuffer(unsafeBuffer:)` takes the buffer as `sending`; do not touch it afterwards. The rules below apply to both APIs.

## AVAssetWriter crash safety and track integrity

**`movieFragmentInterval` makes partial files recoverable** (verified with `.m4a`, not just `.mov`): a force-killed recording keeps everything up to the last fragment, about 10 s loss at the interval above.

**Always set `expectsMediaDataInRealTime = true`**, even in post-processing pipelines. Without it the writer applies backpressure that can deadlock synchronous polling loops.

**Guard writer status in polling loops.** After a failed `append`, the writer is `.failed` and `isReadyForMoreMediaData` stays `false` forever:

```swift
while !input.isReadyForMoreMediaData {
    guard writer.status == .writing else { break }   // without this: infinite loop
    usleep(10_000)
}
```

**Session start in dual-track files.** Start the session on the first *system* audio sample; drop mic samples that arrive earlier (`guard sessionStarted else { return }`).

**Channel-count mismatch is silent.** AVAudioEngine delivers mono mic audio; a mic input configured for 2 channels records silence while every `append` reports success. Configure the mic input as `AVNumberOfChannelsKey: 1` (64 kbps is plenty) and system audio as 2.

**Input format is fixed by the first append.** The AAC encoder configures itself from the first buffer's format description. A later buffer in a different format makes `append` return `false` and eventually fails the writer - losing **both** tracks of a dual-track file. This is exactly what happens when the mic device changes mid-recording and the reinstalled tap delivers the new device's native rate/channels. Fix: resample/downmix every mic buffer into one fixed format (for example mono 48 kHz Float32) before appending, whatever the device delivers. SCStream audio needs no resampling: it always arrives at the configured `sampleRate`/`channelCount`.

**The writer collapses PTS gaps.** No property preserves gaps: if one buffer ends at 10.0 s and the next starts at 12.5 s, AAC writes them back to back and the track ends up 2.5 s short, so dual tracks drift apart over a recording. Detect gaps per input and fill them with explicit silence. Three rules: write silence in small chunks at the normal cadence (one buffer spanning the gap fails with `kCMSampleBufferError_ArrayTooSmall` (-12737) or crashes the encoder); build a clean LPCM format description for silence instead of reusing a pipeline buffer's (those can carry channel layouts or non-interleaved flags that do not match a flat zero block); never let gap-fill failure block the real buffer. A >5 ms threshold (240 samples at 48 kHz) avoids false positives from jitter.

```swift
/// Confined to the writer's append queue.
nonisolated final class TrackWriter {
    let input: AVAssetWriterInput
    private var nextExpectedPTS = CMTime.invalid
    private let silenceFormat: CMAudioFormatDescription
    private let chunkFrames = 1024

    init(input: AVAssetWriterInput, channels: UInt32) throws {
        self.input = input
        var asbd = AudioStreamBasicDescription(
            mSampleRate: 48_000, mFormatID: kAudioFormatLinearPCM,
            mFormatFlags: kAudioFormatFlagIsFloat | kAudioFormatFlagIsPacked,
            mBytesPerPacket: 4 * channels, mFramesPerPacket: 1, mBytesPerFrame: 4 * channels,
            mChannelsPerFrame: channels, mBitsPerChannel: 32, mReserved: 0)
        var desc: CMAudioFormatDescription?
        let status = CMAudioFormatDescriptionCreate(
            allocator: kCFAllocatorDefault, asbd: &asbd, layoutSize: 0, layout: nil,
            magicCookieSize: 0, magicCookie: nil, extensions: nil, formatDescriptionOut: &desc)
        guard status == noErr, let desc else { throw NSError(domain: NSOSStatusErrorDomain, code: Int(status)) }
        silenceFormat = desc
    }

    func append(_ sample: CMSampleBuffer) {
        let incoming = sample.presentationTimeStamp
        if nextExpectedPTS.isValid, incoming > nextExpectedPTS,
           (incoming - nextExpectedPTS).seconds > 0.005 {
            fillGap(from: nextExpectedPTS, to: incoming)
        }
        if input.isReadyForMoreMediaData { input.append(sample) }
        nextExpectedPTS = incoming + sample.duration
    }

    private func fillGap(from start: CMTime, to end: CMTime) {
        var cursor = start
        while cursor < end, input.isReadyForMoreMediaData {
            guard let silent = makeSilence(at: cursor), input.append(silent) else { break } // accept partial fill
            cursor = cursor + CMTime(value: CMTimeValue(chunkFrames), timescale: 48_000)
        }
    }

    private func makeSilence(at pts: CMTime) -> CMSampleBuffer? {
        let length = chunkFrames * Int(silenceFormat.audioStreamBasicDescription!.mBytesPerFrame)
        var block: CMBlockBuffer?
        guard CMBlockBufferCreateWithMemoryBlock(
            allocator: kCFAllocatorDefault, memoryBlock: nil, blockLength: length,
            blockAllocator: kCFAllocatorDefault, customBlockSource: nil, offsetToData: 0,
            dataLength: length, flags: kCMBlockBufferAssureMemoryNowFlag, blockBufferOut: &block) == noErr,
              let block,
              CMBlockBufferFillDataBytes(with: 0, blockBuffer: block, offsetIntoDestination: 0, dataLength: length) == noErr
        else { return nil }
        var sample: CMSampleBuffer?
        guard CMAudioSampleBufferCreateReadyWithPacketDescriptions(
            allocator: kCFAllocatorDefault, dataBuffer: block, formatDescription: silenceFormat,
            sampleCount: chunkFrames, presentationTimeStamp: pts, packetDescriptions: nil,
            sampleBufferOut: &sample) == noErr else { return nil }
        return sample
    }
}
```

**`CMBlockBuffer` memory trap.** `CMBlockBufferCreateWithMemoryBlock` with `memoryBlock: nil` and `flags: 0` defers allocation; a following `CMBlockBufferReplaceDataBytes` writes into memory that does not exist yet. Pass `kCMBlockBufferAssureMemoryNowFlag` (as above) or let CoreMedia allocate via `CMSampleBufferSetDataBufferFromAudioBufferList` (below).

## Buffer conversion and layout traps

**CMSampleBuffer to AVAudioPCMBuffer: check this first when audio is silent.** SCStream delivers Float32 stereo as **non-interleaved** (two buffers in the `AudioBufferList`). Code that `memcpy`s the block buffer into `floatChannelData[0]` as if interleaved produces a valid-looking buffer that plays as silence or garbage; this has killed multi-minute production recordings. Let CoreMedia copy, which handles both layouts:

```swift
nonisolated extension AVAudioPCMBuffer {
    static func from(_ sampleBuffer: CMSampleBuffer) -> AVAudioPCMBuffer? {
        guard let formatDescription = CMSampleBufferGetFormatDescription(sampleBuffer) else { return nil }
        let frames = CMSampleBufferGetNumSamples(sampleBuffer)
        let format = AVAudioFormat(cmAudioFormatDescription: formatDescription)
        guard let pcm = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: AVAudioFrameCount(frames)) else { return nil }
        pcm.frameLength = AVAudioFrameCount(frames)
        let status = CMSampleBufferCopyPCMDataIntoAudioBufferList(
            sampleBuffer, at: 0, frameCount: Int32(frames), into: pcm.mutableAudioBufferList)
        return status == noErr ? pcm : nil
    }
}
```

With a macOS 27 target, `AVAudioFormat(cmAudioFormatDescription:)` is deprecated in favor of the failable `AVAudioFormat(formatDescription:)`. If the destination is AVAssetWriter, skip the conversion entirely and append the SCStream buffer - it avoids every PCM-layout bug.

**AVAudioPCMBuffer to CMSampleBuffer** (mic tap into AVAssetWriter). Let CoreMedia own the block buffer memory:

```swift
nonisolated func makeSampleBuffer(from pcmBuffer: AVAudioPCMBuffer, time: AVAudioTime) -> CMSampleBuffer? {
    let format = pcmBuffer.format
    var timing = CMSampleTimingInfo(
        duration: CMTime(value: 1, timescale: CMTimeScale(format.sampleRate)),
        presentationTimeStamp: CMTime(seconds: AVAudioTime.seconds(forHostTime: time.hostTime),
                                      preferredTimescale: 48_000),
        decodeTimeStamp: .invalid)
    var sampleBuffer: CMSampleBuffer?
    guard CMSampleBufferCreate(
        allocator: kCFAllocatorDefault, dataBuffer: nil, dataReady: false,
        makeDataReadyCallback: nil, refcon: nil, formatDescription: format.formatDescription,
        sampleCount: CMItemCount(pcmBuffer.frameLength),
        sampleTimingEntryCount: 1, sampleTimingArray: &timing,
        sampleSizeEntryCount: 0, sampleSizeArray: nil, sampleBufferOut: &sampleBuffer) == noErr,
          let sb = sampleBuffer else { return nil }
    guard CMSampleBufferSetDataBufferFromAudioBufferList(
        sb, blockBufferAllocator: kCFAllocatorDefault, blockBufferMemoryAllocator: kCFAllocatorDefault,
        flags: 0, bufferList: pcmBuffer.audioBufferList) == noErr else { return nil }
    return sb
}
```

For long recordings convert mic host times through `stream.synchronizationClock` (`macos-screencapturekit.md`).

**Mono downmix that assumes interleaved layout.** Indexing `floatChannelData[0]` as `[L, R, L, R, ...]` is only right for interleaved buffers. `AVAudioPCMBuffer` is often planar, where `floatChannelData[0]` is all of the left channel; interleaved indexing then averages adjacent *left* samples and never reads the right channel. It is audibly wrong but not silent, so it passes smoke tests. Always branch on `isInterleaved`:

```swift
nonisolated func downmixToMono(_ buffer: AVAudioPCMBuffer) -> [Float] {
    guard let data = buffer.floatChannelData else { return [] }
    let frames = Int(buffer.frameLength)
    let channels = Int(buffer.format.channelCount)
    guard channels > 1 else { return Array(UnsafeBufferPointer(start: data[0], count: frames)) }
    var mono = [Float](repeating: 0, count: frames)
    if buffer.format.isInterleaved {
        let p = data[0]
        for i in 0..<frames { mono[i] = (p[i * channels] + p[i * channels + 1]) * 0.5 }
    } else {
        let left = data[0], right = data[1]
        for i in 0..<frames { mono[i] = (left[i] + right[i]) * 0.5 }
    }
    return mono
}
```

Test with opposite-polarity stereo: silence under a correct downmix, full amplitude under the broken one.

## AVAudioFile and format settings

AVAudioFile is simpler but needs `AVAudioPCMBuffer` input (convert first). `settings` is the on-disk format; `commonFormat`/`interleaved` describe the buffers you pass to `write(from:)`:

```swift
let settings: [String: Any] = [
    AVFormatIDKey: kAudioFormatLinearPCM, AVSampleRateKey: 48_000.0, AVNumberOfChannelsKey: 2,
    AVLinearPCMBitDepthKey: 32, AVLinearPCMIsFloatKey: true, AVLinearPCMIsBigEndianKey: false,
    AVLinearPCMIsNonInterleaved: false,
]
let file = try AVAudioFile(forWriting: url, settings: settings,
                           commonFormat: .pcmFormatFloat32, interleaved: false)
try file.write(from: pcm)
file.close()   // macOS 15+; earlier, release the object to finalize the header
```

| Format | Constant | Containers | Required keys |
|---|---|---|---|
| PCM | `kAudioFormatLinearPCM` | WAV, CAF, AIFF | all `AVLinearPCM*` keys (AVAssetWriter) |
| AAC | `kAudioFormatMPEG4AAC` | M4A, MP4 | `AVEncoderBitRateKey` (`AVEncoderBitRatePerChannelKey` is not supported by AVAssetWriter) |
| ALAC | `kAudioFormatAppleLossless` | M4A, CAF | `AVEncoderBitDepthHintKey` |
| FLAC | `kAudioFormatFLAC` | FLAC, CAF | |

## Transcription with SpeechAnalyzer

`SpeechAnalyzer` + `SpeechTranscriber` (Speech framework, macOS 26+ and iOS 26+ alike) transcribe on device. Per Apple's [speech recognition permission doc](https://developer.apple.com/documentation/speech/asking-permission-to-use-speech-recognition), the `SFSpeechRecognizer` authorization flow does not apply: SpeechAnalyzer modules do not send audio to Apple's servers, so no `NSSpeechRecognitionUsageDescription` prompt is needed beyond the capture grants. Feed it the buffers you already have (mic tap, or SCStream audio converted as above).

```swift
@available(macOS 27, *)
func transcribe(_ buffers: AsyncStream<AVAudioPCMBuffer>) async throws -> String {
    guard let locale = await SpeechTranscriber.supportedLocale(equivalentTo: .current) else { return "" }
    let transcriber = SpeechTranscriber(locale: locale, preset: .transcription)
    if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
        try await request.downloadAndInstall()          // model download, once per locale
    }
    let analyzer = SpeechAnalyzer(modules: [transcriber])
    let (inputs, builder) = AsyncStream.makeStream(of: AnalyzerInput.self)
    let converter = try await AnalyzerInputConverter.converter(compatibleWith: [transcriber])

    let collector = Task {
        var text = ""
        for try await result in transcriber.results where result.isFinal {
            text += String(result.text.characters)       // result.text is an AttributedString
        }
        return text
    }
    try await analyzer.start(inputSequence: inputs)
    for await buffer in buffers {
        for input in try converter.convert(buffer, at: nil) { builder.yield(input) }
    }
    for input in try converter.flush() { builder.yield(input) }
    builder.finish()
    try await analyzer.finalizeAndFinishThroughEndOfInput()  // finishing the stream alone does not end the session
    return try await collector.value
}
```

- macOS/iOS 26 (no `AnalyzerInputConverter`): get the target with `await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber])`, convert each buffer with `AVAudioConverter`, wrap with `AnalyzerInput(buffer:)`. Feeding the wrong format fails with `SFSpeechError.Code.unexpectedAudioFormat`.
- Files: `SpeechAnalyzer(inputAudioFile:modules:finishAfterFile: true)` then iterate `transcriber.results`. macOS 27 adds `AssetInputSequenceProvider` (AVAsset) and `CaptureInputSequenceProvider` (AVCaptureDevice) as ready-made input sources.
- Check `SpeechTranscriber.isAvailable`; fall back to `DictationTranscriber` on unsupported hardware.
- The system caps concurrent analyzers (`insufficientResources`); `SpeechAnalyzer.Options(priority:modelRetention:ignoresResourceLimits:)` (27+) lifts the cap at your own risk. Call `prepareToAnalyze(in:)` to preheat models.
- `AnalyzerInput.buffer` is deprecated in 27 (use `bufferFormat`, `bufferDuration`, `bufferStartTime`).

Summarizing the transcript is a separate step: see `foundation-models.md`.

## Microphone permission and entitlements

```swift
switch AVCaptureDevice.authorizationStatus(for: .audio) {
case .authorized: break
case .notDetermined: _ = await AVCaptureDevice.requestAccess(for: .audio)   // system dialog
case .denied, .restricted: SystemSettingsPane.microphone.open()           // user must toggle
@unknown default: break
}
```

Use the system dialog for `.notDetermined`; open Settings only for `.denied`. `SystemSettingsPane` is in `macos-screencapturekit.md`.

| Audio source | TCC grant | Entitlement / Info.plist |
|---|---|---|
| App/system audio via ScreenCaptureKit | Screen Recording | none |
| Mic via AVFoundation/AVAudioEngine | Microphone | `com.apple.security.device.audio-input` (hardened runtime), `NSMicrophoneUsageDescription` |
| Mic via SCStream `captureMicrophone` (macOS 15+) | Screen Recording + Microphone | same as above |
| Core Audio process tap | System Audio Recording | `NSAudioCaptureUsageDescription` (see `macos-core-audio-tap.md`) |

`captureMicrophone` and `AVCaptureDevice.requestAccess(for: .audio)` create separate TCC entries; both must be granted and both show in the Microphone pane. Sandboxed (App Store) builds also need `com.apple.security.app-sandbox` and `com.apple.security.device.microphone`; full entitlement setup is in `macos-distribution.md`. Reset during development: `tccutil reset Microphone com.example.app`.

## TCC after rebuilds, reinstalls and identity changes

All of these present as "permission granted, recording silent" or "re-prompts every launch". None has a programmatic fix (`TCC.db` is SIP-protected).

**Force-replacing the bundle can leave TCC degraded.** TCC keys the grant on the code signature. After `rm -rf /Applications/App.app && cp -R build/App.app /Applications/` with the same Developer ID, TCC still reports authorized and `SCStream` starts without error, but buffers arrive at zero amplitude (RMS stays at `-inf`). The user must toggle the app off and on in Privacy & Security > Screen & System Audio Recording. Prefer an in-place overwrite (let the OS swap the inode) or run `tccutil reset ScreenCapture <bundle-id>` from a signed installer. In `make install` scripts, `killall` the app before replacing it: a running process keeps executing from the unlinked inode and `open -a` brings the stale instance forward.

**Ad-hoc signing resets TCC on every build.** `codesign --sign -` yields a new CDHash each build, and TCC identifies ad-hoc apps by CDHash. Sign development builds with a stable identity - your Apple Development certificate, or a self-signed code-signing certificate - so TCC uses the designated requirement (certificate + bundle ID) and grants survive rebuilds.

**A stale row from a superseded identity.** After switching identity (ad-hoc or self-signed during development, Developer ID for release), System Settings can show the app with the toggle on while `CGPreflightScreenCaptureAccess()` returns `false` and the app re-prompts each launch. The user must select the row, remove it with **-**, deny the pending prompt, relaunch and grant again. Afterwards the grant keys on team ID + bundle ID and survives rebuilds.

**Terminal attribution and bare binaries.** Run capture code from a `.app` bundle, not a binary in a terminal: the grant goes to the terminal app, and some terminals record silence for Core Audio taps without ever prompting.

Unverified: the signing-related behaviors above are production observations across macOS 14-26; Apple does not document TCC's keying rules.
