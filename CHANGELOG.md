# Changelog

All notable changes to Koubou will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.19.3] - 2026-05-03

### Fixed
- Transparent screenshot backgrounds now support `background.type: "transparent"` and preserve PNG alpha when backgrounds use 8-digit hex colors such as `#00000000`.

## [0.19.2] - 2026-04-17

### Fixed
- `kou install-skills` now installs to global agent directories (`~/.claude/skills/`, `~/.cursor/rules/`, etc.) instead of the current project directory.

## [0.19.1] - 2026-04-17

### Added
- `kou install-skills` command — installs the Koubou skill pack to all detected AI coding agents (Claude Code, Cursor, Windsurf, and 40+ others) via `npx skills`. Supports `--yes` for non-interactive installs and `--agent` to target a specific agent.
- `data-kou-id` and `data-kou-role` annotations added to all HTML template examples in `design-guide.md` so agents copy the correct annotation pattern by default.
- Annotation requirement elevated to a hard constraint in SKILL.md — templates with empty layout sidecars are now a QA blocker.

## [0.19.0] - 2026-04-17

### Added
- HTML template screenshots now emit a compact `<screenshot_id>.layout.json` sidecar with normalized element geometry, optional metadata, and mathematical overlaps for annotated `data-kou-id` elements.
- `kou generate --output json` now includes `layout_path` for HTML screenshots so agents and tooling can read the measured layout sidecar directly.
- README, YAML API docs, and Koubou skill documentation now describe the layout JSON workflow, annotation strategy, and agent-facing usage.

### Changed
- **BREAKING**: Project content `alignment` now controls the true horizontal anchor for text and image items. Configs that relied on the previous inconsistent semantics may need their `position.x` values adjusted.
- Project image alignment now uses consistent left/center/right semantics for both framed and unframed assets.
- HTML layout measurement now waits for stylesheets, fonts, and images before extracting geometry, making sidecar output stable against load timing.
- HTML staging now copies template sibling files into the workspace to avoid `file://` CSS quirks during rendering.

### Testing
- 420 tests passing locally

## [0.18.3] - 2026-04-16

### Fixed
- HTML template screenshots now resolve `assets` with the same localization rules as content mode, so both `{lang}/path` conventions and explicit language mappings pick the correct asset per output language.
- Live preview now uses the same base-language fallback for template assets as final generation, keeping preview and exported screenshots aligned.
- `ScreenshotDefinition.assets` now accepts localized asset mappings for HTML templates, with regression tests covering string and dict-based localized resolution.

## [0.18.2] - 2026-04-02

### Fixed
- `position` values with pixel suffixes (e.g. `["100px", "50px"]`) now parse correctly in screenshot generation for both text and image content items.
- Mixed position formats (e.g. `["50%", "120px"]`) now work consistently.
- Added regression tests to prevent reintroducing pixel-position parsing failures in project generation.

## [0.18.1] - 2026-03-24

### Fixed
- iPhone Air native frames now auto-fit inside the requested output canvas, preventing bezel clipping at `iPhone6_9_alt` (`1260×2736`) and similar overflow cases
- Frame lookup now falls back to `src/koubou/frames` when running from a source checkout whose installed wheel does not bundle PNG frame assets
- Development builds no longer attempt impossible frame downloads for non-release version strings such as `0.1.dev1+g...`; they fail with a clearer source-checkout guidance instead

### Testing
- 405 tests passing locally

## [0.18.0] - 2026-03-21

### Added
- **iPhone 17 device frames**: iPhone 17, 17 Pro, 17 Pro Max, and iPhone Air in all available colors (portrait and landscape)
- **New App Store screenshot sizes**: `iPhone6_3` (1206×2622) for iPhone 17/17 Pro, `iPhone6_9_alt` (1260×2736) for iPhone Air
- **Apple Watch Ultra 2 & Ultra 3 frames**: Full set of band variants for both Black and Natural titanium finishes
- **Apple Watch S11 frames**: 42mm and 46mm sizes with Aluminum and Titanium finishes across all band options
- **iPhone 16 Plus frames**: All five colors (Black, Pink, Teal, Ultramarine, White) in portrait and landscape
- **Apple TV 4K frame**
- **MacBook frames**: MacBook Air 13 4th Gen Midnight, MacBook Pro M4 14" and 16" Silver
- Device frame renderer now handles single-segment model names (e.g., "17", "Air") for the new iPhone naming scheme
- **On-demand frame downloads**: Device frame PNGs are no longer bundled in the wheel — they are downloaded automatically on first `kou generate` and cached at `~/.koubou/frames/`. This reduces the PyPI package from 111MB to under 5MB.
- `kou setup-frames` command to explicitly download frames (mirrors `kou setup-html` pattern). Supports `--force` to re-download.
- Source installs (`pip install -e .`) still use local frames with no download needed

## [0.17.1] - 2026-03-16

### Fixed
- Device frame renderer logs now interpolate actual frame names, variants, and screen bounds instead of literal placeholder text when metadata lookup falls back or mask generation runs.

## [0.17.0] - 2026-03-13

### Added
- **Live preview dashboard for `kou live`**: Koubou now opens a local browser dashboard during live mode, showing screenshots in YAML order with per-slide hot reload.
- **Mixed preview support**: HTML screenshots render as live iframes while standard Koubou screenshots render as regenerated PNG previews in the same dashboard.
- **HTML preview staging**: Shared HTML staging now powers both the browser dashboard and final Playwright exports, keeping template siblings, generated assets, and live previews aligned.
- **Mac App Store desktop presets**: Added named `output_size` values for `AppDesktop_1280`, `AppDesktop_1440`, `AppDesktop_2560`, and `AppDesktop_2880`.
- **HTML project scaffolding**: `kou --create-config --mode html` now generates a runnable HTML sample project with `templates/` and sample assets.

### Changed
- `kou --create-config` now creates sample PNG assets alongside the generated YAML, so the default sample project works immediately without manual asset setup.
- `kou live` now provides a consistent preview experience for both HTML templates and the standard content pipeline.
- README and YAML API docs now document the live preview dashboard, mixed preview behavior, and the new `--mode html` sample workflow.

### Testing
- 388 tests passing
- Added coverage for the live preview dashboard, recursive HTML asset tracking, generated sample configs, and end-to-end HTML sample scaffolding

## [0.16.0] - 2026-03-12

### Added
- `kou inspect-frame` command to expose real device frame and screen geometry for layout work
- JSON and table output for frame inspection, including `canvas_class`, safe margins, coverage ratio, and screen bounds
- CLI tests covering `inspect-frame` with named and custom output sizes

### Changed
- README and Koubou skill documentation now describe a geometry-aware screenshot workflow
- Refreshed Undolly HTML example with stronger templates and YAML-driven copy variables
- Koubou skill guidance now separates hard constraints from strong defaults and taste heuristics to keep creativity flexible

## [0.15.1] - 2026-03-12

### Added
- `kou setup-html` command to prepare HTML rendering support in the current Koubou installation
- `--setup-html` flag for `kou generate` and `kou live`
- HTML environment checks and setup tests

### Changed
- Playwright is now installed as part of the base package instead of requiring a separate HTML extra
- HTML renderer errors now guide users to `kou setup-html` instead of `pip install ...`
- README and skill documentation now describe the built-in HTML setup flow for PyPI and Homebrew users

## [0.15.0] - 2026-03-12

### Added
- HTML template rendering mode with Playwright
- HTML template examples
- Koubou skill documentation for compatible coding agents

## [0.14.0] - 2026-02-25

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

[Unreleased]: https://github.com/bitomule/koubou/compare/v0.19.2...HEAD
[0.19.2]: https://github.com/bitomule/koubou/compare/v0.19.1...v0.19.2
[0.19.1]: https://github.com/bitomule/koubou/compare/v0.19.0...v0.19.1
[0.19.0]: https://github.com/bitomule/koubou/compare/v0.18.3...v0.19.0
[0.18.3]: https://github.com/bitomule/koubou/compare/v0.18.2...v0.18.3
[0.18.2]: https://github.com/bitomule/koubou/compare/v0.18.1...v0.18.2
[0.18.1]: https://github.com/bitomule/koubou/compare/v0.18.0...v0.18.1
[0.18.0]: https://github.com/bitomule/koubou/compare/v0.17.1...v0.18.0
[0.17.1]: https://github.com/bitomule/koubou/compare/v0.17.0...v0.17.1
[0.17.0]: https://github.com/bitomule/koubou/compare/v0.16.0...v0.17.0
[0.16.0]: https://github.com/bitomule/koubou/compare/v0.15.1...v0.16.0
[0.15.1]: https://github.com/bitomule/koubou/compare/v0.15.0...v0.15.1
[0.15.0]: https://github.com/bitomule/koubou/compare/v0.11.1...v0.15.0
[0.11.1]: https://github.com/bitomule/koubou/compare/v0.11.0...v0.11.1
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
