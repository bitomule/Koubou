"""Tests for live mode localization functionality."""

import json
import tempfile
import time
from pathlib import Path

import yaml
from PIL import Image

from koubou.live_generator import LiveScreenshotGenerator


class TestLiveLocalization:
    """Tests for live mode with localization support."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "test_config.yaml"
        self.xcstrings_file = self.temp_dir / "Localizable.xcstrings"
        self.output_dir = self.temp_dir / "output"

        # Create test image
        self.test_image_path = self.temp_dir / "test.png"
        test_image = Image.new("RGBA", (200, 400), (255, 0, 0, 255))
        test_image.save(self.test_image_path)

        # Create initial config with localization
        self.config_data = {
            "project": {
                "name": "Live Localization Test",
                "output_dir": str(self.output_dir),
            },
            "localization": {
                "base_language": "en",
                "languages": ["en", "es"],
                "xcstrings_path": str(self.xcstrings_file),
            },
            "screenshots": {
                "welcome": {
                    "content": [
                        {
                            "type": "text",
                            "content": "Welcome",
                            "position": ["50%", "20%"],
                        },
                        {
                            "type": "image",
                            "asset": str(self.test_image_path),
                            "position": ["50%", "60%"],
                        },
                    ]
                }
            },
        }

        with open(self.config_file, "w") as f:
            yaml.dump(self.config_data, f)

        # Create initial xcstrings
        xcstrings_data = {
            "sourceLanguage": "en",
            "strings": {
                "Welcome": {
                    "localizations": {
                        "en": {
                            "stringUnit": {"state": "translated", "value": "Welcome"}
                        },
                        "es": {
                            "stringUnit": {"state": "translated", "value": "Bienvenido"}
                        },
                    }
                }
            },
            "version": "1.0",
        }

        with open(self.xcstrings_file, "w", encoding="utf-8") as f:
            json.dump(xcstrings_data, f, indent=2, ensure_ascii=False)

    def teardown_method(self):
        """Cleanup after test."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_live_generator_loads_localized_config(self):
        """Test that live generator loads localized configuration properly."""
        generator = LiveScreenshotGenerator(self.config_file)
        config = generator.load_config()

        assert config is not None
        assert config.localization is not None
        assert config.localization.base_language == "en"
        assert config.localization.languages == ["en", "es"]

    def test_live_generator_includes_xcstrings_in_asset_paths(self):
        """Test that xcstrings file is included in watched asset paths."""
        generator = LiveScreenshotGenerator(self.config_file)
        generator.current_config = generator.load_config()

        asset_paths = generator.get_asset_paths()

        # Should include xcstrings file
        assert self.xcstrings_file in asset_paths

    def test_live_generator_without_localization_excludes_xcstrings(self):
        """Test that xcstrings is not watched when localization is disabled."""
        # Create config without localization
        config_without_localization = {
            "project": {
                "name": "No Localization Test",
                "output_dir": str(self.output_dir),
            },
            "screenshots": {
                "test": {
                    "content": [
                        {
                            "type": "image",
                            "asset": str(self.test_image_path),
                            "position": ["50%", "50%"],
                        }
                    ]
                }
            },
        }

        config_file_no_loc = self.temp_dir / "no_localization.yaml"
        with open(config_file_no_loc, "w") as f:
            yaml.dump(config_without_localization, f)

        generator = LiveScreenshotGenerator(config_file_no_loc)
        generator.current_config = generator.load_config()

        asset_paths = generator.get_asset_paths()

        # Should not include xcstrings file
        assert self.xcstrings_file not in asset_paths

    def test_initial_generation_with_localization(self):
        """Test initial generation creates localized screenshots."""
        generator = LiveScreenshotGenerator(self.config_file)
        result = generator.initial_generation()

        # Should succeed
        assert not result.has_errors
        assert result.success_count == 2  # 2 languages

        # Should create language-specific directories
        assert (self.output_dir / "en" / "welcome.png").exists()
        assert (self.output_dir / "es" / "welcome.png").exists()

    def test_xcstrings_change_triggers_regeneration(self):
        """Test that changes to xcstrings file trigger regeneration."""
        generator = LiveScreenshotGenerator(self.config_file)

        # Initial generation
        initial_result = generator.initial_generation()
        assert not initial_result.has_errors
        assert initial_result.success_count == 2

        # Get initial modification times
        en_file = self.output_dir / "en" / "welcome.png"
        es_file = self.output_dir / "es" / "welcome.png"

        initial_en_mtime = en_file.stat().st_mtime
        initial_es_mtime = es_file.stat().st_mtime

        # Wait to ensure different timestamps
        time.sleep(0.1)

        # Update xcstrings file
        updated_xcstrings = {
            "sourceLanguage": "en",
            "strings": {
                "Welcome": {
                    "localizations": {
                        "en": {
                            "stringUnit": {"state": "translated", "value": "Welcome"}
                        },
                        "es": {
                            "stringUnit": {
                                "state": "translated",
                                "value": "¡Bienvenido!",  # Changed translation
                            }
                        },
                    }
                }
            },
            "version": "1.0",
        }

        with open(self.xcstrings_file, "w", encoding="utf-8") as f:
            json.dump(updated_xcstrings, f, indent=2, ensure_ascii=False)

        # Handle xcstrings change
        changed_files = {self.xcstrings_file}
        result = generator.handle_file_changes(changed_files)

        # Should regenerate all screenshots
        assert len(result.regenerated_screenshots) == 1  # One screenshot definition
        assert "welcome" in result.regenerated_screenshots
        assert not result.has_errors

        # Files should be updated
        new_en_mtime = en_file.stat().st_mtime
        new_es_mtime = es_file.stat().st_mtime

        assert new_en_mtime > initial_en_mtime
        assert new_es_mtime > initial_es_mtime

    def test_config_change_with_new_text_updates_xcstrings(self):
        """Test that config changes with new text update xcstrings file."""
        generator = LiveScreenshotGenerator(self.config_file)

        # Initial generation
        initial_result = generator.initial_generation()
        assert not initial_result.has_errors

        # Read initial xcstrings
        with open(self.xcstrings_file, encoding="utf-8") as f:
            initial_xcstrings = json.load(f)

        assert len(initial_xcstrings["strings"]) == 1
        assert "Welcome" in initial_xcstrings["strings"]

        # Update config with new text
        self.config_data["screenshots"]["welcome"]["content"].append(
            {
                "type": "text",
                "content": "New Text Key",
                "position": ["50%", "40%"],
            }
        )

        with open(self.config_file, "w") as f:
            yaml.dump(self.config_data, f)

        # Handle config change
        changed_files = {self.config_file}
        result = generator.handle_file_changes(changed_files)

        # Should regenerate screenshots
        assert (
            "welcome" in result.regenerated_screenshots
            or "*ALL*" in result.regenerated_screenshots
        )

        # XCStrings should be updated
        with open(self.xcstrings_file, encoding="utf-8") as f:
            updated_xcstrings = json.load(f)

        assert len(updated_xcstrings["strings"]) == 2
        assert "Welcome" in updated_xcstrings["strings"]
        assert "New Text Key" in updated_xcstrings["strings"]

        # New key should need translation for Spanish
        new_key_data = updated_xcstrings["strings"]["New Text Key"]
        es_localization = new_key_data["localizations"]["es"]
        assert es_localization["stringUnit"]["state"] == "needs_translation"

    def test_regular_asset_change_with_localization(self):
        """Test that regular asset changes work normally with localization enabled."""
        generator = LiveScreenshotGenerator(self.config_file)

        # Initial generation
        initial_result = generator.initial_generation()
        assert not initial_result.has_errors

        # Wait to ensure different timestamps
        time.sleep(0.1)

        # Update test image (simulate asset change)
        updated_image = Image.new(
            "RGBA", (200, 400), (0, 255, 0, 255)
        )  # Green instead of red
        updated_image.save(self.test_image_path)

        # Handle asset change
        changed_files = {self.test_image_path}
        result = generator.handle_file_changes(changed_files)

        # Should regenerate affected screenshots
        assert "welcome" in result.regenerated_screenshots
        assert not result.has_errors

        # Both language versions should be updated
        assert (self.output_dir / "en" / "welcome.png").exists()
        assert (self.output_dir / "es" / "welcome.png").exists()

    def test_nonexistent_xcstrings_file_gets_created(self):
        """Test that missing xcstrings file gets created during live generation."""
        # Remove xcstrings file
        self.xcstrings_file.unlink()

        generator = LiveScreenshotGenerator(self.config_file)
        result = generator.initial_generation()

        # Should succeed and create xcstrings file
        assert not result.has_errors
        assert result.success_count == 2
        assert self.xcstrings_file.exists()

        # Check created xcstrings content
        with open(self.xcstrings_file, encoding="utf-8") as f:
            data = json.load(f)

        assert "Welcome" in data["strings"]
        assert data["sourceLanguage"] == "en"

    def test_live_generator_handles_mixed_changes(self):
        """Test handling of simultaneous config, xcstrings, and asset changes."""
        generator = LiveScreenshotGenerator(self.config_file)

        # Initial generation
        initial_result = generator.initial_generation()
        assert not initial_result.has_errors

        # Wait for timestamp differences
        time.sleep(0.1)

        # Make multiple simultaneous changes

        # 1. Update config
        self.config_data["screenshots"]["settings"] = {
            "content": [
                {
                    "type": "text",
                    "content": "Settings",
                    "position": ["50%", "30%"],
                },
                {
                    "type": "image",
                    "asset": str(self.test_image_path),
                    "position": ["50%", "70%"],
                },
            ]
        }

        with open(self.config_file, "w") as f:
            yaml.dump(self.config_data, f)

        # 2. Update xcstrings
        updated_xcstrings = {
            "sourceLanguage": "en",
            "strings": {
                "Welcome": {
                    "localizations": {
                        "en": {
                            "stringUnit": {"state": "translated", "value": "Welcome"}
                        },
                        "es": {
                            "stringUnit": {
                                "state": "translated",
                                "value": "¡Hola!",  # Changed
                            }
                        },
                    }
                }
            },
            "version": "1.0",
        }

        with open(self.xcstrings_file, "w", encoding="utf-8") as f:
            json.dump(updated_xcstrings, f, indent=2, ensure_ascii=False)

        # 3. Update asset
        updated_image = Image.new("RGBA", (200, 400), (0, 0, 255, 255))  # Blue
        updated_image.save(self.test_image_path)

        # Handle all changes together
        changed_files = {self.config_file, self.xcstrings_file, self.test_image_path}
        result = generator.handle_file_changes(changed_files)

        # Should handle all changes and regenerate everything
        assert not result.has_errors

        # All screenshots should be updated
        expected_screenshots = {"welcome", "settings"}  # Both should be regenerated
        actual_screenshots = set(result.regenerated_screenshots)

        # Either specific screenshots or global regeneration
        assert (
            actual_screenshots.issuperset(expected_screenshots)
            or "*ALL*" in result.regenerated_screenshots
        )

    def test_live_generator_dependency_summary_includes_localization(self):
        """Test that dependency summary includes localization information."""
        generator = LiveScreenshotGenerator(self.config_file)
        generator.current_config = generator.load_config()

        summary = generator.get_dependency_summary()

        # Should include dependency information
        assert "total_dependencies" in summary
        assert "total_screenshots" in summary

        # With localization, should track more dependencies
        assert summary["total_screenshots"] >= 1
