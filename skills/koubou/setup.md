# Setup Guide

## Installation

### Quick install (recommended)

```bash
pip3 install "koubou[html]"
playwright install chromium
```

The `[html]` extra installs Playwright for HTML template rendering.

### Verify installation

```bash
kou --version
kou list-frames "iPhone 16"
```

### Alternative: install from source

```bash
git clone https://github.com/bitomule/Koubou.git /tmp/koubou
cd /tmp/koubou
pip3 install ".[html]"
playwright install chromium
```

## Troubleshooting

### `playwright install chromium` fails

Try installing system Chrome instead — koubou tries system Chrome first before falling back to Playwright's bundled Chromium.

```bash
# macOS
brew install --cask google-chrome
```

### `ModuleNotFoundError: No module named 'playwright'`

You installed koubou without the HTML extra:

```bash
pip3 install "koubou[html]"
```

### `No browser available for HTML rendering`

Neither system Chrome nor Playwright Chromium is available:

```bash
playwright install chromium
# or install Chrome manually
```

### Permission errors on macOS

```bash
pip3 install --user "koubou[html]"
```

### Virtual environment

If the project uses a `.venv`:

```bash
.venv/bin/pip install "koubou[html]"
.venv/bin/playwright install chromium
```

Then run koubou with `.venv/bin/kou` instead of `kou`.
