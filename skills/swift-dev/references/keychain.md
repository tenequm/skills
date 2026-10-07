# Keychain

Storing small secrets (tokens, passwords, call links) as generic-password items with one helper that behaves the same on iOS and macOS, plus the accessibility, sharing and macOS-keychain rules that decide whether a read succeeds.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: the helper compiled with `swiftc -emit-sil` for iOS and macOS (also under `-default-isolation MainActor`); ran it in an app-hosted test on an iOS 27.0 simulator (add, update-on-duplicate, load, delete, accessibility change all pass); ran it from an unsigned and an Apple Development-signed macOS command-line tool (data protection keychain refused with `-34018`).

## Contents
- The helper
- Why update instead of delete + add
- Accessibility: when the item can be read
- macOS: two keychains
- Sharing between apps and extensions
- Errors

## The helper

```swift
import Foundation
import Security

/// Generic-password items in the data protection keychain, the same store on iOS and macOS.
nonisolated enum Keychain {
    struct Failure: Error, CustomStringConvertible {
        let status: OSStatus
        var description: String {
            (SecCopyErrorMessageString(status, nil) as String?) ?? "OSStatus \(status)"
        }
    }

    static func save(
        _ data: Data,
        service: String,
        account: String,
        accessible: CFString = kSecAttrAccessibleAfterFirstUnlock
    ) throws(Failure) {
        let query = itemQuery(service: service, account: account)
        let attributes: [String: Any] = [
            kSecValueData as String: data,
            kSecAttrAccessible as String: accessible,
        ]
        var status = SecItemAdd(query.merging(attributes) { $1 } as CFDictionary, nil)
        if status == errSecDuplicateItem {
            status = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        }
        guard status == errSecSuccess else { throw Failure(status: status) }
    }

    /// Nil when there is no item; throws for anything else, including a locked device.
    static func load(service: String, account: String) throws(Failure) -> Data? {
        var query = itemQuery(service: service, account: account)
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne
        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        if status == errSecItemNotFound { return nil }
        guard status == errSecSuccess else { throw Failure(status: status) }
        return result as? Data
    }

    static func delete(service: String, account: String) throws(Failure) {
        let status = SecItemDelete(itemQuery(service: service, account: account) as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else { throw Failure(status: status) }
    }

    private static func itemQuery(service: String, account: String) -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            // Ignored on iOS; on macOS selects the iOS-style store instead of the login keychain file.
            kSecUseDataProtectionKeychain as String: true,
        ]
    }
}
```

Usage: `try Keychain.save(Data(token.utf8), service: "com.example.VoiceApp", account: "call-link")`, `try Keychain.load(service:account:)`.

- A generic password is identified by class + `kSecAttrService` + `kSecAttrAccount` (+ access group). Use your bundle ID as the service and a fixed key name as the account.
- `load` separates "no item" (`nil`) from "item exists but cannot be read now" (throws). Treating every failure as "not set" makes a locked phone look like a logged-out user and invites overwriting the real secret.
- `nonisolated` keeps the enum callable from any isolation when the target uses `SWIFT_DEFAULT_ACTOR_ISOLATION: MainActor`. SecItem calls block the calling thread ("can cause your app's UI to hang if called from the main thread" - [SecItemUpdate](https://developer.apple.com/documentation/security/secitemupdate(_:_:))); a one-off read of a small item at launch is fine, anything in a loop or on a hot path belongs off the main actor.
- `kSecReturnData` with `kSecMatchLimitOne` returns a single `Data`.

## Why update instead of delete + add

The common shortcut `SecItemDelete(query); SecItemAdd(item)` has three problems the add-then-update helper avoids:

- **It is not atomic.** If the add fails - the device is locked and the item's class is not readable yet, the process is killed between the calls, or the add hits an entitlement error - the old secret is already gone.
- **It drops what you did not re-specify** on the old item: its accessibility, access group, label, creation date.
- **On a synchronizable item, a delete propagates to every device** before the add syncs back ([kSecAttrSynchronizable](https://developer.apple.com/documentation/security/ksecattrsynchronizable): "Updating or deleting items using the kSecAttrSynchronizable key affects all copies of the item").

Apple's own guidance is to update the existing item, since "the new item can't coexist with the old one" and re-adding with changed primary attributes leaves "old, abandoned items" ([Updating and deleting keychain items](https://developer.apple.com/documentation/security/updating-and-deleting-keychain-items)). `SecItemUpdate` can also change `kSecAttrAccessible`: saving with `WhenUnlocked` and then with `AfterFirstUnlock` left the item at `ck` (AfterFirstUnlock) in the simulator test - that is how you migrate existing items.

## Accessibility: when the item can be read

`kSecAttrAccessible` is set when the item is written; the default is `kSecAttrAccessibleWhenUnlocked`.

| Value | Readable | Restores to a new device from an encrypted backup |
|---|---|---|
| `kSecAttrAccessibleWhenUnlocked` (default) | only while unlocked | yes |
| `kSecAttrAccessibleAfterFirstUnlock` | after the first unlock since boot, until reboot - including while locked | yes |
| `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` | only while unlocked | no |
| `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly` | after first unlock, including while locked | no |
| `kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly` | only while unlocked; cannot be stored without a passcode, deleted if the passcode is removed | no |

- **Anything read while the phone is locked needs an `AfterFirstUnlock` class.** A call started from the lock screen or the Action Button, a CallKit/VoIP flow, a background refresh - all run with the device locked, and a `WhenUnlocked` item is unreadable there. Apple recommends AfterFirstUnlock "for items that need to be accessed by background applications" ([kSecAttrAccessibleAfterFirstUnlock](https://developer.apple.com/documentation/security/ksecattraccessibleafterfirstunlock)). After a reboot nothing in that class is readable until the user unlocks once.
- **`ThisDeviceOnly`** items are restored only to the same device that made the backup; on a new phone the user has to sign in again. Use it for device-bound secrets (a device key, a token tied to this install), not for credentials the user expects to survive a phone upgrade. `ThisDeviceOnly` classes cannot be combined with `kSecAttrSynchronizable` (iCloud Keychain).
- Use the most restrictive class that still works. `kSecAttrAccessibleAlways` is deprecated (since iOS 12 / macOS 10.14); for a user-presence check (Face ID / passcode at read time) pass a `SecAccessControl` in `kSecAttrAccessControl` instead of `kSecAttrAccessible` ([Restricting keychain item accessibility](https://developer.apple.com/documentation/security/restricting-keychain-item-accessibility)).
- Unverified: reading a `WhenUnlocked` item on a locked device surfaces as `errSecInteractionNotAllowed` (-25308); not reproduced on hardware.

## macOS: two keychains

macOS has the file-based keychain (login.keychain-db, ACLs, "wants to access your keychain" prompts) and the data protection keychain (the iOS model: access groups, accessibility classes, iCloud sync). **SecItem targets the file-based keychain by default**; `kSecUseDataProtectionKeychain: true` (or `kSecAttrSynchronizable: true`) selects the data protection one ([TN3137](https://developer.apple.com/documentation/technotes/tn3137-on-mac-keychains)). Apple's advice is to set the key on all platforms - other platforms ignore it - so iOS code behaves the same on the Mac.

- **The data protection keychain needs an entitlement-bearing, provisioned signature.** Its access groups come from the code signature's entitlements (`com.apple.application-identifier`, `keychain-access-groups`), and on macOS those "must be authorized by a provisioning profile". Measured: the helper run from a plain command-line tool - ad-hoc signed by the linker, and again signed with an Apple Development identity but no profile - failed on the first `SecItemAdd` with `-34018 A required entitlement is not present.` (`errSecMissingEntitlement`). Per TN3137, an app whose provisioning profile authorizes its app ID gets access; a bare CLI tool needs an app-like bundle with an embedded profile or must use the file-based keychain.
- **The file-based keychain worked from the same unsigned tool** (add, duplicate add -> `-25299`, read, delete; no prompt, because the creating process is on the item's ACL). The trade-off: ACL-based access control instead of access groups, no accessibility classes, no iCloud sync. Unverified: a rebuilt ad-hoc binary (new code signature) gets the "wants to access your keychain" prompt for items an earlier build created. It is also the only option for `launchd` daemons - the data protection keychain exists only in a user login session.
- Mac Catalyst and iOS apps on the Mac always use the data protection keychain.
- Keychain Access shows data protection items under "Local Items" / "iCloud", and only password items; the `security` CLI mostly sees the file-based keychain.

## Sharing between apps and extensions

An item belongs to exactly one access group; an app belongs to several ([Sharing access to keychain items](https://developer.apple.com/documentation/security/sharing-access-to-keychain-items-among-a-collection-of-apps)):

1. groups from the Keychain Sharing capability (`keychain-access-groups`), each prefixed with the team ID,
2. its application identifier, `TEAMID.bundle.id` - the private default group,
3. its App Groups (`group.com.example...`, no team prefix).

Without `kSecAttrAccessGroup` an item goes to the first group in that list: the app ID unless a Keychain Sharing group is listed. The simulator test item landed in `ABCDE12345.com.example.VoiceApp` (team ID prefix + bundle ID). To share a secret with a widget, intent or notification extension, add the same Keychain Sharing group (or App Group) to both targets and pass `kSecAttrAccessGroup: "ABCDE12345.com.example.shared"` in every query, including reads (replace `ABCDE12345` with your Team ID). Naming a group the app is not entitled to fails with `errSecMissingEntitlement`; check the real entitlements with `codesign -d --entitlements :- <App.app>` on a device build. In XcodeGen, declare them under the target's `entitlements:` with `path` and `properties`.

## Errors

`SecCopyErrorMessageString(status, nil)` (iOS 11.3+, macOS) turns any `OSStatus` into text - the helper's `Failure.description` uses it. The codes you will meet:

| Status | Constant | Meaning |
|---|---|---|
| `-25299` | `errSecDuplicateItem` | add hit an existing item - update it |
| `-25300` | `errSecItemNotFound` | no matching item (a normal "not set") |
| `-25308` | `errSecInteractionNotAllowed` | "User interaction is not allowed." - item not readable in the current state |
| `-34018` | `errSecMissingEntitlement` | "A required entitlement is not present." - access group not entitled, or a macOS process without a provisioned signature using the data protection keychain |
| `-25293` | `errSecAuthFailed` | authentication failed (wrong password, cancelled user-presence check) |
