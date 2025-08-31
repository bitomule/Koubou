# 🎯 Koubou v0.5.0 YAML API Reference

Complete reference for Koubou's YAML configuration format with all options, defaults, and examples. This documentation covers the v0.5.0 API with live editing support and dictionary-based screenshot configuration.

## Table of Contents

- [Project Configuration](#project-configuration)
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
  
  # Fill Options (choose exactly one):
  color: string?             # Solid color (hex format, e.g., "#000000")
  # OR
  gradient: object?          # Text gradient (see Gradient Configuration below)
  
  weight: string?            # "normal" or "bold" (default: "normal")
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

### Image Content Item

```yaml
- type: "image"
  asset: string              # Path to image file (required)
  position: [string, string] # Position as ["50%", "60%"] or ["200px", "300px"] (required)
  scale: float?              # Scale factor (default: 1.0)
  frame: bool?               # Apply device frame around image (default: false)
```

### Position Format

Positions can be specified as:
- **Percentages**: `["50%", "20%"]` - Relative to canvas size
- **Pixels**: `["100px", "50px"]` - Absolute positioning
- **Mixed**: `["50%", "100px"]` - Percentage width, pixel height

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

*This documentation covers all available options in Koubou's v0.5.0 YAML API with live editing support. For more examples and tutorials, visit the project repository.*