# CI on GitHub Actions

Efficient GitHub Actions CI for Swift iOS and macOS apps and packages: runner choice and cost, exact Xcode selection, job shape and the required-check trap, build flags that pay, Xcode's compilation cache, what not to cache, cache scoping, simulators and UI tests on hosted runners, permission-gated macOS tests, signing and notarization in CI, supply chain, and how to debug a slow or hanging run.

Verified 2026-11-18 against the [runner-images](https://github.com/actions/runner-images) READMEs (`xcode-27` image 20261104.0337.1, `macos-26` arm64 image 20261102.0473.1), GitHub's Actions docs and changelogs linked inline, swift-build `main` ([c6a6491](https://github.com/swiftlang/swift-build/tree/c6a6491a4212b7bcee141e89f0e8d7b059b051cb)) for the compilation-cache settings, and `xcodebuild -help` on Xcode 27.2 (27B52). Re-checked 2026-11-19: runner-images README labels, the `ubuntu-26.04` image README, the `xcode-27` prerelease 20261119.0378.1, and XcodeGen 2.48.0. Points marked "verified on Xcode 27.2 locally" were built on a Mac (macOS 27.3, Xcode 27.2, Swift 6.4.2), not on a runner. Measured numbers come from two production pipelines: an XcodeGen iOS app on `xcode-27` (unit, app and UI tests, compilation cache) and a SwiftPM macOS app on `macos-26` (SwiftPM cache, signed bundle, permission-gated tests, notarized releases). Each number says which, and how many runs back it.

## Contents
- Runners and cost
- Selecting an exact Xcode
- Linux for package tests
- Job shape
- Build flags that pay
- Xcode compilation cache
- What not to cache
- SwiftPM-only apps
- Cache scoping rules
- Simulators on hosted runners
- UI tests
- Permission-gated tests on macOS runners
- Signing, TestFlight and notarization
- Supply chain
- Debugging slow or hanging CI

## Runners and cost

| Label | Image | Xcode | Notes |
|---|---|---|---|
| `xcode-27`, `xcode-27-xlarge` | macOS 27, arm64 only | 27.0, 27.1 (default), 27.2 | The only way to macOS 27: there is no `macos-27` label |
| `macos-26`, `macos-latest`, `macos-26-xlarge` | macOS 26, arm64 | 26.0.1 to 26.6 | Use for Xcode 26 |
| `macos-26-intel`, `macos-26-large`, `macos-latest-large` | macOS 26, x64 | Xcode 26 only | Intel stops at Xcode 26: Xcode 27 installs only on Apple silicon |
| `macos-15`, `macos-15-intel` | macOS 15 | - | `macos-14` left Actions on 2026-11-02 |

- GitHub now builds one image per **major Xcode** rather than per macOS ([changelog](https://github.blog/changelog/2026-07-16-xcode-27-runner-image-now-in-public-preview/)). `xcode-27` went GA on [2026-10-15](https://github.blog/changelog/2026-10-15-xcode-27-runner-image-generally-available/), though the runner-images README badge and [issue #14404](https://github.com/actions/runner-images/issues/14404) still say "preview". Where `macos-latest` points next is unannounced; never use it for app builds.
- Standard arm64 runners are a **3 vCPU M1 with 7 GB RAM and 14 GB SSD**, public or private; xlarge is a 5-core M2 Pro with 14 GB and needs Team or Enterprise ([hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), [larger runners](https://docs.github.com/en/actions/reference/runners/larger-runners)). That runner is the low-core, low-memory machine your laptop is not: it exposes concurrency and memory bugs that never show locally (see Debugging).
- On private repos a macOS minute costs about 10x a Linux one ([pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing)), and minutes round up per job. Standard runners are free on public repos; larger runners are billed even there.
- At most **5 concurrent macOS jobs** on Free, Pro and Team, shared between standard and larger macOS runners ([limits](https://docs.github.com/en/actions/reference/limits)). Observed once: only 3 `xcode-27` jobs ran at a time on a free account, a fourth queued.
- **Capacity fails jobs.** Observed on `macos-26` arm64: a job queued 15 minutes with no steps, then failed with `The job was not acquired by Runner of type hosted even after multiple attempts` next to the notice `Due to capacity constraints, jobs targeting macOS arm64 runners may experience longer queue times.` Queue waits of 5 and 15 minutes also occurred on ordinary days. Re-run it; do not debug it. Keep every job that does not need macOS (lint, release tooling, changelogs, PR-title checks) on Linux so it never competes for a macOS slot.

## Selecting an exact Xcode

```yaml
jobs:
  build:
    runs-on: xcode-27
    timeout-minutes: 20
    env:
      DEVELOPER_DIR: /Applications/Xcode_27.2.app/Contents/Developer
    steps:
      - run: xcodebuild -version && xcrun simctl list runtimes
```

- `DEVELOPER_DIR` overrides `xcode-select` per process with no `sudo` (`man xcode-select`). Set it in job `env:` or append it to `$GITHUB_ENV` from a setup step.
- Pin the **major.minor** path (`Xcode_27.2.app`, `Xcode_26.4.app`), not a patch path: images replace the previous patch when a new one ships ([image policy](https://github.com/actions/runner-images)), and two-part aliases such as `Xcode_26.4.app -> Xcode_26.4.1.app` survive that. A pin can still vanish (on `macos-15` a workflow's `Xcode_26.0.app` was gone after a January 2026 image update, [OneBusAway #1151](https://github.com/OneBusAway/onebusaway-ios/pull/1151)), so fail fast with `test -d "$DEVELOPER_DIR"` in the first step.
- Log `xcodebuild -version` and the runtimes in every job. Images roll back and the README can list what is not installed: image 20261112.0361.1 was rolled back and its README named an Xcode 27.3 beta that was not there ([#15337](https://github.com/actions/runner-images/issues/15337)). The README and #14404 disagree on the `macos-26` default (26.6 vs 26.5), so read the log, not the table.
- Pick the Xcode your Mac builds with, then check the image has a simulator runtime for it (see Simulators). Runners lag developer Macs by months (observed: a runner on Swift 6.3.3 / Xcode 26.6 for three months while the Mac moved to Swift 6.4), so breakage from a newer local toolchain never shows in CI until you move the pin.
- Match `runs-on` to the deployment target: a macOS test binary with a macOS 26.1 minimum compiles on `macos-15` and then will not launch there (observed).
- XcodeGen is not on the images. Download a pinned release and check its SHA-256 (1-2 s, cheaper than any cache); use 2.48.0 with Xcode 27.2: 2.47.0 and 2.48.0 fix 27.2 project-open and conversion bugs in affected layouts, and 2.47.0 makes schemes default to `buildArchitectures: matchRunDestination` ([2.47.0](https://github.com/yonaskolb/XcodeGen/releases/tag/2.47.0), [2.48.0](https://github.com/yonaskolb/XcodeGen/releases/tag/2.48.0)). A plain app from 2.46.0 still built (verified on Xcode 27.2 locally).

## Linux for package tests

`ubuntu-24.04` and `ubuntu-26.04` (also `-arm`) ship Swift 6.4.2, Swift Testing is part of the Linux toolchain, and a Linux job costs a tenth of a macOS one. Run a package there only when it is platform-neutral:

- Linux Foundation is swift-foundation plus swift-corelibs-foundation, compatible with Darwin Foundation on a "best-effort" basis ([corelibs-foundation](https://github.com/swiftlang/swift-corelibs-foundation)). No SwiftUI, UIKit, AppKit, SwiftData, Combine or `os`; CryptoKit needs swift-crypto. One `import CryptoKit` or `OSAllocatedUnfairLock` keeps the whole package on macOS (that is why the XcodeGen iOS app's core tests stayed there).
- Guard platform code with `#if canImport(...)` (spm-and-builds.md, Conditional compilation) and add a Linux job only after `swift build` passes in a `swift:6.4` container locally.
- For a library others consume, the [swiftlang/github-workflows](https://github.com/swiftlang/github-workflows) reusable workflow tests Linux and Windows across Swift versions; pin it by SHA.
- Cache `.build` keyed on `Package.resolved` plus the Swift version, exactly as for SwiftPM-only apps below.

## Job shape

Cheap work first and on Linux, macOS jobs in parallel, every job bounded, one required gate.

```yaml
on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  changes:
    runs-on: ubuntu-slim
    timeout-minutes: 5
    permissions:
      pull-requests: read
    outputs:
      app: ${{ steps.filter.outputs.app }}
    steps:
      # Pull requests only: the action lists changed files through the API, no checkout.
      - uses: dorny/paths-filter@ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d # v4.0.3
        id: filter
        if: github.event_name == 'pull_request'
        with:
          predicate-quantifier: every
          filters: |
            app:
              - '**'
              - '!**/*.md'
              - '!docs/**'

  app-tests:
    needs: changes
    if: github.event_name != 'pull_request' || needs.changes.outputs.app == 'true'
    runs-on: xcode-27
    timeout-minutes: 25
    steps:
      - run: echo "build and test here"

  gate:
    if: always()
    needs: [changes, app-tests]
    runs-on: ubuntu-slim
    timeout-minutes: 5
    env:
      RESULTS: ${{ join(needs.*.result, ' ') }}
    steps:
      - run: |
          for r in $RESULTS; do
            case $r in success|skipped) ;; *) echo "a job ended $r" >&2; exit 1 ;; esac
          done
```

- **The required-check trap.** A workflow skipped by `paths`/`paths-ignore`, a branch filter or a skip-ci commit message leaves its checks **Pending**, and a PR that requires them can never merge ([skipping runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs)). A *job* skipped by an `if:` reports success. So: never put `paths-ignore` on a workflow whose jobs are required; always trigger, skip heavy jobs with a job-level `if:` on a paths-filter output, and make the single `if: always()` gate the only required check. Filter only `pull_request` runs and filter by exclusion (everything except docs): on `push` and `workflow_dispatch` paths-filter diffs against the previous push or only the last commit, and an allow-list of source globs skips the job for asset, plist and entitlement changes. Without `if: always()` the gate itself is skipped when a dependency fails, and skipped counts as passing. [re-actors/alls-green](https://github.com/re-actors/alls-green) is the packaged version of the loop above.
- **Timeouts on every macOS job.** The default `timeout-minutes` is 360; a hung `swift test` or `xcodebuild` prints nothing and bills six hours. Measured job lengths for sizing: core package tests 1m38s, an unsigned device build 3m31s, build-for-testing plus app tests 11m39s (XcodeGen iOS app); a whole SwiftPM-app job 2.5 to 4.5 minutes. Set the limit at roughly twice the normal time; add step-level `timeout-minutes` on the first `simctl` call and on test steps.
- **`concurrency`** as above cancels superseded PR runs and keeps every push to `main`. A workflow-wide `cancel-in-progress: true` also cancels `main` runs when two pushes land together (observed). Put publish jobs in their own workflow so no cancel group reaches them.
- **`needs:` costs wall time.** Gating the two long macOS jobs on a 1m38s core job delayed every green run by that much plus runner pickup. On a public repo, where minutes are free, run macOS jobs in parallel; gate on a cheap job only when the minutes cost money and the cheap job fails often.
- **Fan-out on macOS is expensive**: each job pays checkout, toolchain setup, cache restore and a cold simulator, under a 5-job cap. One job that runs `build-for-testing` once and then `test-without-building` beats per-target jobs; split only where wall time matters (a slow UI suite).
- Keep a PR-title or description lint in its own Linux workflow, so its `edited` trigger never starts a macOS job.
- Steps can run in parallel inside one job (`background: true`, `wait`, [changelog 2026-06-25](https://github.blog/changelog/2026-06-25-actions-steps-can-now-be-run-in-parallel)), but see Simulators before booting one beside a build, and Supply chain for actionlint's false reports on them.

## Build flags that pay

```bash
xcodebuild build-for-testing -project App.xcodeproj -scheme App \
  -destination "id=$SIM_UDID" -derivedDataPath build \
  -onlyUsePackageVersionsFromResolvedFile -disableAutomaticPackageResolution \
  -skipPackagePluginValidation -skipMacroValidation \
  COMPILER_INDEX_STORE_ENABLE=NO CODE_SIGNING_ALLOWED=NO
xcodebuild test-without-building -project App.xcodeproj -scheme App \
  -destination "id=$SIM_UDID" -derivedDataPath build
```

- **Commit `Package.resolved`** and pass `-disableAutomaticPackageResolution`, which Apple's [CI guide](https://developer.apple.com/documentation/xcode/building-swift-packages-or-apps-that-use-them-in-continuous-integration-workflows) names; `-onlyUsePackageVersionsFromResolvedFile` has the identical `xcodebuild -help` description. XcodeGen users: the file lives inside the gitignored `.xcodeproj` (ios-project-setup.md).
- **`-skipPackagePluginValidation -skipMacroValidation`**: without them a headless build stops on the trust prompt; they are the trust boundary for build-time code, so only for vetted dependencies (spm-and-builds.md, CI and headless traps).
- **`COMPILER_INDEX_STORE_ENABLE=NO`**: CI never reads the index; community numbers are 6-8% ([tuist#6532](https://github.com/tuist/tuist/issues/6532)). It also removes a large directory from anything you cache.
- **A concrete destination, not a generic simulator.** `generic/platform=iOS Simulator` built x86_64 plus arm64 on Apple silicon with Xcode 26.3, and pinning `ARCHS=arm64` cut warm builds 29% on [one project](https://github.com/kaeawc/auto-mobile/issues/5024). Xcode 27.2 still resolves `ARCHS = arm64 x86_64` for the generic simulator destination (`-showBuildSettings`, verified on Xcode 27.2 locally); a `-destination "id=..."` avoids it.
- **`CODE_SIGNING_ALLOWED=NO`** for device compile checks (`generic/platform=iOS`) and simulator tests; simulator builds are ad hoc signed anyway (ios-devices-and-signing.md). A device compile check catches the `#if !targetEnvironment(simulator)` branches the simulator build never compiles.
- **Build once, test separately**: `build-for-testing` then `test-without-building` with the same destination and `-derivedDataPath`. `-testProductsPath` (or the `.xctestrun` plus products as an artifact) ships one build to several test jobs.
- `-showBuildTimingSummary` prints where build time went; read it before adding a cache.
- Xcode 26+ fetches prebuilt swift-syntax for macro packages automatically, which removes most macro build time ([Xcode 26 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-26-release-notes)).
- SwiftPM with `@testable import`: `swift test -c release` rebuilds everything (testability flips with configuration), so a job that needs a release bundle and tests compiles two trees. Keep tests in debug and build release only where a signed bundle is needed.

## Xcode compilation cache

Xcode 26+ can cache compiler outputs by content (Swift and C-family) in a CAS ([Xcode 26 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-26-release-notes)). A restored CAS is keyed by inputs, not timestamps, so it survives the fresh checkout that defeats a DerivedData cache. This is the cache to try first for app builds.

```yaml
      - name: Configure compilation cache
        id: cas
        run: |
          build=$(xcodebuild -version | awk '/Build version/ {print $3}')
          echo "prefix=cas-$build-$RUNNER_ARCH-$GITHUB_JOB" >> "$GITHUB_OUTPUT"
          cat > "$RUNNER_TEMP/cas.xcconfig" <<'EOF'
          COMPILATION_CACHE_ENABLE_CACHING = YES
          COMPILATION_CACHE_KEEP_CAS_DIRECTORY = YES
          EOF
          echo "XCODE_XCCONFIG_FILE=$RUNNER_TEMP/cas.xcconfig" >> "$GITHUB_ENV"
      - name: Restore compilation cache
        id: restore-cas
        uses: actions/cache/restore@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0
        with:
          path: build/CompilationCache.noindex
          key: ${{ steps.cas.outputs.prefix }}-${{ hashFiles('project.yml', '**/Package.resolved', '**/*.swift') }}
          restore-keys: |
            ${{ steps.cas.outputs.prefix }}-
      - run: xcodegen generate
      - run: |
          xcodebuild build -project App.xcodeproj -scheme App -destination 'generic/platform=iOS' \
            -derivedDataPath build CODE_SIGNING_ALLOWED=NO COMPILER_INDEX_STORE_ENABLE=NO
      - name: Save compilation cache
        if: ${{ !cancelled() && github.event_name == 'push' && steps.restore-cas.outputs.cache-primary-key != '' && steps.restore-cas.outputs.cache-hit != 'true' }}
        uses: actions/cache/save@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0
        with:
          path: build/CompilationCache.noindex
          key: ${{ steps.restore-cas.outputs.cache-primary-key }}
```

- **Measured** (XcodeGen iOS app, `xcode-27`, unsigned device build): 4m14s without the cache, **2m21s with a warm cache**, and a cold run that saved the cache was not slower (4m31s, within noise). One warm datapoint, not a series: measure your own before keeping it.
- **Why each piece.** `XCODE_XCCONFIG_FILE` applies the settings to every target without touching the project, and reaches `xcodebuild` calls made by scripts. The CAS lives at `$(DERIVED_DATA_DIR)/CompilationCache.noindex` for scheme builds ([swift-build Settings.swift](https://github.com/swiftlang/swift-build/blob/c6a6491a4212b7bcee141e89f0e8d7b059b051cb/Sources/SWBCore/Settings/Settings.swift#L2195-L2210)), so `-derivedDataPath build` puts it at a stable path; cache only that directory, never the rest of DerivedData. With `COMPILATION_CACHE_KEEP_CAS_DIRECTORY = NO` swift-build deletes the CAS after the build "to reduce resource usage in environments not configured to preserve it" ([BuildOperation.swift](https://github.com/swiftlang/swift-build/blob/c6a6491a4212b7bcee141e89f0e8d7b059b051cb/Sources/SWBBuildSystem/BuildOperation.swift#L1654-L1659)); open-source `main` defaults it to YES and so does Xcode 27.2 (`-showBuildSettings`, verified on Xcode 27.2 locally); set it anyway for Xcode 26, which was not checked. With only that directory restored and every source touched, every compile hit the cache (verified on Xcode 27.2 locally).
- **The key**: Xcode build number (the toolchain is part of every compile key, so a new Xcode is a clean start), runner arch, job name (a device build and a simulator build produce different outputs) and a hash of the sources. An unchanged tree is an exact hit with no save; any change restores the newest entry under the prefix and saves a new one. `github.sha` in place of the source hash also works. The save step reuses `cache-primary-key` because `hashFiles` at save time would also hash the `.swift` files of packages checked out under `build/`.
- **Bound it**: `COMPILATION_CACHE_LIMIT_SIZE = 2G` (K/M/G/T suffixes, [CASOptions.swift](https://github.com/swiftlang/swift-build/blob/c6a6491a4212b7bcee141e89f0e8d7b059b051cb/Sources/SWBCore/Settings/CASOptions.swift#L224-L240)) is honored only when the keep setting is YES. Without a limit the CAS grows each run (Xcode 27.2 reports `COMPILATION_CACHE_LIMIT_SIZE = 0`, which means no limit, while open-source `main` falls back to half the free disk) and every entry counts against the 10 GB repo quota.
- **What it does not cache**: storyboards, XIBs, asset catalogs, script phases, Core Data models, dSYM generation and linking ([Bitrise FAQ](https://docs.bitrise.io/en/bitrise-build-cache/build-cache-for-xcode/xcode-compilation-cache-faq)); it speeds up compiling, not running tests. Swift package targets were not cacheable as of Xcode 26.0.x (Bitrise, [Tuist](https://tuist.dev/blog/2025/10/22/xcode-cache)). On Xcode 27.2 they are: with only the CAS restored, a local package target's Swift compiles and the SDK module PCMs replayed (`Replay cache hit (in target 'Core' from project 'Core')`, verified on Xcode 27.2 locally; remote packages and C/ObjC sources not tested, and Tuist says C/ObjC sharing needs a remote service). Add `COMPILATION_CACHE_ENABLE_DIAGNOSTIC_REMARKS = YES` to the xcconfig for one run to count `cache hit` against `cache miss` lines before keeping the cache.
- **Prefix mapping and remote caches** are out of scope on hosted runners: the workspace path is stable, so prefix mapping only re-keys everything ([Tuist](https://tuist.dev/en/docs/guides/features/cache/xcode-cache)), and a remote cache service never pairs with a restored DerivedData ([Depot](https://depot.dev/blog/xcode-compilation-caching-with-depot-cache)).

## What not to cache

| Candidate | Verdict | Why |
|---|---|---|
| Whole DerivedData | No | `actions/checkout` sets every source mtime to now and the build system keys on mtime, so every target recompiles ([aleos.dev](https://aleos.dev/posts/2026-02-17-xcode-ci-build-caching)). New inodes are not the problem on current Xcode: swift-build defaults to a device-agnostic file-system mode ([UserDefaults.swift](https://github.com/swiftlang/swift-build/blob/c6a6491a4212b7bcee141e89f0e8d7b059b051cb/Sources/SWBUtil/UserDefaults.swift#L126-L152)), and a tar round trip of sources and DerivedData with mtimes preserved recompiled nothing (verified on Xcode 27.2 locally). A DerivedData cache therefore needs mtime restoration, which is fragile. The CAS avoids the whole problem. |
| `SourcePackages` (`-clonedSourcePackagesDirPath`) | Not unless measured | Saves clone time only, never compile time. Measured on the XcodeGen iOS app: resolution 40 s cold; with a 155 MB hit, 27 s plus 8 s restore, and 12 s to save on a miss: about 5 s net, inside noise. Removed. |
| Tools (just, XcodeGen) | No | Pinned release downloads take 1-2 s. |
| Anything with secrets | Never | Anyone who can open a PR can read base-branch caches. |

## SwiftPM-only apps

A macOS app built with `swift build` (no Xcode project) caches like a package:

```yaml
      - id: swift
        run: echo "hash=$(swift --version 2>&1 | head -1 | shasum -a 256 | cut -c1-12)" >> "$GITHUB_OUTPUT"
      - uses: actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0
        with:
          path: |
            .build
            ~/Library/Caches/org.swift.swiftpm
          key: spm-v1-${{ runner.os }}-${{ runner.arch }}-${{ steps.swift.outputs.hash }}-${{ hashFiles('Package.resolved') }}
          restore-keys: |
            spm-v1-${{ runner.os }}-${{ runner.arch }}-${{ steps.swift.outputs.hash }}-
```

Plain `actions/cache` is right here: the key changes only with `Package.resolved`, so a PR that leaves dependencies alone gets an exact hit from `main` and saves nothing. A cache keyed on sources (the CAS above) needs the restore/save split.

- **Measured** (SwiftPM macOS app, 51 green runs): about 630 MB compressed, 12 s to restore; it saves 20-35 s per build configuration, 45-70 s per run (a debug test build plus a release bundle build). SwiftPM's llbuild manifests are device-agnostic, so a tar round trip keeps it incremental (a no-op rebuild took 0.81 s locally on the native build system; with the Swift Build backend a tar round trip of `.build` rebuilt nothing and touching the app's sources recompiled only the app target, verified on Swift 6.4.2 locally). Your own targets still recompile after checkout (about 30 s each for a mid-size app); the cache pays only for dependencies.
- Do not put `github.sha` or `run_id` in this key: a new 300+ MB entry per run churns the quota for nothing, since dependencies change only with `Package.resolved`. Entries are immutable, so bump the `spm-v1-` prefix when the cached content's shape changes. A restored `.build` across a dependency bump can produce release-mode `undefined reference` link errors ([swift-package-manager#8260](https://github.com/swiftlang/swift-package-manager/issues/8260)); the same prefix bump clears it.
- Swift 6.4 builds with Swift Build: products move to `.build/out/Products/<Config>`, so hard-coded `.build/arm64-apple-macosx/release` globs in packaging scripts silently match nothing. Use the `.build/release` symlink, which resolves under both backends (SKILL.md, Xcode 27 changes).

## Cache scoping rules

From [dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) unless noted.

- **PR saves are invisible to `main`.** A run restores from its own ref and the default branch (a PR also from its base). A cache saved by a `pull_request` run is scoped to `refs/pull/N/merge`, usable only by re-runs of that PR. Observed: after a 7-day idle eviction a PR logged `Cache saved with key: spm-v1-...`, and the `main` push an hour later logged `Cache not found for input keys:` for the identical key and built cold again. Save source-keyed caches from `push` to the default branch only: `actions/cache/restore` everywhere, `actions/cache/save` gated on `github.event_name == 'push'` (the compilation-cache snippet); that is the default branch only while `on.push.branches` is limited to it, as in Job shape.
- Only `push`, `schedule`, `workflow_dispatch` and a few other events can write default-branch caches; `pull_request_target`, `issue_comment` and `workflow_run` get read-only access and a save there is a warning. A `cache-mode: read|write|write-only|none` key at workflow or job level sets this explicitly.
- **Immutable entries.** An existing key is never overwritten; an exact hit logs `Cache hit occurred on the primary key <key>, not saving cache.` Hence a changing suffix plus a `restore-keys` prefix for build caches ([caching strategies](https://raw.githubusercontent.com/actions/cache/main/caching-strategies.md)).
- **Lookup order**: exact key, then the key as a prefix, then each restore-key, on the current branch and then the default branch; among several prefix matches the newest wins. A different `path` list between save and restore is a miss (the path is part of the cache version).
- **10 GB per repository**, raisable on user repos and billed above 10 GB. Entries unused for 7 days are evicted; over the limit the oldest by last access go first, so one fat cache can evict the rest. An exceeded budget makes the cache read-only.
- `actions/cache` saves automatically only when the job succeeds; use the split form with a `!cancelled()` save condition to warm even when tests fail. `lookup-only: true` checks for a key without downloading. Use v5 or later (v4 runs on Node 20, which runners drop in fall 2026); v5.1+ treat a denied save as a warning.
- Purge with `gh cache delete --all -R <owner>/<repo>` (needs `actions: write`).

## Simulators on hosted runners

```yaml
      - name: Pick the image's simulator
        timeout-minutes: 5
        run: |
          sdk=$(xcrun --sdk iphonesimulator --show-sdk-version)
          rt="com.apple.CoreSimulator.SimRuntime.iOS-${sdk//./-}"
          udid=$(xcrun simctl list devices available -j |
            jq -r --arg rt "$rt" 'first(.devices[$rt][]? | select(.name == "iPhone 18 Pro Max") | .udid) // empty')
          [ -n "$udid" ] || { echo "no iPhone 18 Pro Max on $rt" >&2; xcrun simctl list runtimes; exit 1; }
          echo "SIM_UDID=$udid" >> "$GITHUB_ENV"
```

- **Use a device the image ships, on a runtime it ships.** Measured on `xcode-27`: one of the image's own simulators booted in about 90 s; a freshly created one (`simctl create` with the Mac's device type) took 5.4 minutes. Pick it by UDID.
- **Never let `xcodebuild -downloadPlatform` run.** It fetches the newest runtime even when a usable one is installed; one project lost 2-3 minutes and exit-70 flakes to it and went from 20-55 minutes to 6m31s after removing implicit downloads ([OneBusAway #1151](https://github.com/OneBusAway/onebusaway-ios/pull/1151)).
- **Runtimes per image** ([xcode-27 README](https://github.com/actions/runner-images/blob/main/images/macos/xcode-27-arm64-Readme.md), [macos-26 README](https://github.com/actions/runner-images/blob/main/images/macos/macos-26-arm64-Readme.md)): `xcode-27` has iOS 27.0 (iPhone 17, 17e, 18 Pro, 18 Pro Max, Air, iPads), **27.1 with iPhone Duo only** (Apple's packaging, [#15000](https://github.com/actions/runner-images/issues/15000)) and 27.2 (full device set). Selecting Xcode 27.1 therefore means testing on 27.0 or 27.2 runtimes, or on the Duo. `macos-26` has iOS 26.2, 26.4 and 26.5 only, no 26.6 runtime.
- **The first `simctl` call of a job stalls** while `simdiskimaged` mounts runtimes: median 33.7 s and up to 153 s on `macos-15`, median 7.3 s (max 66 s) on `macos-26`, median 4 s on `xcode-27`; later calls take under 2.5 s, and `-runFirstLaunch` does not help ([#15247](https://github.com/actions/runner-images/issues/15247)). Make it its own step with a timeout, as above.
- **Build first, then boot.** On the 7 GB runner a build beside a booted simulator took two to three times as long, and booting beside tool installs stalled `brew` for 5 minutes (measured, XcodeGen iOS app). Boot explicitly after the build with `xcrun simctl bootstatus "$SIM_UDID" -b` so `xcodebuild`'s own boot deadline does not fire.
- **Cold-boot keyboard delay**: the text-input service can start 16-28 s late on a first boot (`macos-15`, Xcode 26.3), so `typeText` with a 10 s wait fails intermittently ([#15252](https://github.com/actions/runner-images/issues/15252)). Wait for the keyboard element, not a fixed time.
- **Notification permission has no CLI grant** on a simulator that never ran the app (testing.md, Simulator toolkit). Skip the dependent test by name in CI with `-skip-testing:Target/Suite/test()` and keep it for local runs on a Simulator granted once by hand; a SpringBoard "Allow" UI test failed on a never-booted clone and is not a reliable gate. Microphone and similar services do take `simctl privacy ... grant`.
- **Do not assume `timeout` exists.** macOS 26 has none and neither does `xcode-27` while it is on macOS 27.0.1 (observed: a harness died with `FileNotFoundError` and two tests silently skipped). Apple's BSD `/usr/bin/timeout` is present on macOS 27.2 and later (observed; no release note mentions it), and the `xcode-27` prerelease image 20261119.0378.1 moves to macOS 27.2 ([release](https://github.com/actions/runner-images/releases/tag/xcode-27-arm64/20261119.0378)) - check rather than assume which image you got. Check `command -v timeout`, install GNU `timeout` with `brew install coreutils` (about 9 s, unpinned), or bound runs with step `timeout-minutes`.
- On Xcode 26.1 and 26.4, boots are slow while dyld shared caches build; `xcrun simctl runtime dyld_shared_cache update --all` before booting finishes that ([Xcode 26.4 notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-26_4-release-notes)). Xcode 27 runtimes ship a prebuilt dyld cache.

## UI tests

- **Keep UI tests out of the PR gate**: a `workflow_dispatch` (or nightly `schedule`) workflow with one or two parallel jobs, each running a group of test classes. Measured on hosted runners (XcodeGen iOS app): 1.5-3.5 minutes per class, about 40 s of it per-invocation overhead, about 15 minutes per job; one `launch()` hang (178 s) in about 50 executions, and one photo-picker test that failed 3 of 3 times on runners while passing locally. Without retries a manual run can go red on a flake; that is acceptable outside the gate.
- `workflow_dispatch` appears only once the file is on the default branch. To exercise a new manual workflow from its branch, add a temporary `push` trigger for that branch and remove it before merge.
- Run UI tests serially (`-parallel-testing-enabled NO`) on 3-core runners, one simulator per job. Use `-retry-tests-on-failure -test-iterations 2` only on a quarantined suite, never on the gate.
- Bound every `xcodebuild test` (stalls after a failure, hangs after a pass) and guard against selectors that match nothing: testing.md, UI tests under xcodebuild.
- Upload the `.xcresult` only `if: failure()`: an always-on upload cost about 9 minutes per green run in [one project](https://github.com/OneBusAway/onebusaway-ios/pull/1151). Result bundles capture the test runner's environment, so keep secrets out of it (testing.md). For screenshots of a failing check, attach them in the test (`XCTAttachment`, Swift Testing attachments) so they land in the bundle you upload.
- Xcode 27 adds a test-plan setting for how an app crash during UI tests is treated (off, warning, failure, fatal) ([release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes)).

## Permission-gated tests on macOS runners

Hosted macOS images can run Screen Recording and Microphone tests (measured on `macos-26`, SwiftPM macOS app): SIP is disabled on the image, the system `TCC.db` is writable with `sudo`, and the runner-images maintainers endorse editing it at runtime ([#9529](https://github.com/actions/runner-images/issues/9529)). The image also has virtual audio devices (one default input/output plus a null device), enough for device-switch tests; Bluetooth paths still need hardware.

- **Sign the test bundle with a real certificate.** TCC keys a grant to the designated requirement; an ad hoc signature's cdhash changes every build, so a seeded row never matches twice (macos-distribution.md, TCC).
- Compile the designated requirement on its own: `codesign -d -r- App.app 2>/dev/null | sed -n 's/^designated => //p' | csreq -r- -b req.bin` (without the `sed`, `csreq` writes a requirement set, magic `fade0c01` instead of `fade0c00`, and the row never matches). Insert `kTCCServiceScreenCapture` into the system database and `kTCCServiceMicrophone` into the user database **with named columns** (positional inserts break when Apple adds a column; macOS 26's `access` table has 17), then assert `auth_value = 2` before running tests.
- Probe in a throwaway job before designing around it: preflight APIs can disagree with expectations (`CGPreflightScreenCaptureAccess()` returned true inside the SwiftPM test process on a runner, so a test expected to skip ran; mechanism unknown).
- Make missing grants fail with a message, not skip: a silent skip on CI reports green for code that never ran.

## Signing, TestFlight and notarization

Key roles and headless signing are in ios-devices-and-signing.md (use an Admin **team** API key), export options such as `testFlightInternalTestingOnly` for branch builds in ios-distribution.md, Developer ID signing and notarization rejections in macos-distribution.md. What CI adds:

- **The API key on disk.** Write the `.p8` from a secret into `$RUNNER_TEMP` with `umask 077`, pass `-allowProvisioningUpdates -authenticationKeyPath <absolute path> -authenticationKeyID -authenticationKeyIssuerID` to every signing step, and delete it in an `if: always()` step. The API has no App Groups or iCloud containers resource (registering a group needs Account Holder or Admin in the [developer portal](https://developer.apple.com/help/account/identifiers/register-an-app-group)): create those and the app record once by hand; the key then attaches the capability and regenerates profiles (inferred from the API index and one real workflow).
- **Manual signing keychain** (Developer ID, or a key whose role cannot cloud-sign), per [GitHub's recipe](https://docs.github.com/en/actions/how-tos/deploy/deploy-to-third-party-platforms/sign-xcode-applications) plus what a real pipeline needed:
  ```bash
  [ -n "$P12_BASE64" ] || { echo "signing certificate secret is empty" >&2; exit 1; }
  KC="$RUNNER_TEMP/signing.keychain-db"
  KC_PW=$(openssl rand -base64 24)
  echo "$P12_BASE64" | base64 --decode > "$RUNNER_TEMP/cert.p12"
  security create-keychain -p "$KC_PW" "$KC"
  security set-keychain-settings -lut 21600 "$KC"
  security unlock-keychain -p "$KC_PW" "$KC"
  security list-keychains -d user -s "$KC" login.keychain-db
  security import "$RUNNER_TEMP/cert.p12" -k "$KC" -P "$P12_PASSWORD" -f pkcs12 \
    -T /usr/bin/codesign -T /usr/bin/security
  security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$KC_PW" "$KC"
  rm "$RUNNER_TEMP/cert.p12"
  ```
  Fail on an empty secret (otherwise a build can quietly ad hoc sign), keep the login keychain in the search list, and without `set-key-partition-list` `codesign` blocks on a GUI prompt and the job hangs. After signing, assert the authority: `codesign -dvvv App.app 2>&1 | grep -q 'Authority=Developer ID Application'`. Install profiles into `~/Library/Developer/Xcode/UserData/Provisioning Profiles` (Xcode 16+; the old `~/Library/MobileDevice` location is still read). Cloud-managed distribution certificates need no `.p12` at all (ios-devices-and-signing.md).
- **`notarytool submit --wait` exits 0 when the result is `Invalid`** (observed). Gate on the JSON status and print the log on failure:
  ```bash
  NOTARY=(--key "$KEY_P8" --key-id "$KEY_ID" --issuer "$ISSUER_ID")
  out=$(xcrun notarytool submit build/MyApp.dmg "${NOTARY[@]}" --wait --output-format json)
  id=$(jq -r .id <<<"$out")
  if [ "$(jq -r .status <<<"$out")" != Accepted ]; then
    xcrun notarytool log "$id" "${NOTARY[@]}"
    exit 1
  fi
  xcrun stapler staple build/MyApp.dmg
  ```
  Notarization took 71-82 s per release (measured). Check Gatekeeper on the `.app` inside the mounted DMG with `spctl -a -t exec -vv` (expect `Notarized Developer ID`); `spctl -t open` on the `.dmg` without `--context context:primary-signature` reports `no usable signature` by design.
- **Keep a dispatch-only release dry run** that does everything except publish: real signing, real notarization, update-feed signing, token permission checks. It found three bugs before a first automated release and takes about 3 minutes (measured); the notary failures it surfaces are in macos-distribution.md, Notarization rejections.
- **A step-level `if:` that references `secrets.X` makes the workflow invalid**: the run shows zero jobs and `gh run view` says the log is not found. Lift the secret into job `env:` and test `env.X != ''`. actionlint reports it.
- Derive the build number from the last release tag, not by incrementing in place: re-runs double-bumped it (Sparkle compares `CFBundleVersion`). For TestFlight, a clock-stamped number needs no tag at all (ios-distribution.md).
- **Tag last.** Build, sign, notarize and staple against a tag created only inside the runner, then create the release as a draft, upload the artifacts and publish it, which creates the real tag. A notarization failure then leaves no tag and no empty release to clean up. With release-please, set `skip-github-release: true` so it only maintains the release PR, and treat "manifest version has no `v<version>` tag on the remote" as the release trigger.
- **Plist tools are macOS-only.** `/usr/libexec/PlistBuddy` and `plutil` do not exist on `ubuntu-latest` (exit 127); keep plist edits on a macOS job or use Python's `plistlib`. A conditional release job that has never run hides this until the first release (observed).

## Supply chain

- **Pin actions.** Either adopt [workflow lockfiles](https://docs.github.com/en/actions/concepts/security/workflow-dependency-lockfiles) (GA [2026-10-28](https://github.blog/changelog/2026-10-28-github-actions-workflow-lockfiles-are-generally-available)): the `gh actions-lock` extension (`gh extension install github/gh-actions-lock`; not built into `gh`) writes `.github/workflows/actions.lock` with every action and its transitive dependencies, workflows keep readable tags, and Dependabot updates the lock in the same PR. Lockfiles do not cover reusable workflows (`jobs.<id>.uses`): pin those by SHA. Or pin full commit SHAs with a `# vX.Y.Z` comment, verified against the action's own repository (`gh api repos/actions/cache/git/ref/tags/v6.1.0`); Dependabot updates the comment with the SHA, but security alerts do not fire for SHA-pinned actions ([secure use](https://docs.github.com/en/actions/reference/security/secure-use)).
- `permissions: contents: read` at the top of every workflow; widen per job (`pull-requests: read` for a paths filter, `contents: write` only in a publish job).
- `persist-credentials: false` on every `actions/checkout` that does not push. Checkout v6+ keeps the token in a file under `$RUNNER_TEMP` rather than `.git/config`, but still persists it unless told not to; v7 refuses fork-PR checkouts under `pull_request_target`/`workflow_run` without `allow-unsafe-pr-checkout: true` ([checkout](https://github.com/actions/checkout)).
- Pass `${{ github.event.* }}`, `github.head_ref` and other user-controlled values through `env:` and quote them in shell; never interpolate them into `run:`.
- **Lint workflows**: [actionlint](https://github.com/rhysd/actionlint) (1.7.12 is the latest) does not know the `xcode-27` labels yet ([#739](https://github.com/rhysd/actionlint/issues/739)); declare them so it stops reporting unknown labels, and delete the file once it learns them:
  ```yaml
  # .github/actionlint.yaml
  self-hosted-runner:
    labels:
      - xcode-27
      - xcode-27-xlarge
  ```
  1.7.12 also predates `cache-mode`, `background` and `wait` and reports them as unexpected keys; those reports are false positives until a release knows the keys.
  [zizmor](https://docs.zizmor.sh/audits/) (`zizmor .github/workflows`) audits template injection, persisted credentials (`artipacked`), stale action refs and ref-version mismatches. Run both on Linux, not as a `brew install` step inside the macOS job (6-14 s of macOS time per run, measured).
- Third-party downloads in setup steps (just, XcodeGen) get a pinned version and a SHA-256 check with `shasum -a 256 -c`.

## Debugging slow or hanging CI

Measure before caching. In the SwiftPM macOS app, the first "slow CI" looked like dependency compilation and got a cache; per-step timings then showed build 51 s cold and the test step 20-31 minutes before manual cancels, against 3.2 s locally. It was a deadlock.

1. **Per-step timings** for every job:
   ```bash
   gh run view <run-id> --json jobs --jq '.jobs[] | .name as $j | .steps[] |
     "\($j)\t\(.name)\t\(((.completedAt | fromdateiso8601) - (.startedAt | fromdateiso8601)))s"'
   ```
   `gh run view` reports only the latest attempt: check `gh api repos/<owner>/<repo>/actions/runs/<run-id> --jq .run_attempt` before trusting queue or step times. For `xcodebuild`, `-showBuildTimingSummary`.
2. **Sample the stalled test process** from a dispatch-only diagnostic job. `act` cannot run macOS jobs, so iterate on the real runner:
   ```bash
   swift test --disable-xctest > "$RUNNER_TEMP/test.log" 2>&1 &
   pid=$!
   for _ in $(seq 120); do kill -0 "$pid" 2>/dev/null || break; sleep 5; done
   if kill -0 "$pid" 2>/dev/null; then
     sample "$(pgrep -f swiftpm-testing-helper | head -1)" 3 -mayDie -file "$RUNNER_TEMP/stall.sample"
     cat "$RUNNER_TEMP/test.log" "$RUNNER_TEMP/stall.sample"
     kill "$pid"
     exit 1
   fi
   wait "$pid"
   ```
   Under `xcodebuild`, sample the `xctest` process or the app instead.
3. **Bisect** with `swift test --filter <Suite>` (or `-only-testing:`) several times in one job, and print `sysctl -n hw.ncpu` (3 on standard arm64).
4. **Read the sample for pool starvation.** The cause here: a blocking `AVAssetReader.copyNextSampleBuffer` loop inside `Task.detached`. Four parallel tests occupied all three cooperative-pool threads and the readers never made progress: every pool thread sat in `copyNextSampleBuffer -> pthread_cond_wait` with the main thread idle in `CFRunLoopRun` (why the reader needs a free pool thread was not established). Moving the loop to a dedicated serial queue behind a continuation fixed CI (80 tests in 66 s) and a production bug on low-core Macs. A many-core dev Mac has a wide pool and never shows it. Rule: no synchronous framework waits, semaphores or blocking I/O on the cooperative pool, including inside `@concurrent` functions and `Task.detached`; bridge them from a dispatch queue with a continuation (concurrency-tasks.md).
5. **Two traps on any CI-only hang.** An `--xunit-output` file gets its header early, so check for its closing tag or the final `Test run with N tests ... passed` line before concluding tests passed and the process hangs on exit (testing.md, `swift test` command line). A suite that never finishes only on 3 cores is a pool-starvation suspect before it is a platform limitation: a skip for a VM without a Neural Engine changed nothing.
