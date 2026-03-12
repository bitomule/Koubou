# Setup Guide

## Installation

### Quick install (recommended)

```bash
pip3 install koubou
kou setup-html
```

If Google Chrome is already installed, `kou setup-html` will usually confirm that HTML rendering is already ready without downloading Chromium.

### Verify installation

```bash
kou --version
kou list-frames "iPhone 16"
kou setup-html --help
```

### Alternative: install from source

```bash
git clone https://github.com/bitomule/Koubou.git /tmp/koubou
cd /tmp/koubou
pip3 install .
kou setup-html
```

## Troubleshooting

### `kou setup-html` fails

Try installing system Chrome instead — koubou tries system Chrome first before falling back to Playwright's bundled Chromium.

```bash
# macOS
brew install --cask google-chrome
```

### `ModuleNotFoundError: No module named 'playwright'`

Your koubou installation predates the built-in HTML runtime dependency. Update koubou, then run setup again:

```bash
pip3 install --upgrade koubou
kou setup-html
```

### `No browser available for HTML rendering`

Neither system Chrome nor Playwright Chromium is available:

```bash
kou setup-html
# or install Chrome manually
```

### Permission errors on macOS

```bash
pip3 install --user koubou
kou setup-html
```

### Virtual environment

If the project uses a `.venv`:

```bash
.venv/bin/pip install koubou
.venv/bin/kou setup-html
```

Then run koubou with `.venv/bin/kou` instead of `kou`.
