# 🎯 Koubou (工房) - The Artisan Workshop for App Store Screenshots

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-%3E%3D3.9-blue.svg)](https://python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)]()
[![PyPI Version](https://img.shields.io/pypi/v/koubou)](https://pypi.org/project/koubou/)

**Koubou (工房) transforms YAML into handcrafted App Store screenshots with artisan quality.**

工房 (koubou) means "artisan's workshop" in Japanese - where masters create their finest work. Every screenshot is carefully crafted with professional precision using device frames, rich backgrounds, and elegant typography.

## ✨ Features

- **🔄 Live Editing** - Real-time screenshot regeneration when config or assets change
- **🖥️ Live Preview Dashboard** - Auto-open a local dashboard for screenshot previews with hot reload
- **🧩 HTML/CSS Templates** - Render polished marketing layouts with Chrome or Playwright Chromium
- **🌍 Multi-Language Localization** - Generate localized screenshots using familiar xcstrings format from Xcode
- **🖼️ Localized Assets** - Automatic language-specific asset resolution with convention-based and explicit mapping
- **🎨 100+ Device Frames** - iPhone 16 Pro, iPad Air M2, MacBook Pro, Apple Watch Ultra, and more
- **🌈 Professional Backgrounds** - Linear, radial, conic gradients with precise color control
- **✨ Rich Typography** - Advanced text overlays with stroke, alignment, wrapping, and custom fonts
- **🌈 Gradient Typography** - Linear, radial, and conic gradients for text with custom color stops
- **📱 YAML-First Configuration** - Elegant, declarative screenshot definitions
- **🚀 Batch Processing** - Generate multiple screenshots efficiently from a single config
- **🔦 Highlight Annotations** - Circle, rounded rect, and rect shapes with spotlight dimming and background blur
- **🔍 Zoom Callouts** - Magnified callout bubbles with source indicators, advanced connectors (straight/curved/facing), and drop shadows
- **✨ Anti-Aliased Rendering** - Supersampled shape rendering for smooth edges at any resolution
- **🔧 Flexible API** - Both simple and advanced configuration options
- **💎 Artisan Quality** - Pixel-perfect output ready for App Store submission

## 📦 Installation

### Package Managers (Recommended)

**PyPI (All Platforms)**
```bash
pip install koubou
```

**macOS/Linux - Homebrew**
```bash
brew install bitomule/tap/koubou
```

**HTML Templates**
```bash
kou setup-html
```

If Google Chrome is already installed, HTML template rendering usually works without any extra setup. `kou setup-html` installs Playwright Chromium only when it is needed.

**Python Developers**
```bash
pip install koubou[dev]  # With development dependencies
```

### Manual Installation

**Option 1: Install Script (Recommended)**
```bash
git clone https://github.com/bitomule/koubou.git
cd koubou
./install.sh
```

**Option 2: From Source**
```bash
git clone https://github.com/bitomule/koubou.git
cd koubou
pip install .
```

### Verification

Verify your installation:
```bash
kou --version
kou --help
kou setup-html --help
```

## 🚀 Quick Start

```bash
# Create a sample configuration
kou --create-config my-screenshots.yaml

# Generate screenshots
kou generate my-screenshots.yaml

# Prepare HTML rendering if your project uses HTML templates
kou setup-html

# Inspect real frame geometry before designing HTML layouts
kou inspect-frame "iPhone 16 Pro - Black Titanium - Portrait" --output-size iPhone6_9

# Live editing mode - regenerate automatically when files change
kou live my-screenshots.yaml
```

## 🧩 HTML Templates

Use `template:` when a screenshot needs full HTML/CSS layout control instead of the standard content pipeline.

```yaml
screenshots:
  hero:
    template: "templates/hero.html"
    variables:
      headline: "Private cleanup, instantly"
    assets:
      screen: "screenshots/home.png"
```

- `variables:` are localizable `{{key}}` substitutions
- `assets:` are file-path substitutions exposed to the template as `{{key}}`
- `kou generate config.yaml --setup-html` prepares HTML rendering and generates in one run
- `kou live config.yaml --setup-html` does the same before starting live mode
- `kou inspect-frame "<device>" --output-size <size> --output json` exposes frame and screen geometry for layout decisions

## 🔄 Live Editing

Real-time screenshot regeneration when your YAML configuration or assets change.

```bash
# Start live editing mode
kou live my-screenshots.yaml

# Adjust debounce delay (default: 0.5s)
kou live my-screenshots.yaml --debounce 1.0

# Enable verbose logging
kou live my-screenshots.yaml --verbose
```

`kou live` also starts a local browser dashboard that previews screenshots in YAML order. HTML slides render as live iframes, while standard Koubou slides render as regenerated PNGs in the same grid.

![HTML live preview dashboard](docs/images/html-live-preview-dashboard.png)

**How it works:**
- Monitors YAML config and all referenced assets
- Regenerates only affected screenshots
- Debounces rapid changes to prevent excessive regeneration
- Starts a local preview dashboard and auto-opens it when possible
- Shows HTML slides as live HTML and standard Koubou slides as PNG previews
- Uses the base language for preview while localized outputs continue regenerating on disk

**Perfect for iterative design** - edit assets in design tools, update text, tweak positioning, and see results instantly.

**Platform support:** macOS and Linux only (standard generation works on Windows)

---

## 🌍 Multi-Language Localization

Generate localized screenshots for international App Store submissions using xcstrings format from Xcode.

```yaml
project:
  name: "My App Screenshots"
  output_dir: "Screenshots/Generated"
  device: "iPhone 15 Pro Portrait"
  output_size: "iPhone6_9"

localization:
  base_language: "en"
  languages: ["en", "es", "ja", "fr", "de"]
  xcstrings_path: "Localizable.xcstrings"  # Optional - auto-creates if missing

screenshots:
  welcome_screen:
    content:
      - type: "text"
        content: "Welcome to Amazing App"  # Text becomes localization key
        position: ["50%", "20%"]
        size: 48
        color: "#8E4EC6"
      - type: "image"
        asset: "screenshots/home.png"
        position: ["50%", "60%"]
```

**Output structure:**
```
Screenshots/Generated/
├── en/iPhone_15_Pro_Portrait/welcome_screen.png
├── es/iPhone_15_Pro_Portrait/welcome_screen.png
├── ja/iPhone_15_Pro_Portrait/welcome_screen.png
├── fr/iPhone_15_Pro_Portrait/welcome_screen.png
└── de/iPhone_15_Pro_Portrait/welcome_screen.png
```

**Workflow:** Koubou extracts text content and creates/updates your xcstrings file. Edit translations in Xcode's xcstrings editor, then regenerate screenshots. Live mode watches both YAML config and xcstrings file for changes.

**Key benefits:** Uses iOS-native xcstrings format, natural text as keys (no IDs), supports plurals and device variants, works seamlessly with live mode.

---

## 🖼️ Localized Assets

Automatically resolve language-specific images for multi-language screenshots. Perfect for RTL layouts, region-specific content, or tools like Maestro that generate per-locale screenshots.

### Convention-Based (Recommended)

Organize assets in `{lang}/` subdirectories - Koubou resolves them automatically:

```yaml
localization:
  base_language: "en"
  languages: ["en", "es", "ja"]

screenshots:
  hero_screen:
    content:
      - type: "image"
        asset: "screenshots/hero.png"  # Auto-resolves to screenshots/{lang}/hero.png
        position: ["50%", "50%"]
```

**Directory structure:**
```
screenshots/
├── en/hero.png
├── es/hero.png
├── ja/hero.png
└── hero.png  # Fallback for missing languages
```

**Resolution order:** `{lang}/path` → `{base_lang}/path` → `direct_path`

### Explicit Mapping

For non-standard structures or external tool outputs:

```yaml
screenshots:
  onboarding:
    content:
      - type: "image"
        asset:
          en: "maestro/en_iphone/onboarding.png"
          es: "maestro/es_iphone/onboarding.png"
          ja: "maestro/ja_iphone/onboarding.png"
          default: "screenshots/fallback.png"  # Optional
        position: ["50%", "50%"]
```

Mix both approaches in the same screenshot as needed.

---

## 📱 App Store Screenshot Sizes

Koubou provides predefined App Store screenshot sizes configured at the project level. All screenshots in a single YAML file use the same output size.

### Using Named Sizes

Specify the output size once in your project configuration:

```yaml
project:
  name: "My App Screenshots"
  output_dir: "Screenshots/Generated"
  device: "iPhone 15 Pro Portrait"
  output_size: "iPhone6_9"  # All screenshots will be 1320×2868

screenshots:
  welcome_screen:
    content:
      - type: "image"
        asset: "screenshots/home.png"
```

### Available Sizes

View all available sizes with descriptions:

```bash
kou list-sizes
```

**Common Sizes:**
- `iPhone6_9` - iPhone 16 Pro Max, 15 Pro Max (1320×2868)
- `iPhone6_7` - iPhone 15/14/13/12 Pro Max, Plus (1290×2796)
- `iPhone6_1` - iPhone 16/15/14/13 Pro (1179×2556)
- `iPadPro12_9` - iPad Pro 12.9" (2048×2732)
- `iPadPro11` - iPad Pro 11", iPad Air 11" M2 (1668×2388)

### Custom Sizes

You can still specify custom dimensions when needed:

```yaml
project:
  name: "My App Screenshots"
  device: "iPhone 15 Pro Portrait"
  output_size: [1200, 2600]  # Custom width × height
```

### Multiple Sizes

To generate screenshots for different sizes, create separate YAML files:
- `iphone-6-9.yaml` - All iPhone 6.9" screenshots
- `iphone-6-7.yaml` - All iPhone 6.7" screenshots
- `ipad-pro.yaml` - All iPad Pro screenshots

---

## 🎨 Configuration

Create screenshots with YAML configuration:

```yaml
project:
  name: "My Beautiful App"
  output_dir: "Screenshots/Generated"
  device: "iPhone 15 Pro Portrait"
  output_size: "iPhone6_9"  # iPhone 16 Pro Max, 15 Pro Max

defaults:
  background:
    type: linear
    colors: ["#E8F0FE", "#F8FBFF"]
    direction: 180

screenshots:
  welcome_screen:
    content:
      - type: "text"
        content: "Beautiful App"
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
```

See the YAML API Reference below for all available options including gradients, strokes, and advanced positioning.

## 🎯 Commands

### Core Commands

- `kou generate <config.yaml>` - Generate screenshots from configuration
- `kou setup-html` - Prepare HTML rendering support for the current installation
- `kou live <config.yaml>` - Live editing mode with real-time regeneration
- `kou inspect-frame "<device>" --output-size <size>` - Inspect real frame and screen geometry for layout decisions
- `kou list-sizes` - List available App Store screenshot sizes
- `kou --create-config <output.yaml>` - Create a sample configuration file
- `kou --version` - Show version information
- `kou --help` - Show detailed help

### Command Options

#### Generate Command
```bash
# Emit machine-readable results
kou generate config.yaml --output json

# Prepare HTML rendering and generate in one run
kou generate config.yaml --setup-html

# Enable verbose logging
kou generate config.yaml --verbose
```

#### HTML Setup
```bash
# Prepare HTML rendering for the current installation
kou setup-html

# See setup diagnostics
kou setup-html --verbose
```

#### Frame Inspection
```bash
# Human-readable geometry summary
kou inspect-frame "iPhone 16 Pro - Black Titanium - Portrait" --output-size iPhone6_9

# Machine-readable output for agents or tooling
kou inspect-frame "iPhone 16 Pro - Black Titanium - Portrait" --output-size iPhone6_9 --output json

# Custom canvas size
kou inspect-frame "iPhone 16 Pro - Black Titanium - Portrait" --output-size 1200x2600 --output json
```

#### Live Editing Command
```bash
# Start live editing with default settings
kou live config.yaml

# Prepare HTML rendering before starting live mode
kou live config.yaml --setup-html

# Adjust debounce delay (default: 0.5s)
kou live config.yaml --debounce 1.0

# Enable verbose logging to see file changes
kou live config.yaml --verbose
```

`kou live` also prints a local preview URL and opens a browser tab with the live preview dashboard. HTML screenshots are previewed as live HTML, standard screenshots are previewed as PNGs, the dashboard uses the base language for preview, and changed slides hot-reload without waiting for a full page refresh.

#### Configuration Creation
```bash
# Create config with custom project name
kou --create-config config.yaml --name "My App Screenshots"
```

#### Upload to App Store Connect

For uploading screenshots, we recommend [App Store Connect CLI](https://github.com/rudrankriyam/App-Store-Connect-CLI):

```bash
brew install appstoreconnect-cli
asc auth login

# Upload per device type and language
asc assets screenshots upload \
  --version-localization "LOC_ID" \
  --path "./output/en/iPhone_16_Pro_.../" \
  --device-type "IPHONE_69"
```

Koubou outputs screenshots organized by `{language}/{device}/`, mapping directly to individual `asc` upload calls.

## 🎨 Device Frames

Koubou includes 100+ professionally crafted device frames:

### iPhone Frames
- iPhone 16 Pro (Black, Desert, Natural, White Titanium)
- iPhone 16 (Black, Pink, Teal, Ultramarine, White)
- iPhone 15 Pro/Max (All titanium colors)
- iPhone 14 Pro/Max, 12-13 series, and more

### iPad Frames
- iPad Air 11"/13" M2 (Blue, Purple, Space Gray, Stardust)
- iPad Pro 11"/13" M4 (Silver, Space Gray)
- iPad Pro 2018-2021, iPad mini, and classic models

### Mac & Watch Frames
- MacBook Pro 2021 (14" & 16"), MacBook Air 2020/2022
- iMac 24" Silver, iMac 2021
- Apple Watch Series 4/7, Watch Ultra

## 📖 YAML API Reference

### Project Configuration
```yaml
project:
  name: string               # Project name
  output_dir: string         # Output directory (default: "output")
  device: string             # Target device frame (default: "iPhone 15 Pro Portrait")
  output_size: string | [int, int]  # Named size ("iPhone6_9") or custom [width, height] (default: "iPhone6_9")

defaults:                    # Default settings applied to all screenshots
  background:                # Default background configuration
    type: "solid" | "linear" | "radial" | "conic"
    colors: [string, ...]    # Hex colors array
    direction: float?        # Degrees for gradients (default: 0)
```

### Screenshot Configuration
```yaml
screenshots:
  screenshot_id:             # Unique identifier for each screenshot
    content:                 # Array of content items
      - type: "text" | "image" | "highlight" | "zoom"
        # Text content properties
        content: string?     # Text content (for type: "text")
        position: [string, string]  # Position as ["x%", "y%"] or ["xpx", "ypx"]
        size: int?           # Font size (default: 24)
        color: string?       # Hex color (default: "#000000")
        weight: string?      # "normal" or "bold" (default: "normal")
        alignment: string?   # "left", "center", "right" (default: "center")
        # Image content properties
        asset: string | dict? # Image path (string) or localized mapping (dict)
        scale: float?        # Scale factor (default: 1.0)
        frame: bool?         # Apply device frame (default: false)
```

### Background Configuration
```yaml
background:
  type: "solid" | "linear" | "radial" | "conic"
  colors: [string, ...]      # Hex colors (e.g., ["#667eea", "#764ba2"])
  direction: float?          # Degrees for linear gradients (default: 0)
  center: [string, string]?  # Center point for radial/conic ["x%", "y%"]
```

### Content Items
```yaml
# Text Content Item
- type: "text"
  content: string            # Text to display
  position: [string, string] # Position as ["50%", "20%"] or ["100px", "50px"]
  size: int                  # Font size in pixels (default: 24)
  
  # Fill Options (choose exactly one):
  color: string              # Solid color (hex format, e.g., "#000000")
  # OR
  gradient:                  # Text gradient
    type: "linear" | "radial" | "conic"
    colors: [string, ...]    # Hex colors array (minimum 2)
    positions: [float, ...]? # Color stops 0.0-1.0 (optional)
    direction: float?        # Angle in degrees (linear)
    center: [string, string]? # Center point (radial/conic)
    radius: string?          # Radius for radial ("50%", "100px")
    start_angle: float?      # Starting angle (conic)
  
  weight: string             # "normal" or "bold" (default: "normal")
  alignment: string          # "left", "center", "right" (default: "center")
  
  # Stroke Options (optional):
  stroke_width: int?         # Stroke width in pixels
  stroke_color: string?      # Solid stroke color (hex format)
  # OR
  stroke_gradient:           # Gradient stroke (same structure as gradient)

# Image Content Item
- type: "image"
  asset: string              # Path to image file
  position: [string, string] # Position as ["50%", "60%"] or ["200px", "300px"]
  scale: float               # Scale factor (default: 1.0)
  frame: bool                # Apply device frame around image (default: false)

# Highlight Content Item
- type: "highlight"
  shape: "circle" | "rounded_rect" | "rect"  # Shape (required)
  position: [string, string] # Center position as ["50%", "50%"]
  dimensions: [string, string] # Width, height as ["20%", "15%"]
  border_color: string?      # Border color in hex (e.g., "#FF3B30")
  border_width: int?         # Border width in pixels (default: 3)
  fill_color: string?        # Fill color in hex, supports alpha (e.g., "#FF3B3020")
  corner_radius: int?        # Corner radius for rounded_rect (default: 16)
  shadow: bool?              # Enable drop shadow (default: false)
  shadow_color: string?      # Shadow color with alpha (default: "#00000040")
  shadow_blur: int?          # Shadow blur radius (default: 15)
  shadow_offset: [string, string]? # Shadow X,Y offset (default: ["0", "6"])
  spotlight: bool?           # Dim everything except highlight (default: false)
  spotlight_color: string?   # Overlay color (default: "#000000")
  spotlight_opacity: float?  # Overlay opacity 0.0-1.0 (default: 0.5)
  blur_background: bool?     # Blur outside highlight area (default: false)
  blur_radius: int?          # Background blur radius (default: 20)

# Zoom Content Item
- type: "zoom"
  source_position: [string, string]  # Center of area to magnify (required)
  source_size: [string, string]      # Crop region size (required)
  display_position: [string, string] # Where magnified view appears
  display_size: [string, string]     # Size of magnified bubble (or use zoom_level)
  zoom_level: float?         # Auto-calculate display_size (e.g., 2.5 = 2.5x)
  shape: "circle" | "rounded_rect"   # Bubble shape (default: "circle")
  border_color: string?      # Border color in hex
  border_width: int?         # Border width (default: 3)
  corner_radius: int?        # For rounded_rect (default: 16)
  shadow: bool?              # Enable drop shadow (default: false)
  shadow_color: string?      # Shadow color with alpha (default: "#00000040")
  shadow_blur: int?          # Shadow blur radius (default: 15)
  shadow_offset: [string, string]? # Shadow X,Y offset (default: ["0", "6"])
  source_indicator: bool?    # Show outline on source region (default: true)
  source_indicator_style: string? # "border" | "dashed" | "fill" (default: "border")
  connector: bool?           # Draw line from source to display (default: false)
  connector_style: string?   # "straight" | "curved" | "facing" (default: "straight")
  connector_color: string?   # Line color (defaults to border_color)
  connector_width: int?      # Line width (default: 2)
  connector_fill: string?    # Fill color between facing connector lines
```

## 🏗️ Architecture

Koubou uses a clean, modular architecture:

- **CLI Layer** (`koubou.cli`): Command-line interface with rich output
- **Configuration** (`koubou.config`): Pydantic-based type-safe configuration
- **Generation Engine** (`koubou.generator`): Core screenshot generation logic
- **Renderers** (`koubou.renderers`): Specialized rendering for backgrounds, text, frames
- **Device Frames** (`koubou.frames`): 100+ device frame assets and metadata

## 🔧 Development

### Setup Development Environment
```bash
# Clone the repository
git clone https://github.com/bitomule/koubou.git
cd koubou

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black src/ tests/
isort src/ tests/ 
flake8 src/ tests/
mypy src/
```

### Running Tests
```bash
# Run all tests with coverage
pytest -v --cov=src/koubou

# Run specific test file
pytest tests/test_generator.py -v

# Run with live output
pytest -s
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`pytest`, `black`, `isort`, `flake8`, `mypy`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🎯 Koubou Philosophy

In the spirit of Japanese craftsmanship, Koubou embodies:

- **職人気質 (Shokunin-kishitsu)** - Artisan spirit and dedication to craft
- **完璧 (Kanpeki)** - Pursuit of perfection in every detail  
- **簡潔 (Kanketsu)** - Elegant simplicity in design and usage
- **品質 (Hinshitsu)** - Uncompromising quality in output

Every screenshot generated by Koubou reflects these values - carefully crafted, pixel-perfect, and ready for the world's most demanding app stores.
