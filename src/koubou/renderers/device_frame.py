"""Device frame rendering functionality."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image

from ..exceptions import DeviceFrameError

logger = logging.getLogger(__name__)


class DeviceFrameRenderer:
    """Renders device frames around screenshots."""

    def __init__(self, frame_directory: Path):
        """Initialize device frame renderer.

        Args:
            frame_directory: Path to directory containing device frames
        """
        self.frame_directory = frame_directory
        self.frame_metadata: Dict[str, Any] = {}
        self.size_metadata: Dict[str, Any] = {}
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load device frame metadata from JSON files."""
        try:
            frames_json = self.frame_directory / "Frames.json"
            if frames_json.exists():
                with open(frames_json) as f:
                    self.frame_metadata = json.load(f)

            sizes_json = self.frame_directory / "Sizes.json"
            if sizes_json.exists():
                with open(sizes_json) as f:
                    self.size_metadata = json.load(f)

            logger.info(f"Loaded metadata for {len(self.frame_metadata)} device frames")

        except Exception as _e:
            logger.error(f"Failed to load frame metadata: {_e}")
            self.frame_metadata = {}
            self.size_metadata = {}

    def render(
        self, device_frame_name: str, canvas: Image.Image, source_image: Image.Image
    ) -> Image.Image:
        """Render device frame with screenshot.

        Args:
            device_frame_name: Name of device frame to apply
            canvas: Current canvas (may have background/text)
            source_image: Original screenshot to position within frame

        Returns:
            New image with device frame applied

        Raises:
            DeviceFrameError: If frame rendering fails
        """
        try:
            # Load device frame image
            frame_image = self._load_frame_image(device_frame_name)
            logger.info(f"📱 Loaded frame: {frame_image.size}")

            # Get frame metadata
            frame_info = self._get_frame_info(device_frame_name)

            # Create final composition
            if frame_info and ("screen_bounds" in frame_info or "x" in frame_info):
                # Use metadata to position screenshot within frame
                result = self._compose_with_metadata(
                    canvas, source_image, frame_image, frame_info
                )
            else:
                # Fall back to simple overlay approach
                logger.warning(
                    f"No metadata found for {device_frame_name}, using simple overlay"
                )
                result = self._compose_simple_overlay(canvas, frame_image)

            return result

        except Exception as _e:
            raise DeviceFrameError(
                f"Failed to render device frame '{device_frame_name}': {_e}"
            ) from _e

    def _load_frame_image(self, frame_name: str) -> Image.Image:
        """Load device frame image file."""
        # Try different possible file extensions
        for ext in [".png", ".PNG"]:
            frame_path = self.frame_directory / f"{frame_name}{ext}"
            if frame_path.exists():
                opened_image = Image.open(frame_path)
                # Ensure RGBA mode for proper compositing
                if opened_image.mode != "RGBA":
                    return opened_image.convert("RGBA")
                return opened_image

        raise DeviceFrameError(f"Device frame not found: {frame_name}")

    def _get_frame_info(self, frame_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a device frame."""
        # First try direct lookup for backward compatibility
        if frame_name in self.frame_metadata:
            result = self.frame_metadata[frame_name]
            return result if isinstance(result, dict) else None

        # Parse frame name and traverse nested structure
        # Expected format: "iPhone 15 Pro - Natural Titanium - Portrait"
        parts = [part.strip() for part in frame_name.split(" - ")]

        if len(parts) >= 3:
            # Try different parsing strategies for nested JSON
            device_type = parts[0].split()[0]  # "iPhone" from "iPhone 15 Pro"
            model_parts = parts[0].split()[1:]  # ["15", "Pro"] from "iPhone 15 Pro"
            color = parts[1]  # "Natural Titanium"
            orientation = parts[2]  # "Portrait"

            # Navigate nested structure: iPhone -> 15 Pro -> Pro ->
            # Natural Titanium -> Portrait
            current = self.frame_metadata.get(device_type)
            if not current:
                logger.warning(f"Device type '{device_type}' not found in metadata")
                return None

            # Build model key from parts
            if len(model_parts) >= 2:
                model_key = " ".join(model_parts)  # "15 Pro"
                current = current.get(model_key)
                if not current:
                    logger.warning(f"Model '{model_key}' not found under {device_type}")
                    return None

                # Navigate to device variant (e.g., "Pro" for iPhone 15 Pro)
                variant = model_parts[-1]  # "Pro" from ["15", "Pro"]
                current = current.get(variant)
                if not current:
                    logger.warning(
                        f"Variant '{variant}' not found under {device_type} {model_key}"
                    )
                    return None

                # Navigate to color
                current = current.get(color)
                if not current:
                    logger.warning(f"Color '{color}' not found")
                    return None

                # Navigate to orientation
                frame_info = current.get(orientation)
                if frame_info:
                    logger.info(f"📱 Found metadata for {frame_name}: {frame_info}")
                    return frame_info if isinstance(frame_info, dict) else None
                else:
                    logger.warning(f"Orientation '{orientation}' not found")

            elif len(model_parts) == 1:
                model_key = model_parts[0]  # "17" or "Air"
                current = current.get(model_key)
                if not current:
                    logger.warning(f"Model '{model_key}' not found under {device_type}")
                    return None

                current = current.get(color)
                if not current:
                    logger.warning(f"Color '{color}' not found")
                    return None

                frame_info = current.get(orientation)
                if frame_info:
                    logger.info(f"📱 Found metadata for {frame_name}: {frame_info}")
                    return frame_info if isinstance(frame_info, dict) else None
                else:
                    logger.warning(f"Orientation '{orientation}' not found")

        logger.warning(f"No metadata found for frame: {frame_name}")
        return None

    def _compose_with_metadata(
        self,
        canvas: Image.Image,
        source_image: Image.Image,
        frame_image: Image.Image,
        frame_info: Dict[str, Any],
    ) -> Image.Image:
        """Compose screenshot with device frame using metadata positioning."""

        # Get screen bounds from metadata - handle both formats
        if "screen_bounds" in frame_info:
            # New format with screen_bounds object
            screen_bounds = frame_info["screen_bounds"]
            screen_x = int(screen_bounds.get("x", 0))
            screen_y = int(screen_bounds.get("y", 0))
            screen_width = int(screen_bounds.get("width", source_image.width))
            screen_height = int(screen_bounds.get("height", source_image.height))
        else:
            # Legacy format with x, y directly
            screen_x = int(frame_info.get("x", 0))
            screen_y = int(frame_info.get("y", 0))

            # Calculate screen area based on source image and frame size
            frame_width, frame_height = frame_image.size
            screen_width = frame_width - (screen_x * 2)  # Assume symmetric margins
            screen_height = frame_height - (screen_y * 2)

            logger.info(f"📐 Using legacy format: x={screen_x}, y={screen_y}")

        logger.info(
            f"📐 Screen area: {screen_x}, {screen_y}, {screen_width}×{screen_height}"
        )

        # Scale source image to fit the screen area properly
        source_width, source_height = source_image.size

        # Calculate scale to fit source image into screen area
        scale_x = screen_width / source_width
        scale_y = screen_height / source_height
        scale = min(scale_x, scale_y)  # Use smaller scale to maintain aspect ratio

        # Calculate final source dimensions
        final_width = int(source_width * scale)
        final_height = int(source_height * scale)

        logger.info(
            f"📐 Scaling source {source_width}×{source_height} to "
            f"{final_width}×{final_height} (scale: {scale:.2f})"
        )

        # Resize source image to fit screen area
        source_image = source_image.resize(
            (final_width, final_height), Image.Resampling.LANCZOS
        )

        # Center the resized source image within the screen area
        center_x = screen_x + (screen_width - final_width) // 2
        center_y = screen_y + (screen_height - final_height) // 2

        logger.info(f"📐 Positioning scaled source at ({center_x}, {center_y})")

        # Create result image the size of the device frame
        result = Image.new("RGBA", frame_image.size, (255, 255, 255, 0))

        # First, paste the source image at centered position within screen area
        result.paste(source_image, (center_x, center_y), source_image)

        # Then composite the device frame on top
        result = Image.alpha_composite(result, frame_image)

        return result

    def _compose_simple_overlay(
        self, canvas: Image.Image, frame_image: Image.Image
    ) -> Image.Image:
        """Simple overlay composition when metadata is not available."""

        # Scale canvas to match frame size
        scaled_canvas = canvas.resize(frame_image.size, Image.Resampling.LANCZOS)

        # Composite frame over canvas
        result = Image.alpha_composite(scaled_canvas, frame_image)

        return result

    def get_available_frames(self) -> list[str]:
        """Get list of available device frame names."""
        frames: list[str] = []

        # Get from metadata if available
        if self.frame_metadata:
            frames.extend(self.frame_metadata.keys())

        # Also scan directory for PNG files
        for frame_file in self.frame_directory.glob("*.png"):
            frame_name = frame_file.stem
            if frame_name not in frames:
                frames.append(frame_name)

        return sorted(frames)

    def get_frame_size(self, frame_name: str) -> Optional[Tuple[int, int]]:
        """Get the size of a device frame."""
        try:
            frame_image = self._load_frame_image(frame_name)
            return frame_image.size
        except DeviceFrameError:
            return None

    def inspect_frame(self, frame_name: str) -> Dict[str, Any]:
        """Return geometry details for a device frame.

        The returned data is intended for layout tooling and agents that need
        objective information about the frame, screen area, and safe margins.
        """
        frame_image = self._load_frame_image(frame_name)
        frame_info = self._get_frame_info(frame_name)
        frame_width, frame_height = frame_image.size

        screen_mask = self.generate_screen_mask_from_image(frame_image)
        screen_bbox = self._mask_to_bbox(screen_mask)
        screen_bounds = self._resolve_screen_bounds(
            frame_info=frame_info,
            frame_size=(frame_width, frame_height),
            fallback_bbox=screen_bbox,
        )
        safe_margins = self._build_safe_margins(
            frame_size=(frame_width, frame_height),
            screen_bbox=screen_bbox,
        )
        screen_coverage_ratio = self._mask_coverage_ratio(screen_mask)

        return {
            "frame_size": {"width": frame_width, "height": frame_height},
            "screen_bounds": screen_bounds,
            "screen_bbox": screen_bbox,
            "screen_ratio": round(screen_bounds["width"] / screen_bounds["height"], 4),
            "frame_ratio": round(frame_width / frame_height, 4),
            "screen_coverage_ratio": round(screen_coverage_ratio, 4),
            "safe_margins": safe_margins,
        }

    def _mask_to_bbox(self, mask: Image.Image) -> Dict[str, int]:
        bbox = mask.getbbox()
        if bbox is None:
            raise DeviceFrameError("Unable to determine screen bounding box")

        left, top, right, bottom = bbox
        return {
            "left": int(left),
            "top": int(top),
            "right": int(right),
            "bottom": int(bottom),
            "width": int(right - left),
            "height": int(bottom - top),
        }

    def _resolve_screen_bounds(
        self,
        *,
        frame_info: Optional[Dict[str, Any]],
        frame_size: Tuple[int, int],
        fallback_bbox: Dict[str, int],
    ) -> Dict[str, int]:
        frame_width, frame_height = frame_size

        if frame_info and "screen_bounds" in frame_info:
            screen_bounds = frame_info["screen_bounds"]
            return {
                "x": int(screen_bounds.get("x", fallback_bbox["left"])),
                "y": int(screen_bounds.get("y", fallback_bbox["top"])),
                "width": int(screen_bounds.get("width", fallback_bbox["width"])),
                "height": int(screen_bounds.get("height", fallback_bbox["height"])),
            }

        if frame_info and "x" in frame_info and "y" in frame_info:
            x = int(frame_info.get("x", fallback_bbox["left"]))
            y = int(frame_info.get("y", fallback_bbox["top"]))
            return {
                "x": x,
                "y": y,
                "width": int(frame_width - (x * 2)),
                "height": int(frame_height - (y * 2)),
            }

        return {
            "x": fallback_bbox["left"],
            "y": fallback_bbox["top"],
            "width": fallback_bbox["width"],
            "height": fallback_bbox["height"],
        }

    def _build_safe_margins(
        self,
        *,
        frame_size: Tuple[int, int],
        screen_bbox: Dict[str, int],
    ) -> Dict[str, int]:
        frame_width, frame_height = frame_size
        return {
            "left": screen_bbox["left"],
            "top": screen_bbox["top"],
            "right": int(frame_width - screen_bbox["right"]),
            "bottom": int(frame_height - screen_bbox["bottom"]),
        }

    def _mask_coverage_ratio(self, mask: Image.Image) -> float:
        histogram = mask.histogram()
        weighted_pixels = sum(value * count for value, count in enumerate(histogram))
        total_pixels = mask.size[0] * mask.size[1]
        if total_pixels == 0:
            return 0.0
        return weighted_pixels / (255 * total_pixels)

    def generate_screen_mask(self, frame_name: str) -> Image.Image:
        """Generate a screen mask using frame boundary detection.

        Uses outer transparent areas to detect frame boundaries, then excludes
        solid bezels and Dynamic Island areas to create accurate screen mask.

        Args:
            frame_name: Name of the device frame

        Returns:
            Binary mask image where white = screen area, black = bezel/outside area
        """
        try:
            # Load the frame image
            frame_image = self._load_frame_image(frame_name)

            # Ensure RGBA mode
            if frame_image.mode != "RGBA":
                frame_image = frame_image.convert("RGBA")

            # Extract alpha channel
            alpha_channel = frame_image.split()[-1]

            # Create proper screen mask using frame transparency analysis
            # Strategy: Use outer transparency (alpha=0) to detect outside areas
            # and reasonable thresholds for bezels vs screen

            mask = Image.new("L", frame_image.size, 0)  # Start with black (hide all)
            mask_pixels = mask.load()
            alpha_pixels = alpha_channel.load()

            if mask_pixels is None or alpha_pixels is None:
                logger.error("Failed to load pixel data")
                return Image.new("L", frame_image.size, 255)

            # ALPHA PIXEL APPROACH: Use actual frame alpha channel to create mask
            # The frame has alpha=0 in screen areas and alpha>0 in frame/bezel areas

            frame_width, frame_height = frame_image.size

            logger.info("📱 Creating mask from alpha channel analysis")

            # Create mask based on alpha values
            for y in range(frame_height):
                for x in range(frame_width):
                    alpha_value = alpha_pixels[x, y]

                    # Screen area (alpha=0) -> show content
                    if alpha_value == 0:
                        mask_pixels[x, y] = 255  # White = show content
                    # Frame/bezel area (alpha>0) -> hide content
                    else:
                        mask_pixels[x, y] = 0  # Black = hide content

            logger.info(
                "📱 Generated mask using frame alpha channel (alpha=0 -> screen area)"
            )

            screen_mask = mask
            logger.info(
                "📱 Generated screen mask: low_alpha≤50=show, high_alpha>200=hide"
            )

            logger.info(
                f"📱 Generated screen mask for {frame_name} using boundary detection"
            )
            return screen_mask

        except Exception as _e:
            logger.error(f"Failed to generate screen mask for {frame_name}: {_e}")
            # Return a fallback mask (full white - no clipping)
            try:
                frame_image = self._load_frame_image(frame_name)
                return Image.new("L", frame_image.size, 255)
            except Exception:
                # Last resort: return small white mask
                return Image.new("L", (100, 100), 255)

    def generate_screen_mask_from_image(self, frame_image: Image.Image) -> Image.Image:
        """Generate screen mask from a pre-loaded and scaled frame image.

        Uses flood fill to identify the screen area, then inverts the
        frame's alpha channel to create a proper anti-aliased mask that
        preserves smooth rounded corners.

        Args:
            frame_image: Pre-loaded and scaled frame image

        Returns:
            Grayscale mask image with anti-aliased edges (white = screen, black = bezel)
        """
        try:
            # Ensure RGBA mode
            if frame_image.mode != "RGBA":
                frame_image = frame_image.convert("RGBA")

            alpha_channel = frame_image.split()[-1]
            alpha_pixels = alpha_channel.load()
            frame_width, frame_height = frame_image.size

            logger.info(
                f"📱 Creating anti-aliased mask from alpha channel "
                f"({frame_width}x{frame_height})"
            )

            # Use flood fill to identify outer transparent area vs inner screen area
            from collections import deque

            visited: set[tuple[int, int]] = set()
            queue: deque[tuple[int, int]] = deque()

            # Start from all edge pixels
            for x in range(frame_width):
                queue.append((x, 0))
                queue.append((x, frame_height - 1))
            for y in range(frame_height):
                queue.append((0, y))
                queue.append((frame_width - 1, y))

            # Check pixel access is available
            if alpha_pixels is None:
                logger.error("Failed to load alpha pixel data")
                return Image.new("L", frame_image.size, 255)

            # Flood fill to mark outer area
            # Continue through low alpha values (bezel outer edge gradients)
            while queue:
                x, y = queue.popleft()
                if (
                    (x, y) in visited
                    or x < 0
                    or x >= frame_width
                    or y < 0
                    or y >= frame_height
                ):
                    continue
                alpha_val = alpha_pixels[x, y]
                if isinstance(alpha_val, tuple):
                    alpha_val = alpha_val[0] if alpha_val else 0
                if alpha_val > 50:  # Hit solid bezel
                    continue
                visited.add((x, y))
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    queue.append((x + dx, y + dy))

            # Create mask: invert alpha for screen area, black for outer/bezel
            # This preserves the anti-aliasing at rounded corners
            mask = Image.new("L", frame_image.size, 0)
            mask_pixels = mask.load()

            if mask_pixels is None:
                logger.error("Failed to load mask pixel data")
                return Image.new("L", frame_image.size, 255)

            for y in range(frame_height):
                for x in range(frame_width):
                    if (x, y) in visited:
                        # Outer area -> hide content
                        mask_pixels[x, y] = 0
                    else:
                        # Screen or bezel area
                        pixel_val = alpha_pixels[x, y]
                        alpha_val = (
                            pixel_val[0] if isinstance(pixel_val, tuple) else pixel_val
                        )
                        if alpha_val > 50:
                            # Bezel (including outer edge gradients)
                            # -> completely hide content
                            # This includes both solid bezel (alpha=255) and
                            # bezel outer edge (alpha=51-200)
                            mask_pixels[x, y] = 0
                        else:
                            # Screen and immediate screen edge gradient
                            # (alpha 0-50) -> invert alpha
                            # alpha=0 (screen) -> 255 (show)
                            # alpha=10 (edge) -> 245 (mostly show)
                            inverted_val = 255 - alpha_val
                            mask_pixels[x, y] = int(inverted_val)

            screen_pixels = 0
            for y in range(frame_height):
                for x in range(frame_width):
                    pixel_val = mask_pixels[x, y]
                    if isinstance(pixel_val, (int, float)) and pixel_val > 128:
                        screen_pixels += 1

            logger.info(
                f"📱 Generated anti-aliased mask with smooth rounded corners "
                f"({screen_pixels} screen pixels)"
            )

            return mask

        except Exception as _e:
            logger.error(f"Failed to generate screen mask from frame image: {_e}")
            return Image.new("L", frame_image.size, 255)

    def apply_screen_mask(
        self,
        canvas_image: Image.Image,
        mask: Image.Image,
        asset_position: tuple,
        asset_size: tuple,
    ) -> Image.Image:
        """Apply screen mask to canvas to clip content to frame boundaries.

        Args:
            canvas_image: Canvas with positioned asset
            mask: Screen mask (white = show content, black = hide content)
            asset_position: (x, y) position of asset on canvas
            asset_size: (width, height) of asset

        Returns:
            Canvas with content masked to screen area
        """
        try:
            # Ensure canvas is RGBA
            if canvas_image.mode != "RGBA":
                canvas_image = canvas_image.convert("RGBA")

            # Create a mask that matches the canvas size
            canvas_mask = Image.new(
                "L", canvas_image.size, 0
            )  # Start with black (hide all)

            # Paste the screen mask at the correct position (where the frame will be)
            # The mask defines where content should be visible within the frame area
            if mask.size != canvas_image.size:
                # If mask is different size, it needs to be positioned correctly
                # For now, assume mask matches frame size and should be centered
                mask_x = (canvas_image.width - mask.width) // 2
                mask_y = (canvas_image.height - mask.height) // 2
                canvas_mask.paste(mask, (mask_x, mask_y))
            else:
                canvas_mask.paste(mask, (0, 0))

            # Create transparent background
            transparent_bg = Image.new("RGBA", canvas_image.size, (255, 255, 255, 0))

            # Apply mask to canvas: only show content where mask is white
            masked_canvas = Image.composite(canvas_image, transparent_bg, canvas_mask)

            logger.info(
                f"📱 Applied screen mask to canvas at position {asset_position}"
            )
            return masked_canvas

        except Exception as _e:
            logger.error(f"Failed to apply screen mask to canvas: {_e}")
            # Return original canvas if masking fails
            return canvas_image
