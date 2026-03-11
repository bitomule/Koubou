# CLAUDE.md

**Koubou** - Python CLI tool that generates App Store screenshots from YAML configs.

See `AGENTS.md` for full project structure, CLI principles, and command reference.

## Virtual Environment

This project uses a `.venv` virtualenv at the project root. Always use `.venv/bin/` prefixed commands:

```bash
.venv/bin/pytest tests/ -v          # Run tests
.venv/bin/python -m black src/      # Format
.venv/bin/pip install ".[dev]"      # Install dev deps
```

## Quick Reference

```bash
make install-dev   # Setup (uses .venv)
make check         # Format + lint + test
make install-hooks # Pre-commit hooks
```

## Key Commands

```bash
kou generate config.yaml               # Generate screenshots
kou generate config.yaml --output json  # JSON output for automation
kou live config.yaml --verbose          # Live editing mode
kou --create-config sample.yaml         # Create sample config
kou --create-config sample.yaml --force # Overwrite existing
```

## Testing

Run integration tests: `pytest tests/integration/`
Debug with `--verbose` flag for detailed output.