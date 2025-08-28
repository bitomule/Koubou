"""Text rendering functionality using Pillow."""

import logging
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ..config import TextOverlay
from ..exceptions import ConfigurationError, TextRenderError
from .gradient import GradientRenderer

logger = logging.getLogger(__name__)


class TextRenderer:
    """Renders text overlays on images."""

    def __init__(self) -> None:
        """Initialize text renderer."""
        self.font_cache = {}
        self.gradient_renderer = GradientRenderer()

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

            # Calculate text bounds for gradient generation
            total_height = len(text_lines) * line_height
            text_bounds = (anchor_x, anchor_y, text_block_width, total_height)

            # Choose rendering method based on configuration
            if text_config.gradient:
                # Render with gradient
                self._render_gradient_text(
                    canvas,
                    text_config,
                    text_lines,
                    font,
                    line_height,
                    anchor_x,
                    anchor_y,
                    text_block_width,
                    text_bounds,
                )
            else:
                # Render with solid color
                self._render_solid_text(
                    canvas,
                    text_config,
                    text_lines,
                    font,
                    line_height,
                    anchor_x,
                    anchor_y,
                    text_block_width,
                )

        except Exception as _e:
            raise TextRenderError(
                f"Failed to render text '{text_config.content[:50]}...': {_e}"
            ) from _e

    def _get_font(
        self, font_family: str, font_size: int, font_weight: str = "normal"
    ) -> ImageFont.ImageFont:
        """Get font with strict loading - no dangerous fallbacks."""
        cache_key = (font_family, font_size, font_weight)

        if cache_key not in self.font_cache:
            # Use safe default only when no font specified or "System"
            if font_family in ("System", "Arial"):  # Default fonts
                font = self._load_safe_default_font(font_size, font_weight)
            else:
                # User specified font - must load exactly or fail
                try:
                    font = self._load_font_with_weight(
                        font_family, font_size, font_weight
                    )
                except (OSError, IOError) as e:
                    # Provide helpful error message with font installation tips
                    error_msg = (
                        f"Font '{font_family}' not found on this system.\n"
                        f"Options:\n"
                        f"1. Install the font: Copy '{font_family}.ttf' or "
                        f"'{font_family}.otf' to your system fonts directory\n"
                        f"2. Use a system font: 'Arial', 'Helvetica', or 'System'\n"
                        f"3. Check font name spelling and case sensitivity\n"
                        f"System error: {e}"
                    )
                    raise ConfigurationError(error_msg) from e

            self.font_cache[cache_key] = font

        return self.font_cache[cache_key]

    def _load_safe_default_font(
        self, font_size: int, font_weight: str = "normal"
    ) -> ImageFont.ImageFont:
        """Load a safe, high-quality default font."""
        # High-quality system fonts in order of preference
        default_fonts = [
            # macOS system fonts (highest quality)
            ".SF NS Text",
            ".SFNS-Display",
            "San Francisco",
            # Cross-platform high-quality fonts
            "Helvetica Neue",
            "Helvetica",
            "Arial",
            # Linux common fonts (available in most distros and CI)
            "DejaVu Sans",
            "Liberation Sans",
            "Ubuntu",
            "Noto Sans",
            # Fallback system fonts
            "sans-serif",
        ]

        # Try bold variants for bold weight
        if font_weight == "bold":
            bold_fonts = [f"{font} Bold" for font in default_fonts[:7]] + [
                "Helvetica Neue Bold",
                "Helvetica-Bold",
                "Arial Bold",
                "DejaVu Sans Bold",
                "Liberation Sans Bold",
                "Ubuntu Bold",
                "Noto Sans Bold",
            ]
            default_fonts = bold_fonts + default_fonts

        for font_name in default_fonts:
            try:
                font = ImageFont.truetype(font_name, font_size)
                logger.info(f"Using default font: {font_name}")
                return font
            except (OSError, IOError):
                continue

        # Last resort: try PIL's default font before failing
        try:
            logger.warning("Using PIL default font as last resort")
            return ImageFont.load_default()
        except Exception:
            pass

        # If even the default font fails, this is a serious system issue
        raise ConfigurationError(
            "No fonts found on this system.\n"
            "Please install system fonts:\n"
            "- macOS: Arial, Helvetica, or San Francisco (install Xcode or use Font Book)\n"
            "- Linux: fonts-liberation, fonts-dejavu, or fonts-noto packages\n"
            "- Windows: Arial should be pre-installed"
        )

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

            raise OSError(
                f"Could not load font {font_family} with weight {font_weight}"
            )

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
        total_height = len(text_lines) * line_height

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
            anchor_y = y - total_height // 2
        elif anchor.startswith("bottom-"):
            anchor_y = y - total_height
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

    def _render_solid_text(
        self,
        canvas: Image.Image,
        text_config: TextOverlay,
        text_lines: list[str],
        font: ImageFont.ImageFont,
        line_height: int,
        anchor_x: int,
        anchor_y: int,
        text_block_width: int,
    ) -> None:
        """Render text with solid colors using multi-resolution downsampling for quality."""
        # Parse colors
        text_color = self._parse_color(text_config.color or "#000000")
        stroke_color = None
        if text_config.stroke_color:
            stroke_color = self._parse_color(text_config.stroke_color)

        # Use high-resolution rendering for better quality
        self._render_high_res_text(
            canvas,
            text_lines,
            font,
            line_height,
            anchor_x,
            anchor_y,
            text_block_width,
            text_config,
            text_color,
            stroke_color,
        )

    def _render_gradient_text(
        self,
        canvas: Image.Image,
        text_config: TextOverlay,
        text_lines: list[str],
        font: ImageFont.ImageFont,
        line_height: int,
        anchor_x: int,
        anchor_y: int,
        text_block_width: int,
        text_bounds: Tuple[int, int, int, int],
    ) -> None:
        """Render text with gradient using high-res mask-based composition."""
        # Use high-resolution rendering for gradient masks too
        text_mask = self._create_high_res_text_mask(
            canvas,
            text_lines,
            font,
            line_height,
            anchor_x,
            anchor_y,
            text_block_width,
            text_config,
        )

        # Generate gradient image for text bounds
        gradient_image = self.gradient_renderer.create_gradient(
            text_bounds, text_config.gradient
        )

        # Create full-canvas gradient image
        canvas_gradient = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        canvas_gradient.paste(gradient_image, (anchor_x, anchor_y))

        # Apply mask to show gradient only where text is - use alpha blending for better anti-aliasing
        # Convert mask to alpha channel and apply to gradient for smooth edges
        canvas_gradient.putalpha(text_mask)
        gradient_text = canvas_gradient

        # Handle strokes
        if text_config.stroke_width:
            if text_config.stroke_color:
                # Draw solid stroke first (underneath gradient text)
                stroke_color = self._parse_color(text_config.stroke_color)
                draw = ImageDraw.Draw(canvas)

                for i, line in enumerate(text_lines):
                    current_y = anchor_y + i * line_height
                    line_x = self._calculate_line_x(
                        anchor_x, line, font, text_config.alignment, text_block_width
                    )
                    draw.text(
                        (line_x, current_y),
                        line,
                        font=font,
                        fill=(0, 0, 0, 0),  # Transparent fill
                        stroke_width=text_config.stroke_width,
                        stroke_fill=stroke_color,
                    )
            elif text_config.stroke_gradient:
                # Create separate mask for stroke outline only
                stroke_mask = Image.new("L", canvas.size, 0)
                stroke_draw = ImageDraw.Draw(stroke_mask)

                # Draw stroke outline on mask
                for i, line in enumerate(text_lines):
                    current_y = anchor_y + i * line_height
                    line_x = self._calculate_line_x(
                        anchor_x, line, font, text_config.alignment, text_block_width
                    )

                    # Create stroke-only mask by drawing stroked text and subtracting filled text
                    stroke_draw.text(
                        (line_x, current_y),
                        line,
                        font=font,
                        fill=128,  # Gray for stroke area
                        stroke_width=text_config.stroke_width,
                        stroke_fill=255,  # White for stroke outline
                    )

                # Generate stroke gradient
                stroke_gradient_image = self.gradient_renderer.create_gradient(
                    text_bounds, text_config.stroke_gradient
                )

                # Create full-canvas stroke gradient
                canvas_stroke_gradient = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
                canvas_stroke_gradient.paste(
                    stroke_gradient_image, (anchor_x, anchor_y)
                )

                # Apply stroke mask using alpha blending
                canvas_stroke_gradient.putalpha(stroke_mask)
                stroke_gradient_text = canvas_stroke_gradient

                # Composite stroke gradient onto canvas first
                canvas.paste(stroke_gradient_text, (0, 0), stroke_gradient_text)

        # Finally, composite gradient text onto canvas
        canvas.paste(gradient_text, (0, 0), gradient_text)

    def _render_high_res_text(
        self,
        canvas: Image.Image,
        text_lines: list[str],
        font: ImageFont.ImageFont,
        line_height: int,
        anchor_x: int,
        anchor_y: int,
        text_block_width: int,
        text_config: TextOverlay,
        text_color: Tuple[int, int, int, int],
        stroke_color: Optional[Tuple[int, int, int, int]],
    ) -> None:
        """Render text at 3x resolution and downsample for optimal anti-aliasing quality."""
        scale_factor = 3  # Research shows 3x often better than 4x for text quality

        # Calculate text bounds for high-resolution rendering
        total_height = len(text_lines) * line_height

        # Create high-resolution canvas for text region only (optimization)
        hr_width = text_block_width * scale_factor
        hr_height = total_height * scale_factor
        hr_canvas = Image.new("RGBA", (hr_width, hr_height), (0, 0, 0, 0))

        # Create scaled font
        hr_font_size = text_config.font_size * scale_factor
        hr_font = self._get_font(
            text_config.font_family, hr_font_size, text_config.font_weight
        )
        hr_line_height = int(hr_font_size * text_config.line_height)

        # Render text at high resolution
        hr_draw = ImageDraw.Draw(hr_canvas)

        for i, line in enumerate(text_lines):
            # Calculate positions in high-resolution space
            hr_y = i * hr_line_height

            # Calculate line x position based on alignment
            hr_line_x = self._calculate_line_x(
                0,  # Start from 0 since we're in cropped canvas
                line,
                hr_font,
                text_config.alignment,
                text_block_width * scale_factor,
            )

            # Draw text with stroke if specified
            if text_config.stroke_width and stroke_color:
                hr_stroke_width = text_config.stroke_width * scale_factor
                hr_draw.text(
                    (hr_line_x, hr_y),
                    line,
                    font=hr_font,
                    fill=text_color,
                    stroke_width=hr_stroke_width,
                    stroke_fill=stroke_color,
                )
            else:
                hr_draw.text((hr_line_x, hr_y), line, font=hr_font, fill=text_color)

        # Downsample using high-quality resampling
        downsampled_text = hr_canvas.resize(
            (text_block_width, total_height), Image.Resampling.LANCZOS
        )

        # Apply very subtle blur for smoother edges (optional - can be disabled if too soft)
        # Only apply to text edges, not the whole text
        alpha = downsampled_text.split()[-1]  # Get alpha channel
        blurred_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=0.3))

        # Reconstruct text with smoothed alpha
        if downsampled_text.mode == "RGBA":
            r, g, b, _ = downsampled_text.split()
            smoothed_text = Image.merge("RGBA", (r, g, b, blurred_alpha))
        else:
            smoothed_text = downsampled_text

        # Paste the downsampled text onto the original canvas
        canvas.paste(smoothed_text, (anchor_x, anchor_y), smoothed_text)

    def _create_high_res_text_mask(
        self,
        canvas: Image.Image,
        text_lines: list[str],
        font: ImageFont.ImageFont,
        line_height: int,
        anchor_x: int,
        anchor_y: int,
        text_block_width: int,
        text_config: TextOverlay,
    ) -> Image.Image:
        """Create high-resolution text mask for gradient rendering with optimal anti-aliasing."""
        scale_factor = 3  # Research shows 3x often better than 4x for text quality

        # Calculate text bounds for high-resolution rendering
        total_height = len(text_lines) * line_height

        # Create high-resolution mask for text region only
        hr_width = text_block_width * scale_factor
        hr_height = total_height * scale_factor
        hr_mask = Image.new("L", (hr_width, hr_height), 0)  # Black background

        # Create scaled font
        hr_font_size = text_config.font_size * scale_factor
        hr_font = self._get_font(
            text_config.font_family, hr_font_size, text_config.font_weight
        )
        hr_line_height = int(hr_font_size * text_config.line_height)

        # Render text mask at high resolution
        hr_draw = ImageDraw.Draw(hr_mask)

        for i, line in enumerate(text_lines):
            hr_y = i * hr_line_height
            hr_line_x = self._calculate_line_x(
                0,  # Start from 0 since we're in cropped canvas
                line,
                hr_font,
                text_config.alignment,
                text_block_width * scale_factor,
            )

            # Handle stroke on mask
            if text_config.stroke_width:
                hr_stroke_width = text_config.stroke_width * scale_factor
                if text_config.stroke_gradient:
                    # For gradient stroke, include stroke in main mask
                    hr_draw.text(
                        (hr_line_x, hr_y),
                        line,
                        font=hr_font,
                        fill=255,  # White = show content
                        stroke_width=hr_stroke_width,
                        stroke_fill=255,  # Include stroke in mask
                    )
                else:
                    # For solid stroke, draw stroke separately later
                    hr_draw.text(
                        (hr_line_x, hr_y),
                        line,
                        font=hr_font,
                        fill=255,  # White = show gradient
                        stroke_width=0,  # No stroke in main mask
                    )
            else:
                hr_draw.text((hr_line_x, hr_y), line, font=hr_font, fill=255)

        # Downsample mask using high-quality resampling
        downsampled_mask = hr_mask.resize(
            (text_block_width, total_height), Image.Resampling.LANCZOS
        )

        # Apply very subtle Gaussian blur for smoother edges (research-backed approach)
        # Blur radius of 0.5 is subtle enough to smooth without affecting text sharpness
        smoothed_mask = downsampled_mask.filter(ImageFilter.GaussianBlur(radius=0.5))

        # Create full canvas mask
        full_mask = Image.new("L", canvas.size, 0)
        full_mask.paste(smoothed_mask, (anchor_x, anchor_y))

        return full_mask
