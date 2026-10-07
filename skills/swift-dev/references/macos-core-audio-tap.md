# Core Audio Process Taps on macOS

Capturing one process's (or every process's) audio output with `CATapDescription` + a tap-only aggregate device, without ScreenCaptureKit - and why it is the wrong default for long recordings.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every Swift block compiled through SIL (`swiftc -emit-sil -target arm64-apple-macos15.0 -swift-version 6`, with and without `-default-isolation MainActor`); keys, functions and availability read from `CoreAudio.framework/Headers/{AudioHardware,AudioHardwareTapping,CATapDescription}.h` and the CoreAudio Swift overlay in the macOS 27.0 SDK. No tap was created (that would trigger the TCC prompt).

## Contents
- Reality check: when not to use a tap
- Tap vs SCStream
- Creating a tap and a tap-only aggregate (HFP-safe)
- Clock fragility the tap-only pattern does not fix
- Rate-change listener anti-pattern
- Interleaved-stereo frame-count trap
- CFString properties follow the Create Rule
- IO proc isolation
- TCC and permissions

Process taps are macOS-only (`AudioHardwareCreateProcessTap` is macOS 14.2+, unavailable on iOS).

## Reality check: when not to use a tap

A call recorder shipped a Core Audio tap and reverted to display-wide `SCStream` after three distinct silent-recording bugs in five days. The cause is structural: an aggregate device's IO proc is timed by its subdevice clocks - Apple's [`AudioHardwareAggregateDevice`](https://developer.apple.com/documentation/coreaudio/audiohardwareaggregatedevice) "synchronizes the clocks of its subdevices and subtaps when running IO" - so when the default output clock is idle, rate-pinned (Bluetooth HFP) or stalled, the tap has audio but no ticks to deliver it on. A buffer-arrival watchdog restart hits the same idle clock and burns its restart budget. Apple does not document these failure modes, but Chromium ships listeners for all three: alive-state + default-output change ([crbug 436110597](https://chromium.googlesource.com/chromium/src/+/a4545b03c738f0a84468a7f70066c85f80d6b23d)), sample-rate change ([crbug 441729516](https://chromium.googlesource.com/chromium/src/+/e17d528fa243625faeebf4ec1ff500b628f1fd74)) and device-change restart ([crbug 442993607](https://chromium.googlesource.com/chromium/src/+/0cf5a46b9db9820785be8ddaf6ecd62830775501%5E%21)). Display-wide SCStream is clocked by the OS-composited mix, independent of any output device, and ran for weeks on the same workload with no silent-recording reports.

Scenarios that produced silent recordings with taps:

1. **Bluetooth HFP** (AirPods on a call): the aggregate pins to 24 kHz; unless it is tap-only (below) the IO proc never fires. Tap-only fixes this symptom, not the class.
2. **Idle default output**: the IO proc stops during long silences (observed ~18 s post-call tail drops).
3. **In-page audio routing** (Meet or Zoom web sending call audio to a non-default output while the default is idle): the IO proc on the default device never ticks; an hour-long recording ends up mic-only.
4. **Long unattended recordings**, where any of the above can happen and a silent file is worse than a failed start.

For those workloads use display-wide `SCStream` (`macos-screencapturekit.md`).

## Tap vs SCStream

| Need | Process tap | Display-wide SCStream |
|---|---|---|
| Per-process isolation | Yes (process list or bundle IDs) | Per-app via filter, from the composited mix |
| Survives idle default-output clock | **No** (structural) | Yes |
| Survives Bluetooth HFP on default output | Only with a tap-only aggregate | Yes |
| Survives in-page audio re-routing | **No** (structural) | Yes |
| Console noise | None | `stream output NOT found. Dropping frame` unless a `.screen` output is attached |
| Hidden video cost | None | Small with 2x2 at 1 fps |
| Capture latency | A few ms | ~20-50 ms of sample-handler buffering |
| TCC | "System Audio Recording Only" (or the Screen Recording grant) | Screen Recording |

Short take: if you need sub-20 ms latency for live AEC or analysis, a tap is the only option - accept the clock fragility, add a watchdog, and test HFP, idle output and in-page routing before shipping. For disk-bound recording (calls, meetings, lectures) the latency argument does not apply; SCStream is the safer default.

## Creating a tap and a tap-only aggregate (HFP-safe)

Build an aggregate that contains **only the tap** - no physical output subdevice. Adding the output device (`kAudioAggregateDeviceMainSubDeviceKey` / `kAudioAggregateDeviceSubDeviceListKey`) locks the aggregate to that device's rate; when AirPods drop to 24 kHz HFP the 48 kHz tap and the aggregate disagree, the IO proc stops, and `AudioObjectSetPropertyData` reports `noErr` while doing nothing. Reference implementations: [graphaelli/audiotap](https://github.com/graphaelli/audiotap), RecordKit.

The SDK's Swift object API (`AudioHardwareSystem`, `AudioHardwareTap`, `AudioHardwareAggregateDevice`, marked macOS 15+) is the shortest path:

```swift
import CoreAudio

struct TapCapture {
    let tap: AudioHardwareTap
    let aggregate: AudioHardwareAggregateDevice
}

func makeTapCapture(processIDs pids: [pid_t]) throws -> TapCapture {
    let system = AudioHardwareSystem.shared
    let objectIDs = try pids.compactMap { try system.process(for: $0)?.id }
    let description = CATapDescription(stereoMixdownOfProcesses: objectIDs)
    description.isPrivate = true
    description.muteBehavior = .unmuted
    guard let tap = try system.makeProcessTap(description: description) else { throw TapError.noTap }

    let composition: [String: Any] = [
        kAudioAggregateDeviceNameKey: "Recorder Tap",
        kAudioAggregateDeviceUIDKey: UUID().uuidString,
        kAudioAggregateDeviceIsPrivateKey: true,
        kAudioAggregateDeviceIsStackedKey: false,
        // Tap-only: no main subdevice, no subdevice list.
        kAudioAggregateDeviceTapListKey: [[
            kAudioSubTapUIDKey: try tap.uid,
            kAudioSubTapDriftCompensationKey: true,
        ]],
    ]
    guard let aggregate = try system.makeAggregateDevice(description: composition) else {
        try? system.destroyProcessTap(tap)
        throw TapError.noAggregate
    }
    return TapCapture(tap: tap, aggregate: aggregate)
}
// Teardown: destroyAggregateDevice(_:) first, then destroyProcessTap(_:).
```

Escape hatch for macOS 14.2-14.x: the C functions `AudioHardwareCreateProcessTap(description, &tapID)` and `AudioHardwareCreateAggregateDevice(dict as CFDictionary, &aggregateID)` with the same dictionary, reading the tap UID via `kAudioTapPropertyUID` (see the Create Rule section).

Other `CATapDescription` initializers: `monoMixdownOfProcesses:`, `stereoGlobalTapButExcludeProcesses:` (everything except, for example, your own process), `processes:deviceUID:stream:`. macOS 26 adds `bundleIDs` (target by bundle ID instead of process object IDs) and `isProcessRestoreEnabled` (re-attach a tapped app when it quits and relaunches) - useful for call apps that restart their audio helper. `kAudioAggregateDeviceTapAutoStartKey` (private aggregates only) makes `AudioDeviceStart` wait until a tapped process first produces audio.

**Never omit `kAudioSubTapDriftCompensationKey: true`.** Without it CoreAudio reconciles the tap clock against the aggregate on every IO cycle, which produces periodic artifacts in *all system audio* while the tap runs - audible crackling in music and calls - and pitch drift in long recordings. Confirmed in production in [Omi PR #6489](https://github.com/BasedHardware/omi/pull/6489).

## Clock fragility the tap-only pattern does not fix

Tap-only fixes HFP rate pinning. It does not fix the architecture: when the default output's hardware clock is idle, flips transport, or stalls (DeviceIsAlive flapping, a USB hub hiccup), the IO proc gets no callbacks. Observed:

- ~18 s tail drops after a call when nothing plays.
- Hour-long mic-only recordings when a web app routes call audio to a non-default output. Chromium's commit says it verbatim: "CatapAudioInputStream will ignore the change and continue to capture the original default device". Chrome's `kMacCatapCaptureAllDevices` flag exists to capture all outputs instead.
- Watchdog restart + reinstall hits the same idle clock, exhausts the budget (for example 3 restarts / 30 s), and turns a recoverable stall into a terminated recording.

If you ship a tap for long recordings, these are mandatory:

1. **Buffer-arrival watchdog** on the IO-proc delivery path (2 s is reasonable for calls, longer for music). Buffer absence is the failure signal.
2. **Layered listeners** (Chromium's pattern): `kAudioDevicePropertyDeviceIsAlive` on the tap, `kAudioHardwarePropertyDefaultOutputDevice` on the system, `kAudioDevicePropertyNominalSampleRate` on the aggregate. Keep the watchdog anyway; listeners miss same-format, same-rate transitions.
3. **Validation scenarios** before shipping: AirPods HFP on a call, idle default output for 30+ s, in-page routing in Meet/Zoom web, USB mic unplug/replug, a virtual device (BlackHole, Loopback) crashing mid-recording.
4. **A decided fallback** when the watchdog trips: rebuild the aggregate (may re-trip), switch to SCStream, or fail loudly. Silent loss is the worst outcome.

## Rate-change listener anti-pattern

Do not listen for `kAudioDevicePropertyNominalSampleRate` and set the rate back from inside the listener. The set re-fires the listener: one app saw 49 iterations before CoreAudio throttled, and the rate never converged.

```swift
// DO NOT: the set inside the listener re-fires the listener.
let listener: AudioObjectPropertyListenerBlock = { _, _ in
    var addr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyNominalSampleRate,
                                          mScope: kAudioObjectPropertyScopeGlobal,
                                          mElement: kAudioObjectPropertyElementMain)
    var newRate: Float64 = 48_000
    AudioObjectSetPropertyData(tapID, &addr, 0, nil, UInt32(MemoryLayout<Float64>.size), &newRate)
}
AudioObjectAddPropertyListenerBlock(tapID, &rateAddr, queue, listener)
```

Instead either resample to the writer's fixed rate (for example 48 kHz) off the IO thread - each buffer carries its source format - or rely on the tap-only aggregate with drift compensation, which makes the handler unnecessary.

## Interleaved-stereo frame-count trap

Taps deliver 2-channel audio **interleaved** (`kAudioFormatFlagIsNonInterleaved` clear). When wrapping it into a `CMSampleBuffer`, a sample count taken from the wrong field makes the track play back at **half its real duration** because interleaved L/R pairs get counted as two samples. For interleaved data, derive frames from bytes:

```swift
nonisolated func trueFrameCount(_ buffer: AVAudioPCMBuffer) -> Int {
    let bytesPerFrame = Int(buffer.format.streamDescription.pointee.mBytesPerFrame) // all channels
    let byteLength = Int(buffer.audioBufferList.pointee.mBuffers.mDataByteSize)
    return byteLength / bytesPerFrame
}
```

Check the result against `frameLength` in a test with a known-duration signal. SCStream audio is the opposite case (non-interleaved); the conversion and downmix traps for both layouts are in `macos-audio-pipeline.md`.

## CFString properties follow the Create Rule

Reading a `CFString` property (`kAudioTapPropertyUID`, `kAudioDevicePropertyDeviceUID`, `kAudioObjectPropertyName`) with `AudioObjectGetPropertyData` returns a +1 object despite "Get" in the name; `AudioHardware.h` says the caller is responsible for releasing it. Take it with `takeRetainedValue()`; `takeUnretainedValue()` leaks it. The Swift object API (`tap.uid`, `device.name`) handles this for you.

```swift
nonisolated func stringProperty(_ objectID: AudioObjectID, _ selector: AudioObjectPropertySelector) throws -> String {
    var address = AudioObjectPropertyAddress(mSelector: selector, mScope: kAudioObjectPropertyScopeGlobal,
                                             mElement: kAudioObjectPropertyElementMain)
    var value: Unmanaged<CFString>?
    var size = UInt32(MemoryLayout<Unmanaged<CFString>?>.size)
    let status = AudioObjectGetPropertyData(objectID, &address, 0, nil, &size, &value)
    guard status == noErr, let value else { throw TapError.status(status) }
    return value.takeRetainedValue() as String   // Create Rule: we own it
}
```

## IO proc isolation

The IO block runs on CoreAudio's real-time thread. Keep it `nonisolated` - never actor-isolated or `@MainActor` - and do no allocation, locking, `Task {}` or `AsyncStream.yield()` in it. Copy samples into preallocated storage, then hop to a serial queue that is also the actor's executor, where `assumeIsolated` gives synchronous access to actor state:

```swift
actor TapRecorder {
    let audioQueue = DispatchSerialQueue(label: "tap.audio")
    nonisolated var unownedExecutor: UnownedSerialExecutor { audioQueue.asUnownedSerialExecutor() }
    // Preallocated; production code needs a lock-free ring buffer so the next IO cycle cannot overwrite unread data.
    private nonisolated(unsafe) let staging = UnsafeMutablePointer<Float>.allocate(capacity: 1 << 16)
    private var samplesReceived = 0

    nonisolated func makeIOBlock() -> AudioDeviceIOBlock {
        { [weak self] _, inputData, _, _, _ in
            guard let self else { return }
            let buffers = UnsafeMutableAudioBufferListPointer(UnsafeMutablePointer(mutating: inputData))
            guard let first = buffers.first, let src = first.mData else { return }
            let count = min(Int(first.mDataByteSize) / MemoryLayout<Float>.size, 1 << 16)
            staging.update(from: src.assumingMemoryBound(to: Float.self), count: count)
            audioQueue.async {
                self.assumeIsolated { recorder in recorder.consume(count) }
            }
        }
    }

    func consume(_ count: Int) { samplesReceived += count }

    nonisolated func start(on aggregate: AudioHardwareAggregateDevice) throws -> AudioDeviceIOProcID {
        var procID: AudioDeviceIOProcID?
        let status = AudioDeviceCreateIOProcIDWithBlock(&procID, aggregate.id, nil, makeIOBlock())
        guard status == noErr, let procID else { throw TapError.status(status) }
        try aggregate.start(IOProcID: procID)
        return procID
    }
}
```

`audioQueue.async { assumeIsolated { ... } }` is correct only because the queue is the actor's executor. Nesting the same hop inside a CoreAudio property listener that already runs on that queue reorders work; see `concurrency-isolation.md` for the `assumeIsolated` rules.

## TCC and permissions

- Add `NSAudioCaptureUsageDescription` to Info.plist. Per Apple's [Core Audio taps sample](https://developer.apple.com/documentation/coreaudio/capturing-system-audio-with-core-audio-taps), the system prompts the first time you start recording from an aggregate device that contains a tap.
- Granted apps appear under Privacy & Security > Screen & System Audio Recording, in the "System Audio Recording Only" section. The service (`kTCCServiceAudioCapture`) is distinct from Screen Recording (`kTCCServiceScreenCapture`); preflighting one does not answer for the other.
- **There is no public preflight API for tap permission.** Fallbacks: treat a failed create/start, or buffers that stay at zero, as "not granted" and show request UI; use `CGPreflightScreenCaptureAccess()` only as a hint; `TCCAccessPreflight(kTCCServiceAudioCapture, nil)` is private SPI (used by [insidegui/AudioCap](https://github.com/insidegui/AudioCap)) - not App Store safe.
- Never cache "granted" in `UserDefaults`: revocation between launches gives silent recordings (buffers flow, RMS stays at `-inf`).
- Command-line tools run from some terminals (iTerm, editor-embedded terminals) record silence without ever prompting; test from a `.app` bundle.
- "Granted but silent" after a force-replace reinstall, and grants that reset every rebuild, are signing/CDHash problems: see the TCC section of `macos-audio-pipeline.md`.

Unverified: older notes claim that from macOS 26.1 the Screen Recording grant alone also authorizes taps; this was not confirmed against Apple documentation, so request `NSAudioCaptureUsageDescription` access regardless.
