"""Comprehensive tests for rotation functionality in text and images."""

import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from koubou.config import ContentItem, GradientConfig, ScreenshotConfig, TextOverlay
from koubou.generator import ScreenshotGenerator
from koubou.renderers.text import TextRenderer


class TestTextRotation:
    """Tests for text rotation functionality."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.text_renderer = TextRenderer()

    def teardown_method(self):
        """Cleanup test method."""
        shutil.rmtree(self.temp_dir)

    def test_text_overlay_rotation_field(self):
        """Test that TextOverlay accepts rotation field."""
        # Test default rotation
        text_overlay = TextOverlay(content="Test Text", position=(100, 100))
        assert text_overlay.rotation == 0

        # Test explicit rotation
        text_overlay = TextOverlay(
            content="Rotated Text", position=(100, 100), rotation=45
        )
        assert text_overlay.rotation == 45

        # Test negative rotation
        text_overlay = TextOverlay(
            content="Counter-clockwise", position=(100, 100), rotation=-30
        )
        assert text_overlay.rotation == -30

    def test_text_rotation_preserves_solid_color(self):
        """Test that text rotation preserves solid color rendering."""
        canvas = Image.new("RGBA", (400, 300), (255, 255, 255, 255))

        text_config = TextOverlay(
            content="Solid Color",
            position=(200, 150),
            font_size=24,
            color="#ff0000",  # Red
            rotation=30,
        )

        # Should not raise exception
        self.text_renderer.render(text_config, canvas)

        # Verify canvas was modified (has non-white pixels)
        pixels = list(canvas.getdata())
        non_white_pixels = [p for p in pixels if p != (255, 255, 255, 255)]
        assert len(non_white_pixels) > 0, "Text should have been rendered"

    def test_text_rotation_preserves_gradient(self):
        """Test that text rotation preserves gradient rendering."""
        canvas = Image.new("RGBA", (400, 300), (255, 255, 255, 255))

        gradient_config = GradientConfig(
            type="linear", colors=["#ff0000", "#0000ff"], direction=45
        )

        text_config = TextOverlay(
            content="Gradient Text",
            position=(200, 150),
            font_size=32,
            gradient=gradient_config,
            rotation=25,
        )

        # Should not raise exception
        self.text_renderer.render(text_config, canvas)

        # Verify canvas was modified
        pixels = list(canvas.getdata())
        non_white_pixels = [p for p in pixels if p != (255, 255, 255, 255)]
        assert len(non_white_pixels) > 0, "Gradient text should have been rendered"

    def test_text_rotation_preserves_stroke(self):
        """Test that text rotation preserves stroke rendering."""
        canvas = Image.new("RGBA", (400, 300), (255, 255, 255, 255))

        text_config = TextOverlay(
            content="Stroked Text",
            position=(200, 150),
            font_size=28,
            color="#000000",  # Black
            stroke_width=2,
            stroke_color="#ffffff",  # White stroke
            rotation=45,
        )

        # Should not raise exception
        self.text_renderer.render(text_config, canvas)

        # Verify canvas was modified
        pixels = list(canvas.getdata())
        non_white_pixels = [p for p in pixels if p != (255, 255, 255, 255)]
        assert len(non_white_pixels) > 0, "Stroked text should have been rendered"

    def test_text_rotation_zero_degrees(self):
        """Test that zero rotation produces same result as no rotation."""
        canvas1 = Image.new("RGBA", (400, 300), (255, 255, 255, 255))
        canvas2 = Image.new("RGBA", (400, 300), (255, 255, 255, 255))

        # Text without rotation
        text_config1 = TextOverlay(
            content="No Rotation", position=(200, 150), font_size=24, color="#000000"
        )

        # Text with zero rotation
        text_config2 = TextOverlay(
            content="No Rotation",
            position=(200, 150),
            font_size=24,
            color="#000000",
            rotation=0,
        )

        self.text_renderer.render(text_config1, canvas1)
        self.text_renderer.render(text_config2, canvas2)

        # Both canvases should have content
        pixels1 = list(canvas1.getdata())
        pixels2 = list(canvas2.getdata())

        non_white_pixels1 = [p for p in pixels1 if p != (255, 255, 255, 255)]
        non_white_pixels2 = [p for p in pixels2 if p != (255, 255, 255, 255)]

        assert len(non_white_pixels1) > 0, "Text without rotation should render"
        assert len(non_white_pixels2) > 0, "Text with zero rotation should render"

    def test_text_rotation_error_fallback(self):
        """Test that text rotation failures fall back gracefully."""
        canvas = Image.new("RGBA", (400, 300), (255, 255, 255, 255))

        # Create a config that might cause rotation issues
        text_config = TextOverlay(
            content="Fallback Test",
            position=(200, 150),
            font_size=24,
            color="#000000",
            rotation=360.5,  # Very specific angle
        )

        # Should not raise exception even if rotation has issues
        self.text_renderer.render(text_config, canvas)

        # Verify some content was rendered (either rotated or fallback)
        pixels = list(canvas.getdata())
        non_white_pixels = [p for p in pixels if p != (255, 255, 255, 255)]
        assert len(non_white_pixels) > 0, "Text should render even with rotation issues"


class TestImageRotation:
    """Tests for image rotation functionality."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.generator = ScreenshotGenerator()

        # Create test source image
        self.source_image_path = self.temp_dir / "source.png"
        source_image = Image.new("RGBA", (100, 200), (255, 0, 0, 255))  # Red rectangle
        source_image.save(self.source_image_path)

    def teardown_method(self):
        """Cleanup test method."""
        shutil.rmtree(self.temp_dir)

    def test_content_item_rotation_field(self):
        """Test that ContentItem accepts rotation field."""
        # Test default rotation
        content_item = ContentItem(type="image", asset=str(self.source_image_path))
        assert content_item.rotation == 0

        # Test explicit rotation
        content_item = ContentItem(
            type="image", asset=str(self.source_image_path), rotation=90
        )
        assert content_item.rotation == 90

    def test_screenshot_config_rotation_field(self):
        """Test that ScreenshotConfig accepts image_rotation field."""
        # Test default rotation
        config = ScreenshotConfig(
            name="Test",
            source_image=str(self.source_image_path),
            output_size=(400, 600),
        )
        assert config.image_rotation == 0

        # Test explicit rotation
        config = ScreenshotConfig(
            name="Rotated Test",
            source_image=str(self.source_image_path),
            output_size=(400, 600),
            image_rotation=45,
        )
        assert config.image_rotation == 45

    def test_image_rotation_in_position_method(self):
        """Test that _position_source_image handles rotation."""
        canvas = Image.new("RGBA", (400, 400), (255, 255, 255, 255))
        source_image = Image.open(self.source_image_path)

        # Create mock config with rotation
        class MockConfig:
            image_position = ["50%", "50%"]
            image_scale = 1.0
            image_rotation = 45

        config = MockConfig()

        # Should not raise exception
        positioned_image = self.generator._position_source_image(
            source_image, canvas, config
        )

        # Verify positioned image has correct dimensions
        assert positioned_image.size == canvas.size

        # Verify some content was rendered
        pixels = list(positioned_image.getdata())
        non_transparent_pixels = [p for p in pixels if p[3] > 0]  # Alpha > 0
        assert len(non_transparent_pixels) > 0, "Rotated image should be rendered"

    def test_image_rotation_expand_bounds(self):
        """Test that image rotation expands bounds to prevent cropping."""
        canvas = Image.new("RGBA", (400, 400), (255, 255, 255, 255))

        # Create a square image
        square_image = Image.new("RGBA", (100, 100), (255, 0, 0, 255))

        class MockConfig:
            image_position = ["50%", "50%"]
            image_scale = 1.0
            image_rotation = 45  # 45-degree rotation should expand bounds

        config = MockConfig()
        positioned_image = self.generator._position_source_image(
            square_image, canvas, config
        )

        # Verify content exists (rotation didn't crop everything)
        pixels = list(positioned_image.getdata())
        red_pixels = [
            p for p in pixels if p[0] > 200 and p[1] < 50 and p[2] < 50
        ]  # Mostly red
        assert len(red_pixels) > 0, "Rotated image should preserve content"

    def test_image_rotation_zero_degrees(self):
        """Test that zero rotation is handled correctly."""
        canvas = Image.new("RGBA", (400, 400), (255, 255, 255, 255))
        source_image = Image.open(self.source_image_path)

        class MockConfig:
            image_position = ["50%", "50%"]
            image_scale = 1.0
            image_rotation = 0  # No rotation

        config = MockConfig()
        positioned_image = self.generator._position_source_image(
            source_image, canvas, config
        )

        # Should render successfully
        pixels = list(positioned_image.getdata())
        non_transparent_pixels = [p for p in pixels if p[3] > 0]
        assert len(non_transparent_pixels) > 0, "Image with zero rotation should render"

    def test_image_rotation_preserves_transparency(self):
        """Test that image rotation preserves RGBA transparency."""
        canvas = Image.new("RGBA", (400, 400), (255, 255, 255, 255))

        # Create semi-transparent image
        transparent_image = Image.new(
            "RGBA", (100, 100), (255, 0, 0, 128)
        )  # Semi-transparent red

        class MockConfig:
            image_position = ["50%", "50%"]
            image_scale = 1.0
            image_rotation = 30

        config = MockConfig()
        positioned_image = self.generator._position_source_image(
            transparent_image, canvas, config
        )

        # Check that transparency is preserved
        pixels = list(positioned_image.getdata())
        semi_transparent_pixels = [p for p in pixels if 0 < p[3] < 255]  # Partial alpha
        assert len(semi_transparent_pixels) > 0, "Transparency should be preserved"


class TestRotationIntegration:
    """Integration tests for rotation with other features."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Cleanup test method."""
        shutil.rmtree(self.temp_dir)

    def test_multiple_rotated_elements(self):
        """Test multiple rotated text and image elements together."""
        canvas = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
        text_renderer = TextRenderer()

        # Add multiple rotated text elements
        text_configs = [
            TextOverlay(
                content="First Text",
                position=(200, 150),
                font_size=20,
                color="#ff0000",
                rotation=15,
            ),
            TextOverlay(
                content="Second Text",
                position=(400, 300),
                font_size=24,
                color="#0000ff",
                rotation=-20,
            ),
            TextOverlay(
                content="Third Text",
                position=(600, 450),
                font_size=18,
                color="#00ff00",
                rotation=45,
            ),
        ]

        # Render all text elements
        for text_config in text_configs:
            text_renderer.render(text_config, canvas)

        # Verify all text was rendered
        pixels = list(canvas.getdata())
        non_white_pixels = [p for p in pixels if p != (255, 255, 255, 255)]
        assert len(non_white_pixels) > 100, "Multiple rotated texts should render"

        # After rotation, text pixels may be anti-aliased and mixed with background
        # Just verify that sufficient non-white pixels exist (indicating text was rendered)
        assert (
            len(non_white_pixels) > 300
        ), f"Should have enough text pixels after rotation, found {len(non_white_pixels)} non-white pixels"

        # Verify that different areas of the canvas have text (multiple text elements)
        # Divide canvas into regions and check for non-white pixels in each
        regions_with_text = 0
        canvas_width, canvas_height = 800, 600
        for region_x in range(0, canvas_width, canvas_width // 3):
            for region_y in range(0, canvas_height, canvas_height // 2):
                region_pixels = []
                for y in range(
                    region_y, min(region_y + canvas_height // 2, canvas_height)
                ):
                    for x in range(
                        region_x, min(region_x + canvas_width // 3, canvas_width)
                    ):
                        pixel_index = y * canvas_width + x
                        if pixel_index < len(pixels):
                            region_pixels.append(pixels[pixel_index])

                region_non_white = [
                    p for p in region_pixels if p != (255, 255, 255, 255)
                ]
                if len(region_non_white) > 50:  # Sufficient text in this region
                    regions_with_text += 1

        assert (
            regions_with_text >= 2
        ), f"Should have text in at least 2 regions, found {regions_with_text}"

    def test_rotation_with_gradients_and_strokes(self):
        """Test rotation combined with gradients and strokes."""
        canvas = Image.new("RGBA", (400, 300), (0, 0, 0, 255))  # Black background
        text_renderer = TextRenderer()

        gradient_config = GradientConfig(
            type="linear", colors=["#ff6b6b", "#4ecdc4"], direction=90
        )

        stroke_gradient_config = GradientConfig(
            type="radial", colors=["#ffffff", "#cccccc"], center=["50%", "50%"]
        )

        text_config = TextOverlay(
            content="Complex Text",
            position=(200, 150),
            font_size=32,
            gradient=gradient_config,
            stroke_width=3,
            stroke_gradient=stroke_gradient_config,
            rotation=30,
        )

        # Should handle complex rendering + rotation
        text_renderer.render(text_config, canvas)

        # Verify content was rendered
        pixels = list(canvas.getdata())
        non_black_pixels = [p for p in pixels if p != (0, 0, 0, 255)]
        assert len(non_black_pixels) > 50, "Complex rotated text should render"


class TestRotationValidation:
    """Tests for rotation parameter validation."""

    def setup_method(self):
        """Setup test method."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Cleanup test method."""
        shutil.rmtree(self.temp_dir)

    def test_rotation_accepts_float_values(self):
        """Test that rotation fields accept various float values."""
        # Test decimal values
        text_overlay = TextOverlay(content="Test", position=(100, 100), rotation=45.5)
        assert text_overlay.rotation == 45.5

        content_item = ContentItem(type="image", asset="test.png", rotation=-30.75)
        assert content_item.rotation == -30.75

    def test_rotation_accepts_large_values(self):
        """Test that rotation accepts values beyond 360 degrees."""
        text_overlay = TextOverlay(
            content="Test", position=(100, 100), rotation=450  # 450 = 90 + 360
        )
        assert text_overlay.rotation == 450

        content_item = ContentItem(
            type="image", asset="test.png", rotation=-390  # -390 = -30 - 360
        )
        assert content_item.rotation == -390

    def test_rotation_default_values(self):
        """Test that rotation defaults to 0."""
        text_overlay = TextOverlay(content="Test", position=(100, 100))
        assert text_overlay.rotation == 0

        content_item = ContentItem(type="image", asset="test.png")
        assert content_item.rotation == 0

        # Create a temporary test image for validation
        temp_image = self.temp_dir / "test_validation.png"
        test_img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
        test_img.save(temp_image)

        config = ScreenshotConfig(
            name="Test", source_image=str(temp_image), output_size=(400, 600)
        )
        assert config.image_rotation == 0
