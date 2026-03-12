# Setup Guide

## Golden rule

If `kou --version` works, koubou is already installed. Stop there.

Do not run `pip`, `pip3`, or `playwright install` on a working installation just because this skill is being used.

## Preferred setup flow

### 1. Check whether koubou already works

```bash
kou --version
kou list-frames "iPhone 16"
```

If both commands work:
- treat the installation as healthy
- do not reinstall koubou
- do not run low-level Playwright commands

### 2. Always prepare the HTML runtime for this skill

This skill is specifically for HTML template rendering, so run:

```bash
kou setup-html
```

Run it after `kou --version` succeeds. Treat it as safe and idempotent.

Do not replace this with low-level Playwright commands.

### 3. Install koubou only if `kou` is missing

Use installation commands only when `kou --version` fails.

#### macOS with Homebrew

```bash
brew install bitomule/tap/koubou
```

#### PyPI install

```bash
pip3 install koubou
```

#### Install from source

```bash
git clone https://github.com/bitomule/Koubou.git /tmp/koubou
cd /tmp/koubou
pip3 install .
```

## Troubleshooting

### `kou` works, but HTML rendering is not ready

Use the product command first:

```bash
kou setup-html
```

Koubou handles browser/runtime setup through this command. Do not bypass it.

### `kou` is missing

Install koubou first:

```bash
brew install bitomule/tap/koubou
```

Or:

```bash
pip3 install koubou
```

Then verify with:

```bash
kou --version
```

### `No browser available for HTML rendering`

Preferred path:

```bash
kou setup-html
```

If this fails, surface the exact error to the user and stop. Do not jump to manual Playwright commands on your own.

### PEP 668 or externally-managed Python errors

Do not try to force `pip` into a system-managed Python if `kou` already works.

If `kou --version` succeeds:
- treat the installation as valid
- use `kou setup-html` for HTML runtime setup

If `kou` is not installed, prefer a project virtual environment instead of mutating system Python.

### Permission errors on macOS

Prefer using the existing `kou` installation. If installation is truly required, use a project virtual environment.

### Virtual environment

If the project uses a `.venv`:

```bash
.venv/bin/pip install koubou
.venv/bin/kou setup-html
```

Then run koubou with `.venv/bin/kou` instead of `kou`.
