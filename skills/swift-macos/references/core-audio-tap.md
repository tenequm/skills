# CoreAudio Process Tap (CATap)

`CATapDescription` + `AudioHardwareCreateProcessTap` + aggregate device (macOS 14.2+) captures a specific process's audio output directly from CoreAudio, without ScreenCaptureKit. Lower latency and a separate TCC permission from Screen Recording. Used by RecordKit, Chromium's `CatapAudioInputStream`, AudioCap, audiotee, and others.

> **Production reality check before you migrate.** An internal call-recorder shipped CATap and reverted to display-wide SCStream after three distinct silent-recording bugs in five days. The root cause is **structural to CATap**: the aggregate-device IO proc's time base is tied to its subdevice clocks — Apple's `AudioHardwareAggregateDevice` reference states it "synchronizes the clocks of its subdevices and subtaps when running IO" ([docs](https://developer.apple.com/documentation/coreaudio/audiohardwareaggregatedevice)) — so when the default output clock is idle, rate-pinned (Bluetooth HFP), or stalled, the tap has audio to deliver but no ticks to deliver it on. A buffer-arrival watchdog restart hits the same idle clock and exhausts its restart budget. These failure modes are not Apple-documented as such, but the **Chromium audio team has independently shipped listeners for all three**: alive-state + default-output-change listeners ([crbug 436110597](https://chromium.googlesource.com/chromium/src/+/a4545b03c738f0a84468a7f70066c85f80d6b23d)), sample-rate-change error propagation ([crbug 441729516](https://chromium.googlesource.com/chromium/src/+/e17d528fa243625faeebf4ec1ff500b628f1fd74)), and device-change stream-restart ([crbug 442993607](https://chromium.googlesource.com/chromium/src/+/0cf5a46b9db9820785be8ddaf6ecd62830775501%5E%21), which notes "*CatapAudioInputStream will ignore the change and continue to capture the original default device*"). Display-wide SCStream's clock comes from the OS-composited mix, decoupled from any specific hardware output device, and has a multi-week production track record on the same workload with zero silent-recording reports. Read "When NOT to use CATap" below before choosing CATap for long-running recordings.

## Table of Contents
- When NOT to Use CATap
- When to Use CATap vs SCStream
- Tap-Only Aggregate Pattern (HFP-safe)
- Clock Fragility: What the Tap-Only Pattern Does NOT Fix
- The Rate-Change Listener Anti-Pattern
- Interleaved-Stereo Frame-Count Trap
- IO Proc Isolation and `assumeIsolated`
- TCC / Permissions for CATap

## When NOT to Use CATap

Specifically these scenarios have produced silent recordings in production:

1. **Bluetooth HFP path** (AirPods on a call, Mac as the audio device). Aggregate pins to 24 kHz; unless your aggregate is tap-only (see below) the IO proc never fires. Tap-only aggregate fixes *this* specific symptom but not the broader class.
2. **Idle default output device.** IO proc stops emitting during long silences (observed ~18 s post-call tail drops).
3. **In-page audio routing** (Chrome Meet / Zoom web picker sending call audio to a non-default output while the default is idle). IO proc on the default device never ticks; the hour-long recording ends up mic-only.
4. **Long-duration unattended recordings** where any of the above can happen and a silent file is worse than a failed start.

For these workloads, display-wide `SCStream` is more robust even with the cosmetic overhead of a still-running video pipeline (see `screen-capture-audio.md`). macOS 26.1+ also grants audio capture with the Screen Recording TCC grant, neutralizing CATap's permission-UX advantage.

## When to Use CATap vs SCStream

| Need | CATap | Display-wide SCStream |
|------|-------|-----------------------|
| Per-process audio isolation | Yes (target PID) | No (OS-composited mix, exclude by app via filter) |
| Survives idle default-output clock | **No** (structural) | Yes |
| Survives Bluetooth HFP on default output | Only with tap-only aggregate | Yes |
| Survives in-page audio re-routing | **No** (structural) | Yes |
| Cosmetic Console.app noise | None | `stream output NOT found. Dropping frame` (cosmetic) |
| Hidden video-pipeline CPU cost | None | Minor (mitigate with 2x2, `timescale: .max`) |
| TCC permission on macOS 26.1+ | Screen Recording (unified) | Screen Recording |
| TCC permission on macOS 14/15 | Separate "System Audio Recording" | Screen Recording |
| Lower capture latency | Yes (~few ms) | No (SCStream sample-handler buffering ~20-50 ms) |

**Short take**: if you need sub-20 ms capture latency for real-time AEC or live analysis, CATap is the only option and you accept the clock-fragility - pair it with a buffer-arrival watchdog and validate against HFP / idle-output / in-page-routing scenarios before shipping. If you're writing to disk for later playback/transcription (call recording, lecture capture, meeting archival), the latency argument doesn't apply and display-wide SCStream is the safer default.

## Tap-Only Aggregate Pattern (HFP-safe)

The canonical recipe: build an aggregate device that contains **only the tap** (no physical output subdevice). When the output device changes - headphones plug in, AirPods enter HFP at 24 kHz - the tap stays at its own sample rate and keeps delivering frames.

**Why**: including the output device as a subdevice (`kAudioAggregateDeviceMainSubDeviceKey` + `kAudioAggregateDeviceSubDeviceListKey`) locks the aggregate to the output's rate. When AirPods switch to 24 kHz mono HFP, the 48 kHz tap and the aggregate disagree, IO proc stops firing, and `AudioObjectSetPropertyData` will report `noErr` while silently doing nothing.

```swift
import CoreAudio
import AudioToolbox

func makeAggregate(tapID: AudioObjectID, name: String, uid: String) throws -> AudioObjectID {
    let description: [String: Any] = [
        kAudioAggregateDeviceNameKey: name,
        kAudioAggregateDeviceUIDKey: uid,
        kAudioAggregateDeviceIsPrivateKey: 1,
        kAudioAggregateDeviceIsStackedKey: 0,
        // Tap-only. DO NOT include kAudioAggregateDeviceMainSubDeviceKey
        // or kAudioAggregateDeviceSubDeviceListKey - they lock the aggregate
        // to the output device's rate and break under HFP.
        kAudioAggregateDeviceTapListKey: [[
            kAudioSubTapUIDKey: tapUID(for: tapID),
            // Must be true: compensates for tap-vs-device clock drift.
            kAudioSubTapDriftCompensationKey: true,
        ]],
    ]

    var aggregateID: AudioObjectID = 0
    let status = AudioHardwareCreateAggregateDevice(
        description as CFDictionary, &aggregateID
    )
    guard status == noErr else { throw CATapError.create(status) }
    return aggregateID
}
```

Reference: [graphaelli/audiotap](https://github.com/graphaelli/audiotap), RecordKit v0.78.0.

### Don't omit `kAudioSubTapDriftCompensationKey: true`

Without drift compensation, CoreAudio resamples on every IO cycle to reconcile the tap's clock with the aggregate's, producing **periodic artifacts in all system audio** — audible as crackling during normal playback (music, calls) whenever the tap is running, and as pitch drift in long recordings. Confirmed in production by [Omi PR #6489](https://github.com/BasedHardware/omi/pull/6489): "*setting `kAudioSubTapDriftCompensationKey` … tells CoreAudio to reconcile clocks at the sub-tap level … the workaround is no longer needed.*" Keep it on.

## Clock Fragility: What the Tap-Only Pattern Does NOT Fix

The tap-only aggregate fixes the HFP rate-pinning symptom (IO proc never fires when AirPods go to 24 kHz and the aggregate was locked to 48 kHz). It does **not** fix the underlying architectural issue:

> Apple's [`AudioHardwareAggregateDevice`](https://developer.apple.com/documentation/coreaudio/audiohardwareaggregatedevice) "synchronizes the clocks of its subdevices and subtaps when running IO." When the system default output device's hardware clock is idle (no app is actively playing audio), rate-pinned (HFP transport flip), or stalled (DeviceIsAlive flapping, USB hub hiccup), the aggregate's IO proc receives no ticks and no buffer-delivery callbacks. The tap has samples to deliver; the scheduler has no timing source to hand them over on. Apple does not document this specific failure mode, but **Chromium has shipped listeners for all three transitions** (alive, default-output-change, sample-rate-change): [crbug 436110597](https://chromium.googlesource.com/chromium/src/+/a4545b03c738f0a84468a7f70066c85f80d6b23d), [441729516](https://chromium.googlesource.com/chromium/src/+/e17d528fa243625faeebf4ec1ff500b628f1fd74), [442993607](https://chromium.googlesource.com/chromium/src/+/0cf5a46b9db9820785be8ddaf6ecd62830775501%5E%21).

Observed production failures (internal recorder + Chromium-mirrored classes):

- Post-call tail drops of ~18 s when nothing plays after the call ends.
- Full-hour mic-only recordings when a web app routes call audio to a non-default output while the default output stays silent. Chromium confirms the class verbatim: "*CatapAudioInputStream will ignore the change and continue to capture the original default device*" ([commit 0cf5a46b](https://chromium.googlesource.com/chromium/src/+/0cf5a46b9db9820785be8ddaf6ecd62830775501%5E%21)). Chrome's `kMacCatapCaptureAllDevices` feature flag exists specifically to work around this by capturing all outputs rather than just the default.
- Watchdog restart + reinstall hits the same idle clock, burns the restart budget (e.g. 3 restarts / 30 s), and converts a recoverable stall into a terminated recording.

If you ship CATap for long-running recordings, mandatory:
1. **Buffer-arrival watchdog** on the IO-proc delivery path with a trip threshold appropriate for your domain (2 s is reasonable for calls; longer for music). Treat buffer absence as the failure mode.
2. **Layered signal sources** — Chromium's pattern: listen on `kAudioDevicePropertyDeviceIsAlive` (tap), `kAudioHardwarePropertyDefaultOutputDevice` (system), and `kAudioDevicePropertyNominalSampleRate` (aggregate). Still run the watchdog as the universal safety net — the listeners can miss same-format / same-rate transitions.
3. **Validation scenarios** before shipping: AirPods HFP on a call, idle default output for >30 s, in-page audio router on Chrome Meet / Zoom web, USB mic unplug-replug, virtual audio device (BlackHole / Loopback) crashing mid-recording.
4. **Fallback path** — decide in advance what happens when the watchdog trips: restart the aggregate (may re-trip immediately), switch to SCStream, or fail loudly. Silently losing audio is the worst outcome.

## The Rate-Change Listener Anti-Pattern

Tempting: subscribe to `kAudioDevicePropertyNominalSampleRate` on the tap and re-configure when the rate changes.

Don't. Calling `AudioObjectSetPropertyData` from inside the listener re-fires the listener, producing an infinite notification storm. Observed in practice: 49 iterations before CoreAudio throttled, with no rate ever converging.

```swift
// DO NOT DO THIS
let listener: AudioObjectPropertyListenerBlock = { _, _ in
    // This call re-fires the listener.
    AudioObjectSetPropertyData(tapID, &addr, 0, nil, size, &newRate)
}
AudioObjectAddPropertyListenerBlock(tapID, &rateAddr, queue, listener)
```

Two safe alternatives:
1. **Linear resampling inside the IO proc** - each buffer is already annotated with its source format; resample to the writer's fixed target rate (e.g. 48 kHz) on the hot path. Same technique used for mic input.
2. **Tap-only aggregate with drift compensation** (above) - the compensation key handles small drift automatically, so the rate-change handler is unnecessary.

## Interleaved-Stereo Frame-Count Trap

CATap delivers 2-channel audio as **interleaved** (`interleaved: true`, `mFormatFlags & kAudioFormatFlagIsNonInterleaved == 0`). When wrapping into a `CMSampleBuffer` via a helper like `asSampleBuffer(sampleCount:)`, passing `pcmBuffer.frameLength` as the sample count produces a track that plays back at **half the expected duration** - `CMSampleTimingInfo` misinterprets interleaved pairs as two samples.

```swift
// WRONG for interleaved stereo: resulting track is 50% of real duration
let sb = pcmBuffer.asSampleBuffer(sampleCount: Int(pcmBuffer.frameLength))

// RIGHT: for interleaved stereo, frame count is bytes / bytesPerFrame / channels
let bytesPerFrame = Int(pcmBuffer.format.streamDescription.pointee.mBytesPerFrame)
let frameCount = pcmBuffer.byteLength / bytesPerFrame
// frameCount is now the true sample (time-domain) count.
```

Rule of thumb: if the source format is interleaved, compute frame count from the byte length of the block buffer divided by `mBytesPerFrame`, not from `frameLength`.

## IO Proc Isolation and `assumeIsolated`

The IO proc closure returned from `AudioHardwareCreateProcessTapWithAggregateDevice` / `makeIOProcBlock` runs on CoreAudio's **real-time thread**. It must stay `nonisolated` - do not make it actor-isolated or `@MainActor`. Allocation, locks, `Task {}`, and `AsyncStream.yield()` are all unsafe there.

Pattern: IO proc `memcpy`s into a pre-allocated staging buffer, then dispatches (via `audioQueue.async`) for off-RT processing. The dispatched block can then synchronously `assumeIsolated` back into the actor to touch actor state.

```swift
actor AudioRecorder {
    let audioQueue = DispatchSerialQueue(label: "audio")
    nonisolated var unownedExecutor: UnownedSerialExecutor {
        audioQueue.asUnownedSerialExecutor()
    }

    // IO proc: nonisolated, no allocation, no Task, no AsyncStream.
    nonisolated func makeIOProc() -> AudioDeviceIOBlock {
        return { [weak self] _, inputData, _, _, _ in
            guard let self else { return }
            // Copy out. No actor state access here.
            let frames = stageBuffer(from: inputData)
            // Hand off to audio queue - assumeIsolated on the other side.
            audioQueue.async {
                self.assumeIsolated { iso in
                    iso.writeFrames(frames)
                }
            }
        }
    }
}
```

See `actors-isolation.md` for the full `assumeIsolated` recipe set, including why `audioQueue.async { assumeIsolated { ... } }` is correct but nesting it inside a CoreAudio listener that already dispatches on the same queue causes an ordering bug.

## TCC / Permissions for CATap

The Privacy & Security pane has been labeled **"Screen & System Audio Recording"** since macOS 14 Sonoma. On macOS 26 it gains a "System Audio Recording Only" subsection and the Screen Recording grant implicitly covers system-audio capture. Under the hood, `kTCCServiceAudioCapture` is a distinct TCC service from `kTCCServiceScreenCapture` — preflighting one does not authoritatively answer for the other, and the two can drift (particularly on macOS 14/15 where they are separately toggleable).

**There is no public `CGPreflightScreenCaptureAccess` equivalent for CATap.** Apple does not expose a documented live "is System Audio Recording authorized?" API. Common fallback patterns:

1. Attempt to create the tap + aggregate. Failure (`kAudioHardwareIllegalOperationError` or `kAudioHardwareBadObjectError` when the TCC prompt is declined) strongly correlates with lack of permission; branch to "request access" UX.
2. Mirror the `CGPreflightScreenCaptureAccess` check as a **proxy only** — the two services share a UI pane on macOS 14+, so Screen Recording authorization is a decent hint, but do not treat it as authoritative for CATap specifically.
3. `insidegui/AudioCap` uses the private SPI `TCCAccessPreflight(kTCCServiceAudioCapture, nil)`. Not App-Store-safe but useful for Developer ID builds.
4. Never rely on a `UserDefaults`-cached "granted" flag — the user can revoke permission in System Settings between launches, and reading stale state leads to silent recordings (buffers flow, RMS stays at -inf).

```swift
// Preferred pattern: live-check on every permission-sensitive UI refresh.
// macOS 26: Screen Recording TCC covers system audio too.
func audioCapturePermissionGranted() -> Bool {
    CGPreflightScreenCaptureAccess()
}
```

For the "granted but silent" failure mode after `rm -rf` + `cp -R` reinstall with the same Developer ID, see `distribution.md` - TCC is keyed by CDHash; a same-CDHash reinstall can leave the entry in a degraded state where it reads authorized but delivers no audio. Fix: toggle off/on in System Settings.
