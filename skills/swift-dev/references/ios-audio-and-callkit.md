# iOS Audio Session and CallKit

Voice-call audio on iPhone: `AVAudioSession` setup, microphone permission, interruptions and route changes, an outgoing-only CallKit call, LiveKit under CallKit, and staying alive with the screen locked.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every block built together in a scratch XcodeGen app on LiveKit 2.17.0 (`xcodebuild -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO`, Swift 6, iOS 26 target), once as is and once with `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`; the CallKit block also compiled with `swiftc -emit-sil` with and without `-default-isolation MainActor`; LiveKit behavior read from the `2.17.0` tag source; availability quoted from the iOS 27.0 SDK headers. Not run on a device.

## Contents
- [Session for a voice call](#session-for-a-voice-call)
- [Microphone permission](#microphone-permission)
- [Interruptions and route changes](#interruptions-and-route-changes)
- [CallKit: outgoing-only call](#callkit-outgoing-only-call)
- [CallKit gotchas](#callkit-gotchas)
- [LiveKit under CallKit](#livekit-under-callkit)
- [Background and the locked screen](#background-and-the-locked-screen)

## Session for a voice call

```swift
enum VoiceAudio {
    /// Call from CXStartCallAction before fulfilling it; CallKit activates the session afterwards.
    static func configure() throws {
        try AVAudioSession.sharedInstance().setCategory(
            .playAndRecord,
            mode: .voiceChat,
            options: [.allowBluetoothHFP, .defaultToSpeaker]
        )
    }
}
```

- `.voiceChat` restricts routes to VoIP-appropriate ones and "has the side effect of setting AVAudioSessionCategoryOptionAllowBluetoothHFP" (header). Echo cancellation and AGC load only when the I/O itself uses voice processing (VPIO unit or `AVAudioEngine` with voice processing on - LiveKit's default); the mode alone does not add them.
- **`.allowBluetoothHFP`, not `.allowBluetooth`.** Same raw value (`0x4`); the iOS 27 SDK header marks the old name `API_DEPRECATED_WITH_REPLACEMENT(... ios(1.0, 8.0))` and the new one `API_AVAILABLE(ios(1.0))`, so the new name back-deploys. Swift warns `'allowBluetooth' was deprecated in iOS 8.0`.
- HFP is what makes AirPods and car kits usable as a **microphone**. `.allowBluetoothA2DP` is output-only. `.bluetoothHighQualityRecording` (iOS 26+) is not for calls: the header says it "may increase input latency ... not recommended for real-time communication usage" and only works with mode `.default`.
- `.defaultToSpeaker`: loudspeaker instead of earpiece when nothing else is connected. Drop it for phone-to-ear.
- **No `.mixWithOthers`.** `.playAndRecord` is non-mixable by default, so activating it pauses Music - what a call should do. LiveKit's README and CallKit example pass `[.mixWithOthers]` in `didActivate`; do not copy that into a call app.
- Under CallKit never call `setActive(true)` yourself - CallKit activates the session (see below). Outside CallKit, `activate(options:) async throws -> Bool` is new in iOS 27; `setActive(_:)` remains for iOS 26.

## Microphone permission

```swift
func microphoneAllowed() async -> Bool {
    switch AVAudioApplication.shared.recordPermission {
    case .granted: true
    case .denied: false // only the Settings app can change it now
    case .undetermined: await AVAudioApplication.requestRecordPermission()
    @unknown default: false
    }
}
```

- `AVAudioApplication` (iOS 17+) owns permission; `AVAudioSession.recordPermission`/`requestRecordPermission(_:)` are deprecated since iOS 17.
- `requestRecordPermission()` shows the prompt only while `.undetermined`; afterwards it returns the stored answer immediately. Ask before starting the call, not inside a CallKit callback.
- Without `NSMicrophoneUsageDescription` in Info.plist "the system terminates your app" ([Apple](https://developer.apple.com/documentation/avfoundation/requesting-authorization-to-capture-and-save-media)). After `.denied`, send the user to `UIApplication.openSettingsURLString` (see ios-swiftui.md).

## Interruptions and route changes

**iOS 27 deprecates the interruption notification.** The SDK marks `AVAudioSessionInterruptionNotification`, its keys and `InterruptionType`/`InterruptionOptions` with `API_DEPRECATED("Use AVAudioSessionDidBecomeInactiveNotification and AVAudioSessionResumptionRecommendationNotification instead", ios(6.0, 27.0), ...)`. The replacements - `didBecomeActive`, `didBecomeInactive`, `resumptionRecommendation` - post on the main queue and have typed `NotificationCenter.MainActorMessage` types. Per Apple's [Handling audio interruptions](https://developer.apple.com/documentation/avfaudio/handling-audio-interruptions) they "don't get out of sync when the system can't deliver an end event".

```swift
@available(iOS 27.0, *)
@MainActor
final class AudioLifecycleObserver {
    private var tokens: [NotificationCenter.ObservationToken] = [] // observation ends when a token is dropped

    func start(onInterrupted: @escaping @MainActor (AVAudioSession.InterruptionReason) -> Void,
               onResumable: @escaping @MainActor () -> Void) {
        let session = AVAudioSession.sharedInstance()
        tokens.append(NotificationCenter.default.addObserver(of: session, for: .didBecomeInactive) { message in
            switch message.deactivationResult {
            case .systemInterruption(let context): onInterrupted(context.reason)
            case .appDeactivated: break
            @unknown default: break
            }
        })
        tokens.append(NotificationCenter.default.addObserver(of: session, for: .resumptionRecommendation) { message in
            if message.recommendation == .shouldResume { onResumable() }
        })
    }
}
```

- With an iOS 26 deployment target, gate this on `if #available(iOS 27, *)` and keep observing `AVAudioSession.interruptionNotification` (userInfo `AVAudioSessionInterruptionTypeKey`) on 26. Swift only warns about the old API once the deployment target reaches iOS 27.
- **There are no typed messages for route changes or media-services resets** in the iOS 27 SDK - only the three above. Use the `Notification.Name`s:

```swift
@MainActor
func observeRouteChanges(_ onChange: (AVAudioSession.RouteChangeReason, AVAudioSession.Port?) -> Void) async {
    let session = AVAudioSession.sharedInstance()
    for await note in NotificationCenter.default.notifications(named: AVAudioSession.routeChangeNotification, object: session) {
        guard let raw = note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt,
              let reason = AVAudioSession.RouteChangeReason(rawValue: raw) else { continue }
        // .oldDeviceUnavailable = headset or AirPods gone; output falls back to the speaker with .defaultToSpeaker.
        onChange(reason, session.currentRoute.outputs.first?.portType)
    }
}
```

- Also observe `AVAudioSession.mediaServicesWereResetNotification`: rebuild every audio object and the session config.
- **During a CallKit call most of this is CallKit's job.** A cellular call that interrupts yours arrives as `CXSetHeldCallAction` or `CXEndCallAction` plus `provider(_:didDeactivate:)`, not as something your app must resolve from session notifications. Route-change observation still matters for UI (speaker vs AirPods indicator).

## CallKit: outgoing-only call

CallKit gives the call the system call UI, lock-screen and AirPods controls, and audio-session priority. `CXProvider` is iOS-only (`API_UNAVAILABLE(macos, tvos)` in `CXProvider.h`).

The flow, from Apple's [Making and receiving VoIP calls](https://developer.apple.com/documentation/callkit/making-and-receiving-voip-calls) and the Speakerbox sample:

| Step | Who | Call |
|---|---|---|
| 1. User taps Call | app | `CXCallController.request(CXTransaction(action: CXStartCallAction(...)))` |
| 2. System accepts | delegate | `provider(_:perform: CXStartCallAction)`: `reportOutgoingCall(with:startedConnectingAt:)`, configure the session, start the network, `action.fulfill()` |
| 3. Session goes live | delegate | `provider(_:didActivate:)`: start audio I/O |
| 4. Far end answers | app | `reportOutgoingCall(with:connectedAt:)` (starts the call timer) |
| 5a. User hangs up (app, lock screen, AirPods) | delegate | `provider(_:perform: CXEndCallAction)`: tear down, `action.fulfill()` |
| 5b. Remote/network ends it | app | `reportCall(with:endedAt:reason:)` with `.remoteEnded` / `.failed` / `.unanswered` |
| 6. Session released | delegate | `provider(_:didDeactivate:)`: stop audio I/O |

```swift
@MainActor
@Observable
final class CallController: NSObject {
    static let shared = CallController()

    enum Phase: Equatable { case idle, connecting, live, ended(String) }

    private(set) var phase: Phase = .idle
    private(set) var isMuted = false

    @ObservationIgnored private let provider: CXProvider
    @ObservationIgnored private let callKit = CXCallController()
    @ObservationIgnored private var callUUID: UUID?

    override private init() {
        let configuration = CXProviderConfiguration()
        configuration.supportsVideo = false
        configuration.maximumCallGroups = 1 // default 2
        configuration.maximumCallsPerCallGroup = 1 // default 5
        configuration.supportedHandleTypes = [.generic]
        configuration.includesCallsInRecents = false // default true: calls land in the Phone app's Recents
        provider = CXProvider(configuration: configuration)
        super.init()
        provider.setDelegate(self, queue: nil) // nil = main queue, which the @MainActor conformance below relies on
    }

    func start(calling name: String) async {
        guard callUUID == nil else { return }
        let uuid = UUID()
        callUUID = uuid // claim the call before the first await, or a second tap during the prompt starts another
        guard await AVAudioApplication.requestRecordPermission() else {
            callUUID = nil
            return phase = .ended("Microphone access is off. Turn it on in Settings.")
        }
        isMuted = false
        phase = .connecting
        let start = CXStartCallAction(call: uuid, handle: CXHandle(type: .generic, value: name))
        do {
            try await callKit.request(CXTransaction(action: start))
        } catch {
            callUUID = nil
            phase = .ended("Could not start the call: \(error.localizedDescription)")
        }
    }

    /// The in-app hang-up button. CallKit answers with CXEndCallAction, same as the lock-screen button.
    func hangUp() {
        guard let uuid = callUUID else { return }
        Task {
            do { try await callKit.request(CXTransaction(action: CXEndCallAction(call: uuid))) } catch {
                finish("Call ended.") // CallKit no longer knows the call
            }
        }
    }

    /// The in-app mute button goes through CallKit too, so the system call UI shows the same state.
    func setMuted(_ muted: Bool) {
        guard let uuid = callUUID else { return }
        Task { try? await callKit.request(CXTransaction(action: CXSetMutedCallAction(call: uuid, muted: muted))) }
    }

    /// Transport callback: the far end is live. Starts the system call timer.
    func remoteAnswered() {
        guard let uuid = callUUID else { return }
        provider.reportOutgoingCall(with: uuid, connectedAt: nil)
        phase = .live
    }

    /// Transport callback: the call ended without a CXEndCallAction (remote hang-up, network failure).
    func remoteEnded(_ message: String, reason: CXCallEndedReason) {
        guard let uuid = callUUID else { return }
        provider.reportCall(with: uuid, endedAt: nil, reason: reason)
        finish(message)
    }

    private func finish(_ message: String) {
        guard callUUID != nil else { return }
        callUUID = nil
        isMuted = false
        phase = .ended(message)
        // disconnect the transport here
    }

    private func connectTransport(_ uuid: UUID) { /* open the media connection; call remoteAnswered() when live */ }
    private func applyMute(_ muted: Bool) async throws { /* mute the uplink; throw if that failed */ }
}

extension CallController: @MainActor CXProviderDelegate {
    func providerDidReset(_: CXProvider) {
        finish("The call was reset.") // drop all call state, no actions follow
    }

    func provider(_ provider: CXProvider, perform action: CXStartCallAction) {
        guard action.callUUID == callUUID else { return action.fail() } // not the call start(calling:) claimed
        provider.reportOutgoingCall(with: action.callUUID, startedConnectingAt: nil)
        do { try VoiceAudio.configure() } catch { /* log it; CallKit still activates the session */ }
        connectTransport(action.callUUID)
        action.fulfill()
    }

    func provider(_: CXProvider, perform action: CXEndCallAction) {
        action.fulfill() // no reportCall(with:endedAt:reason:) for an action CallKit itself sent
        finish("Call ended.")
    }

    func provider(_: CXProvider, perform action: CXSetMutedCallAction) {
        let muted = action.isMuted
        Task {
            do {
                try await applyMute(muted)
                isMuted = muted
                action.fulfill()
            } catch {
                action.fail() // isMuted keeps the state the mic is really in
            }
        }
    }

    func provider(_: CXProvider, didActivate _: AVAudioSession) {
        // Start audio I/O here and only here.
    }

    func provider(_: CXProvider, didDeactivate _: AVAudioSession) {
        // Stop audio I/O; the session is no longer yours.
    }
}
```

- **`didActivate`/`didDeactivate` are the only safe points for audio I/O.** Apple's sample: "Configure the audio session but do not start call audio here. Call audio should not be started until the audio session is activated by the system, after having its priority elevated." Configure the category in `CXStartCallAction` (before `fulfill()`), start the engine in `didActivate`, stop it in `didDeactivate`.
- **Route every user mute through `CXSetMutedCallAction`.** The lock-screen mute button arrives as that action, and since iOS 17 "all CallKit apps will get Press to Mute and Unmute support [for AirPods] with absolutely no additional adoption necessary" ([WWDC23 10233](https://developer.apple.com/videos/play/wwdc2023/10233)). Muting the track directly from your own button leaves the system UI showing the wrong state. Fulfill the action only after the mic change succeeded, else `action.fail()` and keep the old state - as LiveKit's CallKit example does.
- Never report `reportCall(with:endedAt:reason:)` for a call that CallKit ended with `CXEndCallAction` - fulfilling the action is the report.
- `CXProviderConfiguration` defaults: `maximumCallGroups` 2, `maximumCallsPerCallGroup` 5, `includesCallsInRecents` true, `supportsVideo` false. `localizedName` is deprecated (iOS 14); the system shows the bundle display name. `iconTemplateImageData` takes a 40 pt square template image. `CXHandle(type: .generic, value:)` is the right handle for a non-phone-number destination.
- `includesCallsInRecents = false` keeps calls out of the Phone app's Recents - right for calls to an agent or a room rather than a person the user would redial.
- **Outgoing-only needs no VoIP push.** Outgoing calls start from an in-app interaction, a URL, or Siri; PushKit is only how *incoming* calls wake the app. For incoming calls you need PushKit (`PKPushRegistry`, `.voIP`), the push entitlement, and `reportNewIncomingCall(with:update:completion:)` for every VoIP push - since iOS 13, a push that is not reported as a call gets the app terminated, and repeated misses stop push delivery.
- `setDelegate(self, queue: nil)` delivers on the main queue, which is what makes the `@MainActor` conformance safe (it traps if ever called elsewhere). It also lets the mute handler capture the non-`Sendable` action in a `Task` and fulfill it after the `await`; from a `nonisolated` method that capture is `error: sending 'action' risks causing data races`. See concurrency-isolation.md.

## CallKit gotchas

- **CallKit does not work in the Simulator.** Transactions fail or the call is ended immediately, and `didActivate` is not delivered; Apple's docs do not state it, but [Stack Overflow](https://stackoverflow.com/questions/65501603/is-it-possible-to-receive-calls-using-callkit-in-ios-simulator) and Apple forum reports agree. Compile a fallback that skips CallKit and lets LiveKit manage the session:
  ```swift
  #if targetEnvironment(simulator)
  private static let usesCallKit = false
  #else
  private static let usesCallKit = true
  #endif
  ```
- **`didActivate` sometimes never fires**, and every later call then has no audio until relaunch. Apple DTS ([forum 837211](https://developer.apple.com/forums/thread/837211), iOS 27): `callservicesd` holds a stale audio-session ID for the app; one race happens when the provider is created right after first unlock. Fixes from DTS: create the `CXProvider` lazily (first call), and re-push the configuration before reporting a call - `provider.configuration = provider.configuration` is the "setConfiguration" workaround. Also add a timeout: if `didActivate` has not arrived a few seconds after `fulfill()`, end the call with `.failed` so CallKit's state machine resets.
- **`providerDidReset` means `callservicesd` restarted.** Drop all call state; transactions for old UUIDs fail with `unknownCallUUID`. DTS advice ([forum 817614](https://developer.apple.com/forums/thread/817614)): keep the CallKit stack isolated so it can be destroyed and recreated.
- **Double start.** A second tap (or Action Button press) while the microphone prompt is up passes an "is a call active" check placed before the `await`. With `maximumCallGroups = 1` CallKit rejects the second `CXStartCallAction`, and the first call stays stuck in the system UI. Claim the call before the first `await` and `action.fail()` a start whose UUID is not the claimed one (both in `CallController` above). A code-review finding, fixed but not reproduced.
- **China.** App Review rejects apps with CallKit active in the China storefront (Guideline 5.0, at the MIIT's request, since 2018 - [rejection text quoted here](https://github.com/Azure/azure-sdk-for-ios/issues/1537)). Either exclude China in App Store Connect or disable CallKit there and fall back to plain in-app audio.
- Unverified: whether `UIBackgroundModes` must contain `voip` for an outgoing-only provider. Old reports say the provider resets immediately without it; shipping voice-call apps and LiveKit's example declare it, so declare it.

## LiveKit under CallKit

Read from LiveKit Swift at the `2.17.0` tag - [Docs/audio.md](https://github.com/livekit/client-sdk-swift/blob/main/Docs/audio.md), `Sources/LiveKit/Audio/Manager/AudioManager.swift` - and the [CallKit example](https://github.com/livekit-examples/swift-example-collection/tree/main/callkit) (`4482e33`). LiveKit manages `AVAudioSession` itself by default, which fights CallKit. Hand the session to CallKit and gate the engine on the activation window:

```swift
/// LiveKit's side of a CallKit call. One instance per call; each method names the CallController hook that calls it.
@MainActor
final class LiveKitCall: NSObject {
    // Default options cover every publish, including the new track an unmute creates after a full reconnect.
    let room = Room(roomOptions: RoomOptions(defaultAudioPublishOptions: AudioPublishOptions(dtx: false, red: false)))
    var onRemoteLeft: (String?) -> Void = { _ in } // room metadata at the time, e.g. an end reason

    private var wantsMuted = false
    private var joined = false // callbacks before connect returns are a failed connect's cleanup
    private var micPublished = false

    /// CallController.init, before any Room exists. In the Simulator skip this and let LiveKit manage the session.
    static func handAudioToCallKit() throws {
        AudioManager.shared.audioSession.isAutomaticConfigurationEnabled = false
        try AudioManager.shared.setEngineAvailability(.none)
    }

    /// provider(_:didActivate:)
    static func sessionActivated() throws { try AudioManager.shared.setEngineAvailability(.default) }

    /// provider(_:didDeactivate:)
    static func sessionDeactivated() throws { try AudioManager.shared.setEngineAvailability(.none) }

    /// connectTransport(_:), right after CXStartCallAction. Publishing before didActivate is fine:
    /// the engine stays off until then and honors the pending request.
    func join(url: String, token: String) async throws {
        room.add(delegate: self)
        try await room.connect(url: url, token: token)
        joined = true
        // setMicrophone(enabled: false) does nothing before a track exists, so publish one in the wanted state.
        let mic = await LocalAudioTrack.createTrack()
        if wantsMuted { try await mic.mute() }
        try await room.localParticipant.publish(audioTrack: mic)
        micPublished = true
        if mic.isMuted != wantsMuted { try await room.localParticipant.setMicrophone(enabled: !wantsMuted) }
    }

    /// applyMute(_:), from CXSetMutedCallAction. A throw fails the action.
    func setMuted(_ muted: Bool) async throws {
        wantsMuted = muted
        guard micPublished else { return } // join publishes in this state
        try await room.localParticipant.setMicrophone(enabled: !muted)
    }

    /// finish(_:)
    func leave() async {
        joined = false
        await room.disconnect()
    }
}

extension LiveKitCall: RoomDelegate {
    nonisolated func room(_ room: Room, participantDidDisconnect _: RemoteParticipant) {
        // Read SDK state now, not in the task: a full reconnect reports every participant gone while
        // .reconnecting, and a disconnect resets the room (metadata nil) right after this returns.
        guard room.connectionState != .reconnecting else { return }
        let metadata = room.metadata
        Task { @MainActor in if joined { onRemoteLeft(metadata) } }
    }
}
```

- `setEngineAvailability(.none)` keeps the engine off "even if recording or playback is requested"; back at `.default`, "the engine will start as soon as possible if recording and/or playback had been previously requested while disabled (i.e., pending requests are honored once availability allows)" - so connecting and publishing before `didActivate` is correct.
- With automatic configuration off, "the SDK will not touch the session category. Make sure your app sets `.playAndRecord` before unmuting or publishing the mic." `VoiceAudio.configure()` in `CXStartCallAction` does that.
- Permission: `setEngineAvailability(_:)` does not prompt; restoring input without permission throws `LiveKitError` `.deviceAccessDenied`. Request permission before `CXStartCallAction` (the `start(calling:)` guard above).
- `AudioPublishOptions(dtx:red:)` both default to `true`. DTX stops sending packets during silence; turn it off when the far end detects end-of-turn from the silence it hears (voice agents), or it may never see the turn end. `red: false` drops redundant audio encoding. Set them as `RoomOptions.defaultAudioPublishOptions`, not only on the first publish (see the reconnect notes below).
- Mute modes (`AudioManager.shared.set(microphoneMuteMode:)`): `.voiceProcessing` (default) - fast, mic indicator off, but "iOS plays a short system sound when muting or unmuting"; `.inputMixer` - no sound, mic indicator stays on; `.restart` - slow, reconfigures the session, avoid.

```swift
func useSilentMute() throws {
    try AudioManager.shared.set(microphoneMuteMode: .inputMixer) // no system beep; mic indicator stays on
}
```

- Incoming calls (example README): call `reportNewIncomingCall` on the PushKit callback's thread, and set `.playAndRecord` before reporting when woken in the background.
- `RoomDelegate` is `Sendable` and calls back on LiveKit's internal queue, not the main thread: hop with `Task { @MainActor in }` into one idempotent `refresh()` - never `MainActor.assumeIsolated` or an isolated conformance there. Pattern and ordering rules: see concurrency-isolation.md. Caveat: state the SDK resets (`room.metadata`, `connectionState == .reconnecting`) must be read synchronously inside the `nonisolated` callback and passed into the task as values; re-reading it after the hop sees the reset or the next state.

### Room lifecycle traps

From the LiveKit 2.17.0 source, not run, unless marked:

- **Full reconnect looks like everyone leaving.** `Room.cleanUp(isFullReconnect: true)` runs `cleanUpParticipants`, and `Participant.cleanUp` fires `room(_:participantDidDisconnect:)` for every remote participant while `connectionState` is still `.reconnecting` (`Core/Room.swift`, `Participant/Participant.swift`). Guard on it, as `LiveKitCall` does.
- **Muted tracks are not republished.** After a full reconnect `LocalParticipant.republishAllTracks()` skips muted tracks (`Core/Room+EngineDelegate.swift`, `Participant/LocalParticipant.swift`). A later `setMicrophone(enabled: true)` creates a new track with `publishOptions: nil`, which falls back to `roomOptions.defaultAudioPublishOptions` - DTX back on unless the room default turns it off.
- **Muting before the first publish does nothing.** `set(source:enabled:)` mutes an existing publication; with none, `enabled: false` returns `nil` (`Participant/LocalParticipant.swift`). To start muted: `await LocalAudioTrack.createTrack()`, `mute()`, then `publish(audioTrack:options:)`.
- **Room state is reset before `didDisconnectWithError`.** `cleanUp` replaces the whole state (metadata `nil`, `.disconnected`) and the state observer then notifies the delegate (`Core/Room.swift`, `Core/Room+EngineDelegate.swift`), so `room.metadata` is already gone there. Cache it from `room(_:didUpdateMetadata:)`, or read it in `participantDidDisconnect`, which the SDK awaits before resetting.
- **A failed connect reports participants leaving first.** Observed once in the Simulator: when `room.connect` timed out on ICE, `participantDidDisconnect` for the already-joined agent arrived before `connect` threw, and the app showed "agent left". The source matches: `connect`'s catch runs `cleanUp(withError:)` before rethrowing (`Core/Room.swift`), and the reset from `.connecting` fires `didFailToConnectWithError`, not `didDisconnectWithError`. Ignore room callbacks until `connect` returns (`joined` above); the fix is build-tested only.
- **Agent captions are text streams.** livekit-agents 1.x sends transcriptions on the text-stream topic `lk.transcription` (`Agent/Chat/Receive/TranscriptionStreamReceiver.swift`); `room(_:participant:trackPublication:didReceiveTranscriptionSegments:)` fires only for the legacy transcription data packet (`Core/Room.swift`); do not wait on it for agent captions. `Room.registerTextStreamHandler(for:onNewStream:)` registers unordered: each stream's handler runs in its own detached task (`DataStream/Incoming/IncomingStreamManager.swift`), so sort by `info.timestamp`. A second handler for the same topic throws `StreamError.handlerAlreadyRegistered` - the SDK's agent `Session` registers `lk.transcription` itself.

```swift
struct Caption: Sendable {
    let segment: String
    let text: String
    let isFinal: Bool
    let sentAt: Date
}

/// Register before room.connect so early captions are not missed.
func listenForCaptions(in room: Room, _ onCaption: @escaping @MainActor (Caption) -> Void) async throws {
    try await room.registerTextStreamHandler(for: "lk.transcription") { reader, _ in
        let text = try await reader.readAll()
        let info = reader.info
        await onCaption(Caption(segment: info.attributes["lk.segment_id"] ?? info.id, text: text,
                                isFinal: info.attributes["lk.transcription_final"] == "true", sentAt: info.timestamp))
    }
}
```

## Background and the locked screen

Info.plist keys for a call app (XcodeGen `info.properties` form; these keys built in the scratch app):

```yaml
NSMicrophoneUsageDescription: Sends your voice to the person you call.
UIBackgroundModes: [audio, voip]
```

- What keeps the app running with the screen locked is an **active audio session doing I/O** under the `audio` mode. CallKit itself grants nothing: "It provides no additional facilities for ring indication or background execution" (Apple DTS, [forum 87551](https://developer.apple.com/forums/thread/87551)). Once CallKit activates the session and the engine runs, the app (and its WebSocket/WebRTC connection) keeps running; once `didDeactivate` stops the engine, normal suspension applies again.
- `voip` is what PushKit VoIP pushes require; see the Unverified note above for outgoing-only.
- Secrets the call needs while locked (tokens) must be readable after first unlock - `kSecAttrAccessibleAfterFirstUnlock`, see keychain.md.
- Starting the call from the Action Button or Siri is an App Intent - see app-intents.md.
- Unverified: a web page (Safari, WebRTC) cannot keep the microphone running with the screen locked the way a CallKit app can - observed while building a voice-call app, not documented by Apple.
