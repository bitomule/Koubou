"""Background rendering functionality using unified gradient system."""

import logging
from typing import Tuple

from PIL import Image

from ..config import GradientConfig
from ..exceptions import BackgroundRenderError
from .gradient import GradientRenderer

logger = logging.getLogger(__name__)


class BackgroundRenderer:
    """Renders various types of backgrounds on images using unified gradient system."""

    def __init__(self) -> None:
        """Initialize background renderer with gradient renderer."""
        self.gradient_renderer = GradientRenderer()

    def render(self, background_config: GradientConfig, canvas: Image.Image) -> None:
        """Render background on the provided canvas using unified gradient system.

        Args:
            background_config: Background configuration
            canvas: PIL Image to render background on (modified in place)

        Raises:
            BackgroundRenderError: If rendering fails
        """
        try:
            if background_config.type == "solid":
                self._render_solid(background_config, canvas)
            else:
                # Use unified gradient renderer for all gradients
                gradient = self.gradient_renderer.create_gradient(
                    (0, 0, canvas.width, canvas.height), background_config
                )
                canvas.paste(gradient, (0, 0))

        except Exception as e:
            raise BackgroundRenderError(
                f"Failed to render {background_config.type} background: {e}"
            ) from e

    def _render_solid(self, config: GradientConfig, canvas: Image.Image) -> None:
        """Render solid color background."""
        if not config.colors:
            raise BackgroundRenderError("No colors specified for solid background")

        color = self._parse_color(config.colors[0])

        # Create solid color overlay
        overlay = Image.new("RGBA", canvas.size, color)
        canvas.paste(overlay, (0, 0))

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
            raise BackgroundRenderError(f"Invalid color format: {color_string}")

        return (r, g, b, a)
