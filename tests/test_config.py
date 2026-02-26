"""Tests for configuration models."""

import pytest
from pydantic import ValidationError

from koubou.config import (
    ContentItem,
    GradientConfig,
    ProjectConfig,
    ScreenshotConfig,
    TextOverlay,
)


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
        with pytest.raises(ValidationError, match="Invalid dimensions"):
            ScreenshotConfig(
                name="Test", source_image=sample_image, output_size=(0, 800)
            )

    def test_output_size_too_large(self, sample_image):
        """Test output size too large fails validation."""
        with pytest.raises(ValidationError, match="too large"):
            ScreenshotConfig(
                name="Test", source_image=sample_image, output_size=(20000, 800)
            )

    def test_named_appstore_size(self, sample_image):
        """Test named App Store size is resolved correctly."""
        config = ScreenshotConfig(
            name="Test", source_image=sample_image, output_size="iPhone6_9"
        )
        # iPhone6_9 should resolve to (1320, 2868)
        assert config.output_size == (1320, 2868)

    def test_named_appstore_desktop_size(self, sample_image):
        """Test named desktop App Store size is resolved correctly."""
        config = ScreenshotConfig(
            name="Desktop Test",
            source_image=sample_image,
            output_size="AppDesktop_2880",
        )
        assert config.output_size == (2880, 1800)

    def test_invalid_named_size(self, sample_image):
        """Test invalid named size fails validation."""
        with pytest.raises(ValidationError, match="Unknown App Store size"):
            ScreenshotConfig(
                name="Test", source_image=sample_image, output_size="InvalidSize"
            )


class TestContentItemFontFamily:
    """Tests for ContentItem font_family field."""

    def test_font_family_default(self):
        item = ContentItem(type="text", content="Hello", position=("50%", "50%"))
        assert item.font_family == "Arial"

    def test_font_family_custom(self):
        item = ContentItem(
            type="text",
            content="Hello",
            position=("50%", "50%"),
            font_family="Helvetica",
        )
        assert item.font_family == "Helvetica"

    def test_font_family_none_uses_default(self):
        item = ContentItem(
            type="text",
            content="Hello",
            position=("50%", "50%"),
            font_family=None,
        )
        assert item.font_family is None


class TestContentItemHighlight:
    """Tests for ContentItem with type='highlight'."""

    def test_valid_highlight(self):
        item = ContentItem(
            type="highlight",
            shape="circle",
            position=("50%", "50%"),
            dimensions=("20%", "15%"),
            border_color="#FF3B30",
            border_width=4,
        )
        assert item.type == "highlight"
        assert item.shape == "circle"

    def test_highlight_all_shapes(self):
        for shape in ["circle", "rounded_rect", "rect"]:
            item = ContentItem(
                type="highlight",
                shape=shape,
                position=("50%", "50%"),
            )
            assert item.shape == shape

    def test_highlight_missing_shape_raises(self):
        with pytest.raises(ValidationError, match="shape"):
            ContentItem(
                type="highlight",
                position=("50%", "50%"),
            )

    def test_highlight_with_fill(self):
        item = ContentItem(
            type="highlight",
            shape="rect",
            position=("50%", "50%"),
            fill_color="#FF3B3020",
            border_color="#FF3B30",
        )
        assert item.fill_color == "#FF3B3020"

    def test_highlight_invalid_border_color(self):
        with pytest.raises(ValidationError, match="hex format"):
            ContentItem(
                type="highlight",
                shape="circle",
                position=("50%", "50%"),
                border_color="red",
            )

    def test_highlight_invalid_fill_color(self):
        with pytest.raises(ValidationError, match="hex format"):
            ContentItem(
                type="highlight",
                shape="circle",
                position=("50%", "50%"),
                fill_color="invalid",
            )


class TestContentItemZoom:
    """Tests for ContentItem with type='zoom'."""

    def test_valid_zoom(self):
        item = ContentItem(
            type="zoom",
            source_position=("65%", "45%"),
            source_size=("15%", "10%"),
            display_position=("25%", "20%"),
            display_size=("35%", "30%"),
            shape="circle",
            border_color="#007AFF",
        )
        assert item.type == "zoom"
        assert item.source_position == ("65%", "45%")

    def test_zoom_missing_source_position_raises(self):
        with pytest.raises(ValidationError, match="source_position"):
            ContentItem(
                type="zoom",
                source_size=("15%", "10%"),
                display_size=("35%", "30%"),
            )

    def test_zoom_missing_source_size_raises(self):
        with pytest.raises(ValidationError, match="source_size"):
            ContentItem(
                type="zoom",
                source_position=("65%", "45%"),
                display_size=("35%", "30%"),
            )

    def test_zoom_missing_display_size_raises(self):
        with pytest.raises(ValidationError, match="display_size.*zoom_level"):
            ContentItem(
                type="zoom",
                source_position=("65%", "45%"),
                source_size=("15%", "10%"),
            )

    def test_zoom_defaults(self):
        item = ContentItem(
            type="zoom",
            source_position=("50%", "50%"),
            source_size=("10%", "10%"),
            display_size=("30%", "30%"),
        )
        assert item.connector is False
        assert item.connector_width == 2
        assert item.border_width == 3
        assert item.corner_radius == 16

    def test_zoom_invalid_connector_color(self):
        with pytest.raises(ValidationError, match="hex format"):
            ContentItem(
                type="zoom",
                source_position=("50%", "50%"),
                source_size=("10%", "10%"),
                display_size=("30%", "30%"),
                connector_color="blue",
            )

    def test_zoom_with_connector(self):
        item = ContentItem(
            type="zoom",
            source_position=("50%", "50%"),
            source_size=("10%", "10%"),
            display_size=("30%", "30%"),
            connector=True,
            connector_color="#FF0000",
            connector_width=3,
        )
        assert item.connector is True
        assert item.connector_color == "#FF0000"

    def test_zoom_with_zoom_level(self):
        item = ContentItem(
            type="zoom",
            source_position=("50%", "50%"),
            source_size=("10%", "10%"),
            zoom_level=2.5,
        )
        assert item.zoom_level == 2.5
        assert item.display_size is None

    def test_zoom_with_zoom_level_and_display_size(self):
        item = ContentItem(
            type="zoom",
            source_position=("50%", "50%"),
            source_size=("10%", "10%"),
            display_size=("30%", "30%"),
            zoom_level=2.5,
        )
        assert item.zoom_level == 2.5
        assert item.display_size == ("30%", "30%")

    def test_zoom_connector_styles(self):
        for style in ["straight", "curved", "facing"]:
            item = ContentItem(
                type="zoom",
                source_position=("50%", "50%"),
                source_size=("10%", "10%"),
                display_size=("30%", "30%"),
                connector=True,
                connector_style=style,
            )
            assert item.connector_style == style

    def test_zoom_connector_fill(self):
        item = ContentItem(
            type="zoom",
            source_position=("50%", "50%"),
            source_size=("10%", "10%"),
            display_size=("30%", "30%"),
            connector=True,
            connector_style="facing",
            connector_fill="#007AFF20",
        )
        assert item.connector_fill == "#007AFF20"

    def test_zoom_invalid_connector_fill(self):
        with pytest.raises(ValidationError, match="hex format"):
            ContentItem(
                type="zoom",
                source_position=("50%", "50%"),
                source_size=("10%", "10%"),
                display_size=("30%", "30%"),
                connector_fill="blue",
            )

    def test_zoom_source_indicator_defaults(self):
        item = ContentItem(
            type="zoom",
            source_position=("50%", "50%"),
            source_size=("10%", "10%"),
            display_size=("30%", "30%"),
        )
        assert item.source_indicator is True
        assert item.source_indicator_style == "border"

    def test_zoom_source_indicator_styles(self):
        for style in ["border", "dashed", "fill"]:
            item = ContentItem(
                type="zoom",
                source_position=("50%", "50%"),
                source_size=("10%", "10%"),
                display_size=("30%", "30%"),
                source_indicator_style=style,
            )
            assert item.source_indicator_style == style


class TestContentItemShadow:
    """Tests for shadow fields on ContentItem."""

    def test_shadow_defaults(self):
        item = ContentItem(
            type="highlight",
            shape="circle",
            position=("50%", "50%"),
        )
        assert item.shadow is False
        assert item.shadow_color == "#00000040"
        assert item.shadow_blur == 15
        assert item.shadow_offset == ("0", "6")

    def test_shadow_custom(self):
        item = ContentItem(
            type="highlight",
            shape="circle",
            position=("50%", "50%"),
            shadow=True,
            shadow_color="#FF000080",
            shadow_blur=20,
            shadow_offset=("5", "10"),
        )
        assert item.shadow is True
        assert item.shadow_color == "#FF000080"
        assert item.shadow_blur == 20
        assert item.shadow_offset == ("5", "10")

    def test_shadow_invalid_color(self):
        with pytest.raises(ValidationError, match="hex format"):
            ContentItem(
                type="highlight",
                shape="circle",
                position=("50%", "50%"),
                shadow_color="red",
            )


class TestContentItemSpotlight:
    """Tests for spotlight fields on ContentItem."""

    def test_spotlight_defaults(self):
        item = ContentItem(
            type="highlight",
            shape="circle",
            position=("50%", "50%"),
        )
        assert item.spotlight is False
        assert item.spotlight_color == "#000000"
        assert item.spotlight_opacity == 0.5

    def test_spotlight_custom(self):
        item = ContentItem(
            type="highlight",
            shape="circle",
            position=("50%", "50%"),
            spotlight=True,
            spotlight_color="#0000FF",
            spotlight_opacity=0.7,
        )
        assert item.spotlight is True
        assert item.spotlight_opacity == 0.7

    def test_spotlight_invalid_color(self):
        with pytest.raises(ValidationError, match="hex format"):
            ContentItem(
                type="highlight",
                shape="circle",
                position=("50%", "50%"),
                spotlight_color="invalid",
            )

    def test_spotlight_opacity_out_of_range(self):
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            ContentItem(
                type="highlight",
                shape="circle",
                position=("50%", "50%"),
                spotlight_opacity=1.5,
            )


class TestContentItemBlurBackground:
    """Tests for blur background fields on ContentItem."""

    def test_blur_defaults(self):
        item = ContentItem(
            type="highlight",
            shape="circle",
            position=("50%", "50%"),
        )
        assert item.blur_background is False
        assert item.blur_radius == 20

    def test_blur_custom(self):
        item = ContentItem(
            type="highlight",
            shape="circle",
            position=("50%", "50%"),
            blur_background=True,
            blur_radius=30,
        )
        assert item.blur_background is True
        assert item.blur_radius == 30


class TestProjectConfig:
    """Tests for ProjectConfig model."""

    def test_project_config(self):
        """Test project configuration."""
        from koubou.config import ContentItem, ProjectInfo, ScreenshotDefinition

        config = ProjectConfig(
            project=ProjectInfo(
                name="Test Project",
                output_dir="./output",
                device="iPhone 15 Pro Portrait",
            ),
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
        assert config.project.device == "iPhone 15 Pro Portrait"
        assert len(config.screenshots) == 1
