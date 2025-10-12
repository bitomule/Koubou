# Changelog

All notable changes to Koubou will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/bitomule/koubou/compare/v0.8.2...HEAD
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
