# YAML Config Reference

## Minimal config (HTML template mode)

```yaml
project:
  name: "My App"
  output_dir: "output"
  device: "iPhone 16 Pro - Black Titanium - Portrait"
  output_size: "iPhone6_9"

screenshots:
  01_hero:
    template: "templates/hero.html"
    variables:
      headline: "Your Headline"
      subtitle: "Your subtitle text"
    assets:
      app_screenshot: "screenshots/home.png"
```

## Project section

```yaml
project:
  name: "App Name"                                        # Project name
  output_dir: "output"                                    # Where screenshots go
  device: "iPhone 16 Pro - Black Titanium - Portrait"     # Device frame to use
  output_size: "iPhone6_9"                                # App Store size (or [width, height])
```

`output_size` accepts named sizes or custom `[width, height]` arrays. See sizes table below.

## Screenshots section

Each key under `screenshots:` is a screenshot ID (used as filename).

### HTML template mode (recommended)

```yaml
screenshots:
  01_hero:
    template: "templates/hero.html"        # Path to HTML template
    variables:                             # Text — localizable via xcstrings
      headline: "Clean Your iPhone"
      subtitle: "Free up space instantly"
    assets:                                # Images — pre-rendered with device frame
      app_screenshot: "screenshots/home.png"
```

### variables vs assets

| Field | Template syntax | What it does | Localized? |
|-------|----------------|-------------|-----------|
| `variables` | `{{key}}` | Text substitution | Yes (via xcstrings) |
| `assets` | `{{key}}` | Image path, pre-rendered with device frame | Via directory convention |

Both use `{{key}}` in the HTML. The difference:
- **variables**: Pure text replacement. Values are extracted as xcstrings keys for localization
- **assets**: File paths. Koubou pre-renders each image with the configured device frame, then symlinks the composited image into the template sandbox

### Disabling device frame

By default, all image assets get the device frame applied. To disable per-screenshot:

```yaml
  fullscreen_slide:
    template: "templates/contrast.html"
    frame: false                          # No device frame for this slide
    variables:
      headline: "Bold Statement"
```

## Defaults section (optional)

```yaml
defaults:
  background:
    type: linear
    colors: ["#1a1a2e", "#16213e"]
    direction: 180
```

Applied to content-mode screenshots that don't specify their own background. Not used by HTML template mode (templates define their own backgrounds in CSS).

## Localization

```yaml
localization:
  base_language: "en"
  languages: ["en", "es", "de", "ja"]
  xcstrings_path: "koubou-strings.xcstrings"
```

### How text localization works

1. All `variables` values are extracted as localization keys
2. Koubou creates/updates the xcstrings file with these keys
3. Base language gets the value as-is with `state: "translated"`
4. Other languages get empty values with `state: "needs_translation"`
5. Edit translations in Xcode or any xcstrings editor
6. On generation, koubou substitutes the translated text for each language

### How asset localization works

**Convention-based** (recommended): Place localized screenshots in language subdirectories.

```
screenshots/
  en/
    home.png
    features.png
  es/
    home.png
    features.png
```

Config just references the base path — koubou resolves `screenshots/home.png` to `screenshots/{lang}/home.png` automatically:

```yaml
assets:
  app_screenshot: "screenshots/home.png"
```

Resolution order: `screenshots/{current_lang}/home.png` → `screenshots/{base_lang}/home.png` → `screenshots/home.png`

**Explicit mapping** (content mode only):

```yaml
asset:
  en: "screenshots/en/home.png"
  es: "screenshots/es/home.png"
  default: "screenshots/home.png"
```

### Localized output structure

```
output/
  en/
    iPhone_16_Pro_-_Black_Titanium_-_Portrait/
      01_hero.png
      02_feature.png
  es/
    iPhone_16_Pro_-_Black_Titanium_-_Portrait/
      01_hero.png
      02_feature.png
```

## Complete example

```yaml
project:
  name: "Undolly"
  output_dir: "AppStore/output"
  device: "iPhone 16 Pro - Black Titanium - Portrait"
  output_size: "iPhone6_9"

localization:
  base_language: "en"
  languages: ["en", "es"]
  xcstrings_path: "AppStore/koubou-strings.xcstrings"

screenshots:
  01_hero:
    template: "AppStore/templates/hero.html"
    variables:
      headline: "Find Duplicate Photos"
      subtitle: "Free up gigabytes of space"
      bg_start: "#1a1a2e"
      bg_end: "#0f3460"
    assets:
      app_screenshot: "screenshots/home.png"

  02_scan:
    template: "AppStore/templates/feature_top.html"
    variables:
      headline: "Smart Scanning"
      subtitle: "AI-powered duplicate detection"
      bg_start: "#0f3460"
      bg_end: "#1a1a2e"
    assets:
      app_screenshot: "screenshots/scan.png"

  03_results:
    template: "AppStore/templates/feature_side.html"
    variables:
      headline: "Review Results"
      subtitle: "Keep what matters"
      bg_start: "#1a1a2e"
      bg_mid: "#162447"
      bg_end: "#1b1b3a"
    assets:
      app_screenshot: "screenshots/results.png"

  04_statement:
    template: "AppStore/templates/contrast.html"
    frame: false
    variables:
      headline: "Your Photos, Organized"
      subtitle: "Made for people who care"
      bg_start: "#0f3460"
      bg_end: "#1a1a2e"

  05_more:
    template: "AppStore/templates/features_list.html"
    frame: false
    variables:
      headline: "And So Much More"
      feature_1: "iCloud Sync"
      feature_2: "Batch Delete"
      feature_3: "Smart Albums"
      feature_4: "Privacy First"
      feature_5: "No Ads"
      feature_6: "Widgets"
      bg_start: "#1a1a2e"
      bg_end: "#0f3460"
```

## Devices

### Recommended defaults

| Use case | Device name | Output size |
|----------|------------|-------------|
| iPhone (standard) | `iPhone 16 Pro - Black Titanium - Portrait` | `iPhone6_9` |
| iPhone (max) | `iPhone 16 Pro Max - Black Titanium - Portrait` | `iPhone6_9` |
| iPad | `iPad Pro 13 - M4 - Space Gray - Portrait` | `iPadPro13` |

### Finding device names

```bash
kou list-frames                    # All available frames (100+)
kou list-frames "iPhone 16"        # Filter by search term
kou list-frames "iPad"             # iPad frames
kou list-frames --output json      # Machine-readable
```

Device names must match exactly as shown by `kou list-frames`.

## App Store Sizes

| Name | Dimensions | Devices |
|------|-----------|---------|
| `iPhone6_9` | 1320x2868 | iPhone 16 Pro Max, 15 Pro Max (6.9") |
| `iPhone6_7` | 1290x2796 | iPhone 15/14/13/12 Pro Max, Plus (6.7") |
| `iPhone6_5` | 1242x2688 | iPhone 11 Pro Max, XS Max (6.5") |
| `iPhone6_1` | 1179x2556 | iPhone 16/15/14/13 Pro, 12 Pro, 11, XR (6.1") |
| `iPhone5_5` | 1242x2208 | iPhone 8 Plus, 7 Plus, 6s Plus (5.5") |
| `iPadPro13` | 2064x2752 | iPad Pro 13" M4, iPad Air 13" M2 |
| `iPadPro12_9` | 2048x2732 | iPad Pro 12.9" (3rd gen and later) |
| `iPadPro11` | 1668x2388 | iPad Pro 11", iPad Air 11" M2 |

List all: `kou list-sizes`

Custom dimensions: `output_size: [1320, 2868]`
