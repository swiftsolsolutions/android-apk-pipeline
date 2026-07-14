# Play Store graphics — specs, generation, persistence

Every Play listing needs graphics before it can go live. Generate them with
`assets/gen-play-graphics.py`, commit them into the repo in the **fastlane
`supply` image layout**, and they become both version-controlled and
auto-uploadable by `upload_to_play_store`.

## Required assets & exact specs (enforced by the generator)

| Asset | Size | Format | Notes |
|-------|------|--------|-------|
| App icon | **512×512** | 32-bit PNG (alpha OK) | ≤1 MB. Full-bleed square; Play masks it. |
| Feature graphic | **1024×500** | 24-bit PNG/JPEG, **NO transparency** | Flatten to RGB or Play rejects it. |
| Phone screenshots | 1080×1920 (9:16) | 24-bit PNG/JPEG | **≥2** (up to 8). Each side 320–3840 px; ratio 9:16–16:9. |
| 7-inch tablet | 1200×1920 | 24-bit | ≥2. Field accepts phone screenshots too. |
| 10-inch tablet | 1600×2560 | 24-bit | ≥2. |

Common rejections: alpha channel in the feature graphic; screenshot ratio
outside 9:16–16:9; a side under 320 px. The generator sizes everything inside
these bounds, so its output uploads cleanly.

## fastlane `supply` layout (commit here)

```
fastlane/metadata/android/en-US/
  images/
    icon.png
    featureGraphic.png
    phoneScreenshots/    1.png 2.png 3.png
    sevenInchScreenshots/1.png 2.png
    tenInchScreenshots/  1.png 2.png
```

With images present here and `skip_upload_images`/`skip_upload_screenshots`
**not** set, `upload_to_play_store` pushes them alongside the listing text.

## Generate

1. **Screenshots need source images.** Either capture real screens on the
   emulator via the `screengrab` lane (best), or draw faithful UI mockups. The
   generator *frames* these sources (phone frame + branded background + caption)
   into the required sizes — it does not invent the app's UI. Keep the raw
   sources in `store-assets/captures/` so the framing is reproducible.
2. Write a `play-graphics.config.json` (see below) and run:
   ```
   pip install "Pillow" "qrcode[pil]" --break-system-packages -q
   python3 tools/gen-play-graphics.py --config play-graphics.config.json
   ```
3. The icon + feature graphic are generated from brand config (built-in `qr` or
   `mono` motif), or pass `icon_src` to reuse the app's real launcher art.

### config shape
```json
{
  "app_name": "QR Studio",
  "subtitle": "Scan & Create QR codes",
  "tagline": "Fast · Private · No ads",
  "brand": { "c1": [45,212,191], "c2": [13,148,136], "accent": [15,118,110] },
  "motif": "qr",
  "out_dir": "fastlane/metadata/android/en-US/images",
  "screenshots": [
    { "src": "store-assets/captures/scan.png",    "caption": "Scan any QR code instantly" },
    { "src": "store-assets/captures/create.png",  "caption": "Create & share your own QR codes" },
    { "src": "store-assets/captures/history.png", "caption": "Every scan saved in your history" }
  ]
}
```
Set `"motif": "mono"` for a lettermark icon (uses the app name's initials) when
the app has no QR-style identity.

## Persist in the repo (what to commit)

- `tools/gen-play-graphics.py` — the generator (copy of `assets/gen-play-graphics.py`).
- `play-graphics.config.json` — the app's brand + captions.
- `store-assets/captures/*.png` — raw UI sources (so graphics are reproducible).
- `fastlane/metadata/android/en-US/images/**` — the generated deliverables.

Regenerate anytime the brand or screens change by re-running the generator and
committing the refreshed `images/**` (bump nothing else — graphics are
independent of `versionCode`).

## Which items this clears on "Finish setting up your app"
App icon, Feature graphic, Phone screenshots, 7-inch tablet, 10-inch tablet.
Still manual/Console-only: content rating, data safety, target audience, and a
**privacy policy URL** (host on the user's own site).
