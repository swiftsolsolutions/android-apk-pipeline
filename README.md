# android-apk-pipeline (Claude skill)

Build an Android app into an installable APK using a **phone-driven GitHub
Actions pipeline** — no local machine or Android Studio required. Claude
generates the project, GitHub's runners compile it, and the signed APK lands in
a GitHub Release you can install from your phone.

This is a [Claude skill](https://docs.claude.com). It bundles:

- `SKILL.md` — the procedure Claude follows
- `references/` — stacks, versions, automation, Play-store assets, and
  **`lessons.md`** (hard-won fixes from real builds: stable signing, the
  "package conflicts" wall, release-only lint, native-crash pitfalls, and
  diagnosing failures when runner logs aren't reachable)
- `assets/compose-starter/` — a known-good Kotlin/Compose baseline to adapt
- `assets/build-android.yml` — the reusable CI workflow (release signing via
  secrets + failure-log capture)
- `assets/gen-keystore.yml`, `assets/play-publish.yml`, `assets/gen-play-graphics.py`
  — signing and Play-publish helpers

## How to use it in a Claude conversation

Skills are **not** auto-loaded from GitHub. To reuse this in a new chat, either:

1. **Upload the packaged skill.** Download `android-apk-pipeline.skill` from this
   repo's latest Release and upload it into the conversation, or
2. **Point Claude at this repo.** Give Claude this repo's URL and ask it to fetch
   `SKILL.md` and the referenced files, or
3. **Clone it yourself:** `git clone https://github.com/swiftsolsolutions/android-apk-pipeline`

## License

MIT (see `LICENSE`). The bundled workflow and starter are templates — no keys,
tokens, or secrets are included; you supply your own via GitHub Actions Secrets.
