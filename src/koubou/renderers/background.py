"""Background rendering functionality using Pillow."""

import logging
import math
from typing import List, Tuple

from PIL import Image, ImageDraw

from ..config import BackgroundConfig
from ..exceptions import BackgroundRenderError

logger = logging.getLogger(__name__)


class BackgroundRenderer:
    """Renders various types of backgrounds on images."""

    def render(self, background_config: BackgroundConfig, canvas: Image.Image) -> None:
        """Render background on the provided canvas.

        Args:
            background_config: Background configuration
            canvas: PIL Image to render background on (modified in place)

        Raises:
            BackgroundRenderError: If rendering fails
        """
        try:
            if background_config.type == "solid":
                self._render_solid(background_config, canvas)
            elif background_config.type == "linear":
                self._render_linear_gradient(background_config, canvas)
            elif background_config.type == "radial":
                self._render_radial_gradient(background_config, canvas)
            elif background_config.type == "conic":
                self._render_conic_gradient(background_config, canvas)
            else:
                raise BackgroundRenderError(
                    "Unknown background type: {background_config.type}"
                )

        except Exception as _e:
            raise BackgroundRenderError(
                f"Failed to render {background_config.type} background: {_e}"
            ) from _e

    def _render_solid(self, config: BackgroundConfig, canvas: Image.Image) -> None:
        """Render solid color background."""
        if not config.colors:
            raise BackgroundRenderError("No colors specified for solid background")

        color = self._parse_color(config.colors[0])

        # Create solid color overlay
        overlay = Image.new("RGBA", canvas.size, color)
        canvas.paste(overlay, (0, 0))

    def _render_linear_gradient(
        self, config: BackgroundConfig, canvas: Image.Image
    ) -> None:
        """Render linear gradient background."""
        if len(config.colors) < 2:
            raise BackgroundRenderError("Linear gradient requires at least 2 colors")

        width, height = canvas.size
        colors = [self._parse_color(c) for c in config.colors]
        direction = config.direction or 0

        # Create gradient
        gradient = self._create_linear_gradient(width, height, colors, direction)
        canvas.paste(gradient, (0, 0))

    def _render_radial_gradient(
        self, config: BackgroundConfig, canvas: Image.Image
    ) -> None:
        """Render radial gradient background."""
        if len(config.colors) < 2:
            raise BackgroundRenderError("Radial gradient requires at least 2 colors")

        width, height = canvas.size
        colors = [self._parse_color(c) for c in config.colors]

        # Determine center point
        if config.center:
            center_x = self._parse_position(config.center[0], width)
            center_y = self._parse_position(config.center[1], height)
        else:
            center_x = width // 2
            center_y = height // 2

        # Create radial gradient
        gradient = self._create_radial_gradient(
            width, height, colors, (center_x, center_y)
        )
        canvas.paste(gradient, (0, 0))

    def _render_conic_gradient(
        self, config: BackgroundConfig, canvas: Image.Image
    ) -> None:
        """Render conic (angular) gradient background."""
        if len(config.colors) < 2:
            raise BackgroundRenderError("Conic gradient requires at least 2 colors")

        width, height = canvas.size
        colors = [self._parse_color(c) for c in config.colors]

        # Determine center point
        if config.center:
            center_x = self._parse_position(config.center[0], width)
            center_y = self._parse_position(config.center[1], height)
        else:
            center_x = width // 2
            center_y = height // 2

        # Create conic gradient
        gradient = self._create_conic_gradient(
            width, height, colors, (center_x, center_y)
        )
        canvas.paste(gradient, (0, 0))

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

    def _parse_position(self, position: str, total: int) -> int:
        """Parse position string (e.g., '50%' or '100') to pixel value."""
        if position.endswith("%"):
            percent = float(position[:-1])
            return int(total * percent / 100)
        else:
            return int(float(position))

    def _create_linear_gradient(
        self,
        width: int,
        height: int,
        colors: List[Tuple[int, int, int, int]],
        direction: float,
    ) -> Image.Image:
        """Create linear gradient image."""
        # Convert direction from degrees to radians
        angle = math.radians(direction)

        # Create gradient
        gradient = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(gradient)

        # Calculate gradient vector
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)

        # For each pixel, calculate position along gradient
        for y in range(height):
            for x in range(width):
                # Normalize coordinates to center
                nx = (x - width / 2) / (width / 2)
                ny = (y - height / 2) / (height / 2)

                # Project onto gradient direction
                t = (nx * cos_angle + ny * sin_angle + 1) / 2
                t = max(0, min(1, t))

                # Interpolate color
                color = self._interpolate_colors(colors, t)
                draw.point((x, y), color)

        return gradient

    def _create_radial_gradient(
        self,
        width: int,
        height: int,
        colors: List[Tuple[int, int, int, int]],
        center: Tuple[int, int],
    ) -> Image.Image:
        """Create radial gradient image."""
        gradient = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(gradient)

        center_x, center_y = center
        max_distance = max(
            math.sqrt(center_x**2 + center_y**2),
            math.sqrt((width - center_x) ** 2 + center_y**2),
            math.sqrt(center_x**2 + (height - center_y) ** 2),
            math.sqrt((width - center_x) ** 2 + (height - center_y) ** 2),
        )

        for y in range(height):
            for x in range(width):
                distance = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                t = distance / max_distance
                t = max(0, min(1, t))

                color = self._interpolate_colors(colors, t)
                draw.point((x, y), color)

        return gradient

    def _create_conic_gradient(
        self,
        width: int,
        height: int,
        colors: List[Tuple[int, int, int, int]],
        center: Tuple[int, int],
    ) -> Image.Image:
        """Create conic gradient image."""
        gradient = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(gradient)

        center_x, center_y = center

        for y in range(height):
            for x in range(width):
                # Calculate angle from center
                angle = math.atan2(y - center_y, x - center_x)
                # Normalize to 0-1
                t = (angle + math.pi) / (2 * math.pi)

                color = self._interpolate_colors(colors, t)
                draw.point((x, y), color)

        return gradient

    def _interpolate_colors(
        self, colors: List[Tuple[int, int, int, int]], t: float
    ) -> Tuple[int, int, int, int]:
        """Interpolate between colors based on position t (0-1)."""
        if t <= 0:
            return colors[0]
        if t >= 1:
            return colors[-1]

        # Find the two colors to interpolate between
        segment_size = 1.0 / (len(colors) - 1)
        segment_index = int(t / segment_size)

        if segment_index >= len(colors) - 1:
            return colors[-1]

        # Calculate local interpolation factor
        local_t = (t - segment_index * segment_size) / segment_size

        # Interpolate between the two colors
        color1 = colors[segment_index]
        color2 = colors[segment_index + 1]

        r = int(color1[0] + (color2[0] - color1[0]) * local_t)
        g = int(color1[1] + (color2[1] - color1[1]) * local_t)
        b = int(color1[2] + (color2[2] - color1[2]) * local_t)
        a = int(color1[3] + (color2[3] - color1[3]) * local_t)

        return (r, g, b, a)
