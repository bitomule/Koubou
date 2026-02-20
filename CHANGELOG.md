# Changelog

All notable changes to Koubou will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Text auto-sizing**: Automatically find the largest font size that fits within a pixel height budget. Set `min_size`, `max_width`, and `max_height` on text content items — Koubou shrinks from `size` down to `min_size` until the wrapped text block fits within `max_height`. Ideal for multi-language screenshots where translation lengths vary.
- `max_width`, `max_lines`, `max_height`, `min_size` fields on `ContentItem` for text content
- `min_font_size`, `max_height` fields on `TextOverlay`
- Validation: `min_size` requires both `max_width` and `max_height`, and must be <= `size`

## [0.13.0] - 2026-02-14

### Added
- **Text content items**: `font_family` field to specify custom fonts (default: "Arial")

## [0.12.0] - 2026-02-14

### Added
- **Highlight annotations**: drop shadow, spotlight mode, blur background
- **Zoom callouts**: drop shadow, source region indicator (border/dashed/fill), advanced connectors (straight/curved/facing with optional fill), zoom_level shorthand
- Anti-aliased shape rendering via 2x supersampling
- Shared renderer utilities (`renderers/utils.py`)
- Example YAML and documentation for all new features

### Fixed
- Zoom bubble no longer captures source indicator and connector lines in cropped content
- Source indicator uses rectangular shape matching the crop region
- Border-only highlights render outline shadow instead of filled shadow

### Testing
- 317 tests passing

## [0.11.1] - 2026-02-11

### Fixed
- Frame-aware image rotation: `rotation` now applies to the entire framed asset (screen content + bezel) instead of being ignored when `frame: true`

### Changed
- Refactored `_apply_asset_frame` to compose framed assets in local coordinates before canvas placement, improving clarity and enabling rotation support

### Testing
- 246 tests passing
- Added regression test for framed image rotation

## [0.11.0] - 2026-02-11

### Removed
- **BREAKING**: Removed `upload` command and all App Store Connect upload code
- Removed `pyjwt`, `cryptography`, `httpx` dependencies
- Removed `responses`, `pytest-httpx` dev dependencies
- Removed `src/koubou/appstore/` module (auth, client, uploader)
- Removed all upload-related tests
- Removed interactive prompts (`typer.confirm`)
- Removed single-letter flag abbreviations (`-v`, `-n`, `-m`)

### Added
- `--output json` flag for `generate`, `list-sizes`, `list-frames` commands
- `--force` flag to overwrite existing files in `--create-config`
- `AGENTS.md` with agent-first CLI documentation
- `Makefile` with standard development targets (`format`, `lint`, `test`, `check`)
- `.githooks/pre-commit` hook (activate with `make install-hooks`)
- JSON output sends structured data to stdout, progress/errors to stderr

### Changed
- Upload workflow now recommends [App Store Connect CLI](https://github.com/rudrankriyam/App-Store-Connect-CLI) (`asc`)
- All CLI flags are explicit (no abbreviations) for unambiguous agent usage
- Updated README and CLAUDE.md documentation

### Testing
- 245 tests passing
- All linters passing (black, isort, flake8, mypy)

## [0.10.3] - 2025-11-27

### Changed
- **BREAKING**: Migrated from Pydantic v1 to v2 field validators
- All 19 validators updated to use `@field_validator` with `ValidationInfo`
- `output_size` now properly converts named sizes (e.g., "iPhone6_9") to tuples before validation

### Fixed
- **CRITICAL**: Fixed missing f-string prefixes in generator.py logging (2 locations)
- **CRITICAL**: Added division-by-zero validation for image scaling calculations
- Fixed iPadPro13 dimensions from 2048x2732 to correct 2064x2752
- Removed placeholder email from `__init__.py` and `pyproject.toml`
- Removed broken Read the Docs link from project URLs

### Added
- Proper hex color validation with regex pattern (#RGB, #RRGGBB, #RRGGBBAA)
- `validate_hex_color()` helper function with clear error messages
- Improved error messages for invalid color formats

### Testing
- All 310 tests passing across Python 3.9, 3.10, 3.11, 3.12
- All linters passing (black, isort, flake8, mypy)
- CI/CD pipeline verified and working

## [0.10.2] - 2025-11-01

### Fixed
- **CRITICAL**: Removed alpha channel from PNG screenshots - App Store does not accept images with alpha channels
- All generated PNG files now saved as RGB (without alpha) instead of RGBA
- Previously, PNG screenshots included an alpha channel that would cause App Store Connect to reject the images

### Added
- Test to verify PNG files don't contain alpha channel
- Test to verify JPEG files are properly saved as RGB

### Changed
- Unified image saving logic to always convert RGBA canvas to RGB before saving
- Both PNG and JPEG outputs now use the same RGB conversion process

### Testing
- All 310 tests passing
- New tests specifically verify no alpha channel in generated images
- All linters passing (black, isort, flake8, mypy)

## [0.10.1] - 2025-10-31

### Fixed
- **CRITICAL**: Fixed device field default value bug that was silently overriding user-specified device values from YAML files
- The `device` field now properly requires explicit configuration instead of using a hardcoded default
- Users must ensure their YAML configs include the `device` field inside the `project:` section

### Changed
- Made `device` field required in `ProjectInfo` to prevent configuration issues
- Updated all test fixtures to include explicit device field
- All 308 tests passing

### Testing
- Verified fix with real-world Boxy YAML config files
- Confirmed proper validation errors when device field is missing
- All linters passing (black, isort, flake8, mypy)

## [0.10.0] - 2025-10-31

### Changed
- **BREAKING**: Simplified configuration structure - `device` and `output_size` moved from per-screenshot to project level
- `device` now set once in `project:` section (default: "iPhone 15 Pro Portrait")
- `output_size` now set once in `project:` section (default: "iPhone6_9")
- One YAML file = one device/size combination for clearer project organization
- Relaxed mypy type checking configuration for better maintainability
- All linters passing (black, isort, flake8, mypy)

### Added
- App Store standard screenshot sizes with friendly names (iPhone6_9, iPhone6_7, iPadPro12_9, etc.)
- `appstore_sizes.json` with 8 predefined screenshot dimensions
- `kou list-sizes` command to display all available App Store sizes with descriptions
- Named size resolution system - use "iPhone6_9" or custom tuple [1320, 2868]
- Automatic size validation and conversion via Pydantic validators

### Fixed
- Screenshot output now matches App Store required dimensions (screen-only, not full frame with bezel)
- Canvas sizing now uses project-level `output_size` instead of frame PNG dimensions
- Type annotation compatibility issues across codebase

### Migration Guide
**Old config** (multiple devices per file):
```yaml
project:
  name: "My App"
  output_dir: "output"
devices:
  - "iPhone 15 Pro Portrait"
  - "iPad Pro 12.9-inch Portrait"
```

**New config** (single device per file):
```yaml
project:
  name: "My App"
  output_dir: "output"
  device: "iPhone 15 Pro Portrait"
  output_size: "iPhone6_9"
```

For multiple devices, create separate YAML files (e.g., `iphone-6-9.yaml`, `ipad-pro.yaml`)

## [0.9.0] - 2025-10-31

### Added
- Localized asset support with hybrid approach (convention-based and explicit mapping)
- `resolve_localized_asset()` function for automatic language-specific asset resolution
- Convention-based asset resolution using `{lang}/` directory pattern
- Explicit per-language asset mapping with dict format `{"en": "path/en.png", "es": "path/es.png"}`
- Fallback chain: explicit mapping → lang directory → base_lang directory → direct path
- Comprehensive unit and integration tests for localized assets
- Dependency analyzer support for dict-based asset tracking

### Changed
- `ContentItem.asset` field now accepts both string and dict formats for maximum flexibility
- Enhanced asset resolution to work seamlessly with multi-language projects

## [0.8.4] - 2025-10-30

### Fixed
- Device frame rendering with automatic screen bounds detection using flood fill algorithm
- Asset overflow at rounded corners with anti-aliased alpha channel masking
- Blank space between assets and device frames
- Smooth rounded corners preserved with alpha threshold of 50 for bezel separation

### Changed
- Replaced manual screen_bounds metadata with automatic detection
- Improved mask generation using alpha channel inversion instead of binary flood fill
- Enhanced type annotations and fixed all linting issues (black, isort, flake8, mypy)

### Added
- Comprehensive tests for flood fill algorithm and anti-aliased masking
- Test coverage for automatic screen bounds detection and aspect ratio preservation

## [0.8.3] - 2024-12-12

### Fixed
- Release workflow now uses mindsers/changelog-reader-action for reliable changelog extraction
- Release notes now display actual changelog content instead of fallback message

## [0.8.2] - 2024-12-12

### Added
- App Store Connect upload with `--mode` flag for replace/append control (default: replace)
- Upload mode documentation in README

### Fixed
- **CRITICAL**: Generator now always creates device subdirectories for proper App Store upload detection
- DeviceMapper loads dimensions dynamically from Sizes.json instead of hardcoded values
- CLI guidance now shows correct `kou generate` command instead of `kou`
- Updated example configs (basic_example.yaml, advanced_example.yaml) to new schema
- Updated tests to expect device subdirectories in output structure
- App Store upload now works correctly for both single-language and multi-language projects

## [0.8.1] - 2024-12-XX

### Fixed
- Multi-device screenshot generation with localization support
- CI test and lint failures after multi-device support

## [0.8.0] - 2024-12-XX

### Added
- Comprehensive rotation support for images and text
- `rotation` parameter for content items (e.g., `rotation: 15` for 15 degrees clockwise)

## [0.7.0] - 2024-XX-XX

### Fixed
- Removed unnecessary f-string placeholders to resolve flake8 errors
- CI issues and security alerts cleanup
- Applied Black formatting to resolve CI linting issues

### Added
- Comprehensive App Store Connect screenshot upload integration

## [0.6.1] - 2024-XX-XX

### Added
- Comprehensive multi-language localization support

## [0.6.0] - 2024-XX-XX

### Added
- Multi-language localization support with xcstrings format
- Automatic xcstrings file generation and updates
- Language-specific screenshot generation (e.g., `output/en/device/screenshot.png`)
- Live editing with localization support

## [0.5.9] - 2024-XX-XX

### Added
- `kou list-frames` command with fuzzy search capability
- Search filter support for finding specific device frames

## [0.5.8] - 2024-XX-XX

### Added
- Multi-image layer support for complex screenshot compositions

## [0.5.7] - 2024-XX-XX

### Fixed
- PNG asset inclusion in package distribution
- Path resolution for frame files

## [0.5.6] - 2024-XX-XX

### Fixed
- All device frame PNG files now properly included in production installations
- Strict error handling - no more silent fallbacks when frames are missing

### Added
- Screenshot-level frame control (`frame: false` to disable per screenshot)

### Improved
- Better error messages when configuration issues occur

## [0.5.5] - 2024-XX-XX

### Fixed
- Test failures and improved frame handling

## [0.5.4] - 2024-XX-XX

### Fixed
- Added MANIFEST.in to include PNG files in source distribution

## [0.5.3] - 2024-XX-XX

### Fixed
- Include PNG frame files in package and remove silent fallbacks

## [0.5.2] - 2024-XX-XX

### Fixed
- Line length violations in config.py

## [0.5.1] - 2024-XX-XX

### Changed
- Comprehensive v0.5.0 documentation update and test fixes

## [0.5.0] - 2024-XX-XX

### Added
- **Live editing mode** - Real-time screenshot regeneration with `kou live` command
- Smart change detection for YAML config and referenced assets
- Selective regeneration for affected screenshots only
- Dependency tracking for automatic asset monitoring
- Debounced updates to prevent excessive regeneration

### Fixed
- Removed artificial canvas bounds limitation for device frames

## [0.4.8] - 2024-XX-XX

### Changed
- Added no_fork parameter to push Homebrew formula directly without PRs

## [0.4.0-0.4.7] - 2024-XX-XX

### Added
- Homebrew distribution support via bitomule/tap
- Automated Homebrew formula updates in release workflow

### Fixed
- Various Homebrew integration issues and configuration tweaks

## [0.3.0] - 2024-XX-XX

### Changed
- Restructured CLI to support both global options and subcommands
- Resolved linting issues and improved CLI test coverage

## [0.2.0] - 2024-XX-XX

### Changed
- Simplified CLI to ultra-minimal interface
- Finalized Homebrew Releaser integration

## [0.1.0] - 2024-XX-XX

### Added
- Unified gradient system with per-screenshot background control
- Gradient text rendering with enhanced quality
- Dynamic version detection from git tags

### Fixed
- CI issues with fonts and imports
- Applied Black formatting across codebase

## [0.0.4] - 2024-XX-XX

### Fixed
- Used valid PyPI classifier for package metadata

## [0.0.3] - 2024-XX-XX

### Fixed
- Excluded checksums.txt from PyPI upload

## [0.0.2] - 2024-XX-XX

### Changed
- Testing release process improvements

## [0.0.1] - 2024-XX-XX

### Added
- Initial Koubou implementation
- Device frame system with 100+ frames (iPhone, iPad, Mac, Watch)
- Professional gradient backgrounds (linear, radial, conic)
- Advanced typography with stroke, alignment, and wrapping
- YAML-first configuration with content-based API
- Batch screenshot processing
- PyPI distribution
- GitHub Actions CI/CD pipeline

[Unreleased]: https://github.com/bitomule/koubou/compare/v0.11.1...HEAD
[0.11.1]: https://github.com/bitomule/koubou/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/bitomule/koubou/compare/v0.10.3...v0.11.0
[0.10.3]: https://github.com/bitomule/koubou/compare/v0.10.2...v0.10.3
[0.10.2]: https://github.com/bitomule/koubou/compare/v0.10.1...v0.10.2
[0.10.1]: https://github.com/bitomule/koubou/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/bitomule/koubou/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/bitomule/koubou/compare/v0.8.3...v0.9.0
[0.8.3]: https://github.com/bitomule/koubou/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/bitomule/koubou/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/bitomule/koubou/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/bitomule/koubou/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/bitomule/koubou/compare/v0.6.1...v0.7.0
[0.6.1]: https://github.com/bitomule/koubou/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/bitomule/koubou/compare/v0.5.9...v0.6.0
[0.5.9]: https://github.com/bitomule/koubou/compare/v0.5.8...v0.5.9
[0.5.8]: https://github.com/bitomule/koubou/compare/v0.5.7...v0.5.8
[0.5.7]: https://github.com/bitomule/koubou/compare/v0.5.6...v0.5.7
[0.5.6]: https://github.com/bitomule/koubou/compare/v0.5.5...v0.5.6
[0.5.5]: https://github.com/bitomule/koubou/compare/v0.5.4...v0.5.5
[0.5.4]: https://github.com/bitomule/koubou/compare/v0.5.3...v0.5.4
[0.5.3]: https://github.com/bitomule/koubou/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/bitomule/koubou/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/bitomule/koubou/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/bitomule/koubou/compare/v0.4.8...v0.5.0
[0.4.8]: https://github.com/bitomule/koubou/compare/v0.4.7...v0.4.8
[0.3.0]: https://github.com/bitomule/koubou/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/bitomule/koubou/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/bitomule/koubou/compare/v0.0.4...v0.1.0
[0.0.4]: https://github.com/bitomule/koubou/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/bitomule/koubou/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/bitomule/koubou/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/bitomule/koubou/releases/tag/v0.0.1
