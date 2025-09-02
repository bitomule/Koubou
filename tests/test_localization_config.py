"""Tests for localization configuration integration."""

import tempfile

import pytest
import yaml

from koubou.config import (
    ContentItem,
    LocalizationConfig,
    ProjectConfig,
    ProjectInfo,
    ScreenshotDefinition,
)


class TestLocalizationConfigIntegration:
    """Tests for localization configuration integration with ProjectConfig."""

    def test_project_config_without_localization(self):
        """Test ProjectConfig without localization (backward compatibility)."""
        config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir="output"),
            screenshots={
                "test": ScreenshotDefinition(
                    content=[
                        ContentItem(type="text", content="Hello"),
                    ]
                )
            },
        )

        assert config.localization is None

    def test_project_config_with_localization(self):
        """Test ProjectConfig with localization configuration."""
        config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir="output"),
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es", "ja"],
                xcstrings_path="custom.xcstrings",
            ),
            screenshots={
                "test": ScreenshotDefinition(
                    content=[
                        ContentItem(type="text", content="Hello"),
                    ]
                )
            },
        )

        assert config.localization is not None
        assert config.localization.base_language == "en"
        assert config.localization.languages == ["en", "es", "ja"]
        assert config.localization.xcstrings_path == "custom.xcstrings"

    def test_yaml_parsing_without_localization(self):
        """Test YAML parsing without localization block."""
        yaml_content = """
        project:
          name: "Test Project"
          output_dir: "output"

        screenshots:
          welcome:
            content:
              - type: "text"
                content: "Welcome"
        """

        config_data = yaml.safe_load(yaml_content)
        config = ProjectConfig(**config_data)

        assert config.localization is None

    def test_yaml_parsing_with_localization(self):
        """Test YAML parsing with localization block."""
        yaml_content = """
        project:
          name: "Test Project"
          output_dir: "output"

        localization:
          base_language: "en"
          languages: ["en", "es", "ja"]
          xcstrings_path: "MyApp.xcstrings"

        screenshots:
          welcome:
            content:
              - type: "text"
                content: "Welcome to App"
              - type: "text"
                content: "Get Started"
        """

        config_data = yaml.safe_load(yaml_content)
        config = ProjectConfig(**config_data)

        assert config.localization is not None
        assert config.localization.base_language == "en"
        assert config.localization.languages == ["en", "es", "ja"]
        assert config.localization.xcstrings_path == "MyApp.xcstrings"

    def test_yaml_parsing_with_default_xcstrings_path(self):
        """Test YAML parsing with default xcstrings path."""
        yaml_content = """
        project:
          name: "Test Project"

        localization:
          base_language: "en"
          languages: ["en", "fr"]

        screenshots:
          test:
            content:
              - type: "text"
                content: "Test"
        """

        config_data = yaml.safe_load(yaml_content)
        config = ProjectConfig(**config_data)

        assert config.localization.xcstrings_path == "Localizable.xcstrings"

    def test_localization_validation_errors(self):
        """Test localization validation errors."""
        # Empty base language
        with pytest.raises(ValueError, match="Base language cannot be empty"):
            ProjectConfig(
                project=ProjectInfo(name="Test"),
                localization=LocalizationConfig(
                    base_language="",
                    languages=["en", "es"],
                ),
                screenshots={"test": ScreenshotDefinition(content=[])},
            )

        # Empty languages list
        with pytest.raises(ValueError, match="Languages list cannot be empty"):
            ProjectConfig(
                project=ProjectInfo(name="Test"),
                localization=LocalizationConfig(
                    base_language="en",
                    languages=[],
                ),
                screenshots={"test": ScreenshotDefinition(content=[])},
            )

        # Base language not in languages list
        with pytest.raises(
            ValueError, match="Base language 'en' must be included in languages list"
        ):
            ProjectConfig(
                project=ProjectInfo(name="Test"),
                localization=LocalizationConfig(
                    base_language="en",
                    languages=["es", "fr"],
                ),
                screenshots={"test": ScreenshotDefinition(content=[])},
            )

    def test_complex_localization_config(self):
        """Test complex localization configuration with full project."""
        yaml_content = """
        project:
          name: "Multi-Language App Screenshots"
          output_dir: "Screenshots/Generated"

        devices:
          - "iPhone 15 Pro Portrait"
          - "iPad Pro 12.9-inch Portrait"

        defaults:
          background:
            type: "linear"
            colors: ["#E8F0FE", "#F8FBFF"]
            direction: 180

        localization:
          base_language: "en"
          languages: ["en", "es", "ja", "fr", "de"]
          xcstrings_path: "AppScreenshots.xcstrings"

        screenshots:
          welcome_screen:
            content:
              - type: "text"
                content: "Welcome to Amazing App"
                position: ["50%", "15%"]
                size: 48
                color: "#8E4EC6"
                weight: "bold"
              - type: "text"
                content: "Transform your workflow today"
                position: ["50%", "25%"]
                size: 24
                color: "#1A73E8"
              - type: "image"
                asset: "screenshots/home.png"
                position: ["50%", "60%"]
                scale: 0.6
                frame: true

          features_screen:
            content:
              - type: "text"
                content: "✨ Amazing Features"
                position: ["50%", "10%"]
                size: 42
                color: "#8E4EC6"
                weight: "bold"
              - type: "text"
                content: "Discover what makes us different"
                position: ["50%", "20%"]
                size: 20
              - type: "image"
                asset: "screenshots/features.png"
                position: ["50%", "65%"]
                scale: 0.5
                frame: true
        """

        config_data = yaml.safe_load(yaml_content)
        config = ProjectConfig(**config_data)

        # Validate full configuration
        assert config.project.name == "Multi-Language App Screenshots"
        assert len(config.devices) == 2
        assert config.defaults is not None
        assert config.localization is not None
        assert len(config.localization.languages) == 5
        assert len(config.screenshots) == 2

        # Validate specific localization settings
        loc = config.localization
        assert loc.base_language == "en"
        assert "ja" in loc.languages
        assert loc.xcstrings_path == "AppScreenshots.xcstrings"

    def test_localization_with_relative_paths(self):
        """Test localization with relative xcstrings path."""
        with tempfile.TemporaryDirectory():
            config = ProjectConfig(
                project=ProjectInfo(name="Test Project", output_dir="output"),
                localization=LocalizationConfig(
                    base_language="en",
                    languages=["en", "es"],
                    xcstrings_path="localization/MyApp.xcstrings",
                ),
                screenshots={
                    "test": ScreenshotDefinition(
                        content=[ContentItem(type="text", content="Hello")]
                    )
                },
            )

            # Should handle relative paths properly
            assert config.localization.xcstrings_path == "localization/MyApp.xcstrings"

    def test_localization_config_serialization(self):
        """Test that localization config can be serialized/deserialized."""
        config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir="output"),
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es", "ja"],
                xcstrings_path="test.xcstrings",
            ),
            screenshots={
                "test": ScreenshotDefinition(
                    content=[ContentItem(type="text", content="Hello")]
                )
            },
        )

        # Convert to dict and back
        config_dict = config.dict()
        reconstructed_config = ProjectConfig(**config_dict)

        assert reconstructed_config.localization.base_language == "en"
        assert reconstructed_config.localization.languages == ["en", "es", "ja"]
        assert reconstructed_config.localization.xcstrings_path == "test.xcstrings"

    def test_localization_with_mixed_content(self):
        """Test localization config with mixed text and image content."""
        config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir="output"),
            localization=LocalizationConfig(
                base_language="en",
                languages=["en", "es"],
            ),
            screenshots={
                "mixed_content": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="text",
                            content="Welcome Text",
                            position=("50%", "20%"),
                        ),
                        ContentItem(
                            type="image",
                            asset="test.png",
                            position=("50%", "50%"),
                        ),
                        ContentItem(
                            type="text",
                            content="Footer Text",
                            position=("50%", "80%"),
                        ),
                    ]
                )
            },
        )

        # Should handle mixed content types
        screenshot = config.screenshots["mixed_content"]
        text_items = [item for item in screenshot.content if item.type == "text"]
        image_items = [item for item in screenshot.content if item.type == "image"]

        assert len(text_items) == 2
        assert len(image_items) == 1
        assert text_items[0].content == "Welcome Text"
        assert text_items[1].content == "Footer Text"
