# Native Android build pipeline (phone-driven)

A standard Kotlin + Jetpack Compose app plus a GitHub Actions workflow that
compiles it into an installable APK on GitHub's servers. No local machine needed.

## Version set (known-compatible)
- Gradle 8.9, Android Gradle Plugin 8.7.3
- Kotlin 2.1.0 + Compose compiler plugin 2.1.0
- compileSdk / targetSdk 35, minSdk 24
- Compose BOM 2024.12.01

## How the loop works
1. Commit code to `main` (or run the workflow manually).
2. GitHub Actions builds the APK (~5-10 min first run, faster after caching).
3. Open the repo's **Releases** tab → newest **Build N** → download the `.apk`.
4. On your phone, tap the file to install (allow "install unknown apps" once).

## Build a release (signed) APK
1. Add repo secrets: `KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`, `KEY_ALIAS`,
   `KEY_PASSWORD` (see the pipeline guide's run-once keystore workflow).
2. Actions tab → **Build Android APK** → **Run workflow** → choose `release`.
   If no keystore secret is set, a release build is produced unsigned.

## Heavier / native apps
- **More memory:** raise `org.gradle.jvmargs` in `gradle.properties`.
- **C/C++ (NDK):** uncomment the "Install NDK" step in the workflow.
- **Longer builds:** `timeout-minutes` is already 90; Gradle build cache and
  configuration cache are on. For very large builds, use a GitHub larger runner
  or a self-hosted runner (swap `runs-on:`).
- **Bringing your own project:** drop a real Android Gradle project in the repo.
  If it includes a `./gradlew` wrapper, the workflow uses it automatically;
  otherwise it falls back to the provisioned Gradle 8.9.

## Multiple apps
- Simplest: one repo per app, each with this workflow (use this as a template repo).
- Or a monorepo: build a specific module with `./gradlew :appname:assembleDebug`
  and a build matrix.
