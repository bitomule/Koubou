"""Tests for universal gradient functionality."""

import pytest
from PIL import Image

from koubou.config import GradientConfig, TextOverlay
from koubou.exceptions import TextGradientError
from koubou.renderers.gradient import GradientRenderer


class TestGradientConfig:
    """Test GradientConfig model validation."""

    def test_valid_linear_gradient(self):
        """Test valid linear gradient configuration."""
        config = GradientConfig(
            type="linear", colors=["#FF0000", "#00FF00"], direction=45
        )
        assert config.type == "linear"
        assert config.colors == ["#FF0000", "#00FF00"]
        assert config.direction == 45
        assert config.positions is None

    def test_valid_radial_gradient(self):
        """Test valid radial gradient configuration."""
        config = GradientConfig(
            type="radial",
            colors=["#FF0000", "#00FF00", "#0000FF"],
            center=["50%", "50%"],
            radius="70%",
        )
        assert config.type == "radial"
        assert config.colors == ["#FF0000", "#00FF00", "#0000FF"]
        assert config.center == ("50%", "50%")
        assert config.radius == "70%"

    def test_valid_conic_gradient(self):
        """Test valid conic gradient configuration."""
        config = GradientConfig(
            type="conic",
            colors=["#FF0000", "#00FF00"],
            start_angle=90,
            center=["25%", "75%"],
        )
        assert config.type == "conic"
        assert config.start_angle == 90
        assert config.center == ("25%", "75%")

    def test_gradient_with_color_stops(self):
        """Test gradient with custom color stop positions."""
        config = GradientConfig(
            type="linear",
            colors=["#FF0000", "#00FF00", "#0000FF"],
            positions=[0.0, 0.3, 1.0],
            direction=90,
        )
        assert config.positions == [0.0, 0.3, 1.0]

    def test_invalid_single_color(self):
        """Test that single color gradients are invalid."""
        with pytest.raises(ValueError, match="Gradients require at least 2 colors"):
            GradientConfig(type="linear", colors=["#FF0000"])

    def test_invalid_color_format(self):
        """Test that invalid color formats are rejected."""
        with pytest.raises(ValueError, match="Colors must be in hex format"):
            GradientConfig(type="linear", colors=["red", "#00FF00"])

    def test_invalid_color_stop_count(self):
        """Test that mismatched colors and positions arrays are invalid."""
        with pytest.raises(
            ValueError, match="Positions array must match colors array length"
        ):
            GradientConfig(
                type="linear",
                colors=["#FF0000", "#00FF00"],
                positions=[0.0, 0.5, 1.0],  # 3 positions for 2 colors
            )

    def test_invalid_color_stop_range(self):
        """Test that color stops outside 0.0-1.0 range are invalid."""
        with pytest.raises(
            ValueError, match="Color stop positions must be between 0.0 and 1.0"
        ):
            GradientConfig(
                type="linear",
                colors=["#FF0000", "#00FF00"],
                positions=[0.0, 1.5],  # 1.5 is outside valid range
            )

    def test_invalid_color_stop_order(self):
        """Test that unsorted color stops are invalid."""
        with pytest.raises(
            ValueError, match="Color stop positions must be in ascending order"
        ):
            GradientConfig(
                type="linear",
                colors=["#FF0000", "#00FF00"],
                positions=[0.5, 0.2],  # Not in ascending order
            )

    def test_invalid_direction_range(self):
        """Test that direction outside 0-359 range is invalid."""
        with pytest.raises(
            ValueError, match="Direction must be between 0 and 359 degrees"
        ):
            GradientConfig(
                type="linear",
                colors=["#FF0000", "#00FF00"],
                direction=360,  # Outside valid range
            )

    def test_invalid_start_angle_range(self):
        """Test that start_angle outside 0-359 range is invalid."""
        with pytest.raises(
            ValueError, match="Start angle must be between 0 and 359 degrees"
        ):
            GradientConfig(
                type="conic",
                colors=["#FF0000", "#00FF00"],
                start_angle=-10,  # Outside valid range
            )


class TestTextOverlayGradientValidation:
    """Test TextOverlay gradient validation."""

    def test_valid_solid_color(self):
        """Test valid solid color text overlay."""
        overlay = TextOverlay(content="Test Text", position=(100, 100), color="#FF0000")
        assert overlay.color == "#FF0000"
        assert overlay.gradient is None

    def test_valid_gradient_text(self):
        """Test valid gradient text overlay."""
        gradient = GradientConfig(type="linear", colors=["#FF0000", "#00FF00"])
        overlay = TextOverlay(
            content="Test Text", position=(100, 100), gradient=gradient
        )
        assert overlay.gradient is not None
        assert overlay.color is None  # Should be None when gradient is specified

    def test_default_color_when_neither_specified(self):
        """Test that default color is set when neither color nor gradient is specified."""
        overlay = TextOverlay(content="Test Text", position=(100, 100))
        assert overlay.color is None  # No default color set
        assert overlay.gradient is None

    def test_cannot_specify_both_color_and_gradient(self):
        """Test that both color and gradient cannot be specified."""
        gradient = GradientConfig(type="linear", colors=["#FF0000", "#00FF00"])
        with pytest.raises(
            ValueError, match="Cannot specify both 'color' and 'gradient'"
        ):
            TextOverlay(
                content="Test Text",
                position=(100, 100),
                color="#FF0000",
                gradient=gradient,
            )

    def test_valid_gradient_stroke(self):
        """Test valid gradient stroke configuration."""
        gradient = GradientConfig(type="linear", colors=["#FF0000", "#00FF00"])
        stroke_gradient = GradientConfig(type="radial", colors=["#000000", "#333333"])
        overlay = TextOverlay(
            content="Test Text",
            position=(100, 100),
            gradient=gradient,
            stroke_width=2,
            stroke_gradient=stroke_gradient,
        )
        assert overlay.stroke_gradient is not None
        assert overlay.stroke_color is None

    def test_cannot_specify_both_stroke_types(self):
        """Test that both stroke_color and stroke_gradient cannot be specified."""
        gradient = GradientConfig(type="linear", colors=["#FF0000", "#00FF00"])
        stroke_gradient = GradientConfig(type="linear", colors=["#000000", "#333333"])
        with pytest.raises(
            ValueError, match="Cannot specify both 'stroke_color' and 'stroke_gradient'"
        ):
            TextOverlay(
                content="Test Text",
                position=(100, 100),
                gradient=gradient,
                stroke_width=2,
                stroke_color="#000000",
                stroke_gradient=stroke_gradient,
            )

    def test_stroke_width_requires_stroke_option(self):
        """Test that stroke_width requires either stroke_color or stroke_gradient."""
        gradient = GradientConfig(type="linear", colors=["#FF0000", "#00FF00"])
        with pytest.raises(ValueError, match="When 'stroke_width' is specified"):
            TextOverlay(
                content="Test Text",
                position=(100, 100),
                gradient=gradient,
                stroke_width=2,
                # Missing stroke_color or stroke_gradient
            )


class TestGradientRenderer:
    """Test GradientRenderer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = GradientRenderer()
        self.test_bounds = (0, 0, 200, 100)  # x, y, width, height

    def test_create_linear_gradient(self):
        """Test linear gradient creation."""
        config = GradientConfig(
            type="linear", colors=["#FF0000", "#0000FF"], direction=90
        )

        gradient = self.renderer.create_gradient(self.test_bounds, config)

        assert isinstance(gradient, Image.Image)
        assert gradient.size == (200, 100)
        assert gradient.mode == "RGBA"

    def test_create_radial_gradient(self):
        """Test radial gradient creation."""
        config = GradientConfig(
            type="radial",
            colors=["#FF0000", "#0000FF"],
            center=["50%", "50%"],
            radius="50%",
        )

        gradient = self.renderer.create_gradient(self.test_bounds, config)

        assert isinstance(gradient, Image.Image)
        assert gradient.size == (200, 100)
        assert gradient.mode == "RGBA"

    def test_create_conic_gradient(self):
        """Test conic gradient creation."""
        config = GradientConfig(
            type="conic", colors=["#FF0000", "#0000FF"], start_angle=0
        )

        gradient = self.renderer.create_gradient(self.test_bounds, config)

        assert isinstance(gradient, Image.Image)
        assert gradient.size == (200, 100)
        assert gradient.mode == "RGBA"

    def test_gradient_with_color_stops(self):
        """Test gradient with custom color stops."""
        config = GradientConfig(
            type="linear",
            colors=["#FF0000", "#00FF00", "#0000FF"],
            positions=[0.0, 0.3, 1.0],
            direction=0,
        )

        gradient = self.renderer.create_gradient(self.test_bounds, config)

        assert isinstance(gradient, Image.Image)
        assert gradient.size == (200, 100)

    def test_color_parsing(self):
        """Test color parsing functionality."""
        # Test RGB format
        color = self.renderer._parse_color("#F00")
        assert color == (255, 0, 0, 255)

        # Test RRGGBB format
        color = self.renderer._parse_color("#FF0000")
        assert color == (255, 0, 0, 255)

        # Test RRGGBBAA format
        color = self.renderer._parse_color("#FF000080")
        assert color == (255, 0, 0, 128)

    def test_invalid_color_format(self):
        """Test invalid color format handling."""
        with pytest.raises(TextGradientError, match="Invalid color format"):
            self.renderer._parse_color("#XYZ")

    def test_position_parsing(self):
        """Test position parsing functionality."""
        # Test percentage
        pos = self.renderer._parse_position("50%", 200)
        assert pos == 100

        # Test pixel value
        pos = self.renderer._parse_position("150px", 200)
        assert pos == 150

        # Test plain number
        pos = self.renderer._parse_position("75", 200)
        assert pos == 75

    def test_color_interpolation_without_stops(self):
        """Test color interpolation without custom stops."""
        colors = [(255, 0, 0, 255), (0, 0, 255, 255)]  # Red to Blue

        # Start color
        color = self.renderer._interpolate_with_stops(colors, None, 0.0)
        assert color == (255, 0, 0, 255)

        # End color
        color = self.renderer._interpolate_with_stops(colors, None, 1.0)
        assert color == (0, 0, 255, 255)

        # Mid color (should be purple-ish)
        color = self.renderer._interpolate_with_stops(colors, None, 0.5)
        assert color == (127, 0, 127, 255)

    def test_color_interpolation_with_stops(self):
        """Test color interpolation with custom stops."""
        colors = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)]  # R, G, B
        positions = [0.0, 0.2, 1.0]

        # First color
        color = self.renderer._interpolate_with_stops(colors, positions, 0.0)
        assert color == (255, 0, 0, 255)

        # Between first and second (at 0.1, halfway between 0.0 and 0.2)
        color = self.renderer._interpolate_with_stops(colors, positions, 0.1)
        assert color == (127, 127, 0, 255)  # Halfway red to green

        # Last color
        color = self.renderer._interpolate_with_stops(colors, positions, 1.0)
        assert color == (0, 0, 255, 255)

    def test_invalid_gradient_type(self):
        """Test handling of invalid gradient types."""
        config = GradientConfig(type="linear", colors=["#FF0000", "#0000FF"])
        # Manually change type to invalid value (bypassing validation)
        config.type = "invalid_type"

        with pytest.raises(TextGradientError, match="Unknown gradient type"):
            self.renderer.create_gradient(self.test_bounds, config)
