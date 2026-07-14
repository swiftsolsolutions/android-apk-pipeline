# Known-good version matrix

Use this set unless the user's project pins otherwise. These versions are
mutually compatible and build cleanly on GitHub-hosted `ubuntu-latest` runners.

| Component            | Version         | Declared in                     |
|----------------------|-----------------|---------------------------------|
| Gradle               | 8.9             | workflow `setup-gradle` / wrapper |
| Android Gradle Plugin| 8.7.3           | root `build.gradle.kts`         |
| Kotlin               | 2.1.0           | root `build.gradle.kts`         |
| Compose compiler     | 2.1.0 (plugin)  | root `build.gradle.kts` (`org.jetbrains.kotlin.plugin.compose`) |
| Compose BOM          | 2024.12.01      | `app/build.gradle.kts`          |
| activity-compose     | 1.9.3           | `app/build.gradle.kts`          |
| JDK (build)          | 17 (Temurin)    | workflow `setup-java`           |
| compileSdk / targetSdk | 35            | `app/build.gradle.kts`          |
| minSdk               | 24              | `app/build.gradle.kts`          |

## Compatibility rules that actually bite
- AGP 8.7.x requires **Gradle 8.9+**. If you bump AGP, bump Gradle to match
  (see the AGP release notes' Gradle compatibility table).
- The Compose compiler plugin version must **equal the Kotlin version**
  (Kotlin 2.x uses `org.jetbrains.kotlin.plugin.compose`, not the old
  `composeOptions { kotlinCompilerExtensionVersion }`).
- AGP major version dictates the **minimum JDK**. AGP 8.x needs JDK 17+.

## Targeting Google Play (only if the user later publishes)
Play requires **targetSdk/compileSdk 36 (Android 16)** for new submissions as of
Aug 31, 2026, and native libraries aligned to **16 KB** pages. For phone-only
sideload testing, 35 is fine. To make a build Play-ready:
- Set `compileSdk = 36` and `targetSdk = 36` in `app/build.gradle.kts`.
- Keep Capacitor/AGP current so 16 KB alignment is handled automatically.
- Publishing itself (account, store listing, AAB upload, closed testing) is out
  of scope for this skill — the user handles Play submission.
