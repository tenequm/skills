# Push Notifications on iOS

Remote notifications for an iOS app built from the command line: the `aps-environment` entitlement and tokens, APNs auth keys, the Notification Service Extension, communication notifications, and what the Simulator does and does not prove.

Verified on Xcode 27.2 (iOS 27.2 SDK and Simulator runtime), 2026-11-17 to 2026-11-19: `simctl help push`; the service-extension snippet compiled with `swiftc -emit-sil` in Swift 6 mode and the `async` override error reproduced against the 27.2 Simulator SDK; tokens, the extension, communication notifications, the key-environment error and the `dasd` hang observed in an XcodeGen iOS app pushed through `api.sandbox.push.apple.com` and through `simctl push` in an iOS 27.2 Simulator.

## Contents
- Entitlement and device tokens
- APNs auth keys
- Notification Service Extension
- Communication notifications
- Push in the Simulator
- Delegate callbacks

## Entitlement and device tokens

Map `aps-environment` per configuration in `project.yml` (Xcode expands build settings in entitlements files):

```yaml
targets:
  MyApp:
    entitlements:
      path: MyApp/MyApp.entitlements
      properties:
        aps-environment: $(APS_ENVIRONMENT)
    settings:
      configs:
        Debug: { APS_ENVIRONMENT: development }
        Release: { APS_ENVIRONMENT: production }
```

- A **Simulator build** with the entitlement registers and gets a real sandbox device token from `registerForRemoteNotifications()`; no provisioning profile is involved. Simulator entitlements are written to `<App>.app-Simulated.xcent` in the build intermediates - check that file when a capability seems missing.
- Without the entitlement, registration fails with `no valid "aps-environment" entitlement string found for application` (Cocoa error 3000).
- Tokens are variable length (80 bytes seen on the Simulator). Store them as hex (`token.map { String(format: "%02x", $0) }.joined()`) and never assume 32 bytes.
- Debug and Simulator builds talk to the sandbox (`api.sandbox.push.apple.com`); TestFlight and App Store builds to production (`api.push.apple.com`).

## APNs auth keys

- An APNs `.p8` is a different key from the App Store Connect API key. It is created only in the developer portal (Certificates, Identifiers & Profiles > Keys) by the Account Holder or an Admin, downloads once, and the App Store Connect API has no resource for it.
- A key limited to one environment, sent to the other host, answers 403 `BadEnvironmentKeyInToken` (observed both ways round; some docs spell it `BadEnvironmentKeyIdInToken`). Match the key's environment to the build: sandbox for Debug and Simulator, production for TestFlight.

## Notification Service Extension

The extension runs only for an alert push with `"mutable-content": 1` in `aps`. On the iOS 27.2 SDK it has no `async` override: `override func didReceive(_ request: UNNotificationRequest) async -> UNNotificationContent` fails with `method does not override any method from its superclass`. Implement the callback form and call the handler exactly once:

```swift
import UserNotifications

final class NotificationService: UNNotificationServiceExtension {
    private var contentHandler: ((UNNotificationContent) -> Void)?
    private var bestAttempt: UNMutableNotificationContent?

    override func didReceive(_ request: UNNotificationRequest,
                             withContentHandler contentHandler: @escaping (UNNotificationContent) -> Void) {
        guard let content = request.content.mutableCopy() as? UNMutableNotificationContent else {
            return contentHandler(request.content)
        }
        self.contentHandler = contentHandler
        bestAttempt = content
        content.title = "Decrypted title"    // decrypt, fetch an avatar, update from an intent
        finish(content)
    }

    override func serviceExtensionTimeWillExpire() {
        if let bestAttempt { finish(bestAttempt) }
    }

    private func finish(_ content: UNNotificationContent) {
        contentHandler?(content)
        contentHandler = nil                  // the handler must run exactly once
    }
}
```

- The extension target is `type: app-extension` in XcodeGen with its own bundle ID (`$(APP_BUNDLE_ID).NotificationService`) and its own provisioning profile.
- Its build logs `Metadata extraction skipped, no AppIntents.framework dependency found`; that is harmless.

## Communication notifications

- A sender name and avatar from `content.updating(from: intent)` (an `INSendMessageIntent`) need `com.apple.developer.usernotifications.communication` on the app **and** on the service extension. Without it `updating(from:)` still succeeds and the banner is plain.
- `UNNotificationSettings.directMessagesSetting` reads `.notSupported` without the entitlement and `.enabled` with it - a reliable assertion for a test.
- An incoming `INSendMessageIntent` built with `recipients: nil` still renders, but Intents logs `Not donating system intent because it does not have any valid parameter combinations` and `donate()` does not throw (5 of 5 pushes; a donation with recipients set was not tried).

## Push in the Simulator

```bash
xcrun simctl push "$UDID" com.example.MyApp payload.json   # or "-" for stdin
```

- The payload needs a top-level `aps` object and at most 4096 bytes; a `Simulator Target Bundle` key in it replaces the bundle ID argument.
- **`simctl push` never runs the Notification Service Extension**, even with `mutable-content: 1`. It proves delivery, `userNotificationCenter(_:willPresent:)` and the banner, not the extension. A provider push to `api.sandbox.push.apple.com` with the Simulator's real token does run it (observed: an extension that rewrote the title changed the sandbox push and left `simctl push` of the same payload untouched).
- **Notification calls can hang after a boot** (iOS 27.2 runtime, 3 of 3 boots on a loaded Mac): the permission prompt never shows, `registerForRemoteNotifications()` never returns, `notificationSettings()` never answers, `simctl push` hangs, and a banner UI test fails as "banner missing" - which reads like a bundle-ID or payload bug. Registered notification ports (`launchctl print` inside the device) do not prove the service is healthy. Restart `dasd` after every boot, before the app's first launch:
  ```bash
  xcrun simctl bootstatus "$UDID" -b
  xcrun simctl spawn "$UDID" launchctl kickstart -k "user/$(id -u)/com.apple.dasd"
  ```
  A helper that reboots with a plain `bootstatus -b` loses the fix.
- A fresh Simulator has no notification grant and no CLI to give one: testing.md, Simulator toolkit.

## Delegate callbacks

Implement `UNUserNotificationCenterDelegate` with the completion-handler methods, not the imported `async` variants: in a MainActor-default app, `nonisolated func userNotificationCenter(_:didReceive:) async` crashed on a banner tap because UIKit's completion ran off the main thread. The pattern is in concurrency-isolation.md (imported async delegate variants).
