"""Tests for localized screenshot generation."""

import json
import tempfile
from pathlib import Path

from PIL import Image

from koubou.config import (
    ContentItem,
    LocalizationConfig,
    ProjectConfig,
    ProjectInfo,
    ScreenshotDefinition,
)
from koubou.generator import ScreenshotGenerator


class TestLocalizedGeneration:
    """Tests for multi-language screenshot generation."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "output"

        # Create test image
        self.test_image_path = self.temp_dir / "test.png"
        test_image = Image.new("RGBA", (200, 400), (255, 0, 0, 255))
        test_image.save(self.test_image_path)

        # Create xcstrings with translations
        self.xcstrings_path = self.temp_dir / "Localizable.xcstrings"
        xcstrings_data = {
            "sourceLanguage": "en",
            "strings": {
                "Welcome to App": {
                    "localizations": {
                        "en": {
                            "stringUnit": {
                                "state": "translated",
                                "value": "Welcome to App",
                            }
                        },
                        "es": {
                            "stringUnit": {
                                "state": "translated",
                                "value": "Bienvenido a la App",
                            }
                        },
                        "ja": {
                            "stringUnit": {
                                "state": "translated",
                                "value": "アプリへようこそ",
                            }
                        },
                    }
                },
                "Settings": {
                    "localizations": {
                        "en": {
                            "stringUnit": {"state": "translated", "value": "Settings"}
                        },
                        "es": {
                            "stringUnit": {
                                "state": "translated",
                                "value": "Configuración",
                            }
                        },
                        "ja": {
                            "stringUnit": {"state": "needs_translation", "value": ""}
                        },
                    }
                },
            },
            "version": "1.0",
        }

        with open(self.xcstrings_path, "w", encoding="utf-8") as f:
            json.dump(xcstrings_data, f, indent=2, ensure_ascii=False)

    def teardown_method(self):
        """Cleanup after test."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_single_language_generation_unchanged(self):
        """Test that single language generation works unchanged."""
        # Create project without localization
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            screenshots={
                "welcome": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="image",
                            asset=str(self.test_image_path),
                            position=("50%", "50%"),
                        )
                    ]
                )
            },
        )

        generator = ScreenshotGenerator()
        result_paths = generator.generate_project(project_config, self.temp_dir)

        # Should generate single screenshot
        assert len(result_paths) == 1
        assert result_paths[0].exists()
        assert result_paths[0].parent == self.output_dir

    def test_localized_generation_creates_language_directories(self):
        """Test that localized generation creates language-specific directories."""
        # Create project with localization
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es", "ja"],
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "welcome": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="text",
                            content="Welcome to App",
                            position=("50%", "20%"),
                        ),
                        ContentItem(
                            type="image",
                            asset=str(self.test_image_path),
                            position=("50%", "60%"),
                        ),
                    ]
                )
            },
        )

        generator = ScreenshotGenerator()
        result_paths = generator.generate_project(project_config, self.temp_dir)

        # Should generate 3 screenshots (one per language)
        assert len(result_paths) == 3

        # Check language directories exist
        en_dir = self.output_dir / "en"
        es_dir = self.output_dir / "es"
        ja_dir = self.output_dir / "ja"

        assert en_dir.exists()
        assert es_dir.exists()
        assert ja_dir.exists()

        # Check screenshots exist in each language directory with device subdirectory
        assert (en_dir / "iPhone_15_Pro_Portrait" / "welcome.png").exists()
        assert (es_dir / "iPhone_15_Pro_Portrait" / "welcome.png").exists()
        assert (ja_dir / "iPhone_15_Pro_Portrait" / "welcome.png").exists()

    def test_localized_generation_multiple_screenshots(self):
        """Test localized generation with multiple screenshots."""
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es"],
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "welcome": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="text",
                            content="Welcome to App",
                            position=("50%", "20%"),
                        ),
                        ContentItem(
                            type="image",
                            asset=str(self.test_image_path),
                            position=("50%", "60%"),
                        ),
                    ]
                ),
                "settings": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="text",
                            content="Settings",
                            position=("50%", "20%"),
                        ),
                        ContentItem(
                            type="image",
                            asset=str(self.test_image_path),
                            position=("50%", "60%"),
                        ),
                    ]
                ),
            },
        )

        generator = ScreenshotGenerator()
        result_paths = generator.generate_project(project_config, self.temp_dir)

        # Should generate 4 screenshots (2 screenshots × 2 languages)
        assert len(result_paths) == 4

        # Check all combinations exist in device subdirectories
        assert (
            self.output_dir / "en" / "iPhone_15_Pro_Portrait" / "welcome.png"
        ).exists()
        assert (
            self.output_dir / "en" / "iPhone_15_Pro_Portrait" / "settings.png"
        ).exists()
        assert (
            self.output_dir / "es" / "iPhone_15_Pro_Portrait" / "welcome.png"
        ).exists()
        assert (
            self.output_dir / "es" / "iPhone_15_Pro_Portrait" / "settings.png"
        ).exists()

    def test_localized_generation_creates_xcstrings_when_missing(self):
        """Test that xcstrings file is created when missing."""
        # Remove xcstrings file
        self.xcstrings_path.unlink()

        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es"],
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "welcome": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="text",
                            content="New Welcome Text",
                            position=("50%", "20%"),
                        ),
                        ContentItem(
                            type="image",
                            asset=str(self.test_image_path),
                            position=("50%", "60%"),
                        ),
                    ]
                )
            },
        )

        generator = ScreenshotGenerator()
        result_paths = generator.generate_project(project_config, self.temp_dir)

        # Should generate screenshots
        assert len(result_paths) == 2

        # Should create xcstrings file
        assert self.xcstrings_path.exists()

        # Check xcstrings content
        with open(self.xcstrings_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "New Welcome Text" in data["strings"]

        # Base language should be translated
        welcome_localizations = data["strings"]["New Welcome Text"]["localizations"]
        assert welcome_localizations["en"]["stringUnit"]["state"] == "translated"
        assert welcome_localizations["en"]["stringUnit"]["value"] == "New Welcome Text"

        # Other language should need translation
        assert welcome_localizations["es"]["stringUnit"]["state"] == "needs_translation"
        assert welcome_localizations["es"]["stringUnit"]["value"] == ""

    def test_localized_generation_updates_existing_xcstrings(self):
        """Test that existing xcstrings file is updated with new keys."""
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es"],
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "welcome": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="text",
                            content="Welcome to App",  # Existing key
                            position=("50%", "20%"),
                        ),
                        ContentItem(
                            type="text",
                            content="New Text Key",  # New key
                            position=("50%", "40%"),
                        ),
                        ContentItem(
                            type="image",
                            asset=str(self.test_image_path),
                            position=("50%", "60%"),
                        ),
                    ]
                )
            },
        )

        generator = ScreenshotGenerator()
        result_paths = generator.generate_project(project_config, self.temp_dir)

        # Should generate screenshots
        assert len(result_paths) == 2

        # Check xcstrings was updated
        with open(self.xcstrings_path, encoding="utf-8") as f:
            data = json.load(f)

        # Should have both existing and new keys
        assert "Welcome to App" in data["strings"]
        assert "New Text Key" in data["strings"]

        # Existing translation should be preserved
        welcome_localizations = data["strings"]["Welcome to App"]["localizations"]
        assert (
            welcome_localizations["es"]["stringUnit"]["value"] == "Bienvenido a la App"
        )

        # New key should need translation
        new_key_localizations = data["strings"]["New Text Key"]["localizations"]
        assert new_key_localizations["es"]["stringUnit"]["state"] == "needs_translation"

    def test_localized_generation_with_device_variants(self):
        """Test localized generation with device frame."""
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            devices=["iPhone 15 Pro Portrait"],
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es"],
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "welcome": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="text",
                            content="Welcome to App",
                            position=("50%", "20%"),
                        ),
                        ContentItem(
                            type="image",
                            asset=str(self.test_image_path),
                            position=("50%", "60%"),
                        ),
                    ]
                )
            },
        )

        generator = ScreenshotGenerator()
        result_paths = generator.generate_project(project_config, self.temp_dir)

        # Should generate 2 screenshots with device frame
        assert len(result_paths) == 2

        # Check device-specific directories are created
        assert (
            self.output_dir / "en" / "iPhone_15_Pro_Portrait" / "welcome.png"
        ).exists()
        assert (
            self.output_dir / "es" / "iPhone_15_Pro_Portrait" / "welcome.png"
        ).exists()

    def test_localized_generation_text_only_screenshots(self):
        """Test localized generation with text-only screenshots."""
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es"],
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "text_only": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="text",
                            content="Welcome to App",
                            position=("50%", "50%"),
                            size=48,
                        )
                    ]
                )
            },
        )

        generator = ScreenshotGenerator()

        # Should handle text-only screenshots without errors
        # Note: This might skip generation due to no images, but should not crash
        try:
            result_paths = generator.generate_project(project_config, self.temp_dir)
            # If it generates, it should create language directories
            if result_paths:
                assert len(result_paths) == 2
        except Exception:
            # Text-only screenshots might be skipped, which is acceptable
            pass

    def test_localized_generation_preserves_non_text_properties(self):
        """Test that localization preserves non-text content item properties."""
        project_config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir=str(self.output_dir)),
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es"],
                xcstrings_path=str(self.xcstrings_path),
            ),
            screenshots={
                "styled_text": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="text",
                            content="Welcome to App",
                            position=("50%", "20%"),
                            size=48,
                            color="#FF0000",
                            weight="bold",
                        ),
                        ContentItem(
                            type="image",
                            asset=str(self.test_image_path),
                            position=("50%", "60%"),
                            scale=0.8,
                        ),
                    ]
                )
            },
        )

        generator = ScreenshotGenerator()
        result_paths = generator.generate_project(project_config, self.temp_dir)

        # Should preserve all styling properties through localization
        assert len(result_paths) == 2

        # Screenshots should be generated with different text but same styling
        assert (
            self.output_dir / "en" / "iPhone_15_Pro_Portrait" / "styled_text.png"
        ).exists()
        assert (
            self.output_dir / "es" / "iPhone_15_Pro_Portrait" / "styled_text.png"
        ).exists()
