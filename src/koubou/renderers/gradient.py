"""Universal gradient rendering functionality using Pillow."""

import logging
import math
from typing import List, Optional, Tuple

from PIL import Image

from ..config import GradientConfig
from ..exceptions import TextGradientError

logger = logging.getLogger(__name__)


class GradientRenderer:
    """Renders gradient effects for any rectangular area."""

    def create_gradient(
        self, bounds: Tuple[int, int, int, int], gradient_config: GradientConfig
    ) -> Image.Image:
        """Create gradient image for any rectangular bounds.

        Args:
            bounds: (x, y, width, height) bounding box for gradient area
            gradient_config: Gradient configuration

        Returns:
            PIL Image with gradient pattern

        Raises:
            TextGradientError: If gradient creation fails
        """
        try:
            x, y, width, height = bounds

            if gradient_config.type == "linear":
                return self._create_linear_gradient(
                    (width, height),
                    gradient_config.colors,
                    gradient_config.direction or 0,
                    gradient_config.positions,
                )
            elif gradient_config.type == "radial":
                return self._create_radial_gradient(
                    (width, height),
                    gradient_config.colors,
                    gradient_config.center,
                    gradient_config.radius,
                    gradient_config.positions,
                )
            elif gradient_config.type == "conic":
                return self._create_conic_gradient(
                    (width, height),
                    gradient_config.colors,
                    gradient_config.center,
                    gradient_config.start_angle or 0,
                    gradient_config.positions,
                )
            else:
                raise TextGradientError(
                    f"Unknown gradient type: {gradient_config.type}"
                )

        except Exception as e:
            raise TextGradientError(
                f"Failed to create {gradient_config.type} gradient: {e}"
            ) from e

    def _create_linear_gradient(
        self,
        size: Tuple[int, int],
        colors: List[str],
        direction: float,
        positions: Optional[List[float]] = None,
    ) -> Image.Image:
        """Create linear gradient image."""
        width, height = size

        # Parse colors to RGBA tuples
        parsed_colors = [self._parse_color(color) for color in colors]

        # Convert direction from degrees to radians
        angle = math.radians(direction)

        # Create gradient image
        gradient = Image.new("RGBA", (width, height))

        # Calculate gradient vector
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)

        # For each pixel, calculate position along gradient
        pixels = []
        for y in range(height):
            for x in range(width):
                # Normalize coordinates to center
                nx = (x - width / 2) / (width / 2) if width > 0 else 0
                ny = (y - height / 2) / (height / 2) if height > 0 else 0

                # Project onto gradient direction
                t = (nx * cos_angle + ny * sin_angle + 1) / 2
                t = max(0, min(1, t))

                # Interpolate color
                color = self._interpolate_with_stops(parsed_colors, positions, t)
                pixels.append(color)

        gradient.putdata(pixels)
        return gradient

    def _create_radial_gradient(
        self,
        size: Tuple[int, int],
        colors: List[str],
        center: Optional[Tuple[str, str]] = None,
        radius: Optional[str] = None,
        positions: Optional[List[float]] = None,
    ) -> Image.Image:
        """Create radial gradient image."""
        width, height = size

        # Parse colors to RGBA tuples
        parsed_colors = [self._parse_color(color) for color in colors]

        # Determine center point
        if center:
            center_x = self._parse_position(center[0], width)
            center_y = self._parse_position(center[1], height)
        else:
            center_x = width // 2
            center_y = height // 2

        # Determine radius
        if radius:
            if radius.endswith("%"):
                max_radius = max(width, height) / 2
                gradient_radius = max_radius * float(radius[:-1]) / 100
            else:
                gradient_radius = float(radius.replace("px", ""))
        else:
            # Default: distance to furthest corner
            gradient_radius = max(
                math.sqrt(center_x**2 + center_y**2),
                math.sqrt((width - center_x) ** 2 + center_y**2),
                math.sqrt(center_x**2 + (height - center_y) ** 2),
                math.sqrt((width - center_x) ** 2 + (height - center_y) ** 2),
            )

        # Create gradient image
        gradient = Image.new("RGBA", (width, height))
        pixels = []

        for y in range(height):
            for x in range(width):
                distance = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                t = distance / gradient_radius if gradient_radius > 0 else 0
                t = max(0, min(1, t))

                color = self._interpolate_with_stops(parsed_colors, positions, t)
                pixels.append(color)

        gradient.putdata(pixels)
        return gradient

    def _create_conic_gradient(
        self,
        size: Tuple[int, int],
        colors: List[str],
        center: Optional[Tuple[str, str]] = None,
        start_angle: float = 0,
        positions: Optional[List[float]] = None,
    ) -> Image.Image:
        """Create conic gradient image."""
        width, height = size

        # Parse colors to RGBA tuples
        parsed_colors = [self._parse_color(color) for color in colors]

        # Determine center point
        if center:
            center_x = self._parse_position(center[0], width)
            center_y = self._parse_position(center[1], height)
        else:
            center_x = width // 2
            center_y = height // 2

        # Convert start angle to radians
        start_radians = math.radians(start_angle)

        # Create gradient image
        gradient = Image.new("RGBA", (width, height))
        pixels = []

        for y in range(height):
            for x in range(width):
                # Calculate angle from center
                angle = math.atan2(y - center_y, x - center_x)
                # Adjust by start angle
                angle = (angle - start_radians) % (2 * math.pi)
                # Normalize to 0-1
                t = angle / (2 * math.pi)

                color = self._interpolate_with_stops(parsed_colors, positions, t)
                pixels.append(color)

        gradient.putdata(pixels)
        return gradient

    def _parse_color(self, color_string: str) -> Tuple[int, int, int, int]:
        """Parse hex color string to RGBA tuple."""
        hex_color = color_string.lstrip("#")

        try:
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
                raise TextGradientError(f"Invalid color format: {color_string}")
        except ValueError:
            raise TextGradientError(f"Invalid color format: {color_string}")

        return (r, g, b, a)

    def _parse_position(self, position: str, total: int) -> int:
        """Parse position string (e.g., '50%' or '100') to pixel value."""
        if position.endswith("%"):
            percent = float(position[:-1])
            return int(total * percent / 100)
        else:
            return int(float(position.replace("px", "")))

    def _interpolate_with_stops(
        self,
        colors: List[Tuple[int, int, int, int]],
        positions: Optional[List[float]],
        t: float,
    ) -> Tuple[int, int, int, int]:
        """Interpolate between colors with optional color stops."""
        if t <= 0:
            return colors[0]
        if t >= 1:
            return colors[-1]

        # If no positions specified, distribute colors evenly
        if positions is None:
            positions = [i / (len(colors) - 1) for i in range(len(colors))]

        # Find the two colors to interpolate between
        for i in range(len(positions) - 1):
            if positions[i] <= t <= positions[i + 1]:
                # Calculate local interpolation factor
                start_pos = positions[i]
                end_pos = positions[i + 1]
                local_t = (
                    (t - start_pos) / (end_pos - start_pos)
                    if end_pos > start_pos
                    else 0
                )

                # Interpolate between colors
                color1 = colors[i]
                color2 = colors[i + 1]

                r = int(color1[0] + (color2[0] - color1[0]) * local_t)
                g = int(color1[1] + (color2[1] - color1[1]) * local_t)
                b = int(color1[2] + (color2[2] - color1[2]) * local_t)
                a = int(color1[3] + (color2[3] - color1[3]) * local_t)

                return (r, g, b, a)

        # Fallback to last color
        return colors[-1]
