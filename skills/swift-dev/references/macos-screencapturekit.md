# ScreenCaptureKit on macOS

Capturing displays, windows and app audio with `SCStream`: content discovery, filters, configuration, outputs, the audio-only pattern, error recovery, teardown, recording/picker/screenshot APIs and Screen Recording TCC.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every Swift block compiled through SIL (`swiftc -emit-sil -target arm64-apple-macos15.0 -swift-version 6`, with and without `-default-isolation MainActor`) so region-isolation errors surface; availability, defaults and error codes read from the macOS 27.0 SDK headers (`SCStream.h`, `SCError.h`, `SCScreenshotManager.h`, `SCRecordingOutput.h`, `SCClipBufferingOutput.h`, `SCRecordingEditor.h`). No capture code was run.

## Contents
- Content discovery and filters
- Configuration
- Stream lifecycle and sample handling
- Audio-only capture pattern
- Production gotchas
- Error codes and recovery
- Teardown gotchas
- SCRecordingOutput, picker, screenshots, clip buffering
- Delegate callbacks and clock sync
- Screen Recording TCC

For writing the audio to disk (AVAssetWriter, AVAudioFile, PCM layout traps, transcription, signing-related TCC breakage) see `macos-audio-pipeline.md`. For per-process taps without ScreenCaptureKit see `macos-core-audio-tap.md`.

**Isolation.** The capture objects in this file are `nonisolated final class Capture: NSObject, SCStreamOutput, SCStreamDelegate, @unchecked Sendable`, with mutable state confined to the sample-handler queue. Write the `nonisolated` explicitly: under `-default-isolation MainActor` (the Xcode 26+ app template default) the class otherwise becomes MainActor-isolated while ScreenCaptureKit calls it on its own queues, and the teardown closures below fail to compile (`non-Sendable type 'SCStream?' ... cannot exit main actor-isolated context`). `SCStream` is not Sendable, and `CMSampleBuffer` and `AVAssetWriter` explicitly mark Sendable unavailable, so keep each one on a single queue rather than passing it between tasks.

ScreenCaptureKit also ships on iOS 27, but as a picker-driven subset: no `SCShareableContent`, no display/window filters, no `minimumFrameInterval`; the user picks content via `SCContentSharingPicker.shared.presentForCurrentApplication()` and the picker can expose mic/camera toggles (`showsMicrophoneControl`, `showsCameraControl`). Everything below is macOS.

## Content discovery and filters

```swift
let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
guard let display = content.displays.first else { throw CaptureError.noDisplay }
// content.displays: displayID, width, height
// content.applications: bundleIdentifier, applicationName, processID
// content.windows: windowID, title, isOnScreen, owningApplication
```

The first `SCShareableContent` call triggers the Screen Recording prompt if access is not yet granted (see TCC below).

| Use case | Initializer |
|---|---|
| One window, follows it across displays | `SCContentFilter(desktopIndependentWindow:)` |
| Whole display minus your own app | `SCContentFilter(display:excludingApplications:exceptingWindows:)` |
| Only specific apps | `SCContentFilter(display:including:exceptingWindows:)` |
| Specific windows | `SCContentFilter(display:including:)` |
| Display minus specific windows | `SCContentFilter(display:excludingWindows:)` |

```swift
let mine = content.applications.filter { $0.bundleIdentifier == Bundle.main.bundleIdentifier }
let filter = SCContentFilter(display: display, excludingApplications: mine, exceptingWindows: [])
```

Audio filtering is per application: the filter decides whose audio is captured.

## Configuration

```swift
let config = SCStreamConfiguration()
config.width = 1920                     // default 1920x1080 on macOS
config.height = 1080
config.minimumFrameInterval = CMTime(value: 1, timescale: 60)
config.pixelFormat = kCVPixelFormatType_32BGRA
config.queueDepth = 5                   // default 8, must not exceed 8
config.showsCursor = true

config.capturesAudio = true             // macOS 13+
config.sampleRate = 48_000              // default 48000
config.channelCount = 2                 // default 2
config.excludesCurrentProcessAudio = true

config.captureMicrophone = true         // macOS 15+
config.microphoneCaptureDeviceID = AVCaptureDevice.default(for: .audio)?.uniqueID

config.captureResolution = .best        // macOS 14+
config.captureDynamicRange = .hdrCanonicalDisplay // macOS 15+, Apple silicon only
```

Prefer a preset as the starting point when color space and pixel format must agree, then override fields: `SCStreamConfiguration(preset: .captureHDRStreamCanonicalDisplay)` (macOS 15+; `.captureHDRRecordingPreservedSDRHDR10` is macOS 26+). The header notes HDR recording is not supported: adding an `SCRecordingOutput` to a stream with an HDR dynamic range fails.

Other properties worth knowing:

| Property | Use |
|---|---|
| `sourceRect` / `destinationRect` | Capture a sub-region / place it in the output surface |
| `preservesAspectRatio` | Letterbox instead of stretch (macOS 14+) |
| `showMouseClicks` | Visualize clicks for demo recordings (macOS 15+) |
| `includeChildWindows` | Child windows of a captured window (macOS 14.2+) |
| `capturesShadowsOnly`, `shouldBeOpaque` | Window shadow handling (macOS 14+) |
| `colorMatrix`, `colorSpaceName` | YCbCr matrix (420v/420f only) and output color space |
| `ignoreGlobalClipDisplay` / `ignoreGlobalClipSingleWindow` | Bypass global clipping (macOS 14+) |
| `streamName` | Shows in system UI (macOS 14+) |

## Stream lifecycle and sample handling

```swift
let stream = SCStream(filter: filter, configuration: config, delegate: self)
try stream.addStreamOutput(self, type: .screen, sampleHandlerQueue: videoQueue)
try stream.addStreamOutput(self, type: .audio, sampleHandlerQueue: audioQueue)
try stream.addStreamOutput(self, type: .microphone, sampleHandlerQueue: audioQueue) // macOS 15+
try await stream.startCapture()
try await stream.updateConfiguration(newConfig)   // no restart needed
try await stream.updateContentFilter(newFilter)
try await stream.stopCapture()
```

`SCStream.isCapturing` (macOS 27+) reports the stream's own state; on earlier targets track it yourself.

```swift
func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer,
            of type: SCStreamOutputType) {
    guard sampleBuffer.isValid else { return }
    switch type {
    case .screen: handleVideo(sampleBuffer)
    case .audio: handleAudio(sampleBuffer)
    case .microphone: break
    @unknown default: break
    }
}

func handleVideo(_ sampleBuffer: CMSampleBuffer) {
    guard let attachments = CMSampleBufferGetSampleAttachmentsArray(sampleBuffer, createIfNecessary: false)
            as? [[SCStreamFrameInfo: Any]],
          let rawStatus = attachments.first?[.status] as? Int,
          SCFrameStatus(rawValue: rawStatus) == .complete,  // idle/blank frames carry no new pixels
          let pixelBuffer = sampleBuffer.imageBuffer else { return }
    let image = CIImage(cvPixelBuffer: pixelBuffer)
}
```

Audio arrives as Float32 in the configured `sampleRate`/`channelCount`, and in practice non-interleaved. Converting it to `AVAudioPCMBuffer` has a silent-output trap; use the conversion in `macos-audio-pipeline.md`, or append the `CMSampleBuffer` straight to an `AVAssetWriterInput`.

## Audio-only capture pattern

ScreenCaptureKit has no documented audio-only mode, but a stream with `capturesAudio = true` and only an `.audio` output works in practice (validated across macOS 14, 15 and 26 in several shipping recorders). Two caveats:

1. The video pipeline still runs. With no `.screen` output attached the framework logs `stream output NOT found. Dropping frame` for every frame. Attach a `.screen` output that ignores its buffers, on its own queue so video can never delay audio.
2. That pipeline costs real CPU: every frame is a WindowServer recomposite of the display. At native refresh on a 5K display this measured ~15-20% of a core across the app, `replayd` and WindowServer for the whole recording. Throttle it.

**`minimumFrameInterval` trap.** It is the minimum gap between frames, so larger means fewer frames. `CMTime(value: 1, timescale: CMTimeScale.max)` reads like "infinite interval" but is ~0.5 ns, and the header documents `kCMTimeZero` as "capture at display's native refresh rate" - it requests the maximum frame rate. One shipping recorder ran that line for several releases before a user measured the 60 fps recomposite. `CMTime(value: 1, timescale: 1)` is 1 fps.

```swift
let config = SCStreamConfiguration()
config.capturesAudio = true
config.sampleRate = 48_000
config.channelCount = 2
config.excludesCurrentProcessAudio = true
config.width = 2                                        // minimal video: 2x2 at 1 fps
config.height = 2
config.minimumFrameInterval = CMTime(value: 1, timescale: 1)

let stream = SCStream(filter: filter, configuration: config, delegate: self)
try stream.addStreamOutput(self, type: .screen, sampleHandlerQueue: videoQueue) // ignored, silences the log
try stream.addStreamOutput(self, type: .audio, sampleHandlerQueue: audioQueue)
```

App-specific audio: `SCContentFilter(display:including:exceptingWindows:)` with just the target apps.

**Do not swap in a Core Audio tap as the "zero-overhead" replacement without reading `macos-core-audio-tap.md`.** A call recorder shipped CATap and reverted to display-wide SCStream five days later: the tap's IO proc is clocked by the hardware output device, so an idle, HFP-pinned or stalled output clock silently stops buffers. Display-wide SCStream is clocked from the OS-composited mix and is more robust for long recordings. Use CATap only when you need sub-20 ms latency (live AEC, live analysis).

## Production gotchas

**SCStream is not reusable after an error.** After `didStopWithError` the XPC connection to `replayd` is gone; `startCapture()` on the same object throws `attemptToStartStreamState`. Release it and build a new `SCStream`.

```swift
func stream(_ stream: SCStream, didStopWithError error: any Error) {
    self.stream = nil                                    // never restart the dead stream
    Task { try? await self.restartWithNewStream() }
}
```

**`SCRecordingOutput` stops when you call `updateConfiguration()`** on a running stream. If you need mid-stream config changes (device following, resolution), use `SCStreamOutput` + `AVAssetWriter` instead.

**VPIO and SCStream do not mix.** `setVoiceProcessingEnabled(true)` on an `AVAudioEngine` creates a hidden VPIO aggregate that hooks the system output path for its echo reference and silences SCStream's system audio. It also ducks all other audio by about 20 dB (see `macos-audio-pipeline.md`). Use an independent mic pipeline or post-processing AEC.

**The `.microphone` output is unreliable for dual-track files.** Written as a second `AVAssetWriterInput` next to system audio it produced duration mismatches and corrupted data. Capture the mic with an independent `AVAudioEngine` (`macos-audio-pipeline.md`).

**Multiple streams work.** Two `SCStream`s (say, display-wide plus per-app) can run in one process; each is its own XPC connection and both deliver audio concurrently.

**Virtual audio processors cause echo in display-wide capture.** Krisp, SoundSource and similar re-emit audio ~50 ms late; display-wide capture records both the original and the delayed copy. Use a per-app filter that leaves the processor out.

**Chrome/Electron report a helper as the audio client** (`com.google.Chrome.helper.renderer`). Strip the suffix to find the app for `SCContentFilter`:

```swift
nonisolated func resolveParentBundleID(_ bundleID: String) -> String {
    if let range = bundleID.range(of: ".helper", options: .literal) {
        return String(bundleID[..<range.lowerBound])
    }
    return bundleID
}
```

**Never mutate SCStream's `CMSampleBuffer` in place.** The buffers are framework-managed and may be shared; writing through `CMBlockBufferGetDataPointer` is undefined behavior. Mix by writing separate tracks.

## Error codes and recovery

`SCStreamError.Code` from `SCError.h` (domain `SCStreamErrorDomain`), with the macOS version each appeared in:

| Code | Case | Since | Meaning |
|---|---|---|---|
| -3801 | `userDeclined` | 12.3 | User did not authorize capture (TCC) |
| -3802 | `failedToStart` | 12.3 | Generic start failure |
| -3803 | `missingEntitlements` | 12.3 | Missing entitlements |
| -3804 | `failedApplicationConnectionInvalid` | 12.3 | Recording connection invalid |
| -3805 | `failedApplicationConnectionInterrupted` | 12.3 | Recording connection interrupted |
| -3806 | `failedNoMatchingApplicationContext` | 12.3 | Context id does not match app |
| -3807 | `attemptToStartStreamState` | 12.3 | Start on a stream already running (or dead) |
| -3808 | `attemptToStopStreamState` | 12.3 | Stop on a stream already stopped |
| -3809 | `attemptToUpdateFilterState` | 12.3 | Filter update on a stopped stream |
| -3810 | `attemptToConfigState` | 12.3 | Config update on a stopped stream |
| -3811 | `internalError` | 12.3 | Video/audio capture failure |
| -3812 | `invalidParameter` | 12.3 | Invalid parameter |
| -3813 | `noWindowList` | 12.3 | No window list |
| -3814 | `noDisplayList` | 12.3 | No display list |
| -3815 | `noCaptureSource` | 12.3 | Nothing to capture |
| -3816 | `removingStream` | 12.3 | Failed to remove stream |
| -3817 | `userStopped` | 12.3 | User stopped via system UI |
| -3818 | `failedToStartAudioCapture` | 13.0 | Audio capture failed to start |
| -3819 | `failedToStopAudioCapture` | 13.0 | Audio capture failed to stop |
| -3820 | `failedToStartMicrophoneCapture` | 15.0 | Mic capture failed to start |
| -3821 | `systemStoppedStream` | 15.0 | System stopped it (sleep/wake, policy) |
| -3822 | `insufficientStorage` | 27.0 | Stopped: not enough storage for recording |
| -3823 | `notSupported` | 27.0 | Operation not supported on this platform |

(-3824 `missingBackgroundMode` is iOS/visionOS/tvOS only.)

```swift
let ns = error as NSError
if ns.domain == SCStreamErrorDomain, let code = SCStreamError.Code(rawValue: ns.code) {
    switch code {
    case .userDeclined, .missingEntitlements: break       // stop, send user to Settings
    case .userStopped: break                               // user intent: save and stop
    case .failedToStartAudioCapture, .failedToStartMicrophoneCapture: break // restart without that track
    case .systemStoppedStream: break                       // wait ~1 s, restart with a NEW stream
    default: break
    }
}
```

Rate-limit automatic restarts (for example at most 3 in 30 s) so a persistent failure cannot loop. Keep the start-time and stop-time error mappings in one function: in practice they drift (one shipping app mapped -3801/-3802/-3821 at stop but only -3801 at start) and users get misleading messages.

## Teardown gotchas

Teardown is where SCStream apps lose files, hang and leak state.

**`stopCapture()` can hang.** Under WindowServer stalls or TCC revoked mid-stream it can block 10+ s. `applicationShouldTerminate` leaves roughly 8 s before a force kill, so an unguarded stop means the writer never finalizes. Bound both steps:

```swift
func stopSafely() async {
    _ = await withTimeout(seconds: 3) { try? await self.stream?.stopCapture() }
    audioInput?.markAsFinished()
    _ = await withTimeout(seconds: 3) { await self.writer?.finishWriting() }
}

nonisolated func withTimeout<T: Sendable>(seconds: Double, _ op: @escaping @Sendable () async -> T) async -> T? {
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

**Assign the stream before awaiting `startCapture()`**, so a failed start (TCC revoked between preflight and start) goes through the same teardown path:

```swift
func start(filter: SCContentFilter, config: SCStreamConfiguration) async throws {
    let s = SCStream(filter: filter, configuration: config, delegate: self)
    try s.addStreamOutput(self, type: .audio, sampleHandlerQueue: audioQueue)
    stream = s
    do {
        try await s.startCapture()
    } catch {
        await stopSafely()
        throw error
    }
}
```

This opens a short window where `stream` is set but not capturing; a concurrent stop must tolerate `stopCapture()` on an unstarted stream. Test that path.

**Do not re-enumerate everything in restart paths.** `excludingDesktopWindows(false, onScreenWindowsOnly: false)` walks off-screen, minimized and other-Space windows; calling it on every auto-restart caused visible UI stalls. Audio streams rarely need the window list: cache the display from the first start, and when you must refresh use the on-screen-only query.

```swift
private var cachedDisplay: SCDisplay?

func display() async throws -> SCDisplay {
    if let cachedDisplay { return cachedDisplay }
    let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: true)
    guard let d = content.displays.first else { throw CaptureError.noDisplay }
    cachedDisplay = d
    return d
}
```

## SCRecordingOutput, picker, screenshots, clip buffering

**`SCRecordingOutput` (macOS 15+)** writes a movie without manual buffer handling. Add it before `startCapture()` to guarantee the first frame is recorded. One recording output per stream; defaults are H.264 in MPEG-4 (check `availableVideoCodecTypes` / `availableOutputFileTypes`).

```swift
let recordingConfig = SCRecordingOutputConfiguration()
recordingConfig.outputURL = fileURL                      // a file URL, not a folder
recordingConfig.outputFileType = .mov
recordingConfig.videoCodecType = .hevc
if #available(macOS 27, *) { recordingConfig.mixesAudioWithMicrophone = false } // separate system/mic tracks
let recordingOutput = SCRecordingOutput(configuration: recordingConfig, delegate: self)
try stream.addRecordingOutput(recordingOutput)
try await stream.startCapture()
// recordingOutput.recordedDuration, .recordedFileSize while running
try stream.removeRecordingOutput(recordingOutput)        // stop recording, keep streaming
```

Delegate: `recordingOutputDidStartRecording(_:)`, `recordingOutput(_:didFailWithError:)`, `recordingOutputDidFinishRecording(_:)`. Remember it stops on `updateConfiguration()`. For audio-only files use `AVAssetWriter`.

**`SCContentSharingPicker` (macOS 14+)** is the system picker and Apple's preferred way to pick content (it also avoids the recurring re-authorization prompts, below). `SCContentSharingPickerConfiguration` is a Swift struct.

```swift
let picker = SCContentSharingPicker.shared
var pickerConfig = SCContentSharingPickerConfiguration()
pickerConfig.allowedPickerModes = [.singleWindow, .multipleWindows, .singleApplication]
pickerConfig.excludedBundleIDs = ["com.example.excluded"]
picker.defaultConfiguration = pickerConfig
picker.add(self)                    // SCContentSharingPickerObserver
picker.isActive = true              // required or present() shows nothing
picker.present()                    // or present(using: .window), present(for: existingStream)

func contentSharingPicker(_ picker: SCContentSharingPicker, didUpdateWith filter: SCContentFilter,
                          for stream: SCStream?) {
    guard let stream else { return }  // nil: build a new stream with this filter
    // Completion-handler form: a Task capturing the non-Sendable stream/filter is a region-isolation error.
    stream.updateContentFilter(filter) { error in if let error { print(error) } }
}
func contentSharingPicker(_ picker: SCContentSharingPicker, didCancelFor stream: SCStream?) {}
func contentSharingPickerStartDidFailWithError(_ error: any Error) {}
```

`picker.isAvailable` (macOS 27+) reports whether screen recording is supported and allowed on the device.

**Screenshots.** `SCScreenshotManager.captureImage(contentFilter:configuration:)` and `captureSampleBuffer(contentFilter:configuration:)` (macOS 14+) take an `SCStreamConfiguration`. On macOS 26+ prefer `SCScreenshotConfiguration`, which handles HDR without stream presets and can save straight to a file (`contentType`, `fileURL`):

```swift
if #available(macOS 26, *) {
    let shot = SCScreenshotConfiguration()
    shot.width = 3840
    shot.height = 2160
    shot.dynamicRange = .bothSDRAndHDR   // .sdr, .hdr
    shot.showsCursor = false
    let output = try await SCScreenshotManager.captureScreenshot(contentFilter: filter, configuration: shot)
    let sdr = output.sdrImage, hdr = output.hdrImage
}
```

For 14/15 back-deployment use `SCStreamConfiguration(preset: .captureHDRScreenshotLocalDisplay)` with `captureImage`.

**macOS 27 additions.** `SCClipBufferingOutput` keeps a rolling buffer so you can save "the last N seconds" without a hand-rolled ring buffer over `SCStreamOutput`; `SCRecordingEditor` presents a system-owned preview UI for a finished recording (it does not expose editing APIs).

```swift
@available(macOS 27, *)
func saveLastClip(stream: SCStream, to url: URL) async throws {
    let clip = SCClipBufferingOutput(delegate: nil)
    try stream.addClipBufferingOutput(clip)      // normally once, at stream setup
    try await clip.exportClip(to: url, duration: 30)
}

@available(macOS 27, *)
@MainActor func preview(url: URL, from window: NSWindow) async throws {
    try await SCRecordingEditor(url: url).present(from: window)
}
```

## Delegate callbacks and clock sync

**Presenter Overlay** (camera composited over the shared screen during calls): the Swift names are `outputVideoEffectDidStart(for:)` and `outputVideoEffectDidStop(for:)` (macOS 14+). A method spelled `stream(_:outputVideoEffectDidStartFor:)` compiles as an unrelated method and is never called. Handle them to warn users that an overlay is being baked into a recording; `config.presenterOverlayPrivacyAlertSetting` (`.system`/`.never`) controls the system alert.

**Activity (macOS 15.2+).** `streamDidBecomeActive(_:)` / `streamDidBecomeInactive(_:)`: the system can idle a stream (for example fully occluded content) without stopping it. Drive a recording indicator from these, not from your own start/stop flags.

**`synchronizationClock`** is the `CMClock` SCStream timestamps against. When muxing SCStream output with another source (AVAudioEngine mic, CATap, AVCaptureSession), convert the other side's times into this clock instead of subtracting a captured start time, which accumulates drift over long recordings:

```swift
if let clock = stream.synchronizationClock {
    let hostNow = CMClockGetTime(CMClockGetHostTimeClock())
    let streamTime = CMSyncConvertTime(hostNow, from: CMClockGetHostTimeClock(), to: clock)
}
```

## Screen Recording TCC

Screen capture has no entitlement; it is a TCC runtime grant. The pane is "Screen & System Audio Recording" (macOS 14+), with a separate "System Audio Recording Only" section for apps that asked only for audio (Core Audio taps).

| Call | Shows dialog | Use |
|---|---|---|
| `CGPreflightScreenCaptureAccess()` | No | Every permission-sensitive UI refresh and every recording start. Cheap. |
| `CGRequestScreenCaptureAccess()` | Yes, once | Exactly once, at the onboarding step the user is looking at |

- Never cache "granted" in `UserDefaults`. Users revoke between launches, and a stale flag means silent recordings with no error. Re-check on `NSApplication.didBecomeActiveNotification` too: state read in `onAppear` goes stale when the user visits Settings and returns.
- Call `CGRequestScreenCaptureAccess()` at the "Grant Screen Recording" step, not at a final "Complete Setup" - users who click "Open System Settings" first otherwise never hit the in-app request.
- Do not call it in `App.init()`: the grant can be attributed to the parent process (the terminal). Call it from `applicationDidFinishLaunching` or later.
- After granting, macOS offers "Quit & Reopen"; capture typically needs the relaunch. Make Screen Recording the last onboarding step and frame the restart as "setup complete".
- `captureMicrophone = true` needs both Screen Recording and Microphone grants, plus `NSMicrophoneUsageDescription` and (hardened runtime) `com.apple.security.device.audio-input`. Mic permission handling is in `macos-audio-pipeline.md`.
- macOS 15+ shows periodic re-authorization prompts for apps capturing outside the picker. Options: use `SCContentSharingPicker`; request the `com.apple.developer.persistent-content-capture` entitlement from Apple (remote-desktop class apps); or MDM `forceBypassScreenCaptureAlert` (managed fleets).
- Test from a `.app` bundle (`open MyApp.app`), never the bare binary: a binary run from a terminal gets the grant attributed to the terminal, and binaries without a bundle and `CFBundleIdentifier` cannot reliably get Screen Recording at all.

Deep links (the `com.apple.settings.PrivacySecurity.extension` form lands on the subpane on macOS 26; the legacy `com.apple.preference.security` prefix only opens the top Privacy pane there). Use `Privacy_ScreenCapture` for SCStream apps - `Privacy_AudioCapture` lands on an inactive pane for them. Centralize the URLs so they cannot drift:

```swift
enum SystemSettingsPane: String {
    case screenCapture = "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_ScreenCapture"
    case microphone = "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Microphone"
    case accessibility = "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Accessibility"
    case loginItems = "x-apple.systempreferences:com.apple.LoginItems-Settings.extension"

    @MainActor func open() { NSWorkspace.shared.open(URL(string: rawValue)!) }
}
```

Development reset: `tccutil reset ScreenCapture com.example.app`. Grants that read "on" but deliver silence, or reset on every rebuild, are signing/CDHash problems - see the TCC section of `macos-audio-pipeline.md`.

Unverified: the deep-link behavior on macOS 26/27 and the Sequoia re-authorization cadence come from production use, not Apple documentation.
