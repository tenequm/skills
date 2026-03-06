# Screen Capture & Audio Recording

## Table of Contents
- SCShareableContent - Content Discovery
- SCContentFilter - Filtering
- SCStream & SCStreamConfiguration
- SCStreamOutput - Receiving Samples
- SCRecordingOutput (macOS 15+)
- SCContentSharingPicker (macOS 14+)
- SCScreenshotManager (macOS 14+)
- Audio-Only Capture Pattern
- AVAssetWriter for Audio
- AVAudioFile for Audio
- CMSampleBuffer to AVAudioPCMBuffer
- Audio Format Settings
- Permissions
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
