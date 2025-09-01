"""Core screenshot generation functionality."""

import json
import logging
from pathlib import Path
from typing import List, Optional

from PIL import Image

from .config import GradientConfig, ProjectConfig, ScreenshotConfig, TextOverlay
from .exceptions import ConfigurationError, RenderError
from .renderers.background import BackgroundRenderer
from .renderers.device_frame import DeviceFrameRenderer
from .renderers.text import TextRenderer

logger = logging.getLogger(__name__)


class ScreenshotGenerator:
    """Main class for generating screenshots with backgrounds, text, and frames."""

    def __init__(self, frame_directory: Optional[str] = None):
        """Initialize the screenshot generator.

        Args:
            frame_directory: Path to directory containing device frames.
                           If None, uses bundled frames.
        """
        self.frame_directory = (
            Path(frame_directory)
            if frame_directory
            else self._get_bundled_frames_path()
        )
        self.background_renderer = BackgroundRenderer()
        self.text_renderer = TextRenderer()
        self.device_frame_renderer = DeviceFrameRenderer(self.frame_directory)

        # Load device frame metadata
        self._load_frame_metadata()

    def _get_bundled_frames_path(self) -> Path:
        """Get path to bundled device frames."""
        return Path(__file__).parent / "frames"

    def _load_frame_metadata(self) -> None:
        """Load device frame metadata from JSON files."""
        try:
            frames_json = self.frame_directory / "Frames.json"
            sizes_json = self.frame_directory / "Sizes.json"

            if frames_json.exists():
                with open(frames_json) as f:
                    self.frame_metadata = json.load(f)
            else:
                logger.warning(f"Frames.json not found at {frames_json}")
                self.frame_metadata = {}

            if sizes_json.exists():
                with open(sizes_json) as f:
                    self.size_metadata = json.load(f)
            else:
                logger.warning(f"Sizes.json not found at {sizes_json}")
                self.size_metadata = {}

        except Exception as _e:
            logger.error(f"Failed to load frame metadata: {_e}")
            self.frame_metadata = {}
            self.size_metadata = {}

    def generate_screenshot(self, config: ScreenshotConfig) -> Path:
        """Generate a single screenshot based on configuration.

        Args:
            config: Screenshot configuration

        Returns:
            Path to generated screenshot

        Raises:
            RenderError: If generation fails
        """
        try:
            logger.info(f"🎬 Starting generation: {config.name}")

            # Load source image
            source_image = self._load_source_image(config.source_image)
            logger.info(f"📷 Loaded source: {source_image.size}")

            # Create canvas at target size
            canvas = Image.new("RGBA", config.output_size, (255, 255, 255, 0))
            logger.info(f"🎨 Created canvas: {config.output_size}")

            # Render background if specified
            if config.background:
                logger.info(f"🌈 Rendering background: {config.background.type}")
                self.background_renderer.render(config.background, canvas)

            # Position and composite source image with optional frame
            logger.info("📐 Positioning source image")
            positioned_image = self._position_source_image(source_image, canvas, config)

            # Apply device frame to individual image if frame: true
            if config.image_frame and config.device_frame:
                logger.info(f"📱 Applying device frame to asset: {config.device_frame}")
                positioned_image = self._apply_asset_frame(
                    positioned_image, canvas, config
                )

            canvas = Image.alpha_composite(canvas, positioned_image)

            # Render text overlays
            if config.text_overlays:
                logger.info(f"✏️  Rendering {len(config.text_overlays)} text overlays")
                for overlay in config.text_overlays:
                    self.text_renderer.render(overlay, canvas)

            # Save final image
            output_path = self._get_output_path(config)
            logger.info(f"💾 Saving to: {output_path}")

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Convert to RGB if saving as JPEG, keep RGBA for PNG
            if output_path.suffix.lower() == ".jpg":
                # Create white background for JPEG
                rgb_canvas = Image.new("RGB", canvas.size, (255, 255, 255))
                rgb_canvas.paste(canvas, mask=canvas)
                rgb_canvas.save(output_path, "JPEG", quality=95)
            else:
                canvas.save(output_path, "PNG")

            logger.info(f"✅ Generated: {config.name}")
            return output_path

        except Exception as _e:
            logger.error(f"❌ Generation failed for {config.name}: {_e}")
            raise RenderError(
                f"Failed to generate screenshot '{config.name}': {_e}"
            ) from _e

    def _load_source_image(self, image_path: str) -> Image.Image:
        """Load and validate source image."""
        try:
            image = Image.open(image_path)
            # Convert to RGBA to ensure consistent handling
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            return image
        except Exception as _e:
            raise RenderError(
                f"Failed to load source image '{image_path}': {_e}"
            ) from _e

    def _position_source_image(
        self, source_image: Image.Image, canvas: Image.Image, config: ScreenshotConfig
    ) -> Image.Image:
        """Position source image on canvas using scale and % coordinates."""
        canvas_width, canvas_height = canvas.size

        # Apply scale factor from config
        scale_factor = config.image_scale or 1.0
        original_width, original_height = source_image.size
        scaled_width = int(original_width * scale_factor)
        scaled_height = int(original_height * scale_factor)

        logger.info(
            "📏 Scaling image: {original_width}×{original_height} → "
            "{scaled_width}×{scaled_height} (scale: {scale_factor})"
        )

        # Resize the source image
        if scale_factor != 1.0:
            source_image = source_image.resize(
                (scaled_width, scaled_height), Image.Resampling.LANCZOS
            )

        # Position image at % coordinates relative to canvas
        position = config.image_position or ["50%", "50%"]
        x_percent, y_percent = position

        # Convert percentage strings to pixel positions (asset center positioning)
        center_x = self._convert_percentage_to_pixels(x_percent, canvas_width)
        center_y = self._convert_percentage_to_pixels(y_percent, canvas_height)

        # Calculate top-left position (center the asset at the % position)
        x = center_x - scaled_width // 2
        y = center_y - scaled_height // 2

        logger.info(
            "📐 Positioning asset: center at {position} → "
            "({center_x}, {center_y}), top-left at ({x}, {y})"
        )

        # Create positioned image
        positioned = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
        positioned.paste(source_image, (x, y), source_image)

        return positioned

    def _convert_percentage_to_pixels(self, percentage_str: str, dimension: int) -> int:
        """Convert percentage string to pixel position."""
        if percentage_str.endswith("%"):
            percentage = float(percentage_str[:-1])
            return int(dimension * percentage / 100.0)
        else:
            # If not a percentage, assume it's already pixels
            return int(percentage_str)

    def _apply_device_frame_overlay(
        self, canvas: Image.Image, device_frame_name: str
    ) -> Image.Image:
        """Apply device frame as an overlay on the canvas."""
        try:
            # Load device frame image
            frame_image = self.device_frame_renderer._load_frame_image(
                device_frame_name
            )
            logger.info(f"📱 Loaded frame overlay: {frame_image.size}")

            # The canvas should already be sized to match the frame
            # Simply composite the frame over the canvas
            if frame_image.size == canvas.size:
                # Perfect match - direct composite
                return Image.alpha_composite(canvas, frame_image)
            else:
                # Size mismatch - need to handle this case
                logger.warning(
                    "Canvas size {canvas.size} doesn't match frame size {frame_image.size}"
                )
                # For now, resize canvas to match frame
                resized_canvas = canvas.resize(
                    frame_image.size, Image.Resampling.LANCZOS
                )
                return Image.alpha_composite(resized_canvas, frame_image)

        except Exception as _e:
            logger.error(f"Failed to apply device frame overlay: {_e}")
            return canvas  # Return original canvas if frame fails

    def _apply_asset_frame(
        self,
        positioned_image: Image.Image,
        canvas: Image.Image,
        config: ScreenshotConfig,
    ) -> Image.Image:
        """Apply device frame to individual asset with proper screen masking."""
        try:
            # Load and scale device frame image first
            frame_image = self.device_frame_renderer._load_frame_image(
                config.device_frame
            )
            original_frame_size = frame_image.size
            logger.info(f"📱 Original frame size: {original_frame_size}")

            # Scale frame to match asset scale
            asset_scale = config.image_scale or 1.0
            scaled_frame_width = int(original_frame_size[0] * asset_scale)
            scaled_frame_height = int(original_frame_size[1] * asset_scale)
            scaled_frame = frame_image.resize(
                (scaled_frame_width, scaled_frame_height), Image.Resampling.LANCZOS
            )

            logger.info(
                "📱 Scaled frame: {original_frame_size} → {scaled_frame.size} (scale: {asset_scale})"
            )

            # Generate screen mask from the already-scaled frame (preserves precise boundaries)
            screen_mask = self.device_frame_renderer.generate_screen_mask_from_image(
                scaled_frame
            )
            logger.info(f"📱 Generated screen mask: {screen_mask.size}")

            # Get asset position to position frame at same location
            position = config.image_position or ["50%", "50%"]
            center_x = self._convert_percentage_to_pixels(position[0], canvas.width)
            center_y = self._convert_percentage_to_pixels(position[1], canvas.height)

            # Calculate frame position (center frame at same position as asset)
            frame_x = center_x - scaled_frame_width // 2
            frame_y = center_y - scaled_frame_height // 2

            logger.info(
                "📱 Positioning frame: center at ({center_x}, {center_y}), top-left at ({frame_x}, {frame_y})"
            )

            # Step 1: Start with the positioned asset (no masking yet)
            result = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
            result = Image.alpha_composite(result, positioned_image)

            # Step 2: Apply screen mask to clip content to frame boundaries
            logger.info("📱 Applying screen mask with precise boundaries")

            # Create canvas-sized mask positioned at the frame location
            canvas_mask = Image.new("L", canvas.size, 0)  # Start with black (hide all)
            canvas_mask.paste(screen_mask, (frame_x, frame_y))

            # Apply mask to result
            transparent_bg = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
            result = Image.composite(result, transparent_bg, canvas_mask)

            # Step 3: Overlay the scaled and positioned frame on top of masked content
            # Apply frame regardless of canvas bounds - let user control positioning
            frame_overlay = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
            frame_overlay.paste(scaled_frame, (frame_x, frame_y), scaled_frame)
            result = Image.alpha_composite(result, frame_overlay)
            logger.info("📱 Applied device frame overlay successfully")

            return result

        except Exception as e:
            logger.error(f"Failed to apply asset frame: {e}")
            raise ConfigurationError(
                f"Frame application failed for '{config.device_frame}': {e}. "
                f"Verify the device frame exists and is properly configured."
            ) from e

    def _get_output_path(self, config: ScreenshotConfig) -> Path:
        """Determine output path for generated screenshot."""
        if config.output_path:
            return Path(config.output_path)

        # Generate default path
        safe_name = "".join(
            c for c in config.name if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        safe_name = safe_name.replace(" ", "_").lower()
        return Path("output") / f"{safe_name}.png"

    def generate_project(
        self, project_config: ProjectConfig, config_dir: Optional[Path] = None
    ) -> List[Path]:
        """Generate all screenshots in a project configuration.

        Args:
            project_config: Complete project configuration
            config_dir: Directory containing the config file (for relative path resolution)

        Returns:
            List of paths to generated screenshots
        """
        logger.info(f"🚀 Starting project: {project_config.project.name}")
        logger.info(f"📁 Output directory: {project_config.project.output_dir}")
        logger.info(f"🎯 Screenshots to generate: {len(project_config.screenshots)}")

        # Get defaults and devices
        defaults = project_config.defaults or {}
        default_background = defaults.get("background")
        device_frame = None
        if project_config.devices:
            device_frame = self._map_device_name(project_config.devices[0])

        results = []
        screenshot_items = list(project_config.screenshots.items())
        for i, (screenshot_id, screenshot_def) in enumerate(screenshot_items, 1):
            logger.info(f"[{i}/{len(project_config.screenshots)}] {screenshot_id}")
            try:
                # Convert to ScreenshotConfig and generate
                temp_config = self._convert_to_screenshot_config(
                    screenshot_def,
                    device_frame,
                    default_background,
                    project_config.project.output_dir,
                    config_dir,
                    screenshot_id,  # Pass the screenshot ID
                )
                if temp_config:
                    output_path = self.generate_screenshot(temp_config)
                    results.append(output_path)
                else:
                    logger.warning(f"Skipping {screenshot_id}: no source image found")
            except Exception as _e:
                logger.error(f"Failed to generate {screenshot_id}: {_e}")
                # Continue with next screenshot instead of failing entire project
                continue

        logger.info(
            "🎉 Project complete! Generated {len(results)}/{len(project_config.screenshots)} screenshots"
        )
        return results

    def _resolve_output_path(
        self, output_dir: str, screenshot_name: str, config_dir: Optional[Path] = None
    ) -> Path:
        """Resolve output path relative to config directory if provided."""
        output_path = Path(output_dir) / f"{screenshot_name}.png"

        if config_dir:
            # Make path relative to config directory
            if not output_path.is_absolute():
                output_path = config_dir / output_path

        return output_path

    def _convert_to_screenshot_config(
        self,
        screenshot_def,
        device_frame,
        default_background,
        output_dir,
        config_dir=None,
        screenshot_id=None,
    ):
        """Convert ScreenshotDefinition to ScreenshotConfig for generation."""

        # Process content items and calculate dimensions
        source_image_path = None
        image_scale = 1.0
        text_overlays = []

        # Store image configurations for proper positioning
        image_config = None

        for item in screenshot_def.content:
            if item.type == "image":
                # Get source image path, scale, and position
                asset_path = item.asset or ""
                if asset_path.startswith("../"):
                    source_image_path = str(
                        Path("/Users/davidcollado/Projects").resolve() / asset_path[3:]
                    )
                else:
                    source_image_path = asset_path
                image_scale = item.scale or 1.0
                image_position = item.position or ["50%", "50%"]  # Default to center

                # Store image configuration including frame setting
                image_config = {
                    "scale": image_scale,
                    "position": image_position,
                    "frame": getattr(item, "frame", False),  # Capture frame setting
                }
                logger.info(
                    f"📏 Image: scale={image_scale * 100:.0f}%, "
                    f"position={image_position}, frame={getattr(item, 'frame', False)}"
                )
                break  # Use first image found

        # Skip if no source image found
        if not source_image_path or not Path(source_image_path).exists():
            logger.warning(
                f"Source image not found for {screenshot_id}: {source_image_path}"
            )
            return None

        # Load source image to get actual dimensions
        from PIL import Image

        source_image = Image.open(source_image_path)
        original_width, original_height = source_image.size

        # Calculate scaled image dimensions
        scaled_width = int(original_width * image_scale)
        scaled_height = int(original_height * image_scale)
        logger.info(
            "📐 Original: {original_width}×{original_height} → Scaled: {scaled_width}×{scaled_height}"
        )

        # Calculate canvas size - use frame size if available, otherwise content-based
        if device_frame:
            frame_size = self.device_frame_renderer.get_frame_size(device_frame)
            if frame_size:
                canvas_width, canvas_height = frame_size
                logger.info(
                    "📐 Canvas: {canvas_width}×{canvas_height} (frame-based sizing)"
                )
            else:
                raise ConfigurationError(
                    f"Device frame '{device_frame}' not found. "
                    f"Frame is required when 'frame: true' is specified. "
                    f"Check available frames or remove 'frame: true' from your configuration."
                )
        else:
            # No frame: canvas = scaled image + padding for text
            canvas_width = max(
                scaled_width + 400, 800
            )  # Minimum width for text, extra space for text
            canvas_height = scaled_height + 800  # Extra space for text above/below
            logger.info(
                "📐 Canvas: {canvas_width}×{canvas_height} (content-based sizing)"
            )

        # Now process text overlays with correct canvas dimensions
        for item in screenshot_def.content:
            if item.type == "text":
                # Convert to TextOverlay
                if item.content:
                    position = self._convert_position(
                        item.position, (canvas_width, canvas_height)
                    )
                    text_overlay = TextOverlay(
                        content=item.content,
                        position=position,
                        font_size=item.size or 24,
                        font_weight=getattr(item, "weight", "normal") or "normal",
                        color=item.color,  # Don't default to black if gradient is provided
                        gradient=item.gradient,  # Pass gradient configuration
                        alignment=getattr(item, "alignment", "center") or "center",
                        anchor="center",  # Use center anchor for percentage-based positioning
                        max_width=getattr(
                            item, "maxWidth", None
                        ),  # User controls maxWidth, default None means no limit
                        max_lines=getattr(
                            item, "maxLines", None
                        ),  # None means unlimited lines with wrapping
                        stroke_width=getattr(item, "stroke_width", None),
                        stroke_color=getattr(item, "stroke_color", None),
                        stroke_gradient=getattr(item, "stroke_gradient", None),
                    )
                    text_overlays.append(text_overlay)

        # Create background config with priority: screenshot background > default background > white
        background_config = None
        if screenshot_def.background:
            # Use per-screenshot background if specified
            background_config = screenshot_def.background
        elif default_background:
            # Fallback to project default background
            background_config = GradientConfig(
                type=default_background.get("type", "solid"),
                colors=default_background.get("colors", ["#ffffff"]),
                direction=default_background.get("direction", 0),
                positions=default_background.get("positions"),
                center=default_background.get("center"),
                radius=default_background.get("radius"),
                start_angle=default_background.get("start_angle"),
            )
        else:
            # Final fallback to white background
            background_config = GradientConfig(type="solid", colors=["#ffffff"])

        # Create screenshot config with calculated dimensions
        # Store scale factor for use during generation
        config = ScreenshotConfig(
            name=screenshot_id,
            source_image=source_image_path,
            device_frame=device_frame,
            output_size=(canvas_width, canvas_height),  # Dynamic size based on content
            background=background_config,
            text_overlays=text_overlays,
            image_position=image_config["position"] if image_config else ["50%", "50%"],
            image_scale=image_config["scale"] if image_config else 1.0,
            image_frame=image_config["frame"] if image_config else False,
            output_path=str(
                self._resolve_output_path(output_dir, screenshot_id, config_dir)
            ),
        )

        # Store scale factor as a custom attribute for positioning
        config._image_scale = image_scale
        config._scaled_dimensions = (scaled_width, scaled_height)

        return config

    def _convert_position(self, position, canvas_size):
        """Convert percentage or pixel position to absolute pixels."""
        canvas_width, canvas_height = canvas_size

        # Convert X position
        if position[0].endswith("%"):
            x = int(canvas_width * float(position[0][:-1]) / 100)
        else:
            x = int(float(position[0]))

        # Convert Y position
        if position[1].endswith("%"):
            y = int(canvas_height * float(position[1][:-1]) / 100)
        else:
            y = int(float(position[1]))

        return (x, y)

    def _map_device_name(self, device):
        """Map device names to device frame names."""
        mapping = {
            "iPhone 15 Pro Portrait": "iPhone 15 Pro - Natural Titanium - Portrait",
            "iPhone 15 Pro Max Portrait": "iPhone 15 Pro Max - Natural Titanium - Portrait",
            "iPhone 16 Pro Portrait": "iPhone 16 Pro - Natural Titanium - Portrait",
            "iPhone 16 Pro Max Portrait": "iPhone 16 Pro Max - Natural Titanium - Portrait",
        }
        return mapping.get(device, "iPhone 15 Pro - Natural Titanium - Portrait")
