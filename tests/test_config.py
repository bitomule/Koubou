"""Tests for configuration models."""

import pytest
from pydantic import ValidationError

from koubou.config import GradientConfig, ProjectConfig, ScreenshotConfig, TextOverlay


class TestGradientConfig:
    """Tests for GradientConfig model."""

    def test_solid_background_valid(self):
        """Test valid solid background configuration."""
        config = GradientConfig(type="solid", colors=["#ff0000"])
        assert config.type == "solid"
        assert config.colors == ["#ff0000"]

    def test_gradient_background_valid(self):
        """Test valid gradient background configuration."""
        config = GradientConfig(
            type="linear", colors=["#ff0000", "#00ff00"], direction=45
        )
        assert config.type == "linear"
        assert config.colors == ["#ff0000", "#00ff00"]
        assert config.direction == 45

    def test_gradient_insufficient_colors(self):
        """Test gradient with insufficient colors fails validation."""
        with pytest.raises(ValidationError, match="at least 2 colors"):
            GradientConfig(type="linear", colors=["#ff0000"])

    def test_invalid_color_format(self):
        """Test invalid color format fails validation."""
        with pytest.raises(ValidationError, match="hex format"):
            GradientConfig(type="solid", colors=["red"])  # Invalid format

    def test_empty_colors(self):
        """Test empty colors list fails validation."""
        with pytest.raises(ValidationError, match="exactly 1 color"):
            GradientConfig(type="solid", colors=[])


class TestTextOverlay:
    """Tests for TextOverlay model."""

    def test_text_overlay_valid(self):
        """Test valid text overlay configuration."""
        overlay = TextOverlay(
            content="Hello World", position=(100, 200), font_size=32, color="#ffffff"
        )
        assert overlay.content == "Hello World"
        assert overlay.position == (100, 200)
        assert overlay.font_size == 32
        assert overlay.color == "#ffffff"

    def test_text_overlay_defaults(self):
        """Test text overlay with default values."""
        overlay = TextOverlay(content="Test", position=(0, 0))
        assert overlay.font_size == 24
        assert overlay.font_family == "Arial"
        assert overlay.color is None
        assert overlay.alignment == "center"

    def test_invalid_color(self):
        """Test invalid color format fails validation."""
        with pytest.raises(ValidationError, match="hex format"):
            TextOverlay(content="Test", position=(0, 0), color="blue")  # Invalid format


class TestScreenshotConfig:
    """Tests for ScreenshotConfig model."""

    def test_screenshot_config_minimal(self, sample_image):
        """Test minimal screenshot configuration."""
        config = ScreenshotConfig(
            name="Test", source_image=sample_image, output_size=(400, 800)
        )
        assert config.name == "Test"
        assert config.source_image == sample_image
        assert config.output_size == (400, 800)
        assert config.background is None
        assert config.text_overlays == []

    def test_screenshot_config_full(self, sample_image):
        """Test full screenshot configuration."""
        config = ScreenshotConfig(
            name="Full Test",
            source_image=sample_image,
            output_size=(400, 800),
            background=GradientConfig(type="solid", colors=["#ff0000"]),
            text_overlays=[TextOverlay(content="Test", position=(50, 50))],
        )
        assert config.background is not None
        assert len(config.text_overlays) == 1

    def test_nonexistent_source_image(self):
        """Test nonexistent source image fails validation."""
        with pytest.raises(ValidationError, match="not found"):
            ScreenshotConfig(
                name="Test", source_image="nonexistent.png", output_size=(400, 800)
            )

    def test_invalid_output_size(self, sample_image):
        """Test invalid output size fails validation."""
        with pytest.raises(ValidationError, match="positive"):
            ScreenshotConfig(
                name="Test", source_image=sample_image, output_size=(0, 800)
            )

    def test_output_size_too_large(self, sample_image):
        """Test output size too large fails validation."""
        with pytest.raises(ValidationError, match="too large"):
            ScreenshotConfig(
                name="Test", source_image=sample_image, output_size=(20000, 800)
            )


class TestProjectConfig:
    """Tests for ProjectConfig model."""

    def test_project_config(self):
        """Test project configuration."""
        from koubou.config import ContentItem, ProjectInfo, ScreenshotDefinition

        config = ProjectConfig(
            project=ProjectInfo(name="Test Project", output_dir="./output"),
            screenshots={
                "test_screenshot": ScreenshotDefinition(
                    content=[
                        ContentItem(
                            type="text", content="Hello World", position=("50%", "50%")
                        )
                    ],
                )
            },
        )
        assert config.project.name == "Test Project"
        assert len(config.screenshots) == 1
