# 🎯 Koubou (工房) - The Artisan Workshop for App Store Screenshots

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-%3E%3D3.9-blue.svg)](https://python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)]()
[![PyPI Version](https://img.shields.io/pypi/v/koubou)](https://pypi.org/project/koubou/)

**Koubou (工房) transforms YAML into handcrafted App Store screenshots with artisan quality.**

工房 (koubou) means "artisan's workshop" in Japanese - where masters create their finest work. Every screenshot is carefully crafted with professional precision using device frames, rich backgrounds, and elegant typography.

## ✨ Features

- **🔄 Live Editing** - Real-time screenshot regeneration when config or assets change
- **🎨 100+ Device Frames** - iPhone 16 Pro, iPad Air M2, MacBook Pro, Apple Watch Ultra, and more
- **🌈 Professional Backgrounds** - Linear, radial, conic gradients with precise color control
- **✨ Rich Typography** - Advanced text overlays with stroke, alignment, wrapping, and custom fonts
- **🌈 Gradient Typography** - Linear, radial, and conic gradients for text with custom color stops
- **📱 YAML-First Configuration** - Elegant, declarative screenshot definitions
- **🚀 Batch Processing** - Generate multiple screenshots efficiently from a single config
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
```

## 🚀 Quick Start

```bash
# Create a sample configuration
kou --create-config my-screenshots.yaml

# Generate screenshots
kou generate my-screenshots.yaml

# Live editing mode - regenerate automatically when files change
kou live my-screenshots.yaml
```

## 🔄 Live Editing

**New in v0.5.0:** Koubou now supports real-time screenshot generation! The `live` command automatically regenerates screenshots when your YAML configuration or referenced assets change.

```bash
# Start live editing mode
kou live my-screenshots.yaml

# Optional: Adjust debounce delay (default: 0.5s)
kou live my-screenshots.yaml --debounce 1.0

# Enable verbose logging to see what's happening
kou live my-screenshots.yaml --verbose
```

### How Live Editing Works

1. **Smart Change Detection**: Monitors your YAML config file and all referenced assets
2. **Selective Regeneration**: Only regenerates screenshots affected by changes
3. **Dependency Tracking**: Automatically detects which assets each screenshot uses
4. **Debounced Updates**: Prevents excessive regeneration during rapid edits

### Live Editing Workflow

```yaml
# my-app-screenshots.yaml
project:
  name: "My App"
  output_dir: "Screenshots/Generated"

screenshots:
  welcome_screen:
    content:
      - type: "image"
        asset: "app-screens/welcome.png"  # Live editing watches this file
        frame: true
      - type: "text"
        content: "Welcome to the future"     # Changes to this regenerate instantly
```

**Perfect for iterative design workflows** - edit your assets in design tools, update text content, or tweak positioning, and see results instantly without manual regeneration!

### Platform Support
- **Live Editing**: macOS and Linux only
- **Standard Generation**: macOS, Linux, and Windows

---

## 🎨 Configuration

Create elegant screenshots with YAML configuration:

```yaml
project:
  name: "My Beautiful App"
  output_dir: "Screenshots/Generated"

devices:
  - "iPhone 15 Pro Portrait"

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

### Advanced Configuration

```yaml
project:
  name: "Feature Showcase"
  output_dir: "Screenshots/Generated"

devices:
  - "iPhone 15 Pro Portrait"

defaults:
  background:
    type: radial
    colors: ["#ff9a9e", "#fecfef", "#feca57"]

screenshots:
  ai_analysis:
    content:
      - type: "text"
        content: "✨ AI-Powered Analysis"
        position: ["50%", "10%"]
        size: 42
        color: "#2c2c54"
        weight: "bold"
      - type: "text"
        content: "Smart insights at your fingertips"
        position: ["50%", "20%"]
        size: 28
        color: "#1A73E8"
      - type: "image"
        asset: "screenshots/analysis.png"
        position: ["50%", "65%"]
        scale: 0.5
        frame: true
```

### Gradient Text Configuration

```yaml
screenshots:
  gradient_showcase:
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
      - type: "text"
        content: "Advanced Color Control"
        position: ["50%", "35%"]
        size: 28
        gradient:
          type: linear
          colors: ["#f093fb", "#f5576c", "#4facfe"]
          positions: [0.0, 0.3, 1.0]
          direction: 90
        stroke_width: 2
        stroke_gradient:
          type: linear
          colors: ["#333333", "#666666"]
          direction: 45
```

## 🎯 Commands

### Core Commands

- `kou generate <config.yaml>` - Generate screenshots from configuration
- `kou live <config.yaml>` - **[New]** Live editing mode with real-time regeneration
- `kou --create-config <output.yaml>` - Create a sample configuration file
- `kou --version` - Show version information
- `kou --help` - Show detailed help

### Command Options

#### Generate Command
```bash
# Override output directory
kou generate config.yaml --output ./custom-screenshots

# Use custom frame directory
kou generate config.yaml --frames ./my-frames

# Enable verbose logging
kou generate config.yaml --verbose
```

#### Live Editing Command
```bash
# Start live editing with default settings
kou live config.yaml

# Adjust debounce delay (default: 0.5s)
kou live config.yaml --debounce 1.0

# Enable verbose logging to see file changes
kou live config.yaml --verbose
```

#### Configuration Creation
```bash
# Create config with custom project name
kou --create-config config.yaml --name "My App Screenshots"
```

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

devices: [string, ...]       # Target device list (e.g., ["iPhone 15 Pro Portrait"])

defaults:                    # Default settings applied to all screenshots
  background:                # Default background configuration
    type: "solid" | "linear" | "radial" | "conic"
    colors: [string, ...]    # Hex colors array
    direction: float?        # Degrees for gradients (default: 0)
```

### Screenshot Configuration  
```yaml
screenshots:
  screenshot_id:             # Screenshots are now organized by ID (breaking change in v0.5.0)
    content:                 # Array of content items
      - type: "text" | "image"
        # Text content properties
        content: string?     # Text content (for type: "text")
        position: [string, string]  # Position as ["x%", "y%"] or ["xpx", "ypx"]
        size: int?           # Font size (default: 24)
        color: string?       # Hex color (default: "#000000")
        weight: string?      # "normal" or "bold" (default: "normal")
        alignment: string?   # "left", "center", "right" (default: "center")
        # Image content properties
        asset: string?       # Image file path (for type: "image")
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

### v0.5.6 (Latest)
- ✅ **Fixed**: All device frame PNG files now properly included in production installations
- ✅ **Fixed**: Strict error handling - no more silent fallbacks when frames are missing
- ✅ **Added**: Screenshot-level frame control (`frame: false` to disable per screenshot)
- ✅ **Improved**: Better error messages when configuration issues occur

### v0.5.5
- ⚠️ Known issue: Missing PNG frame files in production (fixed in v0.5.6)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🎯 Koubou Philosophy

In the spirit of Japanese craftsmanship, Koubou embodies:

- **職人気質 (Shokunin-kishitsu)** - Artisan spirit and dedication to craft
- **完璧 (Kanpeki)** - Pursuit of perfection in every detail  
- **簡潔 (Kanketsu)** - Elegant simplicity in design and usage
- **品質 (Hinshitsu)** - Uncompromising quality in output

Every screenshot generated by Koubou reflects these values - carefully crafted, pixel-perfect, and ready for the world's most demanding app stores.