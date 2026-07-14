# Field lessons (hard-won from real phone-driven builds)

Practical failures seen when driving this pipeline end-to-end, and the fixes.
Read this before debugging a red build — most real failures are in here.

## Diagnosing failures when you can't read the runner logs
Claude's sandbox usually **cannot fetch GitHub Actions logs** — the job-logs API
redirects to `*.blob.core.windows.net` (Azure), which is outside the egress
allowlist. So a failed step gives you a conclusion but no error text.

Fix, baked into `build-android.yml`: the build step tees output to a file, and a
`if: failure()` step commits the tail (grepped for `e:`, `error:`, `Could not
find`, `Duplicate class`, etc.) to `build_error.txt` with `[skip ci]` in the
message. You then read it via the **Contents API** (raw), which the sandbox *can*
reach. This one trick turns blind guessing into precise fixes. A normal user
reading logs in the GitHub UI doesn't need it, but Claude-driven builds do.
The next successful push (whose tree omits the file) cleans it up automatically.

## Signing: the "conflicts with existing package" wall
Android refuses to update an installed app when the new APK is signed with a
**different certificate** — it shows "App not installed / package conflicts."
- The default **debug keystore is regenerated per CI run**, so every build gets a
  different cert and none updates over another. Symptom looked like a mystery;
  cause was per-run signing identity.
- Fix for testing: commit a **fixed debug keystore** (standard password `android`)
  and point `signingConfigs.debug` at it — password secrecy is moot for debug, the
  goal is only a *stable* identity.
- Fix for production: a real key in **Actions Secrets** (`KEYSTORE_BASE64` +
  password/alias), decoded on the runner, signed via
  `-Pandroid.injected.signing.*` (already wired in the workflow). Never commit a
  real key; never put it in a Variable (plaintext).
- **Every cert change costs one uninstall.** Moving from per-run → stable debug →
  real release key each changes the cert, so testers must uninstall once at each
  switch, then updates install in place forever after. Do the release-key switch
  *before* you have real users.
- Secrets are **write-only** — they are not a backup. Keep the keystore file +
  password somewhere durable, or a lost key means never updating the app again.

## Release builds fail where debug builds passed
`assembleRelease` runs `lintVitalRelease`, which aborts on lint issues debug
ignores. If a debug build is green but release is red at the build step with no
obvious compile error, it's usually lint. Fix in `app/build.gradle.kts`:
```kotlin
lint { checkReleaseBuilds = false; abortOnError = false }
```

## Native-library crashes are uncatchable — prefer pure-Kotlin
Mixing two MediaPipe artifacts (e.g. `tasks-genai` + `tasks-text`) can cause a
**native abort (SIGABRT)** when the second native stack loads. A Kotlin
`try/catch(Throwable)` does NOT catch it — the process just dies. Symptom: app
starts fine, then hard-crashes the instant the feature runs, with no exception
banner.
- Never do native ML work on the startup path; defer it to first use, off the
  main thread, so a failure can't kill launch.
- For small problems (e.g. retrieval over a few hundred items), a **pure-Kotlin
  approach (TF-IDF cosine)** is crash-proof and dependency-free — often the right
  call over a second native lib.
- Add a top-level `Thread.setDefaultUncaughtExceptionHandler` that writes the
  stack trace to `filesDir/last_crash.txt` and shows it on next launch. It
  surfaces *Java* crashes in-UI (useful for phone-only users with no logcat); a
  crash with no banner tells you it was native.

## Dependency versions
- `tasks-genai` and `tasks-text` version independently — a matching version
  string for one may not exist for the other. `latest.release` resolves to the
  newest available and avoids guessing, at the cost of reproducibility.
- Bundling a model the sandbox can't fetch: have the **workflow** `curl` it into
  `app/src/main/assets/` before the build (the runner has open network), rather
  than committing it.

## Bootstrapping an empty repo via the API
The Git Data API (`/git/blobs`, `/git/trees`, `/git/commits`) needs at least one
existing commit. Create the first commit with the **Contents API**
(`PUT /contents/README.md`), then switch to the Git Data API for bulk tree pushes.

## Getting device logs (for the user)
The reliable way to capture a native crash is `adb logcat` with the phone plugged
into any computer (USB debugging on). Emulators are x86_64, so ARM-only native
libs (MediaPipe/LLM) won't run there — UI/logic test on emulator, native/LLM test
on a real device.
