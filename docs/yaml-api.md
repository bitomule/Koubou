# 🎯 Koubou YAML API Reference

Complete reference for Koubou's YAML configuration format with all options, defaults, and examples.

## Table of Contents

- [Project Configuration](#project-configuration)
- [Screenshot Configuration](#screenshot-configuration)
- [Background Configuration](#background-configuration)
- [Text Overlays](#text-overlays)
- [Device Frames](#device-frames)
- [Complete Examples](#complete-examples)

## Project Configuration

The root level configuration for your Koubou project.

```yaml
project_name: string          # Project name/identifier
output_directory: string      # Output directory path
```

### Defaults
- `project_name`: `"Koubou Project"`
- `output_directory`: `"output"`

### Example
```yaml
project_name: "My Beautiful App Screenshots"
output_directory: "app-store-assets"
```

---

## Screenshot Configuration

Individual screenshot definitions within the `screenshots` array.

```yaml
screenshots:
  - name: string              # Screenshot identifier (required)
    source_image: string      # Path to source image (required)
    output_size: [int, int]   # Output dimensions [width, height] (required)
    device_frame: string?     # Device frame name (optional)
    output_path: string?      # Custom output path (optional)
    background: object?       # Background configuration (optional)
    text_overlays: array?     # Text overlay definitions (optional)
    image_position: [string, string]?  # Image position ["x%", "y%"] (optional)
    image_scale: float?       # Image scale factor (optional)
    image_frame: boolean?     # Apply frame to positioned image (optional)
```

### Defaults
- `device_frame`: `null` (no frame)
- `output_path`: Generated from `name` and `output_directory`
- `background`: `null` (transparent/white)
- `text_overlays`: `[]` (empty array)
- `image_position`: `null` (centered)
- `image_scale`: `null` (auto-fit)
- `image_frame`: `false`

### Example
```yaml
screenshots:
  - name: "Home Screen"
    source_image: "screenshots/home.png"
    output_size: [1320, 2868]
    device_frame: "iPhone 16 Pro - Black Titanium - Portrait"
    background:
      type: "linear"
      colors: ["#667eea", "#764ba2"]
```

---

## Background Configuration

Professional background rendering with gradients and solid colors.

```yaml
background:
  type: "solid" | "linear" | "radial" | "conic"  # Background type (required)
  colors: [string, ...]      # Array of hex colors (required)
  direction: float?          # Direction in degrees (optional)
  center: [string, string]?  # Center point ["x%", "y%"] (optional)
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

### Defaults
- `direction`: `0` (degrees, for linear gradients)
- `center`: `["50%", "50%"]` (for radial and conic gradients)

### Color Format
Colors must be in hex format: `#RRGGBB` or `#RRGGBBAA`

---

## Text Overlays

Rich typography system with advanced text rendering capabilities.

```yaml
text_overlays:
  - content: string          # Text content (required)
    position: [int, int]     # X, Y position in pixels (required)
    font_size: int           # Font size in pixels
    font_family: string      # Font family name
    font_weight: string      # Font weight
    color: string            # Text color in hex
    alignment: string        # Text alignment
    anchor: string           # Anchor point for positioning
    max_width: int?          # Maximum width for text wrapping
    max_lines: int?          # Maximum number of lines
    line_height: float       # Line height multiplier
    stroke_width: int?       # Text outline width
    stroke_color: string?    # Text outline color
```

### Defaults
- `font_size`: `24`
- `font_family`: `"Arial"`
- `font_weight`: `"normal"`
- `color`: `"#000000"`
- `alignment`: `"center"`
- `anchor`: `"center"`
- `max_width`: `null` (no wrapping)
- `max_lines`: `null` (no limit)
- `line_height`: `1.2`
- `stroke_width`: `null` (no stroke)
- `stroke_color`: `null`

### Font Weights
- `"normal"` - Regular weight
- `"bold"` - Bold weight

### Text Alignment
- `"left"` - Left aligned
- `"center"` - Center aligned  
- `"right"` - Right aligned

### Anchor Points
Determines how the position relates to the text:
- `"top-left"`, `"top-center"`, `"top-right"`
- `"center-left"`, `"center"`, `"center-right"`
- `"bottom-left"`, `"bottom-center"`, `"bottom-right"`

### Examples

#### Basic Text
```yaml
text_overlays:
  - content: "Beautiful App"
    position: [100, 200]
    font_size: 48
    color: "#ffffff"
```

#### Advanced Text with Stroke
```yaml
text_overlays:
  - content: "Professional Quality"
    position: [640, 100]
    font_size: 52
    font_weight: "bold"
    color: "#ffffff"
    alignment: "center"
    anchor: "center"
    max_width: 800
    line_height: 1.3
    stroke_width: 2
    stroke_color: "#000000"
```

#### Multi-line Text Block
```yaml
text_overlays:
  - content: "Create stunning screenshots with professional quality and artisan attention to detail."
    position: [50, 300]
    font_size: 24
    color: "#333333"
    alignment: "left"
    max_width: 600
    max_lines: 3
    line_height: 1.4
```

---

## Device Frames

Koubou includes 100+ professionally crafted device frames.

### Frame Categories

#### iPhone Frames
- `iPhone 16 Pro - Black Titanium - Portrait`
- `iPhone 16 Pro - Desert Titanium - Portrait`
- `iPhone 16 Pro - Natural Titanium - Portrait`
- `iPhone 16 Pro - White Titanium - Portrait`
- `iPhone 16 - Black - Portrait`
- `iPhone 16 - Pink - Portrait`
- `iPhone 16 - Teal - Portrait`
- `iPhone 16 - Ultramarine - Portrait`
- `iPhone 16 - White - Portrait`
- `iPhone 15 Pro Max - Black Titanium - Portrait`
- And many more...

#### iPad Frames
- `iPad Air 11" - M2 - Space Gray - Portrait`
- `iPad Air 11" - M2 - Space Gray - Landscape`
- `iPad Air 13" - M2 - Blue - Portrait`
- `iPad Air 13" - M2 - Blue - Landscape`
- `iPad Pro 11 - M4 - Silver - Portrait`
- `iPad Pro 13 - M4 - Space Gray - Landscape`
- And many more...

#### Mac Frames
- `MacBook Pro 2021 14`
- `MacBook Pro 2021 16`
- `MacBook Air 2022`
- `iMac 24" - Silver`
- And more...

#### Apple Watch Frames
- `Watch Series 7 45 Midnight`
- `Watch Series 7 45 Starlight`
- `Watch Ultra 2022`
- And more...

### Finding Available Frames
Use the CLI to list all available frames:
```bash
kou list-frames
```

---

## Complete Examples

### Minimal Configuration
```yaml
project_name: "Simple App"
output_directory: "output"

screenshots:
  - name: "Launch Screen"
    source_image: "app-screenshot.png"
    output_size: [1320, 2868]
```

### Professional App Store Screenshot
```yaml
project_name: "Professional App Screenshots"
output_directory: "app-store"

screenshots:
  - name: "iPhone Main Feature"
    source_image: "screenshots/main.png"
    device_frame: "iPhone 16 Pro - Black Titanium - Portrait"
    output_size: [1320, 2868]
    
    background:
      type: "linear"
      colors: ["#667eea", "#764ba2"]
      direction: 135
    
    text_overlays:
      - content: "Revolutionary App"
        position: [660, 150]
        font_size: 56
        font_weight: "bold"
        color: "#ffffff"
        alignment: "center"
        anchor: "center"
        stroke_width: 2
        stroke_color: "#000000"
      
      - content: "Experience the future of mobile productivity with our award-winning design and lightning-fast performance."
        position: [660, 250]
        font_size: 24
        color: "#ffffff"
        alignment: "center"
        anchor: "center"
        max_width: 1000
        line_height: 1.4

  - name: "iPad Landscape Showcase"
    source_image: "screenshots/ipad-features.png" 
    device_frame: "iPad Air 13\" - M2 - Space Gray - Landscape"
    output_size: [2732, 2048]
    
    background:
      type: "radial"
      colors: ["#ff9a9e", "#fecfef", "#feca57"]
      center: ["30%", "30%"]
    
    text_overlays:
      - content: "Built for iPad"
        position: [1366, 200]
        font_size: 48
        font_weight: "bold"
        color: "#2c2c54"
        alignment: "center"
        anchor: "center"
```

### Multi-Device Campaign
```yaml
project_name: "Cross-Platform Campaign"
output_directory: "campaign-assets"

screenshots:
  - name: "iPhone Portrait"
    source_image: "screenshots/phone.png"
    device_frame: "iPhone 16 Pro - Natural Titanium - Portrait"
    output_size: [1320, 2868]
    background:
      type: "linear"
      colors: ["#667eea", "#764ba2"]

  - name: "iPhone Landscape"  
    source_image: "screenshots/phone-landscape.png"
    device_frame: "iPhone 16 Pro - Natural Titanium - Landscape"
    output_size: [2868, 1320]
    background:
      type: "linear"
      colors: ["#667eea", "#764ba2"]

  - name: "iPad Portrait"
    source_image: "screenshots/tablet.png"
    device_frame: "iPad Air 13\" - M2 - Space Gray - Portrait"
    output_size: [2048, 2732]
    background:
      type: "linear"
      colors: ["#667eea", "#764ba2"]

  - name: "Mac Desktop"
    source_image: "screenshots/desktop.png"
    device_frame: "MacBook Pro 2021 16"
    output_size: [3024, 1964]
    background:
      type: "linear"
      colors: ["#667eea", "#764ba2"]
```

## Best Practices

### Color Harmony
- Use professional color palettes
- Ensure sufficient contrast for text readability
- Consider App Store guidelines for screenshot aesthetics

### Typography
- Use system fonts for compatibility
- Maintain consistent font sizes across screenshots
- Apply stroke to text over complex backgrounds

### Device Frame Selection
- Choose frames that match your target audience
- Use consistent device families across a campaign
- Consider the latest device models for modern appeal

### Composition
- Follow the rule of thirds for text placement
- Leave breathing room around text elements
- Balance visual weight across the composition

---

*This documentation covers all available options in Koubou's YAML API. For more examples and tutorials, see the `examples/` directory.*