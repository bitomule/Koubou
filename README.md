# 🎯 Koubou (工房) - The Artisan Workshop for App Store Screenshots

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-%3E%3D3.9-blue.svg)](https://python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()
[![PyPI Version](https://img.shields.io/pypi/v/koubou)](https://pypi.org/project/koubou/)

**Koubou (工房) transforms YAML into handcrafted App Store screenshots with artisan quality.**

工房 (koubou) means "artisan's workshop" in Japanese - where masters create their finest work. Every screenshot is carefully crafted with professional precision using device frames, rich backgrounds, and elegant typography.

## ✨ Features

- **🎨 100+ Device Frames** - iPhone 16 Pro, iPad Air M2, MacBook Pro, Apple Watch Ultra, and more
- **🌈 Professional Backgrounds** - Linear, radial, conic gradients with precise color control
- **✨ Rich Typography** - Advanced text overlays with stroke, alignment, wrapping, and custom fonts
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
kou create-config my-screenshots.yaml

# Generate screenshots
kou generate my-screenshots.yaml

# List available device frames
kou list-frames
```

## 🎨 Configuration

Create elegant screenshots with YAML configuration:

```yaml
project_name: "My Beautiful App"
output_directory: "screenshots"

screenshots:
  - name: "App Launch"
    source_image: "screenshots/home.png"
    device_frame: "iPhone 16 Pro - Black Titanium - Portrait"
    output_size: [1320, 2868]
    
    background:
      type: "linear"
      colors: ["#667eea", "#764ba2"]
      direction: 45
    
    text_overlays:
      - content: "Beautiful App"
        position: [100, 200]
        font_size: 48
        color: "#ffffff"
        alignment: "center"
        max_width: 700
        stroke_width: 2
        stroke_color: "#000000"
```

### Advanced Configuration

```yaml
screenshots:
  - name: "Feature Showcase"
    source_image: "screenshots/features.png"
    device_frame: "iPad Air 13\" - M2 - Space Gray - Landscape"
    output_size: [2732, 2048]
    
    background:
      type: "radial" 
      colors: ["#ff9a9e", "#fecfef", "#feca57"]
      center: ["30%", "20%"]
    
    text_overlays:
      - content: "✨ AI-Powered Analysis"
        position: [150, 220]
        font_size: 36
        font_weight: "bold"
        color: "#2c2c54"
        alignment: "left"
        max_width: 800
        line_height: 1.4
```

## 🎯 Commands

- `kou generate <config.yaml>` - Generate screenshots from configuration
- `kou create-config <output.yaml>` - Create a sample configuration file
- `kou list-frames` - List all available device frames
- `kou version` - Show version information
- `kou --help` - Show detailed help

### Command Options

```bash
# Override output directory
kou generate config.yaml --output ./custom-screenshots

# Use custom frame directory
kou generate config.yaml --frames ./my-frames

# Enable verbose logging
kou generate config.yaml --verbose
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
project_name: string          # Project name
output_directory: string      # Output directory (default: "output")
```

### Screenshot Configuration  
```yaml
screenshots:
  - name: string              # Screenshot identifier
    source_image: string      # Path to source image
    device_frame: string?     # Device frame name (optional)
    output_size: [int, int]   # Output dimensions [width, height]
    output_path: string?      # Custom output path (optional)
```

### Background Configuration
```yaml
background:
  type: "solid" | "linear" | "radial" | "conic"
  colors: [string, ...]      # Hex colors (e.g., ["#667eea", "#764ba2"])
  direction: float?          # Degrees for linear gradients (default: 0)
  center: [string, string]?  # Center point for radial/conic ["x%", "y%"]
```

### Text Overlays
```yaml
text_overlays:
  - content: string          # Text content
    position: [int, int]     # X, Y position in pixels
    font_size: int           # Font size (default: 24)
    font_family: string      # Font name (default: "Arial")
    font_weight: string      # "normal" or "bold" (default: "normal")
    color: string            # Hex color (default: "#000000")
    alignment: string        # "left", "center", "right" (default: "center")
    anchor: string           # Anchor point (default: "center")
    max_width: int?          # Maximum width for wrapping
    max_lines: int?          # Maximum lines for wrapping
    line_height: float       # Line height multiplier (default: 1.2)
    stroke_width: int?       # Text stroke width
    stroke_color: string?    # Text stroke color
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

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🎯 Koubou Philosophy

In the spirit of Japanese craftsmanship, Koubou embodies:

- **職人気質 (Shokunin-kishitsu)** - Artisan spirit and dedication to craft
- **完璧 (Kanpeki)** - Pursuit of perfection in every detail  
- **簡潔 (Kanketsu)** - Elegant simplicity in design and usage
- **品質 (Hinshitsu)** - Uncompromising quality in output

Every screenshot generated by Koubou reflects these values - carefully crafted, pixel-perfect, and ready for the world's most demanding app stores.