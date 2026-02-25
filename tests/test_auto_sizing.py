"""Tests for text auto-sizing feature."""

import pytest
from PIL import Image
from pydantic import ValidationError

from koubou.config import ContentItem, TextOverlay
from koubou.renderers.text import TextRenderer


class TestAutoSizingConfig:
    """Tests for auto-sizing configuration fields and validation."""

    def test_content_item_auto_sizing_fields(self):
        """Test ContentItem accepts auto-sizing fields."""
        item = ContentItem(
            type="text",
            content="Hello",
            size=120,
            max_width=1000,
            max_height=400,
            min_size=72,
        )
        assert item.max_width == 1000
        assert item.max_height == 400
        assert item.min_size == 72

    def test_content_item_defaults_none(self):
        """Test auto-sizing fields default to None."""
        item = ContentItem(type="text", content="Hello")
        assert item.max_width is None
        assert item.max_height is None
        assert item.max_lines is None
        assert item.min_size is None

    def test_text_overlay_auto_sizing_fields(self):
        """Test TextOverlay accepts auto-sizing fields."""
        overlay = TextOverlay(
            content="Hello",
            position=(100, 100),
            font_size=120,
            color="#000000",
            min_font_size=72,
            max_height=400,
            max_width=1000,
        )
        assert overlay.min_font_size == 72
        assert overlay.max_height == 400

    def test_text_overlay_auto_sizing_defaults_none(self):
        """Test TextOverlay auto-sizing fields default to None."""
        overlay = TextOverlay(
            content="Hello",
            position=(100, 100),
            color="#000000",
        )
        assert overlay.min_font_size is None
        assert overlay.max_height is None

    def test_min_size_requires_max_width(self):
        """Test that min_size without max_width raises validation error."""
        with pytest.raises(ValidationError, match="min_size requires max_width"):
            ContentItem(
                type="text",
                content="Hello",
                size=120,
                max_height=400,
                min_size=72,
            )

    def test_min_size_requires_max_height(self):
        """Test that min_size without max_height raises validation error."""
        with pytest.raises(ValidationError, match="min_size requires max_height"):
            ContentItem(
                type="text",
                content="Hello",
                size=120,
                max_width=1000,
                min_size=72,
            )

    def test_min_size_must_be_lte_size(self):
        """Test that min_size > size raises validation error."""
        with pytest.raises(ValidationError, match="min_size.*must be <= size"):
            ContentItem(
                type="text",
                content="Hello",
                size=72,
                max_width=1000,
                max_height=400,
                min_size=120,
            )

    def test_min_size_equal_to_size_is_valid(self):
        """Test that min_size == size is accepted (fixed size with height check)."""
        item = ContentItem(
            type="text",
            content="Hello",
            size=100,
            max_width=1000,
            max_height=400,
            min_size=100,
        )
        assert item.min_size == 100

    def test_max_width_and_max_lines_without_min_size(self):
        """Test that max_width/max_lines work without min_size (no auto-sizing)."""
        item = ContentItem(
            type="text",
            content="Hello",
            max_width=500,
            max_lines=3,
        )
        assert item.max_width == 500
        assert item.max_lines == 3
        assert item.min_size is None

    def test_max_height_without_min_size_is_valid(self):
        """max_height alone (without min_size) is accepted."""
        item = ContentItem(
            type="text",
            content="Hello",
            max_width=500,
            max_height=400,
        )
        assert item.max_height == 400
        assert item.min_size is None

    def test_non_text_items_ignore_auto_sizing_fields(self):
        """Test that image items can have auto-sizing fields without validation."""
        item = ContentItem(
            type="image",
            asset="test.png",
        )
        assert item.min_size is None
        assert item.max_height is None

    def test_min_size_one_less_than_size_is_valid(self):
        """Test min_size just below size is accepted."""
        item = ContentItem(
            type="text",
            content="Hello",
            size=100,
            max_width=500,
            max_height=400,
            min_size=99,
        )
        assert item.min_size == 99


class TestAutoSizingRenderer:
    """Tests for auto-sizing in the text renderer."""

    def setup_method(self):
        """Setup test method."""
        self.renderer = TextRenderer()
        self.canvas = Image.new("RGBA", (800, 600), (255, 255, 255, 255))

    def test_short_text_renders_at_max_size(self):
        """Short text that fits easily should render at maximum font size."""
        size = self.renderer._auto_size_font(
            text="Hi",
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=72,
            max_width=1000,
            max_height=400,
            line_height_multiplier=1.2,
        )
        assert size == 120

    def test_single_word_renders_at_max_size(self):
        """A single short word should always fit at max size."""
        size = self.renderer._auto_size_font(
            text="Hello",
            font_family="Arial",
            font_weight="normal",
            max_size=100,
            min_size=40,
            max_width=500,
            max_height=200,
            line_height_multiplier=1.2,
        )
        assert size == 100

    def test_long_text_shrinks_below_max(self):
        """Long text that overflows should shrink below max_size."""
        size = self.renderer._auto_size_font(
            text="This is a very long sentence that will definitely need to wrap "
            "across multiple lines and may exceed the height budget",
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=40,
            max_width=400,
            max_height=200,
            line_height_multiplier=1.2,
        )
        assert size < 120
        assert size >= 40

    def test_auto_size_respects_min_floor(self):
        """Even if text doesn't fit at min_size, return min_size."""
        # Use wide characters repeated many times to guarantee overflow
        size = self.renderer._auto_size_font(
            text=" ".join(["WWWWWWWWWW"] * 50),
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=72,
            max_width=200,
            max_height=50,  # Very tight height budget
            line_height_multiplier=1.2,
        )
        assert size == 72

    def test_auto_size_finds_exact_largest(self):
        """Binary search should find the exact largest size that fits."""
        max_height = 400
        text = "This text needs some shrinking to fit properly"
        size = self.renderer._auto_size_font(
            text=text,
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=40,
            max_width=400,
            max_height=max_height,
            line_height_multiplier=1.2,
        )
        # Resolved size should fit
        font = self.renderer._get_font("Arial", size, "normal")
        lines = self.renderer._prepare_text(text, font, 400, None, None)
        assert len(lines) * int(size * 1.2) <= max_height
        # size + 1 should NOT fit (binary search finds the exact boundary)
        if size < 120:
            font_larger = self.renderer._get_font("Arial", size + 1, "normal")
            lines_larger = self.renderer._prepare_text(
                text, font_larger, 400, None, None
            )
            assert len(lines_larger) * int((size + 1) * 1.2) > max_height

    def test_auto_size_height_constraint_verified(self):
        """Verify the resolved size actually fits within max_height."""
        max_height = 200
        text = "Multiple words that will wrap to several lines of text"
        size = self.renderer._auto_size_font(
            text=text,
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=40,
            max_width=300,
            max_height=max_height,
            line_height_multiplier=1.2,
        )
        # Verify: load font at resolved size, wrap text, check height
        font = self.renderer._get_font("Arial", size, "normal")
        lines = self.renderer._prepare_text(text, font, 300, None, None)
        total_height = len(lines) * int(size * 1.2)
        assert total_height <= max_height

    def test_auto_size_next_larger_would_overflow(self):
        """Verify the next size up (size + 1) would exceed max_height."""
        max_height = 200
        text = "Several words forming a sentence that wraps across lines"
        size = self.renderer._auto_size_font(
            text=text,
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=40,
            max_width=300,
            max_height=max_height,
            line_height_multiplier=1.2,
        )
        if size < 120:
            # The next size up should NOT fit
            larger = size + 1
            font = self.renderer._get_font("Arial", larger, "normal")
            lines = self.renderer._prepare_text(text, font, 300, None, None)
            total_height = len(lines) * int(larger * 1.2)
            assert total_height > max_height

    def test_tight_height_forces_smaller_font(self):
        """A very tight max_height should force a small font size."""
        size = self.renderer._auto_size_font(
            text="Some text that needs to fit",
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=20,
            max_width=200,
            max_height=30,  # Only room for ~1 line at small size
            line_height_multiplier=1.2,
        )
        assert size < 120
        # At the resolved size, 1 line should fit in 30px
        assert int(size * 1.2) <= 30

    def test_generous_height_allows_max_size(self):
        """A very generous max_height should allow max_size."""
        size = self.renderer._auto_size_font(
            text="Some text",
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=40,
            max_width=1000,
            max_height=2000,  # Very generous
            line_height_multiplier=1.2,
        )
        assert size == 120

    def test_line_height_multiplier_affects_result(self):
        """A larger line_height_multiplier should produce smaller font sizes."""
        text = "Text that wraps to multiple lines when constrained"
        size_normal = self.renderer._auto_size_font(
            text=text,
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=40,
            max_width=250,
            max_height=300,
            line_height_multiplier=1.2,
        )
        size_spacious = self.renderer._auto_size_font(
            text=text,
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=40,
            max_width=250,
            max_height=300,
            line_height_multiplier=2.0,  # Much taller lines
        )
        assert size_spacious <= size_normal

    def test_narrower_width_forces_smaller_font(self):
        """Narrower max_width means more lines, which may exceed max_height."""
        text = "A sentence with enough words to wrap differently at different widths"
        size_wide = self.renderer._auto_size_font(
            text=text,
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=40,
            max_width=800,
            max_height=300,
            line_height_multiplier=1.2,
        )
        size_narrow = self.renderer._auto_size_font(
            text=text,
            font_family="Arial",
            font_weight="normal",
            max_size=120,
            min_size=40,
            max_width=200,
            max_height=300,
            line_height_multiplier=1.2,
        )
        assert size_narrow <= size_wide


class TestAutoSizingRenderIntegration:
    """Integration tests for auto-sizing through the full render pipeline."""

    def setup_method(self):
        """Setup test method."""
        self.renderer = TextRenderer()
        self.canvas = Image.new("RGBA", (800, 600), (255, 255, 255, 255))

    def test_no_auto_sizing_without_min_font_size(self):
        """Without min_font_size, render() should not auto-size."""
        overlay = TextOverlay(
            content="Hello World",
            position=(100, 100),
            font_size=80,
            color="#000000",
            max_width=300,
            max_height=200,
        )
        self.renderer.render(overlay, self.canvas)
        assert overlay.font_size == 80

    def test_no_auto_sizing_without_max_height(self):
        """Without max_height, render() should not auto-size."""
        overlay = TextOverlay(
            content="Hello World",
            position=(100, 100),
            font_size=80,
            color="#000000",
            max_width=300,
            min_font_size=40,
        )
        self.renderer.render(overlay, self.canvas)
        assert overlay.font_size == 80

    def test_no_auto_sizing_without_max_width(self):
        """Without max_width, render() should not auto-size."""
        overlay = TextOverlay(
            content="Hello World",
            position=(100, 100),
            font_size=80,
            color="#000000",
            max_height=200,
            min_font_size=40,
        )
        self.renderer.render(overlay, self.canvas)
        assert overlay.font_size == 80

    def test_auto_sizing_does_not_mutate_config(self):
        """Render should not mutate the original config object."""
        overlay = TextOverlay(
            content="This is quite a long headline that needs multiple lines "
            "to display properly and will overflow the height",
            position=(400, 100),
            font_size=120,
            color="#000000",
            max_width=400,
            max_height=200,
            min_font_size=40,
        )
        self.renderer.render(overlay, self.canvas)
        assert overlay.font_size == 120

    def test_auto_sizing_short_text_stays_at_max(self):
        """Short text should keep original font_size after render."""
        overlay = TextOverlay(
            content="Hi",
            position=(200, 100),
            font_size=100,
            color="#000000",
            max_width=500,
            max_height=300,
            min_font_size=40,
        )
        self.renderer.render(overlay, self.canvas)
        assert overlay.font_size == 100

    def test_render_with_auto_sizing_does_not_raise(self):
        """Full render with auto-sizing should complete without errors."""
        overlay = TextOverlay(
            content="A beautiful headline for screenshots",
            position=(200, 100),
            font_size=100,
            color="#333333",
            max_width=350,
            max_height=250,
            min_font_size=50,
        )
        self.renderer.render(overlay, self.canvas)
        assert self.canvas.size == (800, 600)

    def test_auto_sizing_with_max_lines_truncation(self):
        """Auto-sizing and max_lines should work together.

        Auto-sizing picks the font size based on max_height, then max_lines
        truncates if needed (as a separate safety net).
        """
        overlay = TextOverlay(
            content="Word " * 30,  # Very long text
            position=(400, 300),
            font_size=80,
            color="#000000",
            max_width=300,
            max_height=250,
            max_lines=3,
            min_font_size=30,
        )
        self.renderer.render(overlay, self.canvas)
        # Auto-sizing should have reduced the font size
        assert overlay.font_size <= 80
        assert overlay.font_size >= 30

    def test_auto_sizing_with_gradient_text(self):
        """Auto-sizing should work with gradient text fills."""
        from koubou.config import GradientConfig

        overlay = TextOverlay(
            content="Gradient headline that may need to shrink",
            position=(400, 100),
            font_size=100,
            gradient=GradientConfig(type="linear", colors=["#ff0000", "#0000ff"]),
            max_width=300,
            max_height=200,
            min_font_size=40,
        )
        # Should not raise
        self.renderer.render(overlay, self.canvas)
        assert overlay.font_size >= 40

    def test_auto_sizing_preserves_alignment(self):
        """Auto-sizing should not affect text alignment settings."""
        for alignment in ["left", "center", "right"]:
            canvas = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
            overlay = TextOverlay(
                content="Aligned auto-sized text",
                position=(400, 100),
                font_size=100,
                color="#000000",
                alignment=alignment,
                max_width=300,
                max_height=200,
                min_font_size=40,
            )
            self.renderer.render(overlay, canvas)
            assert overlay.alignment == alignment


class TestAutoSizingGeneratorMapping:
    """Tests for ContentItem → TextOverlay field mapping in the generator."""

    def test_content_item_fields_map_to_text_overlay(self):
        """Verify that ContentItem auto-sizing fields can construct a TextOverlay."""
        item = ContentItem(
            type="text",
            content="Hello",
            size=120,
            max_width=1000,
            max_lines=3,
            max_height=400,
            min_size=72,
            color="#000000",
        )
        # Simulate what generator.py does
        overlay = TextOverlay(
            content=item.content,
            position=(100, 100),
            font_size=item.size or 24,
            color=item.color,
            max_width=item.max_width,
            max_lines=item.max_lines,
            min_font_size=item.min_size,
            max_height=item.max_height,
        )
        assert overlay.font_size == 120
        assert overlay.max_width == 1000
        assert overlay.max_lines == 3
        assert overlay.min_font_size == 72
        assert overlay.max_height == 400

    def test_content_item_none_fields_map_cleanly(self):
        """ContentItem with no auto-sizing fields maps to TextOverlay with None."""
        item = ContentItem(
            type="text",
            content="Hello",
            color="#000000",
        )
        overlay = TextOverlay(
            content=item.content,
            position=(100, 100),
            font_size=item.size or 24,
            color=item.color,
            max_width=item.max_width,
            max_lines=item.max_lines,
            min_font_size=item.min_size,
            max_height=item.max_height,
        )
        assert overlay.min_font_size is None
        assert overlay.max_height is None
        assert overlay.max_width is None
        assert overlay.max_lines is None
