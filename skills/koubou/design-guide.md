# Design Guide

## Narrative Arc Framework

Plan slides as a story, not a feature list.

| # | Role | What to show | Notes |
|---|------|-------------|-------|
| 1 | **Hero/Hook** | Main value proposition. "What does this app solve?" | App icon + tagline. 80% of users only see this one |
| 2 | **Differentiator** | Star feature. What sets it apart from competitors | The unique selling point |
| 3 | **Ecosystem** | Widgets, extensions, watch, integrations | Breadth of the product |
| 4+ | **Core Features** | One feature per slide, prioritized by importance | One focus per screenshot |
| Second-to-last | **Trust Signal** | Brand identity: "made for people who [X]" | Emotional connection |
| Last | **More Features** | Extra features in pill/list format, "coming soon" | Expanded closing |

**Critical**: Only the first 3 slides are visible in App Store search results without tapping into the listing. They must tell a complete story on their own.

## Copywriting Rules

### Iron rules

- **One idea per headline** — never join concepts with "and"/"y"
- **Simple vocabulary** — prefer 1-2 syllable words
- **3-5 words per line** — readable in App Store thumbnail
- **Arm test**: if you can't read it at arm's length, the text is too small
- **Intentional line breaks** — control wraps with `<br>` when needed

### Three approaches (choose per slide)

1. **Paint a moment** — "Check your coffee without opening the app"
2. **Declare an outcome** — "A home for every coffee you buy"
3. **Kill a pain** — "Never waste a great bag of coffee"

### What NOT to write

- Headlines that are feature lists
- Compound ideas joined with "and"
- Buzzwords without substance ("AI-powered", "revolutionary")
- More than 2 lines of text per screenshot

## CSS Rules for Templates

### Typography

- **Headline**: 100-140px font-size
- **Subtitle**: 50-65px font-size
- **Font stack**: `-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", sans-serif`
- **Font weight**: 700-800 for headlines, 400-500 for subtitles
- **Color**: White text on dark backgrounds. Never gray on gray

### Backgrounds

- Use CSS gradients. Avoid flat solids
- Vary gradients between slides (direction, colors, type)
- Derive gradient colors from the app's brand palette
- Dark backgrounds with light text perform best in App Store

### Device placement

- Width: 70-80% of viewport width
- The `{{asset_name}}` in templates receives the screenshot already composited inside the device frame — just use `<img>` to place it
- Always leave margin between device and edges (minimum 3-5% of viewport)

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

## What NOT to do

- Text smaller than 50px (invisible in thumbnail)
- Same layout on all screenshots
- More than 2 lines of text per screenshot
- Device touching the edge without margin
- Colors outside the brand palette
- Showing features that don't exist in the app
- Flat white or black backgrounds without gradient
- Stacking multiple devices on one slide (unless deliberately showing ecosystem)

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
    background: linear-gradient(180deg, {{bg_start}} 0%, {{bg_end}} 100%);
  }
  .text-area {
    padding-top: 12%;
    text-align: center;
    flex-shrink: 0;
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
    margin-top: auto;
    padding-bottom: 0;
    display: flex;
    justify-content: center;
  }
  .device-area img {
    width: 75%;
    height: auto;
    object-fit: contain;
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
    background: linear-gradient(160deg, {{bg_start}} 0%, {{bg_end}} 100%);
  }
  .device-area {
    padding-top: 5%;
    display: flex;
    justify-content: center;
  }
  .device-area img {
    width: 72%;
    height: auto;
    object-fit: contain;
  }
  .text-area {
    margin-top: auto;
    margin-bottom: 6%;
    text-align: center;
    padding: 0 8%;
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
    width: 55%;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 5%;
  }
  .device-area img {
    width: 90%;
    height: auto;
    object-fit: contain;
  }
  .text-area {
    width: 45%;
    padding-right: 6%;
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
