# Screen Capture & Audio Recording

## Table of Contents
- SCShareableContent - Content Discovery
- SCContentFilter - Filtering
- SCStream & SCStreamConfiguration
- SCStreamOutput - Receiving Samples
- SCStream Production Gotchas
- SCRecordingOutput (macOS 15+)
- SCContentSharingPicker (macOS 14+)
- SCScreenshotManager (macOS 14+)
- Audio-Only Capture Pattern
- AVAudioEngine for Mic (Dual Pipeline)
- AVAssetWriter for Audio
- AVAssetWriter Crash Safety
- AVAudioFile for Audio
- CMSampleBuffer to AVAudioPCMBuffer
- AVAudioPCMBuffer to CMSampleBuffer (for AVAssetWriter)
- Audio Format Settings
- Permissions
- TCC Operational Gotchas
- Complete Examples

## SCShareableContent - Content Discovery

```swift
import ScreenCaptureKit

// Enumerate available content (macOS 12.3+)
let content = try await SCShareableContent.excludingDesktopWindows(
    false, onScreenWindowsOnly: true
)

content.displays       // [SCDisplay]
content.windows        // [SCWindow]
content.applications   // [SCRunningApplication]

// Async property (macOS 14+)
let content = try await SCShareableContent.current
```

Key types:

```swift
// SCDisplay
display.displayID      // CGDirectDisplayID
display.width          // Int
display.height         // Int

// SCRunningApplication
app.bundleIdentifier   // String
app.applicationName    // String
app.processID          // pid_t

// SCWindow
window.windowID        // CGWindowID
window.title           // String?
window.isOnScreen      // Bool
window.owningApplication // SCRunningApplication?
```

**Note**: `SCShareableContent` calls trigger the screen recording permission prompt if not yet granted. First call after granting permission requires app restart.

## SCContentFilter - Filtering

```swift
// Single window (follows across displays)
let filter = SCContentFilter(desktopIndependentWindow: window)

// Specific apps on a display
let filter = SCContentFilter(
    display: display,
    including: [app1, app2],
    exceptingWindows: []
)

// Full display, exclude own app
let excludedApps = content.applications.filter {
    Bundle.main.bundleIdentifier == $0.bundleIdentifier
}
let filter = SCContentFilter(
    display: display,
    excludingApplications: excludedApps,
    exceptingWindows: []
)

// Specific windows on a display
let filter = SCContentFilter(display: display, including: [window1, window2])

// Display minus specific windows
let filter = SCContentFilter(display: display, excludingWindows: [windowToExclude])
```

| Use Case | Initializer |
|----------|------------|
| Single window (follows across displays) | `init(desktopIndependentWindow:)` |
| Entire display minus own app | `init(display:excludingApplications:exceptingWindows:)` |
| Specific apps only | `init(display:including:exceptingWindows:)` |
| Specific windows | `init(display:including:)` |

Audio filtering works at the **application level** - the filter determines which apps' audio is captured.

## SCStream & SCStreamConfiguration

### Configuration

```swift
let config = SCStreamConfiguration()

// Video
config.width = 1920
config.height = 1080
config.minimumFrameInterval = CMTime(value: 1, timescale: 60) // 60 fps
config.pixelFormat = kCVPixelFormatType_32BGRA
config.queueDepth = 5              // max frames in queue (default 3, max 8)
config.showsCursor = true
config.scalesToFit = true

// Audio (macOS 12.3+)
config.capturesAudio = true
config.sampleRate = 48000          // up to 48kHz
config.channelCount = 2            // stereo
config.excludesCurrentProcessAudio = true

// Microphone (macOS 15+)
config.captureMicrophone = true
config.microphoneCaptureDeviceID = AVCaptureDevice.default(for: .audio)?.uniqueID

// HDR (macOS 15+)
config.captureDynamicRange = .hdrCanonicalDisplay

// Resolution (macOS 14+)
config.captureResolution = .best
```

Configuration presets (macOS 15+):

```swift
let config = SCStreamConfiguration(preset: .captureHDRStreamCanonicalDisplay)
let config = SCStreamConfiguration(preset: .captureHDRScreenshotLocalDisplay)
```

### Stream lifecycle

```swift
// Create
let stream = SCStream(filter: filter, configuration: config, delegate: self)

// Add outputs
try stream.addStreamOutput(self, type: .screen, sampleHandlerQueue: videoQueue)
try stream.addStreamOutput(self, type: .audio, sampleHandlerQueue: audioQueue)
try stream.addStreamOutput(self, type: .microphone, sampleHandlerQueue: micQueue) // macOS 15+

// Start/stop
try await stream.startCapture()
try await stream.stopCapture()

// Update without restart
try await stream.updateConfiguration(newConfig)
try await stream.updateContentFilter(newFilter)
```

### SCStreamDelegate

```swift
extension CaptureManager: SCStreamDelegate {
    func stream(_ stream: SCStream, didStopWithError error: Error) {
        // Stream stopped unexpectedly
    }
}
```

## SCStreamOutput - Receiving Samples

```swift
class CaptureEngine: NSObject, SCStreamOutput {

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer,
                of type: SCStreamOutputType) {
        guard sampleBuffer.isValid else { return }

        switch type {
        case .screen:
            handleVideo(sampleBuffer)
        case .audio:
            handleAudio(sampleBuffer)
        case .microphone:  // macOS 15+
            handleMicrophone(sampleBuffer)
        @unknown default:
            break
        }
    }
}
```

### Processing video buffers

```swift
private func handleVideo(_ sampleBuffer: CMSampleBuffer) {
    guard let attachments = CMSampleBufferGetSampleAttachmentsArray(
        sampleBuffer, createIfNecessary: false
    ) as? [[SCStreamFrameInfo: Any]],
    let status = attachments.first?[.status] as? Int,
    SCFrameStatus(rawValue: status) == .complete,
    let pixelBuffer = sampleBuffer.imageBuffer else { return }

    let surface = CVPixelBufferGetIOSurface(pixelBuffer)?.takeUnretainedValue()
    let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
}
```

### Processing audio buffers

```swift
private func handleAudio(_ sampleBuffer: CMSampleBuffer) {
    try? sampleBuffer.withAudioBufferList { audioBufferList, blockBuffer in
        guard let desc = sampleBuffer.formatDescription?.audioStreamBasicDescription,
              let format = AVAudioFormat(
                  standardFormatWithSampleRate: desc.mSampleRate,
                  channels: desc.mChannelsPerFrame
              ),
              let pcmBuffer = AVAudioPCMBuffer(
                  pcmFormat: format,
                  bufferListNoCopy: audioBufferList.unsafePointer
              )
        else { return }
        // Use pcmBuffer for processing, level metering, or writing
    }
}
```

## SCStream Production Gotchas

### SCStream is NOT reusable after error

After `didStopWithError`, the XPC connection to `replayd` is invalidated. Calling `startCapture()` again throws `attemptToStartStreamState`. You must destroy the stream and create a new one:

```swift
func stream(_ stream: SCStream, didStopWithError error: Error) {
    // DO NOT try stream.startCapture() - it will throw
    self.stream = nil // Release the dead stream
    Task { try await restartWithNewStream() } // Create fresh SCStream
}
```

### SCRecordingOutput stops on updateConfiguration()

`SCRecordingOutput` stops recording when `SCStreamConfiguration` is updated on a running stream. This is documented in the Apple header. If your app needs mid-stream config changes (device following, resolution changes), use manual `SCStreamOutput` + `AVAssetWriter` instead.

### VPIO and SCStream are fundamentally incompatible

`AVAudioEngine.setVoiceProcessingEnabled(true)` creates a hidden VPIO aggregate device that hooks into the system audio output path for its AEC reference signal. This silences SCStream's system audio capture. Do not use VPIO and SCStream together. Use post-processing AEC or an independent mic pipeline instead.

### SCStream .microphone output type is unreliable for dual-track

The `.microphone` SCStreamOutputType (macOS 15+) can produce duration mismatches and data corruption when written as a second AVAssetWriterInput alongside system audio. Use an independent AVAudioEngine pipeline for mic capture instead (see "AVAudioEngine for Mic" section).

### Multiple SCStreams can run simultaneously

Two `SCStream` instances (e.g., one display-wide, one per-app) can run from the same process. Each is an independent XPC connection to the ScreenCaptureKit daemon. Both start without error and deliver audio buffers concurrently.

### Virtual audio processors cause duplication in display-wide capture

Virtual audio devices (Krisp, SoundSource) process audio with latency (~50ms). Display-wide capture picks up both the original app output and the virtual device's delayed copy, causing audible echo. Fix: use per-app `SCContentFilter(display:including:[specificApp])` to exclude virtual audio processors.

### Chrome/Electron helper bundle ID resolution

CoreAudio and ScreenCaptureKit report Chrome's renderer subprocess as the audio client (`com.google.Chrome.helper.renderer`). Strip `.helper*` suffix to resolve to the parent app for `SCContentFilter` lookup:

```swift
func resolveParentBundleID(_ bundleID: String) -> String {
    if let range = bundleID.range(of: ".helper", options: .literal) {
        return String(bundleID[..<range.lowerBound])
    }
    return bundleID
}
// "com.google.Chrome.helper.renderer" -> "com.google.Chrome"
```

### Never mutate SCStream's CMSampleBuffer in-place

SCStream sample buffers are framework-managed and potentially shared. Writing into them via `CMBlockBufferGetDataPointer` is undefined behavior. Use dual-track recording (separate AVAssetWriterInputs) instead of mixing into existing buffers.

### SCStream error codes and recovery

| Code | Meaning | Recovery |
|------|---------|---------|
| -3801 | Permission denied (TCC) | Stop, set `permissionNeeded = true`, prompt user |
| -3802 | Display disconnected (undocking) | Auto-restart with new stream |
| -3817 | User stopped via system UI | Respect user intent, save and stop |
| -3818 | System audio failed | Restart without audio |
| -3820 | Mic capture failed | Restart without mic |
| -3821 | System stopped (sleep/wake) | Wait 1s, restart with new file |

Rate-limit restarts (e.g., max 3 in 30s) to prevent infinite loops.

## SCRecordingOutput (macOS 15+)

Simplified file recording without manual AVAssetWriter buffer handling.

```swift
// Configure
let recordingConfig = SCRecordingOutputConfiguration()
recordingConfig.outputURL = fileURL          // file URL, not folder
recordingConfig.outputFileType = .mov        // .mov or .mp4
recordingConfig.videoCodecType = .hevc       // .hevc or .h264

// Create
let recordingOutput = SCRecordingOutput(
    configuration: recordingConfig, delegate: self
)

// Add to stream BEFORE startCapture for guaranteed first-frame capture
try stream.addRecordingOutput(recordingOutput)
try await stream.startCapture()

// Monitor
recordingOutput.recordedDuration  // CMTime
recordingOutput.recordedFileSize  // Int64

// Stop recording only (keep streaming)
try stream.removeRecordingOutput(recordingOutput)

// Or stop everything
try await stream.stopCapture()
```

### SCRecordingOutputDelegate

```swift
extension CaptureManager: SCRecordingOutputDelegate {
    func recordingOutputDidStartRecording(_ output: SCRecordingOutput) { }
    func recordingOutput(_ output: SCRecordingOutput, didFailWithError error: Error) { }
    func recordingOutputDidFinishRecording(_ output: SCRecordingOutput) {
        // File is ready at outputURL
    }
}
```

**Caveats**: Only ONE recording output per stream. Handles video recording; audio-only recording still uses AVAudioFile/AVAssetWriter. Updating `SCStreamConfiguration` on a running stream stops the recording.

## SCContentSharingPicker (macOS 14+)

System-provided picker UI for selecting content. Apple's preferred approach in macOS 15+.

```swift
let picker = SCContentSharingPicker.shared
picker.add(self)        // SCContentSharingPickerObserver
picker.isActive = true

// Present
picker.present()
picker.present(using: .window)         // specific style
picker.present(for: existingStream)    // for existing stream

// Configure
let pickerConfig = SCContentSharingPickerConfiguration()
pickerConfig.allowedPickerModes = [.singleWindow, .multipleWindows, .singleApplication]
pickerConfig.excludedBundleIDs = ["com.example.excluded"]
picker.defaultConfiguration = pickerConfig
```

### Observer

```swift
extension CaptureManager: SCContentSharingPickerObserver {
    func contentSharingPicker(_ picker: SCContentSharingPicker,
                              didUpdateWith filter: SCContentFilter,
                              for stream: SCStream?) {
        if let stream {
            try? await stream.updateContentFilter(filter)
        } else {
            // Create new stream with filter
        }
    }

    func contentSharingPicker(_ picker: SCContentSharingPicker,
                              didCancel forStream: SCStream?) { }

    func contentSharingPickerStartDidFailWithError(_ error: Error) { }
}
```

## SCScreenshotManager (macOS 14+)

Single-frame capture without a persistent stream.

```swift
let image: CGImage = try await SCScreenshotManager.captureImage(
    contentFilter: filter, configuration: config
)

let buffer: CMSampleBuffer = try await SCScreenshotManager.captureSampleBuffer(
    contentFilter: filter, configuration: config
)

// HDR (macOS 15+)
let hdrConfig = SCStreamConfiguration(preset: .captureHDRScreenshotLocalDisplay)
let hdrImage = try await SCScreenshotManager.captureImage(
    contentFilter: filter, configuration: hdrConfig
)
```

## Audio-Only Capture Pattern

ScreenCaptureKit does NOT support audio-only streams. A `.screen` output is always required.

**Workaround**: minimize video overhead:

```swift
let config = SCStreamConfiguration()
config.capturesAudio = true
config.sampleRate = 48000
config.channelCount = 2
config.excludesCurrentProcessAudio = true

// Minimal video to avoid error logs
config.width = 2
config.height = 2
config.minimumFrameInterval = CMTime(value: 1, timescale: CMTimeScale.max)

// Must add screen output even if unused
try stream.addStreamOutput(self, type: .screen, sampleHandlerQueue: nil)
try stream.addStreamOutput(self, type: .audio, sampleHandlerQueue: audioQueue)
```

**App-specific audio**: use `SCContentFilter(display:including:exceptingWindows:)` with specific apps to capture only their audio output.

## AVAudioEngine for Mic (Dual Pipeline)

For dual-track recording (system audio + mic), use SCStream for system audio and AVAudioEngine for mic independently. This avoids SCStream `.microphone` output reliability issues and VPIO incompatibility.

```swift
class DualTrackRecorder {
    private var engine = AVAudioEngine()
    private let audioQueue = DispatchQueue(label: "AudioCapture")

    func startMicCapture() throws {
        let inputNode = engine.inputNode
        let format = inputNode.inputFormat(forBus: 0)

        // CRITICAL: Extract closure to @Sendable to avoid MainActor isolation inheritance
        let tapHandler: @Sendable (AVAudioPCMBuffer, AVAudioTime) -> Void = { [weak self] buffer, time in
            self?.audioQueue.async { self?.handleMicBuffer(buffer, time: time) }
        }
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: format, block: tapHandler)

        engine.prepare()
        try engine.start()
    }
}
```

### AVAudioEngine device following

When audio hardware changes (headphone plug/unplug, Bluetooth connect), handle `AVAudioEngineConfigurationChange`:

```swift
// Use queue: .main to avoid isolation inheritance crash
NotificationCenter.default.addObserver(
    forName: .AVAudioEngineConfigurationChange, object: engine, queue: .main
) { [weak self] _ in
    self?.handleConfigChange()
}

func handleConfigChange() {
    // Use the NEW device's native format, not the stored old one
    let newFormat = engine.inputNode.inputFormat(forBus: 0)
    guard newFormat.sampleRate > 0, newFormat.channelCount > 0 else { return }
    engine.inputNode.removeTap(onBus: 0)
    // Reinstall tap with new format... (see ObjC wrapper section below)
}
```

Debounce config changes (200-500ms) - virtual devices like Krisp fire rapid sequences.

### installTap throws ObjC NSException, not Swift Error

`AVAudioEngine.installTap(onBus:)` throws an ObjC `NSException` when the format is incompatible. Swift `do/catch` does NOT catch NSExceptions. A generic `ObjCTryBlock` wrapper also fails because the Swift compiler eliminates the ObjC trampoline for `NS_NOESCAPE` blocks in release builds.

Fix: purpose-built ObjC wrapper methods where the entire throw-to-catch chain is pure ObjC:

```objc
// ObjCExceptionCatcher.h
#import <AVFAudio/AVFAudio.h>
BOOL ObjCInstallTap(AVAudioNode *node, uint32_t bus, uint32_t bufferSize,
                    AVAudioFormat * _Nullable format,
                    void (^block)(AVAudioPCMBuffer *, AVAudioTime *),
                    NSError **outError);
BOOL ObjCStartEngine(AVAudioEngine *engine, NSError **outError);
```

```objc
// ObjCExceptionCatcher.m
BOOL ObjCInstallTap(AVAudioNode *node, uint32_t bus, uint32_t bufferSize,
                    AVAudioFormat *format,
                    void (^block)(AVAudioPCMBuffer *, AVAudioTime *),
                    NSError **outError) {
    @try {
        [node installTapOnBus:bus bufferSize:bufferSize format:format block:block];
        return YES;
    } @catch (NSException *e) {
        if (outError)
            *outError = [NSError errorWithDomain:@"ObjCException" code:-1
                userInfo:@{NSLocalizedDescriptionKey: e.reason ?: e.name}];
        return NO;
    }
}
```

In SPM, create a separate target for the ObjC code:
```swift
.target(
    name: "ObjCExceptionCatcher",
    path: "Sources/ObjCExceptionCatcher",
    publicHeadersPath: "include",
    linkerSettings: [.linkedFramework("AVFAudio")]
)
```

### VPIO aggregate device reports bogus channel counts

`setVoiceProcessingEnabled(true)` reports combined input+output channels (e.g., 9 = mic + speaker). Pass `nil` as format to `installTap` to let VPIO negotiate internally:

```swift
inputNode.installTap(onBus: 0, bufferSize: 1024, format: nil, block: handler)
```

## AVAssetWriter for Audio

**Preferred for ScreenCaptureKit** - accepts CMSampleBuffer directly (no conversion), supports compressed output.

```swift
let writer = try AVAssetWriter(url: outputURL, fileType: .m4a)

let audioSettings: [String: Any] = [
    AVFormatIDKey: kAudioFormatMPEG4AAC,
    AVSampleRateKey: 48000.0,
    AVNumberOfChannelsKey: 2,
    AVEncoderBitRateKey: 128_000
]

let audioInput = AVAssetWriterInput(mediaType: .audio, outputSettings: audioSettings)
audioInput.expectsMediaDataInRealTime = true
writer.add(audioInput)
writer.startWriting()

// In SCStreamOutput callback:
func handleAudio(_ sampleBuffer: CMSampleBuffer) {
    if !sessionStarted {
        writer.startSession(atSourceTime: sampleBuffer.presentationTimeStamp)
        sessionStarted = true
    }
    if audioInput.isReadyForMoreMediaData {
        audioInput.append(sampleBuffer)
    }
}

// Stop
audioInput.markAsFinished()
await writer.finishWriting()
```

File types: `.m4a` (AAC/ALAC), `.mov` (PCM/AAC/ALAC), `.mp4` (AAC), `.wav` (PCM), `.caf` (any).

Pass `nil` for `outputSettings` to write without re-encoding (pass-through).

## AVAssetWriter Crash Safety

### movieFragmentInterval for crash recovery

Writes fragment headers periodically, making partial files recoverable after crashes or force-kills. Works with `.m4a` container (empirically verified - not just `.mov`):

```swift
writer.movieFragmentInterval = CMTime(seconds: 10, preferredTimescale: 600)
```

A force-killed recording produces a valid file with audio up to the last fragment boundary (~10s max data loss).

### expectsMediaDataInRealTime is critical

Always set `expectsMediaDataInRealTime = true` on inputs, even for post-processing pipelines. Without it, the writer applies internal backpressure that can deadlock synchronous polling loops:

```swift
audioInput.expectsMediaDataInRealTime = true // Prevents backpressure deadlock
```

### Guard writer status in polling loops

After `input.append()` fails, the writer enters `.failed` state and `isReadyForMoreMediaData` returns `false` forever. Without a status guard, polling loops hang infinitely:

```swift
// BAD - hangs forever if writer fails:
while !input.isReadyForMoreMediaData { usleep(10_000) }

// GOOD - break on writer failure:
while !input.isReadyForMoreMediaData {
    guard writer.status == .writing else { break }
    usleep(10_000)
}
```

### Session start timing for multi-track recording

With dual-track (system audio + mic), start the session on the first system audio sample. Gate mic buffer appending on a `sessionStarted` flag. Mic samples arriving before session start must be dropped:

```swift
func handleSystemAudio(_ sampleBuffer: CMSampleBuffer) {
    if !sessionStarted {
        writer.startSession(atSourceTime: sampleBuffer.presentationTimeStamp)
        sessionStarted = true
    }
    systemInput.append(sampleBuffer)
}

func handleMic(_ sampleBuffer: CMSampleBuffer) {
    guard sessionStarted else { return } // Drop pre-session mic samples
    micInput.append(sampleBuffer)
}
```

### Channel count mismatch causes silent audio

Output settings must match actual input format. AVAudioEngine delivers mono (1ch) mic audio. Configuring the writer input for stereo (2ch) causes silent output with 100% append success rate:

```swift
// System audio: 2ch stereo
let systemSettings: [String: Any] = [
    AVFormatIDKey: kAudioFormatMPEG4AAC,
    AVNumberOfChannelsKey: 2, AVEncoderBitRateKey: 128_000, ...
]
// Mic audio: 1ch mono (matches AVAudioEngine input)
let micSettings: [String: Any] = [
    AVFormatIDKey: kAudioFormatMPEG4AAC,
    AVNumberOfChannelsKey: 1, AVEncoderBitRateKey: 64_000, ...
]
```

### CMBlockBuffer memory trap

Never use `CMBlockBufferCreateWithMemoryBlock` with `flags: 0` and `memoryBlock: nil` - this defers memory allocation and `CMBlockBufferReplaceDataBytes` writes to uninitialized memory. Use `kCMBlockBufferAssureMemoryNowFlag` or the `CMSampleBufferSetDataBufferFromAudioBufferList` pattern (see next section).

## AVAudioFile for Audio

Simpler but PCM-only, requires CMSampleBuffer-to-AVAudioPCMBuffer conversion.

```swift
let settings: [String: Any] = [
    AVFormatIDKey: kAudioFormatLinearPCM,
    AVSampleRateKey: 48000.0,
    AVNumberOfChannelsKey: 2,
    AVLinearPCMBitDepthKey: 32,
    AVLinearPCMIsFloatKey: true,
    AVLinearPCMIsBigEndianKey: false,
    AVLinearPCMIsNonInterleaved: false
]

let audioFile = try AVAudioFile(
    forWriting: url,
    settings: settings,
    commonFormat: .pcmFormatFloat32,
    interleaved: false  // AVAudioFile requires non-interleaved
)

// In callback, after converting CMSampleBuffer to AVAudioPCMBuffer:
try audioFile.write(from: pcmBuffer)

// Close by setting to nil
audioFile = nil
```

**`settings`** = file format on disk. **`commonFormat`** = processing format of buffers passed to `write(from:)`.

## CMSampleBuffer to AVAudioPCMBuffer

```swift
extension AVAudioPCMBuffer {
    static func from(_ sampleBuffer: CMSampleBuffer) -> AVAudioPCMBuffer? {
        guard let formatDescription = CMSampleBufferGetFormatDescription(sampleBuffer) else {
            return nil
        }
        let numSamples = CMSampleBufferGetNumSamples(sampleBuffer)
        let avFormat = AVAudioFormat(cmAudioFormatDescription: formatDescription)

        guard let pcmBuffer = AVAudioPCMBuffer(
            pcmFormat: avFormat,
            frameCapacity: AVAudioFrameCount(numSamples)
        ) else { return nil }

        pcmBuffer.frameLength = AVAudioFrameCount(numSamples)
        CMSampleBufferCopyPCMDataIntoAudioBufferList(
            sampleBuffer, at: 0, frameCount: Int32(numSamples),
            into: pcmBuffer.mutableAudioBufferList
        )
        return pcmBuffer
    }
}
```

Modern Swift alternative using `copyPCMData(fromRange:into:)`:

```swift
try sampleBuffer.copyPCMData(
    fromRange: 0..<CMSampleBufferGetNumSamples(sampleBuffer),
    into: pcmBuffer.mutableAudioBufferList
)
```

## AVAudioPCMBuffer to CMSampleBuffer (for AVAssetWriter)

When writing AVAudioEngine tap output to AVAssetWriter, convert `AVAudioPCMBuffer` to `CMSampleBuffer`. Let CoreMedia manage block buffer memory:

```swift
func makeSampleBuffer(from pcmBuffer: AVAudioPCMBuffer, time: AVAudioTime) -> CMSampleBuffer? {
    let format = pcmBuffer.format
    let frameCount = pcmBuffer.frameLength

    guard let formatDesc = format.formatDescription else { return nil }

    var sampleBuffer: CMSampleBuffer?
    var timing = CMSampleTimingInfo(
        duration: CMTime(value: 1, timescale: Int32(format.sampleRate)),
        presentationTimeStamp: CMTime(
            seconds: AVAudioTime.seconds(forHostTime: time.hostTime),
            preferredTimescale: 600
        ),
        decodeTimeStamp: .invalid
    )

    // Create empty sample buffer
    guard CMSampleBufferCreate(
        allocator: kCFAllocatorDefault, dataBuffer: nil, dataReady: false,
        makeDataReadyCallback: nil, refcon: nil,
        formatDescription: formatDesc,
        sampleCount: CMItemCount(frameCount),
        sampleTimingEntryCount: 1, sampleTimingArray: &timing,
        sampleSizeEntryCount: 0, sampleSizeArray: nil,
        sampleBufferOut: &sampleBuffer
    ) == noErr, let sb = sampleBuffer else { return nil }

    // Attach audio data (CoreMedia manages block buffer memory)
    guard CMSampleBufferSetDataBufferFromAudioBufferList(
        sb, blockBufferAllocator: kCFAllocatorDefault,
        blockBufferMemoryAllocator: kCFAllocatorDefault,
        flags: 0, bufferList: pcmBuffer.audioBufferList
    ) == noErr else { return nil }

    return sb
}
```

## Audio Format Settings

| Constant | Value | Container |
|----------|-------|-----------|
| `kAudioFormatLinearPCM` | Uncompressed PCM | WAV, CAF, AIFF |
| `kAudioFormatMPEG4AAC` | AAC (lossy) | M4A, MP4 |
| `kAudioFormatAppleLossless` | ALAC (lossless) | M4A, CAF |
| `kAudioFormatFLAC` | FLAC lossless | FLAC, CAF |

Common settings:

```swift
// WAV (16-bit PCM)
[AVFormatIDKey: kAudioFormatLinearPCM, AVSampleRateKey: 48000.0,
 AVNumberOfChannelsKey: 2, AVLinearPCMBitDepthKey: 16,
 AVLinearPCMIsFloatKey: false, AVLinearPCMIsBigEndianKey: false]

// M4A (AAC)
[AVFormatIDKey: kAudioFormatMPEG4AAC, AVSampleRateKey: 48000.0,
 AVNumberOfChannelsKey: 2, AVEncoderBitRateKey: 128_000]

// M4A (Apple Lossless)
[AVFormatIDKey: kAudioFormatAppleLossless, AVSampleRateKey: 48000.0,
 AVNumberOfChannelsKey: 2, AVEncoderBitDepthHintKey: 16]
```

**AVAssetWriter note**: For `kAudioFormatLinearPCM` output, all `AVLinearPCM*` keys are required. For `kAudioFormatMPEG4AAC`, `AVEncoderBitRateKey` is required (`AVEncoderBitRatePerChannelKey` is NOT supported).

## Permissions

### Screen recording (TCC)

Screen capture has NO dedicated entitlement. It is governed entirely by macOS TCC runtime permission.

```swift
// Check (macOS 11+, does NOT trigger prompt)
let hasAccess = CGPreflightScreenCaptureAccess()

// Request (triggers system prompt once)
CGRequestScreenCaptureAccess()

// Or: calling SCShareableContent also triggers the prompt
let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
```

After granting permission, app restart is typically required.

### macOS 15+ recurring prompts

macOS 15 Sequoia shows monthly re-authorization prompts. Options:
- Use `SCContentSharingPicker` (Apple's preferred approach)
- Request `com.apple.developer.persistent-content-capture` entitlement from Apple (VNC/remote desktop apps)
- MDM: `forceBypassScreenCaptureAlert` key (enterprise only)

### Audio capture permissions

| Audio Type | Permission | Entitlement |
|-----------|-----------|-------------|
| System/app audio via ScreenCaptureKit | Screen Recording (TCC) | None |
| Microphone via AVFoundation | Microphone (TCC) | `com.apple.security.device.audio-input` (Hardened Runtime) |
| Microphone via ScreenCaptureKit (macOS 15+) | Both Screen Recording + Microphone | `com.apple.security.device.audio-input` + `NSMicrophoneUsageDescription` |

Microphone permission check:

```swift
switch AVCaptureDevice.authorizationStatus(for: .audio) {
case .authorized: proceed()
case .notDetermined:
    let granted = await AVCaptureDevice.requestAccess(for: .audio)
case .denied, .restricted:
    // Direct to System Settings
    NSWorkspace.shared.open(URL(string:
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone")!)
}
```

### Entitlements for capture apps

Non-sandboxed (Developer ID):

```xml
<dict>
    <key>com.apple.security.device.audio-input</key>
    <true/>
</dict>
```

Sandboxed (App Store):

```xml
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.device.microphone</key>
    <true/>
    <key>com.apple.security.device.audio-input</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
</dict>
```

Info.plist (required for microphone):

```xml
<key>NSMicrophoneUsageDescription</key>
<string>Record audio alongside screen capture.</string>
```

### Open settings programmatically

```swift
// Screen Recording
NSWorkspace.shared.open(URL(string:
    "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture")!)
// Microphone
NSWorkspace.shared.open(URL(string:
    "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone")!)
```

### Reset permissions (development)

```bash
tccutil reset ScreenCapture com.yourcompany.yourapp
tccutil reset Microphone com.yourcompany.yourapp
```

## TCC Operational Gotchas

### Ad-hoc signing resets TCC on every rebuild

Ad-hoc signing (`codesign --sign -`) generates a different CDHash each build. TCC identifies ad-hoc apps by CDHash, so permissions reset on every rebuild. Fix: use a self-signed development certificate - TCC then uses the designated requirement (cert + bundle ID), and permissions persist across rebuilds.

```bash
# Create self-signed dev cert (one-time)
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes \
    -subj "/CN=My Development"
security import cert.pem -k ~/Library/Keychains/login.keychain-db
security import key.pem -k ~/Library/Keychains/login.keychain-db
```

### Terminal attribution

Running a compiled binary from the terminal attributes Screen Recording permission to the terminal app (e.g., WezTerm, Terminal.app), not the actual app. Always test via `.app` bundle (`open MyApp.app`), not direct binary execution.

### Bare binaries cannot get Screen Recording

Standalone binaries without a `.app` bundle and `CFBundleIdentifier` in Info.plist cannot reliably get Screen Recording permission on modern macOS. TCC expects a proper bundle. Wrap test binaries in a minimal `.app` with Info.plist.

### Two separate TCC entries for microphone

`SCStreamConfiguration.captureMicrophone = true` and `AVCaptureDevice.requestAccess(for: .audio)` create separate TCC entries under different services (`kTCCServiceScreenCapture` vs `kTCCServiceMicrophone`). Both must be granted. System Settings Microphone pane shows both.

### CGRequestScreenCaptureAccess timing

Do NOT call `CGRequestScreenCaptureAccess()` in `App.init()` - macOS attributes the permission to the parent process (terminal). Call it in `applicationDidFinishLaunching` when the app bundle is fully registered.

### Permission status vs action

For `.notDetermined`: trigger `AVCaptureDevice.requestAccess()` (shows system dialog). For `.denied`: redirect to System Settings (user must toggle manually). Don't open Settings for `.notDetermined` - the system dialog is a better UX.

### Refresh permission state when app reactivates

Permission state checked in `onAppear` becomes stale after user switches to Settings and back:

```swift
.onAppear { refreshPermissions() }
.onReceive(NotificationCenter.default.publisher(
    for: NSApplication.didBecomeActiveNotification
)) { _ in refreshPermissions() }
```

### Screen Recording permission requires restart

After granting Screen Recording in System Settings, macOS shows "Quit & Reopen". This is unavoidable system behavior. Design onboarding so Screen Recording is the last permission step, framing the restart as "setup complete."

## Complete Examples

### Audio-only recorder for specific apps

```swift
import ScreenCaptureKit
import AVFoundation

class AppAudioRecorder: NSObject, SCStreamOutput, SCStreamDelegate {
    private var stream: SCStream?
    private var writer: AVAssetWriter?
    private var audioInput: AVAssetWriterInput?
    private var sessionStarted = false
    private let audioQueue = DispatchQueue(label: "AudioCapture")

    func startRecording(appBundleID: String, to url: URL) async throws {
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
        guard let display = content.displays.first,
              let app = content.applications.first(where: { $0.bundleIdentifier == appBundleID })
        else { throw CaptureError.appNotFound }

        let filter = SCContentFilter(display: display, including: [app], exceptingWindows: [])

        let config = SCStreamConfiguration()
        config.capturesAudio = true
        config.sampleRate = 48000
        config.channelCount = 2
        config.excludesCurrentProcessAudio = true
        config.width = 2
        config.height = 2
        config.minimumFrameInterval = CMTime(value: 1, timescale: CMTimeScale.max)

        writer = try AVAssetWriter(url: url, fileType: .m4a)
        audioInput = AVAssetWriterInput(mediaType: .audio, outputSettings: [
            AVFormatIDKey: kAudioFormatMPEG4AAC,
            AVSampleRateKey: 48000.0,
            AVNumberOfChannelsKey: 2,
            AVEncoderBitRateKey: 128_000
        ])
        audioInput!.expectsMediaDataInRealTime = true
        writer!.add(audioInput!)
        writer!.startWriting()

        stream = SCStream(filter: filter, configuration: config, delegate: self)
        try stream!.addStreamOutput(self, type: .screen, sampleHandlerQueue: nil)
        try stream!.addStreamOutput(self, type: .audio, sampleHandlerQueue: audioQueue)
        try await stream!.startCapture()
    }

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer,
                of type: SCStreamOutputType) {
        guard type == .audio, sampleBuffer.isValid,
              let input = audioInput, input.isReadyForMoreMediaData else { return }

        if !sessionStarted {
            writer?.startSession(atSourceTime: sampleBuffer.presentationTimeStamp)
            sessionStarted = true
        }
        input.append(sampleBuffer)
    }

    func stopRecording() async {
        try? await stream?.stopCapture()
        stream = nil
        audioInput?.markAsFinished()
        await writer?.finishWriting()
        writer = nil
        sessionStarted = false
    }

    func stream(_ stream: SCStream, didStopWithError error: Error) {
        Task { await stopRecording() }
    }

    enum CaptureError: Error { case appNotFound }
}
```

### Full display recording with SCRecordingOutput (macOS 15+)

```swift
import ScreenCaptureKit
import AVFoundation

@available(macOS 15.0, *)
class DisplayRecorder: NSObject, SCStreamDelegate, SCRecordingOutputDelegate {
    private var stream: SCStream?
    private var recordingOutput: SCRecordingOutput?

    func startRecording(to url: URL) async throws {
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
        guard let display = content.displays.first else { return }

        let excludeSelf = content.applications.filter {
            $0.bundleIdentifier == Bundle.main.bundleIdentifier
        }
        let filter = SCContentFilter(
            display: display, excludingApplications: excludeSelf, exceptingWindows: []
        )

        let config = SCStreamConfiguration()
        config.width = display.width * 2
        config.height = display.height * 2
        config.minimumFrameInterval = CMTime(value: 1, timescale: 60)
        config.capturesAudio = true
        config.sampleRate = 48000
        config.channelCount = 2
        config.excludesCurrentProcessAudio = true

        let recordingConfig = SCRecordingOutputConfiguration()
        recordingConfig.outputURL = url
        recordingConfig.outputFileType = .mov
        recordingConfig.videoCodecType = .hevc

        stream = SCStream(filter: filter, configuration: config, delegate: self)
        recordingOutput = SCRecordingOutput(configuration: recordingConfig, delegate: self)
        try stream!.addRecordingOutput(recordingOutput!)
        try await stream!.startCapture()
    }

    func stopRecording() async throws {
        try await stream?.stopCapture()
        stream = nil
        recordingOutput = nil
    }

    func recordingOutputDidStartRecording(_ output: SCRecordingOutput) { }
    func recordingOutputDidFinishRecording(_ output: SCRecordingOutput) { }
    func recordingOutput(_ output: SCRecordingOutput, didFailWithError error: Error) { }
    func stream(_ stream: SCStream, didStopWithError error: Error) { }
}
```

## API Availability

| API | Minimum macOS |
|-----|--------------|
| SCShareableContent, SCContentFilter, SCStream, SCStreamOutput | 12.3 |
| SCStreamConfiguration.capturesAudio | 12.3 |
| SCContentSharingPicker, SCScreenshotManager | 14.0 |
| SCRecordingOutput, SCStreamOutputType.microphone | 15.0 |
| HDR capture, configuration presets | 15.0 |
