# AGENTS.md

## What is Koubou?

Koubou generates App Store screenshots from YAML configuration files. Input: YAML config + image assets. Output: pixel-perfect screenshots organized by `{language}/{device}/`.

## CLI Principles

- **Explicit flags only** - no single-letter abbreviations. `--verbose` not `-v`.
- **No interactive prompts** - use `--force` to overwrite, `--confirm` to approve destructive actions.
- **JSON output for agents** - pass `--output json` to get machine-readable output on stdout. Default is `table` (human-readable rich output).
- **`--help` is the source of truth** - run `kou --help` or `kou <command> --help` for full flag documentation.

## Project Structure

```
src/koubou/
  cli.py          # Command-line interface (typer)
  config.py       # YAML parsing with Pydantic models
  generator.py    # Core screenshot generation engine
  renderers/      # Background, text, frame rendering
  frames/         # Device frame PNG assets + Frames.json + Sizes.json
```

## Commands

```bash
kou generate config.yaml              # Generate screenshots
kou generate config.yaml --output json # JSON results to stdout
kou list-sizes                         # Show available App Store sizes
kou list-sizes --output json           # JSON sizes to stdout
kou list-frames                        # Show available device frames
kou list-frames iPhone --output json   # Filtered JSON frames to stdout
kou live config.yaml                   # Live editing mode
kou --create-config sample.yaml        # Create sample config
kou --create-config sample.yaml --force # Overwrite existing
kou --version                          # Show version
```

## Virtual Environment

This project uses a `.venv` virtualenv at the project root. All commands must run through it:

```bash
.venv/bin/pip install ".[dev]"      # Install dev deps (includes playwright)
.venv/bin/playwright install chromium  # Install browser for HTML rendering tests
.venv/bin/pytest tests/ -v          # Run tests
.venv/bin/python -m black src/      # Format
```

## Build & Test

```bash
make install-dev    # Install with dev dependencies
make format         # Run black + isort
make lint           # Run flake8 + mypy
make test           # Run pytest with coverage
make check          # All of the above
make install-hooks  # Enable pre-commit hooks
```

## Output Structure

Screenshots are written to the configured `output_dir`:

```
{output_dir}/
  {language}/
    {device}/
      {screenshot_id}.png
```

Example: `Screenshots/Generated/en/iPhone_15_Pro_Portrait/welcome_screen.png`

## Upload

Koubou does not handle uploads. Use [App Store Connect CLI](https://github.com/rudrankriyam/App-Store-Connect-CLI):

```bash
brew install appstoreconnect-cli
asc auth login

asc assets screenshots upload \
  --version-localization "LOC_ID" \
  --path "./output/en/iPhone_16_Pro_.../" \
  --device-type "IPHONE_69"
```

The output directory structure maps directly to individual `asc` upload calls per device type and language.

## Release Process

Version is derived from git tags via `setuptools-scm`.

```bash
# 1. Update CHANGELOG.md with new version section
# 2. Commit all changes
git add -A && git commit -m "Prepare vX.Y.Z release"

# 3. Tag and push
git tag vX.Y.Z
git push origin main --tags
```

GitHub Actions handles PyPI publishing and Homebrew formula updates on tag push.
