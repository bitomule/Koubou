---
name: koubou
description: Generate App Store screenshots using HTML/CSS templates with real device frames. Creates professional, localized screenshots for iPhone, iPad, Mac, and Watch. Use when user wants to create, design, or update App Store screenshots.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash(kou *)
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

**Creative direction is open by default.** Use the rules in this skill to enforce impact, readability, and canvas-aware scale, not to make every set look the same.

## Rule Hierarchy

Treat the guidance in this skill in this order:

1. **Hard constraints** — readability, scale, thumbnail clarity, truthful product marketing, and real canvas awareness
2. **Strong defaults** — variety, asymmetry, overlap, rhythm, and avoiding generic layouts
3. **Taste preferences** — anti-slop heuristics and stylistic defaults that can be broken when a stronger idea clearly improves the work

If breaking a default produces a better screenshot set, break it deliberately and explain the tradeoff to yourself before generating.

Reference files (read as needed, not upfront):
- `setup.md` — Installation and HTML runtime setup
- `design-guide.md` — Design principles, copywriting rules, CSS rules, HTML template examples
- `style-intake.md` — How to inspect the app's real visual language before asking questions
- `style-interview.md` — Short, high-signal style questions and conversation patterns
- `yaml-reference.md` — YAML config format, localization, assets, devices, sizes
- `capabilities-reference.md` — Full koubou capabilities (content mode, highlights, zoom, gradients)

## Phase 1: Setup (silent, automatic)

Check if `kou` is available first. Do not reinstall or touch Python packaging if `kou` already works.

Preferred order:

```bash
kou --version 2>/dev/null
```

If `kou --version` succeeds:
- treat koubou as installed
- do **not** run `pip`, `pip3`, or `playwright install`
- do **not** try to "upgrade" or "fix" the user's environment proactively
- always run `kou setup-html` before generating, because this skill is HTML-only and the command is designed to be safe to repeat

If `kou --version` fails, read `setup.md` and follow the least invasive path for the environment.

For HTML rendering support:
- always use `kou setup-html`
- do **not** skip it just because HTML worked in a previous run
- do **not** run `playwright install chromium` directly

Only inform the user if setup fails. Never mutate a working installation.

## Phase 2: Read The App, Then Ask

Do not begin with a generic style questionnaire. Inspect the app's real visual language first, then ask only what is still missing or ambiguous.

Read `style-intake.md` before asking style questions. Follow this order.

### 2.1 Style discovery (mandatory before style questions)

Inspect local project sources first. Search automatically before asking the user for visual direction.

Prioritize these sources:

1. `Assets.xcassets`, app icons, illustrations, logos, color assets
2. Existing screenshots and marketing folders:
   - `.maestro/`
   - `screenshots/`
   - `AppStore/`
   - `fastlane/screenshots/`
   - `marketing/`
3. Product docs and positioning:
   - `README*`
   - `CLAUDE.md`
   - launch plans, landing-page copy, docs folders
4. Design tokens and UI code:
   - CSS variables
   - SwiftUI colors, gradients, materials, typography choices
   - web theme files and shared design constants
5. Prior App Store artifacts if they exist:
   - previous templates
   - old screenshot campaigns
   - localized marketing assets

Extract and summarize at least these signals:

- dominant colors and accent colors
- overall contrast: dark, light, mixed, muted, vivid
- UI density: airy, balanced, dense
- shape language: sharp, soft, rounded, card-heavy, flat
- iconography and illustration style
- typography direction if visible
- copy tone: calm, technical, playful, premium, warm, urgent
- whether the app feels calm, technical, warm, energetic, polished, playful, etc.

If the app style is clear:
- summarize the detected signals to the user in plain language
- confirm that you will build from that direction instead of restarting from a generic template language

If the signals are weak, missing, or contradictory:
- say what you found
- ask focused follow-up questions about the uncertainty instead of asking a broad design questionnaire

### 2.2 Intent interview (short, high-signal)

Read `style-interview.md` and ask only the minimum needed. Keep it conversational. Do not dump every question at once.

Required style questions when still needed:

1. What feeling should the campaign project: premium, playful, editorial, utilitarian, technical, warm, etc.?
2. Are there App Store references, brands, or screenshot sets that should influence the direction?
3. What is visually forbidden: loud gradients, glassmorphism, dark-only, card grids, overly playful styling, etc.?
4. What visual trait from the app itself must still be recognizable in the screenshots?

Optional questions only when still unresolved:

5. Preferred type direction or font personality
6. Light, dark, or mixed bias
7. Density preference: more air vs more information
8. Whether the set should feel tightly consistent or visibly varied across slides

### 2.3 Product information (still required)

After style discovery starts, collect the remaining production inputs naturally:

1. **App**: Name, what it does (1 sentence), main value proposition
2. **Screenshots**: Where are the app captures? Search automatically first:
   - If found, show what you found and confirm
   - If not found, ask how the user generates them
   - Prefer clean simulator captures that show the app UI clearly. If the user can choose, prefer recent 6.1-inch iPhone captures as the source material
3. **Features to highlight**: Prioritized list of features/benefits (recommend 3-5). Each slide = 1 feature
4. **Hero assets**: App icon or other brand asset. Search automatically before asking
5. **Slide count**: How many screenshots (recommend 3-5 to start, Apple allows up to 10)

Optional only if relevant:

6. **Device**: Default is `iPhone 16 Pro - Black Titanium - Portrait`. Only ask if iPad/Mac/other makes sense
7. **Localization**: Only if the project already has xcstrings or multiple language support
8. **Extra assets**: Floating UI elements, badges, supporting illustrations
9. **Additional constraints**: Required claims, forbidden styles, or marketing constraints

### 2.4 Style decision (mandatory before HTML)

Before drafting templates, explicitly decide and internally lock these six items:

- `brand signals detected`
- `chosen campaign style`
- `copy voice`
- `background system`
- `device composition rhythm`
- `variation plan across slides`

Each item must be justified by either:

- app evidence from style discovery, or
- direct user feedback from the interview

If you cannot justify one of these, keep asking focused questions before designing.

### Derived (do NOT ask unless blocked)

- Background gradients or textures from brand colors and UI mood
- Layout distribution (hero → feature-top → feature-bottom → alternating)
- Headline copy from features and value proposition
- Secondary palette from the app's actual palette
- Canvas class from `project.device` + `project.output_size` via `kou inspect-frame`
- Whether the app name should appear at all. Default: omit it unless it adds real brand value at readable size
- Whether the app icon should appear. Default: use it sparingly on hero or closing slides, not as a tiny decorative marker

**Principle**: if context is available locally, use it before asking. Style questions come after inspection, not before.

## Phase 3: Generate

Read `design-guide.md` before generating templates. Read `yaml-reference.md` before writing config.

1. Create working directory (e.g., `AppStore/` or wherever makes sense for the project)
2. Run `kou setup-html`
3. Read `project.device` and `project.output_size` from the YAML
4. Run `kou inspect-frame "<device>" --output-size <size> --output json` and use that geometry before writing CSS
5. Draft the narrative arc and 2-3 headline/subtitle options per slide before touching layout. Pick the strongest one first. Copy quality comes before CSS
6. Translate the style decision into a campaign brief:
   - what the set should feel like
   - what motifs are allowed
   - what motifs are banned
   - how much variation the first 5 slides should show
7. Create `templates/` with HTML templates — **minimum 3 distinct layouts**, and the first 3 slides must not repeat the same composition archetype
8. In HTML templates, annotate measurable layout elements with `data-kou-id`; add `data-kou-role` when it clarifies intent. Minimum annotations for most slides: headline, subtitle/supporting text, and main device image
9. Create `config.yaml` with koubou config (read `yaml-reference.md` for format)
10. Use CSS that adapts to the canvas and copy length: use `vw` or `clamp()` deliberately, prefer CSS Grid, overlap, and absolute-positioned layers, and verify the final computed text scale on the real canvas
11. **Before writing HTML**: plan text/device zones for each slide (which area owns what percentage of the canvas). Do not start CSS until zones are clear
12. Run: `kou generate config.yaml --output json`
13. For each generated HTML screenshot, read `layout_path` from the JSON result and inspect the sidecar before deciding the layout is acceptable
14. **Post-render QA** (mandatory — do not skip):
    - Review each generated slide visually
    - Open each `*.layout.json` sidecar referenced by `layout_path`
    - Check against the rejection checklist in `design-guide.md`
    - Check that the rendered set still reflects the app style you discovered instead of generic App Store defaults
    - Use layout JSON only for objective geometry: positions, occupied space, proportions, and mathematical overlaps
    - If `elements` is empty for an HTML slide that should be measured, treat that as missing or broken annotation and fix the template
    - Verify: no emoji icons, no identical card grids, no decentered devices, no text below minimum scale, no unintentional device cropping (device top/notch must be visible on hero slides; screen content must be readable)
    - Apply the logo-swap test: would these slides work for a competitor?
    - If any slide fails, fix and regenerate before showing to the user
15. Open output folder: `open <output_dir>`
16. Ask if the user wants adjustments — iterate on specific slides without regenerating everything

### Iteration Rules

- When user asks to change a specific slide, only modify that template + config entry
- When user asks for a global style change (colors, fonts, mood, density, boldness), update all templates
- Re-run `kou generate config.yaml --output json` after changes so the new `layout_path` values and sidecars stay in sync
- Use `kou live config.yaml` if user wants real-time preview while editing
- If a slide feels small, first increase scale or switch layout. Do not hide the problem with extra gradients or labels
- If copy forces tiny text, rewrite the copy or choose a more suitable layout; never accept a timid slide because "the text had to fit"
- Keep variety high: the goal is campaign consistency, not layout repetition
- Do not stop after the first successful render if the output still violates the design rules or rejection checklist
- If the user asks for a mood change, reinterpret the whole set inside the quality limits instead of defending the previous defaults
- If screenshot and layout JSON disagree, trust the rendered screenshot for taste and investigate the annotation or render timing instead of forcing a layout decision from stale geometry

## Hard Rules

### Hard constraints
- **Never use emoji as icons** — use CSS shapes (accent bars, dots) or text-only
- **Never use banned copy phrases** — "revolutionary", "seamless", "unlock", "game-changing", etc.
- **Apply the logo-swap test** — if a competitor's name would fit, the set is too generic

### Scale
- On tall iPhone portrait (`iPhone6_9`, `iPhone6_7`), hero headlines must be `>=10vw`, side-layout headlines `>=10vw`, subtitles `>=4.5vw`
- Use `vw` or `clamp()` only if the computed size still clears the minimum on the target canvas
- On contrast or closing slides, the content cluster must occupy 60%+ of canvas height

### Strong defaults
- Do not use the same upright, centered phone composition on consecutive slides
- Do not leave large empty bands (>15% canvas height) between headline and device
- Avoid combining `rotate()` + `translate()` on centered devices unless the visual center still feels intentional after render
- Do not use a simple centered flex column when the slide needs overlap, edge-breaking crops, or layered composition
- Plan text/device zones before writing CSS (see design-guide.md Device-Text Zone Planning)
- If you use card grids, stagger, emphasize, or simplify them unless a strict grid genuinely serves the concept

### Content
- Do not add tiny top labels, category labels, or app-name headers by default
- Do not render the app name as small decorative text unless clearly readable and strategic
- Do not use app icons as tiny corner decorations; if used, they should be a real brand element
- Do not use awkward, literal, or unnatural headlines just to be short
- Do not start layout work before the slide narrative and copy are coherent

### Process
- If the first 3 slides do not already feel App Store-ready, keep iterating before presenting them
- Do not present the first technically successful render as final — always review against the rejection checklist in design-guide.md
- Do not let the rules flatten the creative direction. A strange but strong composition is valid if it stays readable and high-impact
- Defaults can be broken when the final result is stronger, clearer, and more specific to the app
- Do not start from the generic fallback of dark gradient + centered phone + big white headline unless the app genuinely supports that language or the user explicitly wants it
- You should be able to explain to yourself why the campaign looks like this app and not a competitor with the same feature list

## Key Technical Details

### How assets work in HTML templates

In template HTML, reference assets with `{{asset_name}}`. In the YAML config, map `asset_name` to a file path under `assets:`.

Koubou automatically pre-renders each image asset with the configured device frame before passing it to the HTML template. The template receives a composited image (screenshot inside device frame) — it just places it with `<img src="{{asset_name}}">`.

To disable frame for a specific screenshot: set `frame: false` in its YAML definition.

### Template variable substitution

- `variables:` in YAML → `{{key}}` in HTML → localizable text (extracted to xcstrings)
- `assets:` in YAML → `{{key}}` in HTML → image file paths (pre-rendered with device frame)

### Layout JSON for HTML screenshots

For HTML screenshots, Koubou can emit a compact sidecar JSON with measured layout geometry.

- Use `data-kou-id` on any element that should be measurable
- Use `data-kou-role` only when the role helps the model interpret the element
- Keep annotations minimal and structural, not exhaustive
- Good defaults: annotate the main headline, supporting copy, and primary device or hero image

Example:

```html
<h1 data-kou-id="headline" data-kou-role="headline">{{headline}}</h1>
<p data-kou-id="subtitle" data-kou-role="supporting">{{subtitle}}</p>
<img data-kou-id="device" data-kou-role="device" src="{{app_screenshot}}" alt="">
```

Generation workflow:

- Run `kou generate config.yaml --output json`
- Read `layout_path` from the command output
- Open the referenced `*.layout.json`

Interpretation rules:

- Geometry fields are normalized ratios from `0..1`
- `elements` contains only annotated nodes
- `overlaps` contains only mathematical box intersections
- Use this file to understand layout facts, not to decide taste
- Do not invent subjective rules such as "too small" from the JSON alone; combine the geometry with the actual screenshot review

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

### Frame inspection for layout decisions

Use `kou inspect-frame "<device>" --output-size <size> --output json` to get:
- real frame size
- screen bounds and screen bbox
- safe margins
- coverage ratio
- orientation
- `canvas_class`

Use this data to choose typography scale, crop aggressiveness, and layout density.

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
