#!/bin/bash
# Koubou Installation Script

set -e

echo "🎯 Installing Koubou (工房) - The Artisan Workshop for App Store Screenshots"
echo ""

# Check if Python 3.9+ is installed
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        echo "✅ Python $PYTHON_VERSION found"
    else
        echo "❌ Python 3.9+ is required but found $PYTHON_VERSION"
        echo "   Please install Python 3.9+ from: https://python.org/"
        exit 1
    fi
else
    echo "❌ Python 3 is required but not installed"
    echo "   Please install Python 3.9+ from: https://python.org/"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed"
    echo "   Please install pip with: python3 -m ensurepip --upgrade"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Determine installation method
if [ -f "pyproject.toml" ] && [ -d "src/koubou" ]; then
    echo "🔨 Installing from source..."
    
    # Install in development mode if we're in the repo
    read -p "Install in development mode? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip3 install -e ".[dev]"
        echo "✅ Koubou installed in development mode with dev dependencies"
    else
        pip3 install .
        echo "✅ Koubou installed from source"
    fi
else
    echo "🔨 Installing from PyPI..."
    pip3 install koubou
    echo "✅ Koubou installed from PyPI"
fi

echo ""
echo "🎉 Koubou installation complete!"
echo ""
echo "Quick start:"
echo "  kou create-config sample.yaml    # Create a sample configuration"
echo "  kou generate sample.yaml         # Generate screenshots"
echo "  kou list-frames                  # List available device frames"
echo "  kou --help                       # Show all commands"
echo ""
echo "📚 Documentation:"
echo "  • README: Comprehensive guide with examples"
echo "  • examples/: YAML configuration samples"
echo "  • docs/: Complete API reference"
echo ""
echo "🎯 Ready to craft beautiful App Store screenshots!"