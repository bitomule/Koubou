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

## Source Material

- Prefer clean simulator captures over noisy marketing exports
- If the user can choose, prefer recent 6.1-inch iPhone captures as the source because they adapt cleanly across App Store compositions
- Use screenshots with obvious focal points. Busy or low-contrast screens make the final slide weaker

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

- **Headline**: 100-140px font-size
- **Subtitle**: 50-65px font-size
- **Font stack**: `-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", sans-serif`
- **Font weight**: 700-800 for headlines, 400-500 for subtitles
- **Color**: White text on dark backgrounds. Never gray on gray
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

- Width: 70-80% of viewport width
- The `{{asset_name}}` in templates receives the screenshot already composited inside the device frame — just use `<img>` to place it
- Always leave margin between device and edges (minimum 3-5% of viewport)
- The device should feel primary, not like a thumbnail floating in empty space
- At least one of the first three slides should use a more assertive composition: tilt, crop, off-center placement, or edge break
- Do not keep every device perfectly upright and centered. Repetition kills the set

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

## What NOT to do

- Text smaller than 50px (invisible in thumbnail)
- Same layout on all screenshots
- More than 2 lines of text per screenshot
- Device touching the edge without margin
- Colors outside the brand palette
- Showing features that don't exist in the app
- Flat white or black backgrounds without gradient
- Stacking multiple devices on one slide (unless deliberately showing ecosystem)
- Tiny top-left labels like "review flow", "smart cleanup", or a miniature app name with no strategic value
- Consecutive slides where the phone sits in nearly the same posture and position
- Huge gaps where neither the text nor the device owns the slide
- Presenting the first technically successful render without a quality pass

## Rejection Checklist

Do not present screenshots as final until all of these are true:

- The first 3 slides tell a complete product story on their own
- No two consecutive slides use the same device posture and composition
- The device feels like a hero element whenever a device is present
- There are no large dead zones between copy and imagery
- Headlines sound like marketing, not documentation or feature labels
- There are no tiny decorative top labels unless the user explicitly asked for them
- The set reads like App Store advertising, not an internal product deck

## HTML Template Examples

All templates use viewport-sized layouts. Koubou sets the viewport to the exact App Store dimensions (e.g., 1320x2868 for iPhone6_9).

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
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(180deg, {{bg_start}} 0%, {{bg_end}} 100%);
    padding: 8% 6% 0;
  }
  .text-area {
    text-align: center;
    flex-shrink: 0;
    max-width: 88%;
  }
  h1 {
    font-size: 120px;
    font-weight: 800;
    color: white;
    line-height: 1.1;
    margin-bottom: 24px;
  }
  p {
    font-size: 56px;
    font-weight: 400;
    color: rgba(255,255,255,0.85);
    line-height: 1.3;
  }
  .device-area {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    width: 100%;
    margin-top: 3%;
  }
  .device-area img {
    width: 82%;
    height: auto;
    object-fit: contain;
    transform: translateY(2%) rotate(-6deg);
    transform-origin: bottom center;
  }
</style>
</head>
<body>
  <div class="text-area">
    <h1>{{headline}}</h1>
    <p>{{subtitle}}</p>
  </div>
  <div class="device-area">
    <img src="{{app_screenshot}}">
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
    font-size: 110px;
    font-weight: 800;
    color: white;
    line-height: 1.1;
    margin-bottom: 20px;
  }
  p {
    font-size: 54px;
    font-weight: 400;
    color: rgba(255,255,255,0.8);
    line-height: 1.3;
  }
</style>
</head>
<body>
  <div class="device-area">
    <img src="{{app_screenshot}}">
  </div>
  <div class="text-area">
    <h1>{{headline}}</h1>
    <p>{{subtitle}}</p>
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
    font-size: 100px;
    font-weight: 800;
    color: white;
    line-height: 1.1;
    margin-bottom: 20px;
  }
  p {
    font-size: 50px;
    font-weight: 400;
    color: rgba(255,255,255,0.8);
    line-height: 1.3;
  }
</style>
</head>
<body>
  <div class="device-area">
    <img src="{{app_screenshot}}">
  </div>
  <div class="text-area">
    <h1>{{headline}}</h1>
    <p>{{subtitle}}</p>
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
    font-size: 140px;
    font-weight: 800;
    color: white;
    line-height: 1.15;
    margin-bottom: 32px;
  }
  p {
    font-size: 60px;
    font-weight: 400;
    color: rgba(255,255,255,0.75);
    line-height: 1.3;
  }
</style>
</head>
<body>
  <h1>{{headline}}</h1>
  <p>{{subtitle}}</p>
</body>
</html>
```

### Feature List Template (pills/badges for "more features" slide)

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
    padding: 0 8%;
  }
  h1 {
    font-size: 110px;
    font-weight: 800;
    color: white;
    line-height: 1.1;
    margin-bottom: 60px;
  }
  .pills {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 24px;
    max-width: 90%;
  }
  .pill {
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 60px;
    padding: 28px 56px;
    font-size: 48px;
    font-weight: 600;
    color: white;
    white-space: nowrap;
  }
</style>
</head>
<body>
  <h1>{{headline}}</h1>
  <div class="pills">
    <span class="pill">{{feature_1}}</span>
    <span class="pill">{{feature_2}}</span>
    <span class="pill">{{feature_3}}</span>
    <span class="pill">{{feature_4}}</span>
    <span class="pill">{{feature_5}}</span>
    <span class="pill">{{feature_6}}</span>
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
