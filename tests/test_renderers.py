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

    def test_solid_background_with_alpha(self):
        """Test solid background rendering preserves color alpha."""
        config = GradientConfig(type="solid", colors=["#00000000"])

        self.renderer.render(config, self.canvas)

        pixel = self.canvas.getpixel((100, 100))
        assert pixel == (0, 0, 0, 0)

    def test_transparent_background(self):
        """Test transparent background clears the canvas alpha."""
        self.canvas.paste(Image.new("RGBA", self.canvas.size, (255, 0, 0, 255)))
        config = GradientConfig(type="transparent")

        self.renderer.render(config, self.canvas)

        pixel = self.canvas.getpixel((100, 100))
        assert pixel == (255, 255, 255, 0)

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
        # Note: Detailed pixel-level checks are difficult without knowing exact
        # font rendering
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

    def test_text_box_paragraph_renders_behind_text(self):
        """Paragraph boxes should paint the configured fill behind text."""
        overlay = TextOverlay(
            content="Boxed",
            position=(40, 60),
            anchor="top-left",
            alignment="left",
            font_size=32,
            color="#000000",
            box={"color": "#ff0000", "padding": 8, "type": "straight"},
        )

        self.renderer.render(overlay, self.canvas)

        assert self.canvas.getpixel((35, 55)) == (255, 0, 0, 255)

    def test_text_box_multiline_paragraph_uses_block_bounds(self):
        """Paragraph boxes should wrap the full text block."""
        overlay = TextOverlay(
            content="Hi longerword",
            position=(30, 30),
            anchor="top-left",
            alignment="left",
            max_width=90,
            font_size=24,
            color="#000000",
            box={"color": "#00ff00", "padding": 4, "type": "straight"},
        )

        self.renderer.render(overlay, self.canvas)

        first_line_y = 28
        assert self.canvas.getpixel((32, first_line_y))[:3] == (0, 255, 0)
        assert self.canvas.getpixel((95, first_line_y))[:3] == (0, 255, 0)

    def test_text_box_character_keeps_wrapped_lines_separate(self):
        """Character level should not fill the vertical gap between wrapped lines."""
        overlay = TextOverlay(
            content="AB C",
            position=(40, 60),
            anchor="top-left",
            alignment="left",
            max_width=45,
            font_size=32,
            color="#000000",
            box={
                "level": "character",
                "color": "#0000ff",
                "padding": 4,
                "type": "straight",
            },
        )

        self.renderer.render(overlay, self.canvas)

        gap_pixels = [self.canvas.getpixel((50, y)) for y in range(88, 98)]
        assert (255, 255, 255, 255) in gap_pixels

    def test_text_box_character_renders_line_fragments(self):
        """Character level should render boxes for wrapped line fragments."""
        overlay = TextOverlay(
            content="AB C",
            position=(40, 60),
            anchor="top-left",
            alignment="left",
            max_width=45,
            font_size=32,
            color="#000000",
            box={"level": "character", "color": "#0000ff", "padding": 4},
        )

        self.renderer.render(overlay, self.canvas)

        blue_pixels = [
            pixel
            for pixel in self.canvas.getdata()
            if pixel[2] == 255 and pixel[0] == 0 and pixel[1] == 0
        ]
        assert len(blue_pixels) > 50

    def test_text_box_accepts_rounded_straight_and_strait(self):
        """All supported box types should render without errors."""
        for box_type in ["rounded", "straight", "strait"]:
            canvas = Image.new("RGBA", (400, 300), (255, 255, 255, 255))
            overlay = TextOverlay(
                content="Boxed",
                position=(40, 60),
                anchor="top-left",
                alignment="left",
                color="#000000",
                box={"type": box_type, "color": "#ff00ff"},
            )

            self.renderer.render(overlay, canvas)

            assert canvas.getbbox() is not None

    def test_text_box_alpha_composites_over_canvas(self):
        """Alpha box colors should composite over the existing canvas."""
        overlay = TextOverlay(
            content="Alpha",
            position=(40, 60),
            anchor="top-left",
            alignment="left",
            font_size=32,
            color="#000000",
            box={"color": "#ff000080", "padding": 8, "type": "straight"},
        )

        self.renderer.render(overlay, self.canvas)

        pixel = self.canvas.getpixel((35, 55))
        assert pixel[0] == 255
        assert 120 <= pixel[1] <= 130
        assert 120 <= pixel[2] <= 130
        assert pixel[3] == 255

    def test_text_box_respects_alignment(self):
        """Box placement should follow the same alignment as the text."""
        cases = [
            ("left", "center-left", (100, 60), (95, 41)),
            ("center", "center", (200, 60), (195, 41)),
            ("right", "center-right", (300, 60), (295, 41)),
        ]

        for alignment, anchor, position, sample in cases:
            canvas = Image.new("RGBA", (400, 300), (255, 255, 255, 255))
            overlay = TextOverlay(
                content="Wide",
                position=position,
                anchor=anchor,
                alignment=alignment,
                max_width=100,
                font_size=24,
                color="#000000",
                box={"color": "#00ffff", "padding": 6, "type": "straight"},
            )

            self.renderer.render(overlay, canvas)

            assert canvas.getpixel(sample)[:3] == (0, 255, 255)

    def test_text_box_with_gradient_text(self):
        """Text boxes should work with gradient text fills."""
        overlay = TextOverlay(
            content="Gradient",
            position=(40, 60),
            anchor="top-left",
            alignment="left",
            font_size=32,
            gradient=GradientConfig(
                type="linear", colors=["#000000", "#333333"], direction=0
            ),
            box={"color": "#ffaa00", "padding": 8},
        )

        self.renderer.render(overlay, self.canvas)

        assert self.canvas.getpixel((35, 66))[:3] == (255, 170, 0)

    def test_text_box_with_stroke(self):
        """Text boxes should work with stroked text."""
        overlay = TextOverlay(
            content="Stroke",
            position=(40, 60),
            anchor="top-left",
            alignment="left",
            font_size=32,
            color="#ffffff",
            stroke_width=2,
            stroke_color="#000000",
            box={"color": "#663399", "padding": 8},
        )

        self.renderer.render(overlay, self.canvas)

        assert self.canvas.getpixel((35, 66))[:3] == (102, 51, 153)

    def test_text_box_with_auto_sizing(self):
        """Text boxes should render after auto-sizing resolves final text layout."""
        overlay = TextOverlay(
            content="This text shrinks to fit the configured box",
            position=(40, 60),
            anchor="top-left",
            alignment="left",
            font_size=40,
            min_font_size=12,
            max_width=160,
            max_height=70,
            color="#000000",
            box={"color": "#008000", "padding": 4},
        )

        self.renderer.render(overlay, self.canvas)

        assert self.canvas.getpixel((38, 58))[:3] == (0, 128, 0)

    def test_text_box_rotates_with_text(self):
        """The box and text should render together when rotated."""
        overlay = TextOverlay(
            content="Rotate",
            position=(160, 130),
            anchor="center",
            alignment="center",
            font_size=36,
            color="#000000",
            rotation=25,
            box={"color": "#ff0000", "padding": 8},
        )

        self.renderer.render(overlay, self.canvas)

        red_pixels = [
            pixel
            for pixel in self.canvas.getdata()
            if pixel[0] == 255 and pixel[1] == 0 and pixel[2] == 0
        ]
        assert len(red_pixels) > 50


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

    def test_generate_screen_mask_from_image_basic(self):
        """Test screen mask generation from frame image."""
        # Create a mock frame with screen area (alpha=0) and bezel (alpha=255)
        frame = Image.new("RGBA", (100, 200), (128, 128, 128, 255))

        # Create screen area in the center (alpha=0)
        for y in range(20, 180):
            for x in range(10, 90):
                frame.putpixel((x, y), (128, 128, 128, 0))

        # Generate mask
        mask = self.renderer.generate_screen_mask_from_image(frame)

        # Verify mask is grayscale
        assert mask.mode == "L"
        assert mask.size == frame.size

        # Check that screen area (center) is white (255)
        center_pixel = mask.getpixel((50, 100))
        assert center_pixel == 255, f"Center should be white (255), got {center_pixel}"

        # Check that bezel area is black (0)
        bezel_pixel = mask.getpixel((5, 5))
        assert bezel_pixel == 0, f"Bezel should be black (0), got {bezel_pixel}"

    def test_generate_screen_mask_from_image_with_rounded_corners(self):
        """Test screen mask generation preserves rounded corners with anti-aliasing."""
        # Create a frame with rounded corners (gradient alpha values)
        frame = Image.new("RGBA", (100, 200), (128, 128, 128, 255))

        # Screen area with rounded corners (gradient alpha values)
        for y in range(10, 190):
            for x in range(10, 90):
                if y < 15 or y > 185:
                    # Corner areas - gradient alpha for anti-aliasing
                    if x < 15 or x > 85:
                        alpha = min(50, abs(x - 50) + abs(y - 100) - 40)
                        frame.putpixel((x, y), (128, 128, 128, alpha))
                    else:
                        frame.putpixel((x, y), (128, 128, 128, 0))
                else:
                    frame.putpixel((x, y), (128, 128, 128, 0))

        # Generate mask
        mask = self.renderer.generate_screen_mask_from_image(frame)

        # Center should be white (full screen)
        center_pixel = mask.getpixel((50, 100))
        assert center_pixel == 255

        # Corner gradients should be preserved (not pure black or white)
        corner_pixel = mask.getpixel((12, 12))
        msg = f"Corner should have gradient, got {corner_pixel}"
        assert 0 < corner_pixel < 255, msg

    def test_generate_screen_mask_from_image_flood_fill(self):
        """Test flood fill correctly identifies outer area vs screen."""
        # Create frame with outer area (alpha=0) and screen area
        # (alpha=0) separated by bezel
        frame = Image.new("RGBA", (100, 200), (128, 128, 128, 0))

        # Add bezel around screen (alpha=255)
        for y in range(200):
            for x in range(100):
                # Outer 5 pixels are transparent (outer area, alpha=0)
                if x < 5 or x >= 95 or y < 5 or y >= 195:
                    frame.putpixel((x, y), (128, 128, 128, 0))
                # Bezel (5 pixels wide, alpha=255)
                elif x < 10 or x >= 90 or y < 10 or y >= 190:
                    frame.putpixel((x, y), (128, 128, 128, 255))
                # Screen area (alpha=0)
                else:
                    frame.putpixel((x, y), (128, 128, 128, 0))

        # Generate mask
        mask = self.renderer.generate_screen_mask_from_image(frame)

        # Outer area should be black (hidden)
        outer_pixel = mask.getpixel((2, 2))
        assert outer_pixel == 0, f"Outer area should be hidden (0), got {outer_pixel}"

        # Bezel should be black (hidden)
        bezel_pixel = mask.getpixel((7, 7))
        assert bezel_pixel == 0, f"Bezel should be hidden (0), got {bezel_pixel}"

        # Screen area should be white (visible)
        screen_pixel = mask.getpixel((50, 100))
        msg = f"Screen should be visible (255), got {screen_pixel}"
        assert screen_pixel == 255, msg

    def test_generate_screen_mask_with_alpha_threshold(self):
        """Test that alpha threshold of 50 correctly separates screen from bezel."""
        # Create frame with realistic layout:
        # - Outer transparent area (alpha=0) connected to edges
        # - Bezel ring (alpha>50) surrounding screen
        # - Inner screen area (alpha=0-50) enclosed by bezel
        frame = Image.new("RGBA", (100, 100), (128, 128, 128, 255))

        # Outer transparent area (alpha=0) - will be marked as "outer" by flood fill
        for y in range(100):
            for x in range(100):
                if x < 5 or x >= 95 or y < 5 or y >= 95:
                    frame.putpixel((x, y), (128, 128, 128, 0))

        # Bezel ring (alpha=255) - separates outer from screen
        for y in range(5, 95):
            for x in range(5, 95):
                if x < 15 or x >= 85 or y < 15 or y >= 85:
                    frame.putpixel((x, y), (128, 128, 128, 255))

        # Inner screen area with gradient edges
        # Center: alpha=0 (pure screen)
        for y in range(25, 75):
            for x in range(25, 75):
                frame.putpixel((x, y), (128, 128, 128, 0))

        # Screen edge gradient (alpha=25) between bezel and center
        for y in range(15, 85):
            for x in range(15, 85):
                if 15 <= x < 25 or 75 <= x < 85 or 15 <= y < 25 or 75 <= y < 85:
                    frame.putpixel((x, y), (128, 128, 128, 25))

        # Generate mask
        mask = self.renderer.generate_screen_mask_from_image(frame)

        # Check outer area (should be black - hidden)
        outer_pixel = mask.getpixel((2, 2))
        assert outer_pixel == 0, f"Outer area should be black (0), got {outer_pixel}"

        # Check bezel area (should be black - hidden)
        bezel_pixel = mask.getpixel((10, 10))
        assert bezel_pixel == 0, f"Bezel should be black (0), got {bezel_pixel}"

        # Check screen center (alpha=0, should be white - visible)
        screen_pixel = mask.getpixel((50, 50))
        assert (
            screen_pixel == 255
        ), f"Screen center should be white (255), got {screen_pixel}"

        # Check screen edge gradient (alpha=25, should be inverted to 230)
        edge_pixel = mask.getpixel((20, 50))
        msg = f"Screen edge (alpha=25) should be inverted to 230, got {edge_pixel}"
        assert edge_pixel == 230, msg

    def test_apply_screen_mask(self):
        """Test applying screen mask to canvas."""
        # Create canvas with content
        canvas = Image.new("RGBA", (200, 300), (255, 0, 0, 255))

        # Create mask (white in center, black on edges)
        mask = Image.new("L", (100, 150), 0)
        for y in range(25, 125):
            for x in range(15, 85):
                mask.putpixel((x, y), 255)

        # Apply mask
        result = self.renderer.apply_screen_mask(
            canvas, mask, asset_position=(50, 75), asset_size=(100, 150)
        )

        # Result should be RGBA
        assert result.mode == "RGBA"
        assert result.size == canvas.size

        # Check that masked area is visible (red)
        center_pixel = result.getpixel((100, 150))
        assert center_pixel[0] == 255, "Center should have red content"
        assert center_pixel[3] > 0, "Center should be opaque"

        # Check that unmasked area is transparent
        edge_pixel = result.getpixel((10, 10))
        assert edge_pixel[3] == 0, "Edge should be transparent"
