---
name: koubou
description: Generate App Store screenshots using HTML/CSS templates with real device frames. Creates professional, localized screenshots for iPhone, iPad, Mac, and Watch. Use when user wants to create, design, or update App Store screenshots.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash(pip *)
  - Bash(pip3 *)
  - Bash(kou *)
  - Bash(playwright *)
  - Bash(python *)
  - Bash(python3 *)
  - Bash(open *)
  - Bash(mkdir *)
  - Bash(ls *)
  - Bash(cp *)
user-invocable: true
---

# Koubou: App Store Screenshot Generator

Generate professional App Store screenshots using HTML/CSS templates with 100+ real device frames, xcstrings localization, and pixel-perfect Apple dimensions.

> Screenshots are advertisements, not documentation. Each slide sells one feeling, outcome, or pain-point solution.

**User instructions always take priority over defaults in this skill.**

Reference files (read as needed, not upfront):
- `setup.md` — Installation of koubou + HTML rendering support
- `design-guide.md` — Design principles, copywriting rules, CSS rules, HTML template examples
- `yaml-reference.md` — YAML config format, localization, assets, devices, sizes
- `capabilities-reference.md` — Full koubou capabilities (content mode, highlights, zoom, gradients)

## Phase 1: Setup (silent, automatic)

Check if koubou is installed. If not, install it. Do not ask the user — just do it.

```bash
command -v kou >/dev/null 2>&1 || pip3 install koubou
kou setup-html 2>/dev/null || true
```

Only inform the user if installation fails. Read `setup.md` for troubleshooting.

## Phase 2: Gather Information

Collect what you need through natural conversation. Do NOT dump all questions at once.

### Required (ask in order, naturally)

1. **App**: Name, what it does (1 sentence), main value proposition
2. **Screenshots**: Where are the app captures? Search automatically first:
   - Glob for: `.maestro/`, `screenshots/`, `AppStore/`, `fastlane/screenshots/`, `marketing/`
   - If found, show what you found and confirm
   - If not found, ask how the user generates them
3. **Visual style**: Brand colors (accent, background), dark/light/colorful preference
   - If `Assets.xcassets`, `marketing/plan.md`, or prior marketing exists, derive colors from there without asking
4. **Features to highlight**: Prioritized list of features/benefits (recommend 3-5). Each slide = 1 feature
5. **Slide count**: How many screenshots (recommend 3-5 to start, Apple allows up to 10)

### Optional (ask only if relevant)

6. **Device**: Default is `iPhone 16 Pro - Black Titanium - Portrait`. Only ask if iPad/Mac/other makes sense
7. **Localization**: Only if the project already has xcstrings or multiple language support
8. **Extra assets**: App icon, floating UI elements, badges

### Derived (do NOT ask — figure out automatically)

- Background gradients (from brand colors)
- Layout distribution (hero → feature-top → feature-bottom → alternating)
- Headline copy (from features and value proposition)
- Secondary palette (variations of brand colors)

**Principle**: If context is available (CLAUDE.md, existing configs, marketing/plan.md, Assets.xcassets), use it without re-asking.

## Phase 3: Generate

Read `design-guide.md` before generating templates. Read `yaml-reference.md` before writing config.

1. Create working directory (e.g., `AppStore/` or wherever makes sense for the project)
2. Create `templates/` with HTML templates — **minimum 3 distinct layouts** (read `design-guide.md` for templates)
3. Create `config.yaml` with koubou config (read `yaml-reference.md` for format)
4. Run: `kou generate config.yaml --setup-html --verbose`
5. Open output folder: `open <output_dir>`
6. Ask if the user wants adjustments — iterate on specific slides without regenerating everything

### Iteration Rules

- When user asks to change a specific slide, only modify that template + config entry
- When user asks for a global style change (colors, fonts), update all templates
- Re-run `kou generate config.yaml --setup-html --verbose` after changes
- Use `kou live config.yaml --setup-html` if user wants real-time preview while editing

## Key Technical Details

### How assets work in HTML templates

In template HTML, reference assets with `{{asset_name}}`. In the YAML config, map `asset_name` to a file path under `assets:`.

Koubou automatically pre-renders each image asset with the configured device frame before passing it to the HTML template. The template receives a composited image (screenshot inside device frame) — it just places it with `<img src="{{asset_name}}">`.

To disable frame for a specific screenshot: set `frame: false` in its YAML definition.

### Template variable substitution

- `variables:` in YAML → `{{key}}` in HTML → localizable text (extracted to xcstrings)
- `assets:` in YAML → `{{key}}` in HTML → image file paths (pre-rendered with device frame)

### Output structure

```
{output_dir}/{language}/{device_name}/{screenshot_id}.png
```

Non-localized projects skip the language directory.

### Device frame names

Use exact names from `kou list-frames`. Common ones:
- `iPhone 16 Pro - Black Titanium - Portrait`
- `iPhone 16 Pro Max - Black Titanium - Portrait`
- `iPad Pro 13 - M4 - Space Gray - Portrait`

Search with: `kou list-frames "iPhone 16"`

### Output sizes (App Store dimensions)

| Name | Dimensions | Devices |
|------|-----------|---------|
| `iPhone6_9` | 1320x2868 | iPhone 16 Pro Max, 15 Pro Max |
| `iPhone6_7` | 1290x2796 | iPhone 15/14/13 Pro Max, Plus |
| `iPhone6_5` | 1242x2688 | iPhone 11 Pro Max, XS Max |
| `iPhone6_1` | 1179x2556 | iPhone 16/15/14/13 Pro |
| `iPhone5_5` | 1242x2208 | iPhone 8 Plus, 7 Plus |
| `iPadPro13` | 2064x2752 | iPad Pro 13" M4 |
| `iPadPro12_9` | 2048x2732 | iPad Pro 12.9" |
| `iPadPro11` | 1668x2388 | iPad Pro 11" |

Custom: `output_size: [1320, 2868]`
