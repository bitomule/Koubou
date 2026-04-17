# Design Guide

## Narrative Arc Framework

Plan slides as a story, not a feature list.

| # | Role | What to show | Notes |
|---|------|-------------|-------|
| 1 | **Hero/Hook** | Main value proposition. "What does this app solve?" | Optional app icon + strong tagline. 80% of users only see this one |
| 2 | **Differentiator** | Star feature. What sets it apart from competitors | The unique selling point |
| 3 | **Ecosystem** | Widgets, extensions, watch, integrations | Breadth of the product |
| 4+ | **Core Features** | One feature per slide, prioritized by importance | One focus per screenshot |
| Second-to-last | **Trust Signal** | Brand identity: "made for people who [X]" | Emotional connection |
| Last | **More Features** | Extra features in pill/list format, "coming soon" | Expanded closing |

**Critical**: Only the first 3 slides are visible in App Store search results without tapping into the listing. They must tell a complete story on their own.

## Planning Before Layout

- Write the full slide story first: slide role, headline, subtitle, screenshot choice
- Do not start CSS until the first 3 slides already feel like a coherent ad campaign
- Pick the strongest screenshot for the hero, not just the first one available
- If the source captures are weak, cropped badly, or inconsistent, ask for better captures before polishing CSS forever

## Style Intake Before Narrative

Before writing the narrative arc, inspect the app's real visual language. The screenshot campaign should feel like a stronger expression of the product, not a detached generic ad system.

Read `style-intake.md` when gathering inputs. Do this before asking broad visual questions.

### Signals to extract from the product

| Signal | What to inspect | What it tells you |
|---|---|---|
| Dominant colors | App icon, color assets, theme tokens, screenshots | Brand palette, accent logic, warmth/coolness |
| Contrast | Light/dark surfaces, text contrast, UI backgrounds | Whether the campaign should feel bright, moody, restrained, or vivid |
| UI density | Screen layouts, card count, spacing, information load | Whether the campaign should simplify, condense, or preserve structure |
| Corners and shadows | Cards, buttons, panels, materials | Whether the style feels soft, tactile, flat, glossy, or technical |
| Iconography | SF Symbols, custom icons, illustrations, badges | How decorative or austere the campaign can be |
| Copy tone | README, landing copy, UI text, onboarding | Whether headlines should feel calm, technical, warm, playful, or premium |
| General feeling | Whole product impression | Calm, technical, warm, energetic, editorial, playful, etc. |

### Translate product signals into screenshot direction

| Product signal combination | Screenshot direction |
|---|---|
| Sober palette + austere type + dense UI | More editorial or utility-led campaign, less glossy, cleaner hierarchy |
| Colorful UI + illustration + casual tone | More layered or playful campaign with richer depth and stronger accents |
| Technical workflow UI + trust-sensitive product | Cleaner, structured, credibility-first campaign with restrained effects |
| Warm palette + rounded cards + friendly voice | Softer, warmer, more tactile campaign with approachable copy |
| Dark UI + neon/vivid accents | High-contrast campaign is valid, but avoid the generic dark-gradient fallback by varying composition and texture |
| Neutral UI with weak branding | Let copy voice and strong UI crops carry identity instead of inventing unrelated decoration |

### When not to copy the app literally

- If the UI is too dense, simplify it for the campaign
- If the UI is visually plain, amplify hierarchy and copy without inventing a foreign brand language
- If the UI style hurts readability at thumbnail size, adapt it for App Store constraints while keeping brand truth

### Style decision record

Before touching layout, explicitly decide:

- `brand signals detected`
- `chosen campaign style`
- `copy voice`
- `background system`
- `device composition rhythm`
- `variation plan across slides`

If any item is unsupported by app evidence or user direction, gather more information first.

## Source Material

- Prefer clean simulator captures over noisy marketing exports
- If the user can choose, prefer recent 6.1-inch iPhone captures as the source because they adapt cleanly across App Store compositions
- Use screenshots with obvious focal points. Busy or low-contrast screens make the final slide weaker

## YAML-Aware Layout System

Always read these fields before writing CSS:

- `project.device`
- `project.output_size`
- screenshot `variables` length, especially `headline` and `subtitle`
- `kou inspect-frame "<device>" --output-size <size> --output json`

Treat the canvas as one of these classes:

| Canvas class | Typical config | What it means |
|---|---|---|
| Tall iPhone portrait | `iPhone6_9`, `iPhone6_7`, `iPhone6_5`, `iPhone6_1` | Aggressive scale, vertical storytelling, large edge-breaking device |
| Short iPhone portrait | `iPhone5_5` | Slightly tighter typography and less vertical dead space |
| iPad portrait | `iPadPro13`, `iPadPro12_9`, `iPadPro11` | More breathing room, but still thumbnail-readable |
| Custom `[width, height]` | Any | Infer orientation from aspect ratio, then match the nearest class |

Do not design with a generic "phone screenshot" mental model. `iPhone6_9` can handle much bolder scale than `iPhone5_5`, and iPad needs a different density again.

## Freedom Within Constraints

- These rules define minimum impact and readability, not one approved visual style
- Creative direction is intentionally open: minimal, bold, editorial, glossy, playful, or dense can all work
- User feedback on mood or style overrides the default direction of the skill
- The wrong move is not "being unusual"; the wrong move is being weak, small, repetitive, or unreadable
- A set can be quiet and premium or loud and editorial; the skill should protect strength, not force one house style

## Rule Hierarchy

Use the guidance in this order:

1. **Hard constraints** — legibility, canvas awareness, clear hierarchy, truthful marketing, and thumbnail strength
2. **Strong defaults** — asymmetry, variety, overlap, rhythm, and avoiding repetitive layouts
3. **Taste heuristics** — anti-slop warnings and stylistic preferences that may be broken when a stronger concept wins

Do not break hard constraints. You may break defaults or taste heuristics if the result is visibly stronger.

## Anti-Slop Detection

AI models converge toward statistically safe, high-probability design choices. This creates recognizable "AI slop." Actively avoid:

### Visual slop signals (warning signs)

- **Emoji as icons** — almost always wrong. Use CSS geometric shapes (colored bars, dots, rounded rects), SVG, or text-only approaches instead
- **Three or four identical cards** in a grid — usually weak. Vary size, emphasis, or rhythm unless a strict grid is genuinely the strongest answer
- **Perfectly symmetrical, emotionally cold layouts** — often a tell. Use asymmetry, overlap, edge breaks, or varied density unless symmetry is part of the concept
- **Glass cards with blurred backgrounds on solid gradients** — often overused. Keep them only if they materially improve depth and hierarchy
- **Generic purple/blue gradients** — common default. Prefer colors derived from the actual brand

### Copy slop signals (banned)

- "Revolutionary", "cutting-edge", "state-of-the-art", "next-generation"
- "Seamless", "frictionless", "streamlined"
- "Unlock", "unleash", "empower", "leverage", "harness"
- "Game-changing", "paradigm shift", "unprecedented"
- Headlines that are feature lists joined with "and"
- Compound buzzword phrases ("AI-powered smart cleaning")

### The logo-swap test

After generating, ask: "Could I replace this app's name with a competitor's and the slides still make sense?" If yes, the set is too generic. Each slide should feel specific to THIS app's actual UI and value proposition.

### Anti-slop replacements

| Slop pattern | Fix |
|---|---|
| Emoji icons in cards | CSS accent bars, colored dots, or text-only |
| Identical card grid | Vary card sizes, stagger layout, or use a simple list with accent marks |
| Centered flex column on every slide | Mix asymmetric splits, edge-breaking devices, overlap compositions |
| `clamp()` that can produce tiny text | Use `vw` or a safer `clamp()`, then verify the computed size on the target canvas |
| Generic gradient (#667eea → #764ba2) | Derive from actual brand colors |
| Buzzword headline | Concrete outcome in simple words |

### Generic fallback warning

The default AI failure mode is:

- dark gradient
- centered phone
- large white headline
- one mild tilt on a later slide

Do not use this as a starting point unless the app really supports that language or the user explicitly asks for it. A valid set should feel grounded in the app's own palette, tone, and UI character.

## Device-Aware Typography

Use viewport-relative sizing. On tall iPhone canvases (iPhone6_9 = 1320x2868), `vw` units produce text that can feel small because the canvas is extremely tall relative to its width. Compensate by going bigger than instinct suggests.

### Minimum scales for tall iPhone portrait (iPhone6_9, iPhone6_7, iPhone6_5)

| Element | Minimum | Recommended | Notes |
|---|---|---|---|
| Hero/statement headline | `10vw` | `11vw` – `14vw` | Single focal point, must dominate |
| Side-layout headline | `10vw` | `10vw` – `13vw` | Occupies ~50% width, needs to compensate |
| Subtitle | `4.5vw` | `4.8vw` – `5.5vw` | Must be readable, not decorative |
| Feature list titles | `5.5vw` | `6vw` – `7vw` | On closing/contrast slides |
| Feature list subtitles | `3.8vw` | `4vw` – `4.5vw` | Secondary but still legible |

### Sizing rules

- **Use `vw` or `clamp()` deliberately**. `clamp()` is useful when the same template serves multiple output sizes, but on a single known canvas it can hide the actual rendered size. If using it, verify the computed size on the target canvas
- **Never go below the minimums above**. If copy doesn't fit at minimum scale, rewrite the copy or switch layout — do not shrink the text
- **3x+ scale jump** between headline and subtitle. If headline is `12vw`, subtitle should be around `4vw`–`5vw`, not `8vw`
- **Weight contrast**: headlines at 700–800, subtitles at 400. Never headline 600 / subtitle 500 — the difference is invisible
- **Letter-spacing**: `-0.02em` to `-0.03em` on headlines signals craft and tightens large text
- **Line-height**: `1.04`–`1.1` for headlines (tight), `1.3` for subtitles

### Why clamp() can mislead

On iPhone6_9 (1320px wide), `clamp(112px, 9.6vw, 150px)` computes to `126px`. That sounds big, but on a 2868px tall canvas it's only ~4.4% of the height. The text will look small. `11.5vw` = `152px` = ~5.3% of height — visibly bigger. Always think in terms of how much vertical canvas the text occupies, not just its pixel size.

## Device-Aware Image Scale

These ranges are starting points for tall iPhone portrait outputs:

| Layout | Device guidance |
|---|---|
| Hero | `82vw` to `94vw`, usually breaking the bottom or side edge |
| Feature-top | `78vw` to `90vw`, often overlapping into a copy card |
| Side layout | container `56vw` to `66vw`, device itself `105%` to `130%` of that container |
| Contrast / closing | no device, so text/cards must carry the visual weight |

Rules:

- A device that sits politely in the middle and leaves a giant moat of background around it is too small
- Side layouts should usually crop or break an edge; otherwise they read as timid
- On contrast slides, the content cluster should occupy roughly `45%` to `60%` of canvas height. Tiny centered title + tiny pills is a reject
- Large crops, odd asymmetry, and aggressive overlap are valid if the slide stays legible and premium

## Thumbnail QA

- Review every generated slide twice: once full-size, once as a reduced thumbnail mental model
- If the headline loses impact or the cards collapse into noise at smaller size, the slide is not ready
- Thumbnail failure should trigger one of three changes: rewrite the copy, increase the scale, or simplify the composition
- Do not preserve a clever layout if it stops reading clearly at App Store browsing size

## Complex Layout Toolkit

Default to richer composition primitives when the slide needs them:

- CSS Grid for asymmetric text/device splits
- Absolute-positioned glow shapes, halos, and background orbs
- Overlapping glass cards behind copy
- Edge-breaking devices with rotation and crop
- Layered panels or staggered stacks instead of one simple column
- Negative margins and `translate()` to tighten copy-to-device distance
- Oversized screenshot crops for detail slides

Do not rely on a plain flex column for every slide. A premium App Store set usually needs at least one or two layouts with overlap, layering, and deliberate asymmetry.

## User Feedback Precedence

When the user gives directional feedback, reinterpret the design without breaking QA:

- "More premium" -> cleaner hierarchy, fewer elements, stronger type, better spacing
- "More bold" -> larger type, stronger crops, more aggressive overlap, higher contrast
- "Less minimal" -> more layers, cards, badges, supporting shapes, richer depth
- "More editorial" -> asymmetry, strong cropping, more deliberate text blocks
- "More air" -> fewer elements, bigger margins, stronger hero focus
- "More density" -> more structured cards/grid, but never micro-text

The feedback changes the expression of the slide, not the minimum quality bar.

## Copywriting Rules

### Iron rules

- **One idea per headline** — never join concepts with "and"/"y"
- **Simple vocabulary** — prefer 1-2 syllable words
- **3-5 words per line** — readable in App Store thumbnail
- **Arm test**: if you can't read it at arm's length, the text is too small
- **One-second rule**: the headline should be understandable in about one second
- **Intentional line breaks** — control wraps with `<br>` when needed

### Three approaches (choose per slide)

1. **Paint a moment** — "Check your coffee without opening the app"
2. **Declare an outcome** — "A home for every coffee you buy"
3. **Kill a pain** — "Never waste a great bag of coffee"

### Copy process

1. Draft at least 2-3 headline directions before choosing one
2. Prefer the simplest line that still feels premium and specific
3. Read it at arm's length and apply the one-second rule
4. Only then move on to layout

### What NOT to write

- Headlines that are feature lists
- Compound ideas joined with "and"
- Buzzwords without substance ("AI-powered", "revolutionary")
- More than 2 lines of text per screenshot
- Tiny category labels pretending to be copy

## CSS Rules for Templates

### Typography

- **Headline**: `10vw`–`14vw` (see Device-Aware Typography for minimums per canvas class)
- **Subtitle**: `4.5vw`–`5.5vw`
- **Font stack**: `-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", sans-serif`
- **Font weight**: 700-800 for headlines, 400 for subtitles (never 500-600 for either — the weight difference must be obvious)
- **Letter-spacing**: `-0.02em` to `-0.03em` on headlines
- **Line-height**: `1.04`–`1.1` for headlines, `1.3` for subtitles
- **Color**: White text on dark backgrounds. Never gray on gray
- **Sizing**: Prefer plain `vw` units on known canvases. Use `clamp()` only for multi-output templates, and verify the computed value meets the minimum
- Avoid micro-labels and eyebrow text by default. If a small label is not essential to the selling message, remove it
- Do not put the app name as a tiny decorative line at the top. Either omit it or render it at a clearly intentional, readable size
- If a line of text feels like a section title, category tag, or UI annotation instead of marketing copy, it probably should not be there
- If an app icon is used, it should support the hero composition or closing brand moment, not act as a miniature badge in a corner

### Backgrounds

- Use CSS gradients. Avoid flat solids
- Vary gradients between slides (direction, colors, type)
- Derive gradient colors from the app's brand palette
- Dark backgrounds with light text perform best in App Store

### Device placement

- Width: 70-85% of viewport width depending on layout
- The `{{asset_name}}` in templates receives the screenshot already composited inside the device frame — just use `<img>` to place it
- The device should feel primary, not like a thumbnail floating in empty space
- At least one of the first three slides should use a more assertive composition: tilt, crop, off-center placement, or edge break
- Do not keep every device perfectly upright and centered. Repetition kills the set

### Transform and positioning safety

- **Be careful with `rotate()` + `translate()` on a centered device** — it often shifts the visual center and makes the device look broken. Use it only if the rendered output still feels intentionally centered
- **Rotation is safe on asymmetric layouts** — when the device is pushed to one side (absolute positioned, breaking an edge), rotation adds dynamism without decentering issues
- **Test after generation**: if the device looks off-center in the rendered output, remove transforms and simplify
- **Device breaking edges intentionally**: use `position: absolute` with negative offsets (`right: -12%`) to crop the device at the canvas edge. This is a strong composition tool for side layouts

### Device-text zone planning

Before writing CSS, sketch which zone each element owns:

- **Hero**: text owns top 30-40%, device owns bottom 60-70%
- **Side-split**: text owns left 45-50%, device owns right 50-55% (device can break the right edge)
- **Feature-top**: device owns top 55-65%, text owns bottom 35-45%
- **Contrast/closing**: text and content own the full canvas

Within each zone, elements should feel anchored, not floating. If there's a gap of more than 15% of canvas height between the last text element and the device top, tighten the composition.

### Device cropping rules

A device image can be intentionally cropped at one edge to create a dynamic "emerging from" effect. But **unintentional cropping is a reject**. Check after every render:

**Intentional crop (acceptable):**
- Device slides up from the bottom edge — the bottom of the phone frame is hidden but the screen content and top bezel/notch are fully visible
- Device breaks the left or right edge in a side layout — one side is hidden but the visible portion shows the full screen content
- The crop is at ONE edge only, and the device clearly "continues" beyond the canvas

**Unintentional crop (reject — fix immediately):**
- The device top (notch/Dynamic Island area) is cut off by text above it or by the canvas edge
- The device is cropped at TWO edges simultaneously (top and bottom, or left and right)
- The visible portion of the screen content is too small to read — the user cannot tell what the app shows
- The text headline overlaps the device in a way that obscures the app content (text should be in its own zone, not on top of the screen area)
- The device frame is cropped so aggressively that it no longer reads as a phone — it just looks like a rectangle with rounded corners

**How to fix cropping issues:**
1. Reduce device image width (e.g., from 88% to 72-78%)
2. Increase `margin-top` or `padding-top` on the device container to push it down
3. If the text zone is too large, tighten the text (shorter copy, less padding) instead of shrinking the device
4. **Switch from flex to absolute positioning** — `flex: 1` + `overflow: hidden` is the #1 cause of silent device cropping. The flex container calculates remaining space but the device image aspect ratio is taller than expected (iPhone frames are ~2:1 height:width). Use `position: absolute; bottom: 2%;` instead, so you control exactly where the device sits
5. After fixing, always re-render and re-check — do not assume the fix worked

**The flex-overflow trap (critical):**
- A common pattern is `display: flex; flex-direction: column` with the device area as `flex: 1; overflow: hidden; align-items: flex-end`. This silently crops the device bottom because the image natural height exceeds the remaining flex space
- iPhone device frames with their bezels have a ~2:1 aspect ratio. At `width: 82vw` on a 1320px-wide canvas, the image is ~1082px wide and ~2212px tall — taller than the remaining space after text
- **Fix**: use `position: absolute` for the device with explicit `bottom` offset, or use `height: 100%; width: auto; max-width: 82%` to force the image to fit the available height
- Calculate: at `72vw` (950px), the device height is ~1942px, which fits on most hero layouts with standard text sizes

### Layout variation (mandatory)

NEVER repeat the same layout in consecutive slides. Alternate between:

1. **Hero**: Text top, device bottom (centered)
2. **Feature-top**: Device top, text bottom
3. **Feature-side**: Device and text side by side
4. **Contrast**: Text only, no device (bold statement slide)

### Visual rhythm

- Alternate light and dark backgrounds
- Include 1-2 contrast slides (no device, just text)
- One focal point per screenshot — never overload

### Vertical spacing

- Large empty bands between headline/subtitle and the device are a failure
- Text and device should feel compositionally related, not stacked as two unrelated blocks
- If the middle of the slide is mostly empty background, tighten the composition
- Use scale, overlap, tilt, and block placement to remove dead space before adding more text
- If text and cards occupy only a tiny island in the center of a tall canvas, the layout is under-scaled

## Length-Aware Layout Choice

- Short, high-impact copy earns big hero or statement layouts
- Medium copy works in feature-top, split, or card-overlap layouts
- Long copy should trigger either a stronger side layout, more width for text, or a rewrite
- Do not keep the same layout and keep shrinking font sizes just because the text is long

## Variety Across the Set

- The set should feel like one campaign with multiple beats, not one layout repeated four times
- Vary at least these axes across the first 4 slides:
  - device posture
  - crop aggressiveness
  - symmetry vs asymmetry
  - card-led vs device-led composition
  - contrast slide vs device slide rhythm
- Consistency should come from palette, typography family, and narrative arc, not from cloning the same composition
- When the user asks for a specific direction, adapt the whole set to that mood without collapsing all slides into one repeated solution

### Sameness check

Reject the set if consecutive slides repeat too many of the same ingredients:

- same background logic
- same text block geometry
- same device posture
- same crop aggressiveness
- same card/list motif
- same emotional tone

Campaign consistency should come from brand signals and narrative, not from reusing the same template shape.

## Closing Slide Rules

- Closing or "more features" slides must feel deliberately oversized, not like metadata pasted into the center
- In tall iPhone portrait, the content cluster should occupy 60-75% of canvas height, centered or anchored to top
- Prefer fewer, larger items over many tiny chips
- Do not default to a perfectly even grid if it kills energy; vary emphasis and rhythm unless a cleaner grid clearly works better
- If the closing slide still reads like a dashboard widget grid, increase the scale or reduce the amount of information

### Iconography on closing slides

- **Never use emoji** as feature icons. Emoji render inconsistently across platforms, look cheap at marketing scale, and are an instant "AI slop" tell
- Preferred alternatives (in order):
  1. **Text-only with accent marks** — a colored vertical bar, dot, or dash next to each feature name. Cleanest, most premium
  2. **CSS geometric shapes** — simple colored circles, rounded rects, or lines as visual anchors
  3. **SVG icons** — only if the user provides custom icons or a specific icon set
  4. **SF Symbols via image assets** — if the user can export them as images
- The accent element should support the typography, not compete with it. A `1vw`-wide gradient bar is more premium than a `7vw` emoji

## What NOT to do

### Scale failures
- Text smaller than 50px (invisible in thumbnail)
- Headlines below the minimum `vw` for the canvas class
- `clamp()` ranges where the computed value is below the minimum — always verify
- Keeping text tiny instead of changing the layout or rewriting the copy
- Treating `iPhone6_9` and `iPadPro13` as if they wanted the same density

### Composition failures
- Same layout on all screenshots
- Consecutive slides where the phone sits in nearly the same posture and position
- Huge gaps where neither the text nor the device owns the slide
- Combining `rotate()` + `translate()` on centered devices (causes decentering)
- Text and device overlapping accidentally without intentional z-index separation
- More than 2 lines of text per screenshot

### Slop failures
- Emoji as icons on any slide
- Three or four identical cards in a uniform grid
- Buzzword headlines ("AI-powered", "revolutionary", "seamless")
- Generic gradients not derived from the brand palette
- Perfectly symmetrical, cold layouts on every slide

### Content failures
- Colors outside the brand palette
- Showing features that don't exist in the app
- Flat white or black backgrounds without gradient
- Tiny top-left labels like "review flow", "smart cleanup", or a miniature app name with no strategic value

### Process failures
- Presenting the first technically successful render without a quality pass
- Not reviewing against the rejection checklist before showing to the user
- Defending a weak slide instead of redesigning it

## Rejection Checklist

Do not present screenshots as final until all of these are true:

### Story and copy
- The first 3 slides tell a complete product story on their own
- Headlines sound like marketing, not documentation or feature labels
- Zero banned copy-slop phrases (see Anti-Slop Detection)
- Each headline is understandable in one second

### Layout and composition
- No two consecutive slides use the same device posture and composition
- The device feels like a hero element whenever a device is present
- There are no large dead zones (>15% canvas height) between copy and imagery
- The layout uses enough visual complexity for the message: overlap, grid, crop, cards, or contrast when needed
- The set shows variety in execution instead of repeating one safe layout

### Scale and readability
- Headlines are at or above the minimum `vw` scale for the target canvas (see Device-Aware Typography)
- There are no tiny decorative top labels unless the user explicitly asked for them
- The typography and device scale match the actual `project.output_size` canvas
- Each slide still reads at thumbnail size without losing the main message

### Visual quality
- No emoji used as icons anywhere
- No identical card grids (vary sizes, emphasis, or use text-only)
- Device transforms don't cause decentering (check hero slides especially)
- **No unintentional device cropping** — the device top (notch/Dynamic Island) must be visible on hero slides. If the bottom is cropped, it must look intentional ("emerging from below"), not accidental. If the screen content is too small to read, the device is over-cropped
- Text and device occupy distinct zones without accidental cheap overlap
- Closing slides carry real visual weight — content cluster fills 60%+ of canvas height
- The set reads like App Store advertising, not an internal product deck

### Logo-swap test
- Could a competitor's name replace the app name and the slides still work? If yes, make them more specific to this app's actual UI and value prop

## HTML Template Examples

All templates use viewport-sized layouts. Koubou sets the viewport to the exact App Store dimensions (e.g., 1320x2868 for iPhone6_9).

Every template body **must** annotate measurable elements so Koubou can emit a layout sidecar JSON:

```html
<!-- data-kou-id: unique identifier — required for JSON layout extraction -->
<!-- data-kou-role: semantic hint — headline | supporting | device | feature-title | feature-sub -->
```

If `data-kou-id` is missing from an element, it will not appear in the sidecar and QA is blind to its geometry.

### Hero Template (text top, device bottom)

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
    background: linear-gradient(180deg, {{bg_start}} 0%, {{bg_end}} 100%);
    position: relative;
  }
  /* Text uses absolute positioning at top */
  .text-area {
    position: absolute;
    top: 7%;
    left: 0;
    right: 0;
    text-align: center;
    padding: 0 6%;
    z-index: 2;
  }
  h1 {
    font-size: 11.5vw;
    font-weight: 800;
    color: white;
    line-height: 1.05;
    margin-bottom: 2.5vh;
    letter-spacing: -0.03em;
  }
  p {
    font-size: 5vw;
    font-weight: 400;
    color: rgba(255,255,255,0.7);
    line-height: 1.3;
  }
  /* Device uses absolute positioning from bottom — prevents the flex-overflow crop trap.
     At 72vw the device frame fits fully on tall iPhone canvases with standard text above. */
  .device-area {
    position: absolute;
    bottom: 2%;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1;
  }
  .device-area img {
    width: 72vw;
    height: auto;
    filter: drop-shadow(0 40px 80px rgba(0,0,0,0.6));
    /* Do NOT add rotate() here — causes decentering on centered layouts.
       Use rotation only on asymmetric/side layouts where the device breaks an edge. */
  }
</style>
</head>
<body>
  <div class="text-area">
    <h1 data-kou-id="headline" data-kou-role="headline">{{headline}}</h1>
    <p data-kou-id="subtitle" data-kou-role="supporting">{{subtitle}}</p>
  </div>
  <div class="device-area">
    <img data-kou-id="device" data-kou-role="device" src="{{app_screenshot}}" alt="">
  </div>
</body>
</html>
```

### Feature-Top Template (device top, text bottom)

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(160deg, {{bg_start}} 0%, {{bg_end}} 100%);
    padding: 5% 6% 6%;
  }
  .device-area {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    width: 100%;
  }
  .device-area img {
    width: 78%;
    height: auto;
    object-fit: contain;
    transform: translateY(-2%);
  }
  .text-area {
    text-align: center;
    padding: 0 6%;
    max-width: 86%;
  }
  h1 {
    font-size: 10.5vw;
    font-weight: 800;
    color: white;
    line-height: 1.08;
    margin-bottom: 2vh;
    letter-spacing: -0.03em;
  }
  p {
    font-size: 4.8vw;
    font-weight: 400;
    color: rgba(255,255,255,0.7);
    line-height: 1.3;
  }
</style>
</head>
<body>
  <div class="device-area">
    <img data-kou-id="device" data-kou-role="device" src="{{app_screenshot}}" alt="">
  </div>
  <div class="text-area">
    <h1 data-kou-id="headline" data-kou-role="headline">{{headline}}</h1>
    <p data-kou-id="subtitle" data-kou-role="supporting">{{subtitle}}</p>
  </div>
</body>
</html>
```

### Feature-Side Template (device left, text right)

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
    display: flex;
    flex-direction: row;
    align-items: center;
    background: linear-gradient(135deg, {{bg_start}} 0%, {{bg_mid}} 50%, {{bg_end}} 100%);
  }
  .device-area {
    width: 58%;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 4% 2% 4% 5%;
  }
  .device-area img {
    width: 96%;
    height: auto;
    object-fit: contain;
    transform: rotate(-7deg);
  }
  .text-area {
    width: 42%;
    padding-right: 7%;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  h1 {
    font-size: 10vw;
    font-weight: 800;
    color: white;
    line-height: 1.08;
    margin-bottom: 2vh;
    letter-spacing: -0.03em;
  }
  p {
    font-size: 4.5vw;
    font-weight: 400;
    color: rgba(255,255,255,0.7);
    line-height: 1.3;
  }
</style>
</head>
<body>
  <div class="device-area">
    <img data-kou-id="device" data-kou-role="device" src="{{app_screenshot}}" alt="">
  </div>
  <div class="text-area">
    <h1 data-kou-id="headline" data-kou-role="headline">{{headline}}</h1>
    <p data-kou-id="subtitle" data-kou-role="supporting">{{subtitle}}</p>
  </div>
</body>
</html>
```

### Contrast Template (text only, no device)

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(180deg, {{bg_start}} 0%, {{bg_end}} 100%);
    text-align: center;
    padding: 0 10%;
  }
  h1 {
    font-size: 13vw;
    font-weight: 800;
    color: white;
    line-height: 1.06;
    margin-bottom: 4vh;
    letter-spacing: -0.03em;
  }
  p {
    font-size: 5vw;
    font-weight: 400;
    color: rgba(255,255,255,0.7);
    line-height: 1.3;
  }
</style>
</head>
<body>
  <h1 data-kou-id="headline" data-kou-role="headline">{{headline}}</h1>
  <p data-kou-id="subtitle" data-kou-role="supporting">{{subtitle}}</p>
</body>
</html>
```

### Closing / Feature List Template (text-only with accent bars)

Uses CSS accent bars instead of emoji or icons. Clean, premium, scales well.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(180deg, {{bg_start}} 0%, {{bg_end}} 100%);
    padding: 0 6%;
  }
  .content {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    gap: 9vh;
  }
  h1 {
    font-size: 14vw;
    font-weight: 800;
    color: white;
    line-height: 1.04;
    letter-spacing: -0.03em;
    text-align: center;
  }
  .features {
    display: flex;
    flex-direction: column;
    gap: 5vh;
    width: 100%;
  }
  .feature {
    display: flex;
    align-items: center;
    gap: 4vw;
    padding: 0 2vw;
  }
  .feature-accent {
    width: 1vw;
    height: 7vh;
    border-radius: 1vw;
    background: linear-gradient(180deg, {{accent_start}}, {{accent_end}});
    flex-shrink: 0;
  }
  .feature-title {
    font-size: 6.5vw;
    font-weight: 700;
    color: white;
    line-height: 1.15;
    letter-spacing: -0.02em;
  }
  .feature-sub {
    font-size: 4.2vw;
    font-weight: 400;
    color: rgba(255,255,255,0.4);
    margin-top: 0.4vh;
  }
</style>
</head>
<body>
  <div class="content">
    <h1 data-kou-id="headline" data-kou-role="headline">{{headline}}</h1>
    <div class="features">
      <div class="feature">
        <div class="feature-accent"></div>
        <div>
          <div data-kou-id="feature-1-title" data-kou-role="feature-title" class="feature-title">{{feature_1_title}}</div>
          <div data-kou-id="feature-1-sub" data-kou-role="feature-sub" class="feature-sub">{{feature_1_sub}}</div>
        </div>
      </div>
      <!-- Repeat for each feature: use data-kou-id="feature-N-title" / "feature-N-sub" -->
    </div>
  </div>
</body>
</html>
```

## Adapting Templates

These are starting points. For each project, adapt:

- **Gradient colors**: Match brand palette
- **Font sizes**: Scale based on text length (shorter text → larger font)
- **Device image width**: Adjust between 65-85% based on how much screen real estate the device needs
- **Spacing**: Adjust padding percentages based on text/device balance
- **Additional elements**: Add app icons, floating UI elements, or badges as extra `<img>` tags using additional asset variables
- **Composition**: If the template still feels generic after first render, change layout, scale, or posture instead of only tweaking colors
- **Quality gate**: Do not ship the first successful render; compare it against the rejection checklist and iterate until it feels like App Store marketing
