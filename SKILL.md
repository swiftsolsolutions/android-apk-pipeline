---
name: android-apk-pipeline
description: >-
  Build an Android app into an installable APK using a phone-driven GitHub
  Actions pipeline, with no local machine or Android Studio required. Use this
  whenever the user wants to turn an app idea into a real APK on their phone,
  scaffold or modify an Android project (Kotlin/Compose, Views, Flutter, or
  React Native), set up or edit a GitHub Actions Android build, add signing for
  release builds, or troubleshoot a cloud Android build. Trigger for any mention
  of building an APK, "make me an Android app," Gradle/CI Android builds, or
  getting a compiled app onto a phone — even if the user never says the word
  "pipeline." Do NOT use for Google Play store submission steps (the user
  handles publishing).
---

# Android APK pipeline (phone-driven)

Turn an app requirement into an installable APK using GitHub's servers as the
build machine and the user's phone as the remote control. The user commits code
(or Claude generates it and the user commits via the GitHub mobile app), GitHub
Actions compiles a real Android Gradle build, and the APK is published to a
GitHub Release so the user can download and install it on their phone.

## The one idea that matters

**The workflow is the reusable part; the app is generated fresh per requirement.**
There is no fixed app "template" the user's ideas must fit into. For each request,
generate the project that actually fits — the right stack, libraries,
permissions, modules, and native code — and reuse the same build workflow, which
compiles whatever Gradle project is in the repo. The bundled `compose-starter` is
a known-good *baseline* to adapt, not a mold.

## Environment honesty

Claude's own sandbox usually **cannot compile an Android build** — Gradle needs
Google's Maven repositories and the Gradle distribution, which are typically
outside the sandbox's network allowlist. The compile happens on the GitHub
runner, which has full network access. So: validate structure, YAML, and version
compatibility locally, but tell the user the **first push is the real end-to-end
test** (green Actions run + an APK under Releases = pipeline proven).

## Before you debug a red build
Read `references/lessons.md` first. It captures real end-to-end failures and
fixes from live phone-driven builds — stable signing and the "package conflicts"
wall, why `assembleRelease` fails where debug passed (lint), uncatchable native
crashes and when to prefer pure-Kotlin, resolving logs the sandbox can't fetch,
and the empty-repo bootstrap. The bundled `build-android.yml` already includes
release signing via secrets and a failure-log capture step.

## Procedure

### 1. Pick the stack from the requirement
Read `references/stacks.md`. Default to native Kotlin + Jetpack Compose for new
apps; use XML Views for the leanest builds; use Flutter or React Native only if
the requirement calls for it. Only the build step differs between stacks.

### 2. Generate the project that fits
- Native Compose: start from `assets/compose-starter/` and adapt it — add
  dependencies, permissions in the manifest, extra screens/modules, NDK, etc.
- Other stacks: generate the appropriate project structure per `stacks.md`.
- **Package identity (required):** set both `namespace` and `applicationId` to
  `com.swiftsol.<appname>` — lowercase letters/digits only, no hyphens or
  underscores (e.g. a QR app → `com.swiftsol.qrscanner`, a game → `com.swiftsol.blockroller`).
  **Never use `com.example.*`** (that is Android's placeholder and must not ship).
  `com.swiftsol` is the user's permanent brand namespace. Make the source
  directory match: `app/src/main/java/com/swiftsol/<appname>/…` with
  `package com.swiftsol.<appname>` in every Kotlin file.
- Use the compatible versions in `references/versions.md` unless the user pins
  otherwise. Keep the Compose-compiler-plugin version equal to the Kotlin
  version, and keep Gradle compatible with the AGP version.
- Since the user is often phone-only and can't run a scaffolding wizard,
  generate all files as text. Do **not** rely on committing a binary Gradle
  wrapper jar; the workflow provisions Gradle when no `./gradlew` is present.

### 3. Provide the build workflow
Use `assets/build-android.yml` at `.github/workflows/build-android.yml`. It:
- builds on push to `main` and on manual dispatch (debug or release),
- prefers `./gradlew` if the repo has a wrapper, else uses provisioned Gradle,
- caches Gradle, and
- publishes the APK to a prerelease GitHub Release for easy phone download.
Adapt only the build step for non-Gradle stacks (see `stacks.md`).

### 4. Delivery and the phone install
- Debug APKs are debug-signed and installable immediately — ideal for the test
  loop. The user downloads from the repo's **Releases** tab and taps to install
  (allowing "install unknown apps" for the browser once).
- **In-place updates (default):** an installed app only *updates* (instead of
  installing as a second copy) when the **applicationId is unchanged** AND every
  build is signed with the **same key**. GitHub runners otherwise generate a
  random debug key per build → signature mismatch → forced uninstall. So for any
  app in the update loop, create ONE stable keystore and sign every build with it:
  `keytool -genkeypair -keystore app/testkey.jks -alias <name> -keyalg RSA
  -keysize 2048 -validity 10000 -storepass <pw> -keypass <pw> -dname "CN=..."`,
  commit `testkey.jks` into the repo (binary commits fine via the blobs API), and
  in `app/build.gradle.kts` add a `signingConfigs { create("stable") { … } }` and
  set both `debug` and `release` `signingConfig` to it. Then bump only
  `versionCode` each build and installs upgrade in place.
  Note: this is a throwaway **debug/test** key for sideloaded APKs — fine to commit
  to a private repo. It is NOT the Play upload key (never commit that; the user
  manages Play signing separately). Changing applicationId OR switching the key
  forces a one-time uninstall of the previously-installed copy; all builds after
  that update seamlessly.
- For a distinct **release** keystore via secrets instead, see `assets/gen-keystore.yml`.
- The final install is always a **manual tap** — Android blocks silent installs.
  (Android's 2026 developer-verification rules for sideloading only enforce in
  Brazil/Indonesia/Singapore/Thailand from Sep 30 2026, global 2027; elsewhere,
  and via ADB/advanced flow everywhere, self-install is unaffected.)

## Full build cycle — run this whenever the user asks to create OR improve an app

When the user asks for an app or any improvement to one, execute the **entire
cycle end to end and return the final APK download link**. Do not make the user
name the push/build/monitor steps — those are implied by "improve it." Steps
(mechanics in `references/automation.md`):

1. Generate or modify the project to fit the request; validate structure locally
   (YAML, XML, brace/paren balance). Bump `versionCode` so releases stay ordered.
2. Ensure a GitHub token for the target repo is available in the session. If none
   is, ask **once** for a fresh fine-grained token scoped to that one repo
   (Contents: write, Workflows: write, Actions: read). Reuse it for the rest of
   the session. **Never** store it (see Access reality).
3. Push all changed files to the default branch in one commit via the Git Data
   API (blobs → tree **on `base_tree`** → commit with parent → update ref) so
   existing files (README, other apps) are preserved.
4. The push triggers the workflow. Poll `GET /actions/runs` until the newest run
   completes.
5. On success, get the APK: list `GET /releases` and take the newest — the
   workflow publishes a **prerelease**, so `/releases/latest` returns 404. Return
   the asset's `browser_download_url`. For a private repo, tell the user the link
   needs them signed into GitHub.
6. On failure, read the failing job/step, fix the code, and repeat from step 3 —
   iterate until green rather than handing back a raw error, unless truly blocked.
7. When the session's builds are done, remind the user they can revoke the token.

The point: the user says "add feature X," and gets back a working APK link.

## Access reality (be honest; never work around this)

Claude cannot persist credentials. A **token must never be placed in this skill,
in memory, or in a repo file** — that would turn a short-lived secret into a
permanent, copyable one. So the cycle needs a token *present in the session*:
obtain it once per session, hold it only in conversation context, and use it for
every push/poll that session. This is the one step the user still supplies; it
can't be baked into the skill. Prefer a GitHub OAuth connector if one ever
becomes available (revocable, nothing pasted). Recommend the token be a
fine-grained PAT scoped to the single repo (Contents: write, Workflows: write,
Actions: read), short expiry, revoked when done. Never handle the user's signing
keystore or its passwords — those are repo secrets the user sets themselves.

If no token is available and the user doesn't want to provide one, fall back to
generating the files (or a zip) for the user to commit themselves; the build then
runs the same way in their repo.

## Heavy builds
Raise `org.gradle.jvmargs`; build/configuration caches are on; install the NDK
for native code (uncomment the NDK step); bump `timeout-minutes` or use a larger
/ self-hosted runner for very long builds. Details in `references/stacks.md`.

## Store graphics (Play listing)
When the user is publishing to Play, the listing needs graphics before it can go
live: a 512×512 icon, a 1024×500 feature graphic (no transparency), and ≥2
screenshots each for phone / 7-inch / 10-inch. Generate them with
`assets/gen-play-graphics.py` (config-driven; built-in `qr`/`mono` icon motif or
pass the app's real launcher art), then **commit them into the repo** in the
fastlane `supply` image layout so they are version-controlled and auto-uploaded
by `upload_to_play_store`. Full specs, the config shape, and exactly what to
commit are in `references/play-assets.md`. Screenshots are built by *framing*
real emulator captures (from the `screengrab` lane) or faithful UI mockups —
keep the raw sources in `store-assets/captures/` so graphics stay reproducible.
The generator clears the icon + graphics rows of "Finish setting up your app";
content rating, data safety, target audience, and the privacy-policy URL remain
Console-only and the user supplies those.

## Console-only publishing steps (the user does these)
Account/org setup, the **first** manual release, content rating, data safety,
target-audience, and the privacy-policy URL are done by the user in Play Console;
the API cannot. Everything else — building the signed **AAB** (not APK) at
**targetSdk 36**, uploading, committing to a track, and pushing listing text +
graphics — is automated via `upload_to_play_store`/`supply`. A brand-new app can
return a misleading "caller does not have permission" on the first API commit
until that first manual release + setup checklist is done; after that the API
commits every future version.

## Versioning — never hand-bump for publishes
Every Play release must carry a **strictly higher `versionCode`** than whatever is
already active on the target track (and any higher-priority track). Hand-bumping
invites collisions, which surface at rollout as this pair of errors:

> "This release does not add or remove any app bundles."
> "You can't rollout this release because it doesn't allow any existing users to
> upgrade to the newly added app bundles."

Both mean the same thing: the release's `versionCode` is not higher than what's
live, so there's no upgrade path. The fix is always a higher `versionCode` — so
**let CI assign it** rather than editing it by hand. Use `assets/play-publish.yml`,
which sets `VERSION_CODE=$(date +%s)` (epoch seconds) before the build:
monotonic, unique even across re-runs, and under Play's 2,100,000,000 ceiling
until ~2036. Pair it with `app/build.gradle.kts`:
```kotlin
versionCode = (System.getenv("VERSION_CODE")?.toIntOrNull()) ?: 1
```
so the CI value wins on publish while local/validation builds use the fallback.
Corollary: don't hand-create releases in the Console with the same bundle — drive
new versions through the publish workflow so a duplicate `versionCode` can't happen.
