# Stack selection — only the build step changes

The pipeline invariant: **checkout → toolchain → build → publish APK to a
Release** is identical across stacks. When the user's requirement calls for a
different stack, swap only the build command (and its toolchain setup step).
Everything else in `assets/build-android.yml` stays the same.

Pick the stack from the requirement, don't force one:

## Native Kotlin + Jetpack Compose  (default for new apps)
Modern declarative UI. Use `assets/compose-starter` as the baseline and adapt
dependencies, permissions, modules, or NDK to the requirement.
- Build: `gradle assembleDebug` (or `./gradlew assembleDebug` if a wrapper exists)

## Native Kotlin/Java + XML Views  (leanest)
Fewest dependencies and no Compose-compiler version coupling. Good for very
light apps or when Compose is overkill. Same Gradle build command as above.

## Flutter
Cross-platform. Project has its own structure (`lib/`, `pubspec.yaml`, `android/`).
- Toolchain: add `subosito/flutter-action@v2` instead of relying only on Gradle
- Build: `flutter pub get && flutter build apk --debug`
- APK path: `build/app/outputs/flutter-apk/app-debug.apk`

## React Native
- Toolchain: `actions/setup-node` + `npm install`, then Gradle in `android/`
- Build: `cd android && ./gradlew assembleDebug`
- APK path: `android/app/build/outputs/apk/debug/app-debug.apk`

## Game engine / other
Unity, Godot, etc. export an Android Gradle project or an APK directly; wire the
engine's CLI export as the build step, then reuse the publish-to-Release step.

## Heavy builds (any stack)
- Raise `org.gradle.jvmargs` (runners have 16 GB).
- Gradle build cache + configuration cache are already enabled.
- C/C++: install the NDK (uncomment the NDK step in the workflow).
- Long builds: bump `timeout-minutes`, or move `runs-on:` to a GitHub larger
  runner or a self-hosted runner.
