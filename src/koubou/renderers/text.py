"""Text rendering functionality using Pillow."""

import logging
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from ..config import TextOverlay
from ..exceptions import TextRenderError

logger = logging.getLogger(__name__)


class TextRenderer:
    """Renders text overlays on images."""

    def __init__(self):
        """Initialize text renderer."""
        self.font_cache = {}

    def render(self, text_config: TextOverlay, canvas: Image.Image) -> None:
        """Render text overlay on the provided canvas.

        Args:
            text_config: Text configuration
            canvas: PIL Image to render text on (modified in place)

        Raises:
            TextRenderError: If rendering fails
        """
        try:
            # Load font
            font = self._get_font(
                text_config.font_family, text_config.font_size, text_config.font_weight
            )

            # Parse colors
            text_color = self._parse_color(text_config.color)
            stroke_color = None
            if text_config.stroke_color:
                stroke_color = self._parse_color(text_config.stroke_color)

            # Prepare text with wrapping if needed
            text_lines = self._prepare_text(
                text_config.content,
                font,
                text_config.max_width,
                text_config.max_lines,
                canvas.width,
            )

            # Calculate total text dimensions
            line_height = int(text_config.font_size * text_config.line_height)
            _total_height = len(text_lines) * line_height

            # Get drawing context
            draw = ImageDraw.Draw(canvas)

            # Calculate anchor-adjusted position
            anchor_x, anchor_y = self._calculate_anchor_position(
                text_config.position,
                text_lines,
                font,
                line_height,
                text_config.anchor,
                text_config.max_width,
                canvas,
                text_config,
            )

            # Calculate the actual text block width (longest line)
            text_block_width = text_config.max_width
            if not text_block_width:
                text_block_width = 0
                for line in text_lines:
                    bbox = font.getbbox(line)
                    line_width = bbox[2] - bbox[0]
                    text_block_width = max(text_block_width, line_width)

            # Render each line
            for i, line in enumerate(text_lines):
                current_y = anchor_y + i * line_height

                # Calculate x position based on alignment within the text block
                line_x = self._calculate_line_x(
                    anchor_x, line, font, text_config.alignment, text_block_width
                )

                # Draw text with stroke if specified
                if text_config.stroke_width and stroke_color:
                    draw.text(
                        (line_x, current_y),
                        line,
                        font=font,
                        fill=text_color,
                        stroke_width=text_config.stroke_width,
                        stroke_fill=stroke_color,
                    )
                else:
                    draw.text((line_x, current_y), line, font=font, fill=text_color)

        except Exception as _e:
            raise TextRenderError(
                f"Failed to render text '{text_config.content[:50]}...': {_e}"
            ) from _e

    def _get_font(
        self, font_family: str, font_size: int, font_weight: str = "normal"
    ) -> ImageFont.ImageFont:
        """Get font, using cache for performance."""
        cache_key = (font_family, font_size, font_weight)

        if cache_key not in self.font_cache:
            try:
                # Try to load the specified font with weight
                font = self._load_font_with_weight(font_family, font_size, font_weight)
            except (OSError, IOError):
                # Fall back to default font
                logger.warning(
                    "Could not load font '{font_family}' with weight '{font_weight}', using default"
                )
                try:
                    font = ImageFont.load_default()
                except Exception:
                    # Last resort: create a basic font
                    font = ImageFont.load_default()

            self.font_cache[cache_key] = font

        return self.font_cache[cache_key]

    def _load_font_with_weight(
        self, font_family: str, font_size: int, font_weight: str
    ) -> ImageFont.ImageFont:
        """Load font with weight support, trying different naming conventions."""
        # Common system fonts with bold variants
        font_variants = {
            "Arial": {
                "normal": ["Arial.ttf", "arial.ttf", "Arial"],
                "bold": ["Arial Bold.ttf", "arial-bold.ttf", "Arial-Bold.ttf", "Arial"],
            },
            "Helvetica": {
                "normal": ["Helvetica.ttc", "helvetica.ttf", "Helvetica"],
                "bold": ["Helvetica-Bold.ttc", "helvetica-bold.ttf", "Helvetica"],
            },
            "System": {
                "normal": [
                    ".SF NS Text",
                    ".SFNS-Display",
                    "San Francisco",
                    "Helvetica Neue",
                ],
                "bold": [
                    ".SF NS Text Bold",
                    ".SFNS-Display Bold",
                    "San Francisco Bold",
                    "Helvetica Neue Bold",
                ],
            },
        }

        # Try to find the appropriate font variant
        variants = font_variants.get(
            font_family, {"normal": [font_family], "bold": [font_family]}
        )
        font_names = variants.get(font_weight, variants.get("normal", [font_family]))

        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, font_size)
            except (OSError, IOError):
                continue

        # If no specific variant found, try the base font name
        try:
            return ImageFont.truetype(font_family, font_size)
        except (OSError, IOError):
            # Try system font approximation for bold
            if font_weight == "bold":
                try:
                    # On macOS, try to find system fonts
                    for system_font in [".SF NS Text", "Helvetica Neue", "Arial"]:
                        try:
                            return ImageFont.truetype(system_font, font_size)
                        except (OSError, IOError):
                            continue
                except Exception:
                    pass

            raise OSError(f"Could not load font {font_family} with weight {font_weight}")

    def _parse_color(self, color_string: str) -> Tuple[int, int, int, int]:
        """Parse hex color string to RGBA tuple."""
        hex_color = color_string.lstrip("#")

        if len(hex_color) == 3:
            # RGB
            r = int(hex_color[0] * 2, 16)
            g = int(hex_color[1] * 2, 16)
            b = int(hex_color[2] * 2, 16)
            a = 255
        elif len(hex_color) == 6:
            # RRGGBB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = 255
        elif len(hex_color) == 8:
            # RRGGBBAA
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16)
        else:
            raise TextRenderError(f"Invalid color format: {color_string}")

        return (r, g, b, a)

    def _prepare_text(
        self,
        text: str,
        font: ImageFont.ImageFont,
        max_width: Optional[int],
        max_lines: Optional[int] = None,
        canvas_width: Optional[int] = None,
    ) -> list[str]:
        """Prepare text with word wrapping if needed."""
        # If no max_width specified, default to 100% of canvas width
        if not max_width:
            if canvas_width:
                max_width = canvas_width  # 100% of canvas width
            else:
                return [text]  # Fallback: no wrapping if canvas width unknown

        # Use textwrap for basic wrapping, then verify with font metrics
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])

            # Check if this line fits within max_width
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:
                current_line.append(word)
            else:
                # Current line is too long, finish previous line and start new one
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, add it anyway
                    lines.append(word)

        # Add remaining words
        if current_line:
            lines.append(" ".join(current_line))

        # Apply max_lines limit if specified
        if max_lines and len(lines) > max_lines:
            lines = lines[:max_lines]
            # Add ellipsis to the last line if text was truncated
            if len(lines) == max_lines and lines:
                lines[-1] += "..."

        return lines

    def _calculate_anchor_position(
        self,
        position: Tuple[int, int],
        text_lines: list[str],
        font: ImageFont.ImageFont,
        line_height: int,
        anchor: str,
        max_width: Optional[int],
        canvas: Image.Image,
        text_config,
    ) -> Tuple[int, int]:
        """Calculate the anchor-adjusted position for text rendering."""
        x, y = position

        # Calculate text dimensions
        _total_height = len(text_lines) * line_height

        # Calculate the widest line to determine text width
        if max_width:
            text_width = max_width
        else:
            text_width = 0
            for line in text_lines:
                bbox = font.getbbox(line)
                line_width = bbox[2] - bbox[0]
                text_width = max(text_width, line_width)

            # Remove auto-scaling - render exactly what user asks for

        # Adjust position based on anchor
        if anchor.endswith("-left"):
            anchor_x = x
        elif anchor.endswith("-center") or anchor == "center":
            anchor_x = x - text_width // 2
        elif anchor.endswith("-right"):
            anchor_x = x - text_width
        else:
            anchor_x = x

        if anchor.startswith("top-"):
            anchor_y = y
        elif anchor.startswith("center-") or anchor == "center":
            anchor_y = y - _total_height // 2
        elif anchor.startswith("bottom-"):
            anchor_y = y - _total_height
        else:
            anchor_y = y

        return (anchor_x, anchor_y)

    def _calculate_line_x(
        self,
        base_x: int,
        line: str,
        font: ImageFont.ImageFont,
        alignment: str,
        alignment_width: int,
    ) -> int:
        """Calculate x position for a line based on alignment within the text area."""
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]

        if alignment == "left":
            return base_x
        elif alignment == "center":
            # Center within the alignment area
            return base_x + (alignment_width - text_width) // 2
        elif alignment == "right":
            # Right align within the alignment area
            return base_x + (alignment_width - text_width)

        return base_x
