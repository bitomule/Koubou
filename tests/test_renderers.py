"""Tests for renderer modules."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from koubou.config import GradientConfig, TextOverlay
from koubou.exceptions import TextRenderError
from koubou.renderers.background import BackgroundRenderer
from koubou.renderers.device_frame import DeviceFrameRenderer
from koubou.renderers.text import TextRenderer


class TestBackgroundRenderer:
    """Tests for BackgroundRenderer."""

    def setup_method(self):
        """Setup test method."""
        self.renderer = BackgroundRenderer()
        self.canvas = Image.new("RGBA", (200, 200), (255, 255, 255, 0))

    def test_solid_background(self):
        """Test solid background rendering."""
        config = GradientConfig(type="solid", colors=["#ff0000"])

        self.renderer.render(config, self.canvas)

        # Check that canvas has been modified
        pixel = self.canvas.getpixel((100, 100))
        assert pixel == (255, 0, 0, 255)  # Red

    def test_linear_gradient(self):
        """Test linear gradient rendering."""
        config = GradientConfig(
            type="linear", colors=["#ff0000", "#0000ff"], direction=0  # Horizontal
        )

        self.renderer.render(config, self.canvas)

        # Canvas should have gradient
        left_pixel = self.canvas.getpixel((10, 100))
        right_pixel = self.canvas.getpixel((190, 100))

        # Pixels should be different (gradient effect)
        assert left_pixel != right_pixel

    def test_radial_gradient(self):
        """Test radial gradient rendering."""
        config = GradientConfig(type="radial", colors=["#ff0000", "#0000ff"])

        self.renderer.render(config, self.canvas)

        # Center and edge should have different colors
        center_pixel = self.canvas.getpixel((100, 100))
        edge_pixel = self.canvas.getpixel((10, 10))

        assert center_pixel != edge_pixel

    def test_conic_gradient(self):
        """Test conic gradient rendering."""
        config = GradientConfig(type="conic", colors=["#ff0000", "#00ff00", "#0000ff"])

        self.renderer.render(config, self.canvas)

        # Different angular positions should have different colors
        top_pixel = self.canvas.getpixel((100, 10))
        right_pixel = self.canvas.getpixel((190, 100))

        assert top_pixel != right_pixel

    def test_invalid_background_type(self):
        """Test invalid background type raises error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Input should be"):
            GradientConfig(type="invalid", colors=["#ff0000"])

    def test_color_parsing(self):
        """Test color parsing functionality."""
        renderer = BackgroundRenderer()

        # Test 3-digit hex
        color = renderer._parse_color("#f0a")
        assert color == (255, 0, 170, 255)

        # Test 6-digit hex
        color = renderer._parse_color("#ff0000")
        assert color == (255, 0, 0, 255)

        # Test 8-digit hex (with alpha)
        color = renderer._parse_color("#ff000080")
        assert color == (255, 0, 0, 128)


class TestTextRenderer:
    """Tests for TextRenderer."""

    def setup_method(self):
        """Setup test method."""
        self.renderer = TextRenderer()
        self.canvas = Image.new("RGBA", (400, 300), (255, 255, 255, 255))

    def test_simple_text_rendering(self):
        """Test simple text rendering."""
        overlay = TextOverlay(
            content="Hello World", position=(50, 50), font_size=24, color="#000000"
        )

        # Should not raise an exception
        self.renderer.render(overlay, self.canvas)

        # Canvas should be modified (basic check)
        # Note: Detailed pixel-level checks are difficult without knowing exact font rendering
        assert self.canvas.size == (400, 300)

    def test_text_with_wrapping(self):
        """Test text with word wrapping."""
        overlay = TextOverlay(
            content="This is a very long text that should wrap to multiple lines",
            position=(50, 50),
            max_width=200,
            font_size=16,
            color="#000000",
        )

        # Should not raise an exception
        self.renderer.render(overlay, self.canvas)

    def test_text_alignment(self):
        """Test different text alignments."""
        for alignment in ["left", "center", "right"]:
            overlay = TextOverlay(
                content="Aligned Text",
                position=(100, 100),
                alignment=alignment,
                max_width=200,
                color="#000000",
            )

            # Should not raise an exception
            self.renderer.render(overlay, self.canvas)

    def test_color_parsing(self):
        """Test color parsing in text renderer."""
        renderer = TextRenderer()

        # Test valid colors
        assert renderer._parse_color("#ff0000") == (255, 0, 0, 255)
        assert renderer._parse_color("#00ff00") == (0, 255, 0, 255)

        # Test invalid color
        with pytest.raises(TextRenderError, match="Invalid color format"):
            renderer._parse_color("invalid")


class TestDeviceFrameRenderer:
    """Tests for DeviceFrameRenderer."""

    def setup_method(self):
        """Setup test method."""
        # Create a temporary directory with mock frame files
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create mock frame image
        frame_image = Image.new("RGBA", (300, 600), (128, 128, 128, 255))
        frame_path = self.temp_dir / "Test Frame.png"
        frame_image.save(frame_path)

        # Create mock metadata
        metadata = {
            "Test Frame": {
                "screen_bounds": {"x": 50, "y": 100, "width": 200, "height": 400}
            }
        }

        import json

        with open(self.temp_dir / "Frames.json", "w") as f:
            json.dump(metadata, f)

        self.renderer = DeviceFrameRenderer(self.temp_dir)

    def teardown_method(self):
        """Cleanup after test."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_available_frames(self):
        """Test getting available frame names."""
        frames = self.renderer.get_available_frames()
        assert "Test Frame" in frames

    def test_get_frame_size(self):
        """Test getting frame size."""
        size = self.renderer.get_frame_size("Test Frame")
        assert size == (300, 600)

    def test_render_with_metadata(self):
        """Test rendering with frame metadata."""
        canvas = Image.new("RGBA", (300, 600), (255, 255, 255, 255))
        source_image = Image.new("RGBA", (100, 200), (255, 0, 0, 255))

        result = self.renderer.render("Test Frame", canvas, source_image)

        # Result should be the size of the device frame
        assert result.size == (300, 600)

        # Should not raise an exception
        assert isinstance(result, Image.Image)

    def test_nonexistent_frame(self):
        """Test rendering with nonexistent frame."""
        canvas = Image.new("RGBA", (300, 600), (255, 255, 255, 255))
        source_image = Image.new("RGBA", (100, 200), (255, 0, 0, 255))

        from koubou.exceptions import DeviceFrameError

        with pytest.raises(DeviceFrameError, match="not found"):
            self.renderer.render("Nonexistent Frame", canvas, source_image)
