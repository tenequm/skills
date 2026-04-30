# Screen Capture & Audio Recording

For per-process system audio without ScreenCaptureKit (call recording, background taps), see `core-audio-tap.md` - CATap is the lower-overhead alternative and has its own HFP / aggregate-device pitfalls.

## Table of Contents
- SCShareableContent - Content Discovery
- SCContentFilter - Filtering
- SCStream & SCStreamConfiguration
- SCStreamOutput - Receiving Samples
- SCStream Production Gotchas
- SCStream Teardown Gotchas
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

Full mapping from `SCError.h` in the macOS 26 SDK. Source (local path on any machine with Xcode 26 installed): `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/System/Library/Frameworks/ScreenCaptureKit.framework/Versions/A/Headers/SCError.h`. API docs: https://developer.apple.com/documentation/screencapturekit/scstreamerrorcode

| Code | Enum case | Since | Meaning |
|------|-----------|-------|---------|
| -3801 | `userDeclined` | 12.3 | User did not authorize capture (TCC) |
| -3802 | `failedToStart` | 12.3 | Stream failed to start (generic) |
| -3803 | `missingEntitlements` | 12.3 | Missing required entitlements |
| -3804 | `failedApplicationConnectionInvalid` | 12.3 | Recording connection became invalid |
| -3805 | `failedApplicationConnectionInterrupted` | 12.3 | Recording connection was interrupted |
| -3806 | `failedNoMatchingApplicationContext` | 12.3 | Context id does not match application |
| -3807 | `attemptToStartStreamState` | 12.3 | Start attempted on a stream already running |
| -3808 | `attemptToStopStreamState` | 12.3 | Stop attempted on a stream already stopped |
| -3809 | `attemptToUpdateFilterState` | 12.3 | Update-filter attempted on stopped stream |
| -3810 | `attemptToConfigState` | 12.3 | Update-config attempted on stopped stream |
| -3811 | `internalError` | 12.3 | Video/audio capture failure |
| -3812 | `invalidParameter` | 12.3 | Invalid parameter |
| -3813 | `noWindowList` | 12.3 | No window list available |
| -3814 | `noDisplayList` | 12.3 | No display list available |
| -3815 | `noCaptureSource` | 12.3 | No display or window list to capture |
| -3816 | `removingStream` | 12.3 | Failed to remove stream |
| -3817 | `userStopped` | 12.3 | User stopped via system UI |
| -3818 | `failedToStartAudioCapture` | 13.0 | Audio capture failed to start |
| -3819 | `failedToStopAudioCapture` | 13.0 | Audio capture failed to stop |
| -3820 | `failedToStartMicrophoneCapture` | 15.0 | Microphone capture failed to start |
| -3821 | `systemStoppedStream` | 15.0 | System stopped the stream (sleep/wake, policy) |

Recovery rules of thumb: `-3801` / `-3803` → permission or entitlement problem, stop and prompt user. `-3817` → user intent, save and stop. `-3818` / `-3820` → restart without the offending track. `-3821` → wait ~1 s and restart with a new stream. Rate-limit restarts (e.g. max 3 in 30 s) to prevent infinite loops. Remember SCStream is not reusable after error — destroy and recreate.

Keep `mappedStartError` and the stop-time error handler in sync - in practice they drift (stop-time maps -3801/-3802/-3821, start-time only maps -3801), producing misleading user-facing error messages.

## SCStream Teardown Gotchas

Teardown is the phase where SCStream apps lose files, hang, and leak state. Three patterns worth internalizing.

### `stopCapture()` can hang; wrap it in a timeout

Under WindowServer stalls or TCC-revoked mid-stream state, `try await stream.stopCapture()` can block for 10+ seconds. `applicationShouldTerminate:` gives the app ~8 seconds total before force-kill, so an unguarded `stopCapture` call blows the budget and the writer never finalizes (partial file, or nothing).

Wrap it in a bounded `withTimeout`:

```swift
func stopSafely() async {
    _ = await withTimeout(seconds: 3) {
        try? await self.stream?.stopCapture()
    }
    self.audioInput?.markAsFinished()
    _ = await withTimeout(seconds: 3) {
        await self.writer?.finishWriting()
    }
}

func withTimeout<T: Sendable>(seconds: TimeInterval,
                              _ op: @escaping @Sendable () async -> T) async -> T? {
    await withTaskGroup(of: T?.self) { group in
        group.addTask { await op() }
        group.addTask {
            try? await Task.sleep(for: .seconds(seconds))
            return nil
        }
        let result = await group.next() ?? nil
        group.cancelAll()
        return result
    }
}
```

### Assign the stream reference *before* awaiting `startCapture()`

```swift
// FRAGILE: if TCC was revoked between preflight and start, catch cannot cleanly stop.
func start() async throws {
    let s = SCStream(filter: filter, configuration: config, delegate: self)
    try s.addStreamOutput(self, type: .audio, sampleHandlerQueue: audioQueue)
    do {
        try await s.startCapture()
        self.stream = s // assigned after success only
    } catch {
        // 's' is out of scope or half-initialized; hard to drive cleanup.
        throw error
    }
}

// BETTER: assign first, so the catch can drive teardown uniformly.
func start() async throws {
    let s = SCStream(filter: filter, configuration: config, delegate: self)
    try s.addStreamOutput(self, type: .audio, sampleHandlerQueue: audioQueue)
    self.stream = s
    do {
        try await s.startCapture()
    } catch {
        await self.stopSafely() // cleans up self.stream uniformly
        throw error
    }
}
```

**Trade-off**: assigning before `startCapture` exposes a short window where `self.stream` is non-nil but not yet capturing. A concurrent `stop()` during that window must be tolerant of `stopCapture()` on an unstarted stream (SCStream handles this, but the undocumented error path is worth a test).

### Prefer `SCShareableContent.current` over `excludingDesktopWindows(false, false)` in restart paths

`SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: false)` is the slow variant - it enumerates off-screen windows, virtual desktops, and minimized windows. Auto-restart paths (up to 3 restarts in 30 s after `.systemStopped`) that re-query this on every attempt produce visible UI stalls.

For audio streams you typically don't need the window list at all; cache the display handle at first start and reuse it. When you do need a fresh enumeration, prefer the narrower `SCShareableContent.current` (macOS 14+) or `excludingDesktopWindows(true, onScreenWindowsOnly: true)`.

```swift
// Keep this cached across restarts:
private var cachedDisplay: SCDisplay?

func refreshDisplayIfNeeded() async throws -> SCDisplay {
    if let d = cachedDisplay { return d }
    let content = try await SCShareableContent.current // fast
    guard let d = content.displays.first else { throw CaptureError.noDisplay }
    cachedDisplay = d
    return d
}
```

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

**ScreenCaptureKit has no documented audio-only mode, but `.audio`-only streams work in practice.** You can create an `SCStream` with `capturesAudio = true` and attach only `addStreamOutput(_:type:.audio,...)` - no `.screen` output. Audio buffers flow. Validated across macOS 14/15/26 in multiple shipping apps (Aperture, Blackbox across v0.3/v0.4/v0.6/v0.8, etc.).

Two caveats that are real but not fatal:
1. The framework logs `stream output NOT found. Dropping frame` to the console for every video frame because the **video pipeline still runs** internally even without a `.screen` consumer. Purely cosmetic noise, but it'll appear in Console.app.
2. That same still-running video pipeline costs CPU/GPU. Mitigate by collapsing the video work to a stub (see below) even though you're not consuming it.

**Do not reach for CATap as the "zero-overhead" replacement without reading `core-audio-tap.md` first.** Production experience (one call-recorder shipped CATap in v0.7.0 and reverted to display-wide SCStream in v0.8.0 five days later) shows CATap has structural clock-fragility: its IO proc is driven by the hardware output clock, so when that clock is idle, pinned by Bluetooth HFP, or stalled, buffers stop flowing silently. Display-wide SCStream's clock comes from the OS-composited mix and is decoupled from hardware output, making it more robust for long-duration recording even with the cosmetic video-pipeline overhead. CATap is the right tool when you specifically need sub-20 ms capture latency (real-time AEC, live analysis); for disk-bound recording workloads (calls, meetings, lectures), SCStream wins on reliability.

If you stay with SCStream audio-only, minimize the hidden video work:

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

// For audio-only, add only the .audio output. For combined capture:
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

### AVAssetWriterInput format is immutable after the first append

The internal AAC encoder configures itself from the **first** appended sample buffer's format description. Appending a buffer with a different format later causes `append()` to fail silently (returns `false` and the writer eventually enters `.failed` state, losing **both** tracks in a dual-track output).

This matters concretely when the mic device changes mid-recording:
- AVAudioEngine rebuilds its tap on `AVAudioEngineConfigurationChange` with whatever the new device's native format is (different sample rate, channel count).
- If you let that new format flow into the writer input directly, the writer goes to `.failed`.

The fix: **resample/downmix into a fixed target format** (e.g. mono 48 kHz Float32) before appending, and reinstall the tap with whatever source format the device dictates. One production-hardened path: mic tap → `resampleToMono48k()` (linear interpolation, any source rate → 48 kHz mono) → `asSampleBuffer()` → writer input. System track (SCStream) bypasses resampling since SCStream always delivers at the configured `sampleRate`/`channelCount` regardless of hardware.

### AVAssetWriter collapses PTS gaps; fill with explicit silence

No AVAssetWriter property makes it preserve gaps between buffers. If buffer A ends at t=10.0 s and buffer B arrives with PTS=12.5 s, the AAC encoder writes them back-to-back and the track ends up 2.5 s shorter than it should be. In a dual-track recording this manifests as one track being seconds shorter than the other, growing over the course of the recording.

Detection / fill pattern (run on the same queue as `append`, per input):

```swift
actor TrackState {
    var nextExpectedPTS: CMTime = .invalid
    let input: AVAssetWriterInput
    let silenceFormat: CMFormatDescription   // clean LPCM, built once

    func append(_ sample: CMSampleBuffer) {
        let incoming = CMSampleBufferGetPresentationTimeStamp(sample)
        if nextExpectedPTS.isValid,
           CMTimeCompare(incoming, nextExpectedPTS) > 0,
           CMTimeGetSeconds(incoming - nextExpectedPTS) > 0.005 {
            fillGap(from: nextExpectedPTS, to: incoming)
        }
        if input.isReadyForMoreMediaData {
            input.append(sample)
        }
        let dur = CMSampleBufferGetDuration(sample)
        nextExpectedPTS = incoming + dur
    }

    private func fillGap(from start: CMTime, to end: CMTime) {
        // Write SMALL chunks (~1024 samples each). One big silent buffer spanning
        // the whole gap causes kCMSampleBufferError_ArrayTooSmall (-12737) or
        // crashes the AAC encoder. Bail out on any failure - never risk the
        // real buffer to chase gap accuracy.
        var cursor = start
        while CMTimeCompare(cursor, end) < 0, input.isReadyForMoreMediaData {
            let silent = makeSilentSampleBuffer(at: cursor, frames: 1024,
                                                 format: silenceFormat)
            if !input.append(silent) { break }
            cursor = cursor + CMTime(value: 1024, timescale: 48_000)
        }
    }
}
```

Three constraints the pattern *must* respect:
1. **Write silence in small chunks** matching normal buffer cadence (~1024 samples at 48 kHz). One large silent buffer covering the full gap fails with `kCMSampleBufferError_ArrayTooSmall` or crashes the AAC encoder.
2. **Build a clean LPCM `CMFormatDescription` from scratch** for the silence (Float32, packed, interleaved, no channel-layout extensions). Do NOT reuse the format description from pipeline buffers - they may carry channel layouts or non-interleaved flags that don't match a flat zero-filled block buffer, and `input.append()` will reject or the writer will fail.
3. **Never block the real buffer on gap-fill success.** If silence `append` fails or `isReadyForMoreMediaData` goes false mid-fill, break out and still try the real buffer. Accept partial desync over data loss. Log the partial fill for diagnostics.

Gap detection threshold >5 ms (240 samples at 48 kHz) avoids false positives from normal PTS jitter.

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

**If audio is silent after the conversion, check this first.** SCStream on macOS 26 delivers Float32 stereo as **non-interleaved** (two separate buffers in the `AudioBufferList`). Code written for interleaved layout that `memcpy`s the `CMBlockBuffer` bytes into `floatChannelData[0]` produces a valid-looking PCM buffer that decodes as silence / garbage. This has silently killed multi-minute recordings in production.

The safe one-liner: let CoreMedia copy into the `AudioBufferList` and handle both layouts:

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
        // Handles both interleaved and non-interleaved source layouts.
        CMSampleBufferCopyPCMDataIntoAudioBufferList(
            sampleBuffer, at: 0, frameCount: Int32(numSamples),
            into: pcmBuffer.mutableAudioBufferList
        )
        return pcmBuffer
    }
}
```

Better yet for AVAssetWriter destinations: **skip the conversion entirely** and append the `CMSampleBuffer` directly to a stereo AAC `AVAssetWriterInput` (see "AVAssetWriter for Audio"). Passthrough is both simpler and avoids every class of PCM-layout bug.

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

### macOS 26 TCC pane layout

The pane is labeled **"Screen & System Audio Recording"** on macOS 14 Sonoma and later (it was renamed from "Screen Recording" in Sonoma; macOS 15.x and 26.x inherit the same label). On macOS 26 there is a separate "System Audio Recording Only" subsection below the main list. Granting Screen Recording on 26 implicitly grants system-audio capture; on 14/15 the `kTCCServiceAudioCapture` service is distinct from `kTCCServiceScreenCapture` — preflighting one does not answer for the other.

The canonical deep-link prefix is `com.apple.settings.PrivacySecurity.extension` on macOS 26; the legacy `com.apple.preference.security` prefix still opens *something*, but on 26 it lands on the top Privacy pane rather than the subpane. Also: the `Privacy_AudioCapture` anchor lands on an inactive pane when the capturing app uses SCStream - use `Privacy_ScreenCapture` for anything SCStream-based.

### Open settings programmatically

To avoid 5-site string duplication (and the Audio-vs-Screen URL drift that duplication invites), centralize the URLs in a small enum:

```swift
enum SystemPreferenceURL: String {
    case screenCapture = "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_ScreenCapture"
    case microphone   = "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Microphone"
    case notifications = "x-apple.systempreferences:com.apple.preference.notifications"
    case accessibility = "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Accessibility"
    case loginItems    = "x-apple.systempreferences:com.apple.LoginItems-Settings.extension"

    var url: URL { URL(string: rawValue)! }
    func open() { NSWorkspace.shared.open(url) }
}

// Usage:
SystemPreferenceURL.screenCapture.open()
```

### Reset permissions (development)

```bash
tccutil reset ScreenCapture com.yourcompany.yourapp
tccutil reset Microphone com.yourcompany.yourapp
```

## TCC Operational Gotchas

### `CGPreflightScreenCaptureAccess` vs `CGRequestScreenCaptureAccess`

Two superficially similar APIs with very different UX:

| Call | Triggers dialog | Triggers "app will relaunch" | Use when |
|------|-----------------|------------------------------|----------|
| `CGPreflightScreenCaptureAccess()` | No | No | Every permission-sensitive UI refresh. Cheap. |
| `CGRequestScreenCaptureAccess()` | Yes (once) | Yes | Exactly once during onboarding, at the step the user sees. |

Call the preflight on every recording start and on `didBecomeActive` rather than caching a `UserDefaults` flag - the user can revoke permission between launches, and a stale cached flag leads to silent recordings with no error surface.

Call `CGRequestScreenCaptureAccess()` at the onboarding *step* (the "Grant Screen Recording" screen), not at "Complete Setup". Users who click "Open System Settings" before hitting "Complete Setup" otherwise never trigger the in-app request path, and your onboarding behaves asymmetrically with mic / notifications (which fire per step).

### Reinstalling via force-recursive replace (rm&#8209;rf + cp&#8209;R) can leave TCC in a degraded state

TCC is keyed by code-signature CDHash. When you replace `/Applications/Blackbox.app` via a force-recursive delete of `/Applications/App.app` followed by `cp -R ./export/App.app /Applications/`, TCC *remembers* the grant (same Developer ID, same CDHash) but content delivery can be broken - permission reads as authorized, `SCStream` starts without error, buffers flow at zero amplitude (RMS stays at `-inf`).

There is no programmatic recovery. Direct-reading `~/Library/Application Support/com.apple.TCC/TCC.db` is blocked by SIP. The remediation the user must take:

1. System Settings → Privacy & Security → Screen & System Audio Recording
2. Toggle the app **off**, then **on** again

Design your installer / update path accordingly - prefer an in-place overwrite (let the OS handle the inode swap) or run a `tccutil reset ScreenCapture $BUNDLE_ID` from a signed installer, rather than a force-recursive replace (rm&#8209;rf + cp). For `make install` dev scripts, always `killall App` before replacing the bundle, otherwise the still-running process keeps executing from its unlinked inode and `open -a` brings the stale instance to front instead of launching the new one.

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
