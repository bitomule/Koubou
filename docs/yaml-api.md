# 🎯 Koubou v0.6.0 YAML API Reference

Complete reference for Koubou's YAML configuration format with all options, defaults, and examples. This documentation covers the v0.6.0 API with multi-language localization, live editing support and dictionary-based screenshot configuration.

## Table of Contents

- [Project Configuration](#project-configuration)
- [Localization Configuration](#localization-configuration)
- [Device Configuration](#device-configuration)
- [Default Settings](#default-settings)
- [Screenshot Configuration](#screenshot-configuration)
- [Content Items](#content-items)
- [Background Configuration](#background-configuration)
- [Live Editing Features](#live-editing-features)
- [Complete Examples](#complete-examples)
- [Breaking Changes in v0.5.0](#breaking-changes-in-v050)

## Project Configuration

The root-level configuration for your Koubou project.

```yaml
project:
  name: string               # Project name/identifier (required)
  output_dir: string         # Output directory path (default: "output")
```

### Defaults
- `output_dir`: `"output"`

### Example
```yaml
project:
  name: "My Beautiful App Screenshots"
  output_dir: "Screenshots/Generated"
```

---

## Localization Configuration

**New in v0.6.0**: Multi-language localization support using xcstrings format familiar to iOS developers.

```yaml
localization:
  base_language: string          # Base/source language code (required)
  languages: [string, ...]       # List of target language codes including base_language (required)
  xcstrings_path: string?        # Path to xcstrings localization file (default: "Localizable.xcstrings")
```

### Defaults
- `xcstrings_path`: `"Localizable.xcstrings"`

### Example
```yaml
localization:
  base_language: "en"
  languages: ["en", "es", "ja", "fr", "de"]
  xcstrings_path: "AppScreenshots.xcstrings"
```

### How Localization Works

1. **Extract Text**: Koubou automatically finds all text content in your screenshots
2. **Generate xcstrings**: Creates or updates your xcstrings file with text as localization keys
3. **iOS-Familiar Format**: Edit translations in Xcode using the xcstrings editor you already know
4. **Auto-Generate Screenshots**: Run `kou generate config.yaml` to create screenshots for all languages

### Output Structure

With localization enabled, screenshots are generated in language-specific directories:

```
Screenshots/Generated/
├── en/iPhone_15_Pro_Portrait/welcome_screen.png
├── es/iPhone_15_Pro_Portrait/welcome_screen.png  
├── ja/iPhone_15_Pro_Portrait/welcome_screen.png
├── fr/iPhone_15_Pro_Portrait/welcome_screen.png
└── de/iPhone_15_Pro_Portrait/welcome_screen.png
```

### Live Editing with Localization

Live mode watches both your YAML config AND the xcstrings file:

```bash
kou live config.yaml  # Watches YAML config AND xcstrings file
```

- **Edit xcstrings in Xcode** → All language screenshots regenerate automatically
- **Update YAML config** → xcstrings file updates with new text keys
- **Change assets** → All localized versions update

### Validation Rules

- Base language cannot be empty
- Languages list cannot be empty  
- Base language must be included in languages list
- Duplicate languages are automatically removed
- Language codes are automatically trimmed of whitespace

### Key Benefits

- **🍎 iOS Developer Friendly**: Uses xcstrings format from Xcode
- **🔑 Natural Keys**: Your actual text becomes the localization key
- **🌍 Complete Localization**: Supports all xcstrings features
- **🚀 Zero Extra Work**: Add localization block and run the same commands
- **🔄 Live Updates**: Edit translations and see all screenshots update instantly

---

## Device Configuration

Target devices for screenshot generation. Each screenshot will be generated for all specified devices.

```yaml
devices: [string, ...]       # Array of device frame names
```

### Example
```yaml
devices:
  - "iPhone 15 Pro Portrait"
  - "iPad Air 13\" - M2 - Space Gray - Portrait"
  - "MacBook Pro 2021 16"
```

### Available Device Frames

Popular device frame options include:

#### iPhone Frames
- `"iPhone 16 Pro Portrait"`, `"iPhone 16 Pro Landscape"`
- `"iPhone 15 Pro Max Portrait"`, `"iPhone 15 Pro Max Landscape"`
- `"iPhone 14 Pro Portrait"`, `"iPhone 14 Pro Landscape"`

#### iPad Frames  
- `"iPad Air 11\" - M2 - Space Gray - Portrait"`
- `"iPad Pro 13 - M4 - Silver - Landscape"`

#### Mac Frames
- `"MacBook Pro 2021 14"`, `"MacBook Pro 2021 16"`
- `"MacBook Air 2022"`, `"iMac 24\" - Silver"`

---

## Default Settings

Settings applied to all screenshots unless overridden at the screenshot level.

```yaml
defaults:
  background: object?        # Default background configuration
  # Future: Additional default settings
```

### Example
```yaml
defaults:
  background:
    type: linear
    colors: ["#E8F0FE", "#F8FBFF"]
    direction: 180
```

---

## Screenshot Configuration

**Breaking Change in v0.5.0**: Screenshots are now organized as a dictionary with IDs as keys, not an array.

```yaml
screenshots:
  screenshot_id:             # Unique identifier for this screenshot
    content: [object, ...]   # Array of content items (text, images)
    background: object?      # Override default background (optional)
```

### Example
```yaml
screenshots:
  welcome_screen:            # Screenshot ID
    content:
      - type: "text"
        content: "Welcome!"
        position: ["50%", "20%"]
        size: 48
        color: "#8E4EC6"
      - type: "image" 
        asset: "screenshots/welcome.png"
        position: ["50%", "60%"]
        frame: true
  
  features_overview:         # Another screenshot ID
    content:
      - type: "text"
        content: "Amazing Features"
        position: ["50%", "15%"]
```

---

## Content Items

Content items define the visual elements within each screenshot.

### Text Content Item

```yaml
- type: "text"
  content: string            # Text to display (required)
  position: [string, string] # Position as ["50%", "20%"] or ["100px", "50px"] (required)
  size: int?                 # Font size in pixels (default: 24)

  # Auto-sizing (optional — all three required to enable):
  min_size: int?             # Minimum font size floor for auto-sizing
  max_width: int?            # Maximum width for text wrapping (pixels)
  max_height: int?           # Maximum height budget for the text block (pixels)
  max_lines: int?            # Maximum number of lines (truncates with "..." if exceeded)

  # Fill Options (choose exactly one):
  color: string?             # Solid color (hex format, e.g., "#000000")
  # OR
  gradient: object?          # Text gradient (see Gradient Configuration below)

  weight: string?            # "normal" or "bold" (default: "normal")
  font_family: string?       # Font family name (default: "Arial")
  alignment: string?         # "left", "center", "right" (default: "center")

  # Stroke Options (optional):
  stroke_width: int?         # Stroke width in pixels
  stroke_color: string?      # Solid stroke color (hex format)
  # OR
  stroke_gradient: object?   # Gradient stroke (same structure as gradient)
```

#### Text Gradient Configuration

```yaml
gradient:
  type: "linear" | "radial" | "conic"  # Gradient type (required)
  colors: [string, ...]      # Hex colors array (minimum 2) (required)
  positions: [float, ...]?   # Color stops 0.0-1.0 (optional)
  
  # Linear gradient options:
  direction: float?          # Angle in degrees (default: 0)
  
  # Radial gradient options:
  center: [string, string]?  # Center point ["50%", "50%"] (default: ["50%", "50%"])
  radius: string?            # Radius "50%" or "100px" (default: "50%")
  
  # Conic gradient options:
  center: [string, string]?  # Center point (default: ["50%", "50%"])
  start_angle: float?        # Starting angle in degrees (default: 0)
```

#### Text Auto-Sizing

When `min_size`, `max_width`, and `max_height` are all set, Koubou automatically finds the largest font size (between `size` and `min_size`) where the wrapped text block fits within the pixel height budget. This is useful for multi-language screenshots where translation lengths vary — each language independently gets the largest font that fits.

```yaml
- type: "text"
  content: "Stay close to God all day"
  position: ["50%", "14%"]
  size: 120              # Maximum / starting font size
  min_size: 72           # Floor — never shrink below this
  max_width: 1161        # Text wrapping width in pixels
  max_height: 400        # Height budget — text block must fit in this many pixels
  color: "#4A2E2E"
  weight: "bold"
  font_family: "assets/MyFont.ttf"
```

**How it works:**
1. Start at `size` (e.g., 120px)
2. Wrap text at `max_width` and compute total height: `lines * font_size * line_height`
3. If total height <= `max_height`, use this size
4. Otherwise, try `size - 2` and repeat
5. If nothing fits by `min_size`, use `min_size` anyway

**When `min_size` is absent**, behavior is unchanged — text renders at exactly `size` with no auto-sizing. `max_width` and `max_lines` still work independently for wrapping and truncation.

### Image Content Item

```yaml
- type: "image"
  asset: string              # Path to image file (required)
  position: [string, string] # Position as ["50%", "60%"] or ["200px", "300px"] (required)
  scale: float?              # Scale factor (default: 1.0)
  frame: bool?               # Apply device frame around image (default: false)
```

### Highlight Content Item

Draw annotation shapes to highlight areas of the screenshot. Supports spotlight dimming, background blur, and drop shadows. All shapes are anti-aliased via 2x supersampling. Rendered after images and before text.

```yaml
- type: "highlight"
  shape: "circle" | "rounded_rect" | "rect"  # Shape type (required)
  position: [string, string]   # Center position as ["50%", "50%"] (required)
  dimensions: [string, string]? # Width, height as ["20%", "15%"] or ["200", "150"]
  border_color: string?        # Border color in hex (e.g., "#FF3B30")
  border_width: int?           # Border width in pixels (default: 3)
  fill_color: string?          # Fill color in hex, supports alpha (e.g., "#FF3B3020")
  corner_radius: int?          # Corner radius for rounded_rect (default: 16)

  # Shadow
  shadow: bool?                # Enable drop shadow (default: false)
  shadow_color: string?        # Shadow color with alpha (default: "#00000040")
  shadow_blur: int?            # Gaussian blur radius (default: 15)
  shadow_offset: [string, string]? # X, Y offset in px (default: ["0", "6"])

  # Spotlight (dims everything outside the highlight)
  spotlight: bool?             # Enable spotlight mode (default: false)
  spotlight_color: string?     # Overlay color (default: "#000000")
  spotlight_opacity: float?    # Overlay opacity 0.0-1.0 (default: 0.5)

  # Background Blur (blurs everything outside the highlight)
  blur_background: bool?       # Enable background blur (default: false)
  blur_radius: int?            # Gaussian blur radius (default: 20)
```

#### Examples
```yaml
# Basic highlight
- type: "highlight"
  shape: "circle"
  position: ["65%", "45%"]
  dimensions: ["20%", "15%"]
  border_color: "#FF3B30"
  border_width: 4
  fill_color: "#FF3B3020"

# Spotlight mode - dims everything except the highlighted area
- type: "highlight"
  shape: "rounded_rect"
  position: ["50%", "45%"]
  dimensions: ["60%", "15%"]
  border_color: "#FF9500"
  border_width: 4
  corner_radius: 20
  spotlight: true
  spotlight_opacity: 0.6

# Background blur - blurs everything outside the highlight
- type: "highlight"
  shape: "circle"
  position: ["50%", "50%"]
  dimensions: ["40%", "20%"]
  border_color: "#007AFF"
  border_width: 4
  blur_background: true
  blur_radius: 25
```

### Zoom Content Item

Magnified callout bubble that crops a source region and displays it enlarged at another position. Features source region indicators, advanced connector styles, drop shadows, and anti-aliased rendering. Rendered after highlights and before text.

```yaml
- type: "zoom"
  source_position: [string, string]   # Center of area to magnify (required)
  source_size: [string, string]       # Crop region size (required)
  display_position: [string, string]? # Where magnified view appears (default: position)
  display_size: [string, string]?     # Size of magnified bubble (required unless zoom_level set)
  zoom_level: float?                  # Auto-calculate display_size = source_size * zoom_level
  shape: "circle" | "rounded_rect"?   # Bubble shape (default: "circle")
  border_color: string?               # Border color in hex
  border_width: int?                  # Border width in pixels (default: 3)
  corner_radius: int?                 # For rounded_rect (default: 16)

  # Shadow
  shadow: bool?                # Enable drop shadow (default: false)
  shadow_color: string?        # Shadow color with alpha (default: "#00000040")
  shadow_blur: int?            # Gaussian blur radius (default: 15)
  shadow_offset: [string, string]? # X, Y offset in px (default: ["0", "6"])

  # Source Region Indicator
  source_indicator: bool?      # Show outline on source region (default: true)
  source_indicator_style: string? # "border" | "dashed" | "fill" (default: "border")

  # Connector
  connector: bool?             # Draw connector from source to display (default: false)
  connector_style: string?     # "straight" | "curved" | "facing" (default: "straight")
  connector_color: string?     # Line color (defaults to border_color)
  connector_width: int?        # Line width in pixels (default: 2)
  connector_fill: string?      # Semi-transparent fill between facing connector lines
```

#### Connector Styles
- **`straight`**: Direct center-to-center line (default)
- **`curved`**: Bezier curve bowing away from the direct path
- **`facing`**: Two-line funnel from nearest edges of source to nearest edges of display, with optional fill

#### Examples
```yaml
# Basic zoom with source indicator
- type: "zoom"
  source_position: ["65%", "45%"]
  source_size: ["15%", "10%"]
  display_position: ["25%", "20%"]
  display_size: ["35%", "30%"]
  shape: "circle"
  border_color: "#007AFF"
  border_width: 3
  source_indicator: true

# Professional zoom with shadow and facing connector
- type: "zoom"
  source_position: ["72%", "38%"]
  source_size: ["22%", "5%"]
  display_position: ["30%", "80%"]
  display_size: ["45%", "12%"]
  shape: "rounded_rect"
  border_color: "#007AFF"
  border_width: 5
  corner_radius: 24
  shadow: true
  connector: true
  connector_style: "facing"
  connector_color: "#007AFF80"
  connector_fill: "#007AFF10"

# Zoom level shorthand (auto-calculates display_size)
- type: "zoom"
  source_position: ["50%", "45%"]
  source_size: ["15%", "8%"]
  display_position: ["50%", "82%"]
  zoom_level: 2.5
  shape: "circle"
  border_color: "#FF3B30"
  connector: true
  connector_style: "curved"
```

### Position Format

Positions can be specified as:
- **Percentages**: `["50%", "20%"]` - Relative to canvas size
- **Pixels**: `["100px", "50px"]` - Absolute positioning
- **Mixed**: `["50%", "100px"]` - Percentage width, pixel height

### Render Layer Order

Content items are rendered in this order regardless of their position in the YAML:
1. **Background** - Gradient or solid color
2. **Images** - Source screenshots with optional device frames
3. **Highlights** - Annotation shapes (circle, rect, rounded_rect)
4. **Zoom callouts** - Magnified callout bubbles with connectors
5. **Text** - Text overlays on top of everything

---

## Background Configuration

Professional background rendering with gradients and solid colors.

```yaml
background:
  type: "solid" | "linear" | "radial" | "conic"  # Background type (required)
  colors: [string, ...]      # Array of hex colors (required)
  
  # Linear gradient options:
  direction: float?          # Direction in degrees (default: 0)
  
  # Radial/Conic gradient options:
  center: [string, string]?  # Center point ["x%", "y%"] (default: ["50%", "50%"])
```

### Background Types

#### Solid Background
```yaml
background:
  type: "solid"
  colors: ["#667eea"]        # Single color required
```

#### Linear Gradient
```yaml
background:
  type: "linear"
  colors: ["#667eea", "#764ba2"]  # 2+ colors required
  direction: 45              # Degrees (default: 0)
```

#### Radial Gradient
```yaml
background:
  type: "radial"
  colors: ["#ff9a9e", "#fecfef"]  # 2+ colors required
  center: ["50%", "50%"]     # Center point (default: ["50%", "50%"])
```

#### Conic Gradient
```yaml
background:
  type: "conic"
  colors: ["#667eea", "#764ba2", "#f093fb"]  # 2+ colors required
  center: ["50%", "50%"]     # Center point (default: ["50%", "50%"])
```

### Color Format
Colors must be in hex format: `#RRGGBB` or `#RRGGBBAA`

---

## Live Editing Features

**New in v0.5.0**: Live editing automatically regenerates screenshots when files change.

### Usage
```bash
# Start live editing mode
kou live my-screenshots.yaml

# Prepare HTML rendering before live mode if the project uses templates
kou live my-screenshots.yaml --setup-html

# With custom debounce delay  
kou live my-screenshots.yaml --debounce 1.0

# With verbose logging
kou live my-screenshots.yaml --verbose
```

### How It Works

1. **File Monitoring**: Watches your YAML config file and all referenced assets
2. **Dependency Analysis**: Automatically detects which assets each screenshot uses
3. **Smart Regeneration**: Only regenerates affected screenshots when changes occur
4. **Debounced Updates**: Prevents excessive regeneration during rapid edits

### HTML Live Preview

Live mode also starts a local browser dashboard on `127.0.0.1` and opens it automatically when possible.

- The dashboard shows screenshots in YAML order
- HTML slides render as live HTML inside iframes
- Standard Koubou slides render as regenerated PNG previews
- Hot reload updates only the changed slides
- The dashboard previews the base language only; localized outputs still regenerate on disk

HTML slides use the same staged template, sibling files, and generated assets as the final Playwright export path, while standard slides reuse the latest PNGs generated by the normal Koubou pipeline.

### Live Editing Workflow

```yaml
# my-app.yaml
project:
  name: "My App"
  output_dir: "Screenshots/Live"

screenshots:
  main_screen:
    content:
      - type: "image"
        asset: "assets/main-screen.png"    # Monitored for changes
        position: ["50%", "60%"]
        frame: true
      - type: "text"
        content: "Revolutionary App"        # Text changes trigger regeneration
        position: ["50%", "15%"]
        size: 48
        color: "#8E4EC6"
```

**Live editing monitors:**
- Changes to the YAML configuration file
- Changes to referenced asset files (images)
- Changes to xcstrings localization files (v0.6.0+)
- Supports both absolute and relative asset paths

### Platform Support
- **Live Editing**: macOS and Linux only
- **Standard Generation**: macOS, Linux, and Windows

---

## Complete Examples

### Minimal Configuration
```yaml
project:
  name: "Simple App"
  output_dir: "output"

devices:
  - "iPhone 15 Pro Portrait"

screenshots:
  launch_screen:
    content:
      - type: "image"
        asset: "app-screenshot.png"
        position: ["50%", "50%"]
```

### Professional App Store Screenshot
```yaml
project:
  name: "Professional App Screenshots"
  output_dir: "AppStore"

devices:
  - "iPhone 16 Pro Portrait"
  - "iPad Air 13\" - M2 - Space Gray - Portrait"

defaults:
  background:
    type: linear
    colors: ["#667eea", "#764ba2"]
    direction: 135

screenshots:
  main_feature:
    content:
      - type: "text"
        content: "Revolutionary App"
        position: ["50%", "15%"]
        size: 56
        weight: "bold"
        color: "#ffffff"
        stroke_width: 2
        stroke_color: "#000000"
      
      - type: "text"
        content: "Experience the future of mobile productivity with award-winning design."
        position: ["50%", "25%"]
        size: 24
        color: "#ffffff"
        alignment: "center"
      
      - type: "image"
        asset: "screenshots/main.png"
        position: ["50%", "65%"]
        scale: 0.8
        frame: true

  gradient_showcase:
    background:
      type: radial
      colors: ["#ff9a9e", "#fecfef", "#feca57"]
      center: ["30%", "30%"]
    content:
      - type: "text"
        content: "🌈 Gradient Magic"
        position: ["50%", "15%"]
        size: 48
        gradient:
          type: linear
          colors: ["#FF6B6B", "#4ECDC4", "#45B7D1"]
          direction: 45
        weight: "bold"
      
      - type: "text"
        content: "Beautiful gradients for stunning text"
        position: ["50%", "25%"]
        size: 24
        gradient:
          type: radial
          colors: ["#667eea", "#764ba2"]
          center: ["50%", "50%"]
          radius: "70%"
```

### Multi-Device Campaign
```yaml
project:
  name: "Cross-Platform Campaign"
  output_dir: "Campaign"

devices:
  - "iPhone 16 Pro Portrait"
  - "iPhone 16 Pro Landscape"  
  - "iPad Air 13\" - M2 - Space Gray - Portrait"
  - "MacBook Pro 2021 16"

defaults:
  background:
    type: linear
    colors: ["#667eea", "#764ba2"]

screenshots:
  phone_portrait:
    content:
      - type: "text"
        content: "Mobile First"
        position: ["50%", "15%"]
        size: 42
        color: "#ffffff"
        weight: "bold"
      - type: "image"
        asset: "screenshots/phone.png"
        position: ["50%", "60%"]
        frame: true

  phone_landscape:
    content:
      - type: "text"
        content: "Landscape Ready"
        position: ["50%", "15%"]
        size: 42
        color: "#ffffff" 
        weight: "bold"
      - type: "image"
        asset: "screenshots/phone-landscape.png"
        position: ["50%", "60%"]
        frame: true

  tablet:
    content:
      - type: "text"
        content: "Built for iPad"
        position: ["50%", "15%"]
        size: 48
        color: "#ffffff"
        weight: "bold"
      - type: "image"
        asset: "screenshots/tablet.png"
        position: ["50%", "65%"]
        frame: true

  desktop:
    content:
      - type: "text"
        content: "Desktop Power"
        position: ["50%", "15%"]
        size: 54
        color: "#ffffff"
        weight: "bold"
      - type: "image"
        asset: "screenshots/desktop.png" 
        position: ["50%", "65%"]
        scale: 0.9
        frame: true
```

### Multi-Language App Store Campaign

**New in v0.6.0**: Generate localized screenshots for international App Store submissions.

```yaml
project:
  name: "Multi-Language App Screenshots"
  output_dir: "Screenshots/Generated"

devices:
  - "iPhone 15 Pro Portrait"
  - "iPad Air 13\" - M2 - Space Gray - Portrait"

defaults:
  background:
    type: linear
    colors: ["#E8F0FE", "#F8FBFF"]
    direction: 180

localization:
  base_language: "en"
  languages: ["en", "es", "ja", "fr", "de"]
  xcstrings_path: "AppScreenshots.xcstrings"

screenshots:
  welcome_screen:
    content:
      - type: "text"
        content: "Welcome to Amazing App"
        position: ["50%", "15%"]
        size: 48
        color: "#8E4EC6"
        weight: "bold"
      - type: "text"
        content: "Transform your workflow today"
        position: ["50%", "25%"]
        size: 24
        color: "#1A73E8"
      - type: "image"
        asset: "screenshots/home.png"
        position: ["50%", "60%"]
        scale: 0.6
        frame: true

  features_screen:
    content:
      - type: "text"
        content: "✨ Amazing Features"
        position: ["50%", "10%"]
        size: 42
        color: "#8E4EC6"
        weight: "bold"
      - type: "text"
        content: "Discover what makes us different"
        position: ["50%", "20%"]
        size: 20
      - type: "image"
        asset: "screenshots/features.png"
        position: ["50%", "65%"]
        scale: 0.5
        frame: true
```

**Output generates 20 screenshots** (2 screenshots × 5 languages × 2 devices):
```
Screenshots/Generated/
├── en/
│   ├── iPhone_15_Pro_Portrait/
│   │   ├── welcome_screen.png
│   │   └── features_screen.png
│   └── iPad_Air_13_M2_Space_Gray_Portrait/
│       ├── welcome_screen.png
│       └── features_screen.png
├── es/ [same structure with Spanish text]
├── ja/ [same structure with Japanese text]  
├── fr/ [same structure with French text]
└── de/ [same structure with German text]
```

---

## Breaking Changes in v0.5.0

### Screenshot Configuration Format

**v0.4.x and earlier** (Array format):
```yaml
screenshots:
  - name: "welcome_screen"
    content: [...]
  - name: "features_screen" 
    content: [...]
```

**v0.5.0+** (Dictionary format):
```yaml
screenshots:
  welcome_screen:           # ID as key
    content: [...]
  features_screen:          # ID as key
    content: [...]
```

### Migration Guide

1. **Remove `name` fields** from screenshot definitions
2. **Convert array to dictionary** using the `name` values as keys
3. **Update any references** to screenshot names in scripts/tools
4. **Test with `kou generate`** to ensure compatibility

### Benefits of New Format

- **Live Editing Support**: Enables selective regeneration by screenshot ID
- **Better Performance**: Faster lookups and change detection
- **Cleaner Configuration**: No duplicate `name` fields
- **Future Features**: Enables advanced features like screenshot dependencies

---

## Best Practices

### Color Harmony
- Use professional color palettes from tools like Coolors.co
- Ensure sufficient contrast for text readability (WCAG AA: 4.5:1 minimum)
- Consider App Store guidelines for screenshot aesthetics

### Typography
- Use system fonts for compatibility across platforms
- Maintain consistent font sizes across screenshots in a set
- Apply stroke to text over complex backgrounds for readability
- Test gradient text on various backgrounds

### Device Frame Selection
- Choose frames that match your target audience and app category
- Use consistent device families across a marketing campaign
- Consider the latest device models for modern appeal
- Test frame positioning - frames can extend beyond canvas bounds

### Asset Organization
- Use relative paths for better project portability
- Organize assets in logical directory structures
- Use consistent naming conventions for screenshots
- Consider asset resolution for crisp output

### Live Editing Workflow
- Start with `kou live config.yaml` for iterative design
- Use `--verbose` flag to understand what's being regenerated
- Adjust `--debounce` for faster/slower response to changes
- Keep asset files organized to avoid path issues

### Composition
- Follow the rule of thirds for text placement
- Leave sufficient breathing room around text elements
- Balance visual weight across the composition
- Consider how the content will appear on different device sizes

---

*This documentation covers all available options in Koubou's v0.6.0 YAML API with multi-language localization and live editing support. For more examples and tutorials, visit the project repository.*
