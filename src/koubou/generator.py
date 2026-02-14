"""Core screenshot generation functionality."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image

from .config import GradientConfig, ProjectConfig, ScreenshotConfig, TextOverlay
from .exceptions import ConfigurationError, RenderError
from .localization import LocalizedContentResolver, XCStringsManager
from .renderers.background import BackgroundRenderer
from .renderers.device_frame import DeviceFrameRenderer
from .renderers.highlight import HighlightRenderer
from .renderers.text import TextRenderer
from .renderers.zoom import ZoomRenderer

logger = logging.getLogger(__name__)


def resolve_localized_asset(
    asset: Union[str, Dict[str, str]],
    language: str,
    base_language: str,
    config_dir: Optional[Path] = None,
) -> str:
    """Resolve localized asset path using hybrid approach.

    Supports two formats:
    1. String: Convention-based resolution with {lang}/ directory pattern
    2. Dict: Explicit per-language paths with 'default' fallback

    Resolution order:
    - Dict format: explicit mapping[language] → mapping['default'] → ""
    - String format: {lang}/path → {base_lang}/path → direct path

    Args:
        asset: Asset path (string or dict with language mappings)
        language: Current language code (e.g., 'en', 'es')
        base_language: Base/fallback language code
        config_dir: Base directory for resolving relative paths

    Returns:
        Resolved asset path (empty string if not found)

    Examples:
        # Dict format (explicit mapping)
        asset = {
            "en": "path/en.png",
            "es": "path/es.png",
            "default": "path/fallback.png"
        }
        resolve_localized_asset(asset, "en", "en") → "path/en.png"

        # String format (convention-based)
        asset = "screenshots/hero.png"
        # Returns "screenshots/es/hero.png" if exists
        resolve_localized_asset(asset, "es", "en")
        # Returns "screenshots/en/hero.png" if es not found
        resolve_localized_asset(asset, "es", "en")
        # Returns "screenshots/hero.png" if none found
        resolve_localized_asset(asset, "es", "en")
    """
    if not asset:
        return ""

    # Case 1: Dict format - Explicit per-language mapping
    if isinstance(asset, dict):
        # Try exact language match
        if language in asset:
            return asset[language]
        # Try default fallback
        if "default" in asset:
            return asset["default"]
        # No match found
        return ""

    # Case 2: String format - Convention-based resolution
    if isinstance(asset, str):
        asset_path = Path(asset)

        # Helper to check if path exists (handles relative/absolute)
        def path_exists(p: Path) -> bool:
            if p.is_absolute():
                return p.exists()
            if config_dir:
                return (config_dir / p).exists()
            return p.exists()

        # Try {lang}/ convention
        lang_path = asset_path.parent / language / asset_path.name
        if path_exists(lang_path):
            return str(lang_path)

        # Try {base_lang}/ convention (if different from current lang)
        if base_language != language:
            base_lang_path = asset_path.parent / base_language / asset_path.name
            if path_exists(base_lang_path):
                return str(base_lang_path)

        # Fallback to direct path
        return asset


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
        self.highlight_renderer = HighlightRenderer()
        self.zoom_renderer = ZoomRenderer()

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

            # Create canvas at target size
            # output_size is validated to tuple by Pydantic
            canvas = Image.new(
                "RGBA", config.output_size, (255, 255, 255, 0)  # type: ignore[arg-type]
            )
            logger.info(f"🎨 Created canvas: {config.output_size}")

            # Render background if specified
            if config.background:
                logger.info(f"🌈 Rendering background: {config.background.type}")
                self.background_renderer.render(config.background, canvas)

            # Process multiple images if available, otherwise use single image
            # (backward compatibility)
            if hasattr(config, "_image_configs") and config._image_configs:
                logger.info(
                    f"📷 Processing {len(config._image_configs)} images in layer order"
                )
                # Process images in YAML order (first = bottom layer, last = top layer)
                for i, img_config in enumerate(config._image_configs):
                    logger.info(
                        f"📐 Layer {i+1}/{len(config._image_configs)}: "
                        f"{Path(img_config['path']).name}"
                    )

                    # Load and position each image
                    source_image = self._load_source_image(img_config["path"])
                    logger.info(f"📷 Loaded source: {source_image.size}")

                    # Create temporary config for this image
                    temp_config = self._create_temp_config_for_image(config, img_config)

                    # Apply device frame if specified for this image
                    if img_config["frame"] and config.device_frame:
                        logger.info(
                            f"📱 Applying device frame to asset: {config.device_frame}"
                        )
                        positioned_image = self._apply_asset_frame(
                            source_image, canvas, temp_config
                        )
                    else:
                        positioned_image = self._position_source_image(
                            source_image, canvas, temp_config
                        )

                    # Composite this layer onto canvas
                    canvas = Image.alpha_composite(canvas, positioned_image)
            else:
                # Backward compatibility: single image processing
                logger.info("📷 Processing single image (legacy mode)")
                source_image = self._load_source_image(config.source_image)
                logger.info(f"📷 Loaded source: {source_image.size}")

                # Apply device frame to individual image if frame: true
                if config.image_frame and config.device_frame:
                    logger.info(
                        f"📱 Applying device frame to asset: {config.device_frame}"
                    )
                    positioned_image = self._apply_asset_frame(
                        source_image, canvas, config
                    )
                else:
                    logger.info("📐 Positioning source image")
                    positioned_image = self._position_source_image(
                        source_image, canvas, config
                    )

                canvas = Image.alpha_composite(canvas, positioned_image)

            # Render highlights (after images, before text)
            if hasattr(config, "_highlight_configs") and config._highlight_configs:
                logger.info(f"🔦 Rendering {len(config._highlight_configs)} highlights")
                for hl_config in config._highlight_configs:
                    self.highlight_renderer.render(hl_config, canvas)

            # Render zoom callouts (after highlights, before text)
            if hasattr(config, "_zoom_configs") and config._zoom_configs:
                logger.info(f"🔍 Rendering {len(config._zoom_configs)} zoom callouts")
                for zm_config in config._zoom_configs:
                    self.zoom_renderer.render(zm_config, canvas)

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

            # Convert RGBA to RGB to remove alpha channel
            # App Store does not accept images with alpha channels
            rgb_canvas = Image.new("RGB", canvas.size, (255, 255, 255))
            rgb_canvas.paste(canvas, mask=canvas)

            # Save based on file extension
            if output_path.suffix.lower() == ".jpg":
                rgb_canvas.save(output_path, "JPEG", quality=95)
            else:
                rgb_canvas.save(output_path, "PNG")

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
            opened_image = Image.open(image_path)
            # Convert to RGBA to ensure consistent handling
            if opened_image.mode != "RGBA":
                return opened_image.convert("RGBA")
            return opened_image
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
            f"📏 Scaling image: {original_width}×{original_height} → "
            f"{scaled_width}×{scaled_height} (scale: {scale_factor})"
        )

        # Resize the source image
        if scale_factor != 1.0:
            source_image = source_image.resize(
                (scaled_width, scaled_height), Image.Resampling.LANCZOS
            )

        # Apply rotation if specified
        rotation_angle = getattr(config, "image_rotation", 0) or 0
        if rotation_angle != 0:
            logger.info(f"🔄 Rotating image by {rotation_angle}°")
            source_image = source_image.rotate(
                -rotation_angle,  # Negative for clockwise rotation
                resample=Image.Resampling.BICUBIC,  # Use BICUBIC for compatibility
                expand=True,  # Expand bounds to prevent cropping
            )
            # Update dimensions after rotation
            scaled_width, scaled_height = source_image.size

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
            f"📐 Positioning asset: center at {position} → "
            f"({center_x}, {center_y}), top-left at ({x}, {y})"
        )

        # Create positioned image
        positioned = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
        positioned.paste(source_image, (x, y), source_image)

        return positioned

    def _create_temp_config_for_image(
        self, base_config: ScreenshotConfig, img_config: dict
    ) -> Any:
        """Create a temporary config for individual image processing."""

        # Create a copy of the base config with image-specific settings
        class TempConfig:
            def __init__(self, base: ScreenshotConfig, img: dict) -> None:
                self.name = base.name
                self.device_frame = base.device_frame
                self.output_size = base.output_size
                self.image_position = img["position"]
                self.image_scale = img["scale"]
                self.image_frame = img["frame"]
                self.image_rotation = img.get("rotation", 0)

        return TempConfig(base_config, img_config)

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
                    f"Canvas size {canvas.size} doesn't match frame size "
                    f"{frame_image.size}"
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
        source_image: Image.Image,
        canvas: Image.Image,
        config: ScreenshotConfig,
    ) -> Image.Image:
        """Apply device frame to individual asset with proper screen fitting.

        This function:
        1. Loads frame and detects screen area from alpha channel
        2. Fits source image to detected screen bounds (maintaining aspect ratio)
        3. Scales both fitted source and frame by image_scale
        4. Positions them together at specified location
        5. Applies mask to preserve rounded corners
        6. Overlays frame on top
        """
        try:
            # Load frame
            if config.device_frame is None:
                raise RenderError("Device frame name is required")
            frame_image = self.device_frame_renderer._load_frame_image(
                config.device_frame
            )
            original_frame_size = frame_image.size
            logger.info(f"📱 Original frame size: {original_frame_size}")

            # Detect screen bounds using flood fill from frame edges
            # Frame structure:
            # outer area (alpha=0) -> bezel (alpha>0) -> screen (alpha=0)
            # We need to exclude the outer area to find just the screen
            if frame_image.mode != "RGBA":
                frame_image = frame_image.convert("RGBA")

            alpha_channel = frame_image.split()[-1]
            alpha_pixels = alpha_channel.load()
            frame_width, frame_height = frame_image.size

            if alpha_pixels is None:
                raise RenderError("Failed to load alpha pixel data from frame")

            # Flood fill from edges to mark outer transparent area
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

            # Flood fill to find outer area
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
                pixel_val = alpha_pixels[x, y]
                alpha_val = pixel_val[0] if isinstance(pixel_val, tuple) else pixel_val
                if alpha_val > 0:  # Hit bezel, stop
                    continue
                visited.add((x, y))
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    queue.append((x + dx, y + dy))

            # Find bounding box of screen area (alpha=0 but NOT in visited)
            min_x, min_y = frame_width, frame_height
            max_x, max_y = 0, 0

            for y in range(frame_height):
                for x in range(frame_width):
                    pixel_val = alpha_pixels[x, y]
                    alpha_val = (
                        pixel_val[0] if isinstance(pixel_val, tuple) else pixel_val
                    )
                    if alpha_val == 0 and (x, y) not in visited:  # Pure screen area
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)

            # Don't expand - use exact detected screen bounds
            # The mask will handle edge gradients via anti-aliasing
            screen_x = min_x
            screen_y = min_y
            screen_width = max_x - min_x + 1
            screen_height = max_y - min_y + 1

            logger.info(
                f"📱 Detected screen area from flood fill: ({screen_x}, {screen_y}) "
                f"{screen_width}×{screen_height}"
            )

            # Step 1: Fit source image to frame's screen area
            source_width, source_height = source_image.size

            # Validate source dimensions to prevent division by zero
            if source_width <= 0 or source_height <= 0:
                raise ValueError(
                    f"Invalid source image dimensions: {source_width}×{source_height}"
                )

            scale_x = screen_width / source_width
            scale_y = screen_height / source_height
            fit_scale = min(scale_x, scale_y)  # Maintain aspect ratio

            fitted_width = int(source_width * fit_scale)
            fitted_height = int(source_height * fit_scale)

            logger.info(
                f"📱 Fitting source {source_width}×{source_height} to screen area "
                f"{screen_width}×{screen_height}: "
                f"scale={fit_scale:.3f}, result={fitted_width}×{fitted_height}"
            )

            fitted_source = source_image.resize(
                (fitted_width, fitted_height), Image.Resampling.LANCZOS
            )

            # Step 2: Apply image_scale to both fitted source and frame
            asset_scale = config.image_scale or 1.0

            final_source_width = int(fitted_width * asset_scale)
            final_source_height = int(fitted_height * asset_scale)
            final_source = fitted_source.resize(
                (final_source_width, final_source_height), Image.Resampling.LANCZOS
            )

            scaled_frame_width = int(original_frame_size[0] * asset_scale)
            scaled_frame_height = int(original_frame_size[1] * asset_scale)
            scaled_frame = frame_image.resize(
                (scaled_frame_width, scaled_frame_height), Image.Resampling.LANCZOS
            )

            logger.info(
                f"📱 Applied scale {asset_scale}: "
                f"source {fitted_width}×{fitted_height} → "
                f"{final_source_width}×{final_source_height}, "
                f"frame → {scaled_frame_width}×{scaled_frame_height}"
            )

            # Step 3: Generate screen mask from scaled frame (preserves rounded corners)
            screen_mask = self.device_frame_renderer.generate_screen_mask_from_image(
                scaled_frame
            )

            # Step 4: Calculate positioning
            position = config.image_position or ["50%", "50%"]
            center_x = self._convert_percentage_to_pixels(position[0], canvas.width)
            center_y = self._convert_percentage_to_pixels(position[1], canvas.height)

            # Source position (centered within frame's screen area)
            scaled_screen_x = int(screen_x * asset_scale)
            scaled_screen_y = int(screen_y * asset_scale)
            scaled_screen_width = int(screen_width * asset_scale)
            scaled_screen_height = int(screen_height * asset_scale)

            # Center source within scaled screen area
            source_offset_x = (scaled_screen_width - final_source_width) // 2
            source_offset_y = (scaled_screen_height - final_source_height) // 2

            source_local_x = scaled_screen_x + source_offset_x
            source_local_y = scaled_screen_y + source_offset_y

            # Step 5: Build framed asset in frame-local coordinates
            framed_asset = Image.new(
                "RGBA", (scaled_frame_width, scaled_frame_height), (255, 255, 255, 0)
            )
            framed_asset.paste(
                final_source, (source_local_x, source_local_y), final_source
            )

            # Clip source to the screen area with anti-aliased mask
            transparent_frame_bg = Image.new(
                "RGBA", (scaled_frame_width, scaled_frame_height), (255, 255, 255, 0)
            )
            framed_asset = Image.composite(
                framed_asset, transparent_frame_bg, screen_mask
            )

            # Overlay frame bezel on top of clipped source
            framed_asset = Image.alpha_composite(framed_asset, scaled_frame)

            # Step 6: Apply optional rotation to the whole framed asset
            rotation_angle = getattr(config, "image_rotation", 0) or 0
            if rotation_angle != 0:
                logger.info(f"🔄 Rotating framed asset by {rotation_angle}°")
                framed_asset = framed_asset.rotate(
                    -rotation_angle,  # Negative for clockwise rotation
                    resample=Image.Resampling.BICUBIC,
                    expand=True,
                )

            # Step 7: Place framed asset on canvas centered at requested position
            framed_width, framed_height = framed_asset.size
            frame_x = center_x - framed_width // 2
            frame_y = center_y - framed_height // 2

            logger.info(
                f"📱 Positioning framed asset: center at ({center_x}, {center_y}), "
                f"top-left at ({frame_x}, {frame_y})"
            )

            result = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
            result.paste(framed_asset, (frame_x, frame_y), framed_asset)

            logger.info(
                "📱 Applied device frame with proper fitting, masking, and rotation"
            )
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
            config_dir: Directory containing the config file (for relative path
                resolution)

        Returns:
            List of paths to generated screenshots
        """
        logger.info(f"🚀 Starting project: {project_config.project.name}")
        logger.info(f"📁 Output directory: {project_config.project.output_dir}")
        logger.info(f"🎯 Screenshots to generate: {len(project_config.screenshots)}")

        # Use unified generation approach (handles both single and multi-language)
        return self._generate_localized_project(project_config, config_dir)

    def _generate_localized_project(
        self, project_config: ProjectConfig, config_dir: Optional[Path] = None
    ) -> List[Path]:
        """Generate screenshots for all configured languages and devices."""

        # Handle both localized and non-localized projects
        if project_config.localization:
            localization_config = project_config.localization
            languages = localization_config.languages
            logger.info(f"🌍 Multi-language mode: {len(languages)} languages")
            logger.info(f"📝 Languages: {', '.join(languages)}")
        else:
            languages = ["en"]  # Default to English for non-localized projects
            localization_config = None
            logger.info("🌍 Single language mode")

        # Initialize localization components only if needed
        if not config_dir:
            config_dir = Path.cwd()

        if localization_config:
            xcstrings_manager = XCStringsManager(localization_config, config_dir)
            content_resolver = LocalizedContentResolver(xcstrings_manager)

            # Extract all text keys from all screenshots
            all_text_keys = set()
            for screenshot_def in project_config.screenshots.values():
                text_keys = content_resolver.extract_text_keys_from_content(
                    screenshot_def.content
                )
                all_text_keys.update(text_keys)

            logger.info(f"🔤 Found {len(all_text_keys)} unique text keys")

            # Create or update xcstrings file
            if not xcstrings_manager.xcstrings_exists():
                logger.info("📝 Creating XCStrings file")
                xcstrings_manager.create_xcstrings_file(all_text_keys)
            else:
                logger.info("📝 Updating XCStrings file with new keys")
                xcstrings_manager.update_xcstrings_with_new_keys(all_text_keys)

        # Get defaults
        defaults = project_config.defaults or {}
        default_background = defaults.get("background")

        # Get device and output_size from project config
        device = project_config.project.device
        # output_size is validated and always a tuple at runtime
        output_size: Tuple[int, int] = (
            project_config.project.output_size  # type: ignore[assignment]
        )
        logger.info(f"📱 Processing device: {device}")
        logger.info(f"📐 Output size: {output_size}")

        all_results = []

        # Generate screenshots for each language
        for language in languages:
            logger.info(
                f"🌐 Generating screenshots for device: {device}, "
                f"language: {language}"
            )

            for i, (screenshot_id, screenshot_def) in enumerate(
                project_config.screenshots.items(), 1
            ):
                logger.info(
                    f"[{device}] [{language}] "
                    f"[{i}/{len(project_config.screenshots)}] {screenshot_id}"
                )
                try:
                    # Create localized content (or use original for non-localized)
                    if localization_config:
                        localized_content = content_resolver.localize_content_items(
                            screenshot_def.content, language
                        )
                        # Create copy with localized content
                        from copy import deepcopy

                        processed_screenshot_def = deepcopy(screenshot_def)
                        processed_screenshot_def.content = localized_content
                    else:
                        processed_screenshot_def = screenshot_def

                    # Generate device and language-specific output directory
                    if localization_config:
                        # Multi-language: output_dir/language/device/
                        device_output_dir = str(
                            Path(project_config.project.output_dir)
                            / language
                            / device.replace(" ", "_")
                        )
                    else:
                        # Single language: output_dir/device/
                        # (ALWAYS include device folder)
                        device_output_dir = str(
                            Path(project_config.project.output_dir)
                            / device.replace(" ", "_")
                        )

                    # Convert to ScreenshotConfig and generate
                    # Get base_language for asset resolution
                    base_lang = (
                        localization_config.base_language
                        if localization_config
                        else None
                    )
                    temp_config = self._convert_to_screenshot_config(
                        processed_screenshot_def,
                        device,  # Use device name directly
                        default_background,
                        device_output_dir,
                        config_dir,
                        screenshot_id,
                        output_size=output_size,  # Pass project-level output size
                        language=language,
                        base_language=base_lang,
                    )
                    if temp_config:
                        output_path = self.generate_screenshot(temp_config)
                        all_results.append(output_path)
                    else:
                        logger.warning(
                            f"Skipping {screenshot_id} for {device}/{language}: "
                            f"no source image found"
                        )
                except Exception as _e:
                    logger.error(
                        f"Failed to generate {screenshot_id} for "
                        f"{device}/{language}: {_e}"
                    )
                    # Continue with next screenshot instead of failing project
                    continue

        logger.info(
            f"🎉 Project complete! Generated {len(all_results)} screenshots "
            f"for {device} across {len(languages)} language(s)"
        )
        return all_results

    def _resolve_output_path(
        self,
        output_dir: str,
        screenshot_name: str,
        config_dir: Optional[Path] = None,
    ) -> Path:
        """Resolve output path relative to config directory."""  # noqa: D401
        output_path = Path(output_dir) / f"{screenshot_name}.png"

        if config_dir:
            # Make path relative to config directory
            if not output_path.is_absolute():
                output_path = config_dir / output_path

        return output_path

    def _convert_to_screenshot_config(
        self,
        screenshot_def: Any,
        device_frame: Any,
        default_background: Any,
        output_dir: str,
        config_dir: Optional[Path] = None,
        screenshot_id: Optional[str] = None,
        output_size: Optional[Tuple[int, int]] = None,
        language: Optional[str] = None,
        base_language: Optional[str] = None,
    ) -> Optional[ScreenshotConfig]:
        """Convert ScreenshotDefinition to ScreenshotConfig for generation."""

        # Process content items and collect ALL images
        image_configs = []
        text_overlays = []
        highlight_configs: List[Dict[str, Any]] = []
        zoom_configs: List[Dict[str, Any]] = []

        # Process all content items to collect images, text, highlights, and zooms
        for item in screenshot_def.content:
            if item.type == "image":
                # Resolve localized asset path
                if language and base_language:
                    # Use localized asset resolution
                    asset_path = resolve_localized_asset(
                        item.asset or "", language, base_language, config_dir
                    )
                else:
                    # Non-localized fallback
                    asset_path = (
                        item.asset
                        if isinstance(item.asset, str)
                        else (item.asset or "")
                    )

                # Handle absolute vs relative paths
                if not asset_path:
                    source_image_path = ""
                elif Path(asset_path).is_absolute():
                    source_image_path = asset_path
                elif config_dir and asset_path:
                    # Resolve relative paths against config directory
                    try:
                        source_image_path = str((config_dir / asset_path).resolve())
                    except (OSError, ValueError):
                        source_image_path = asset_path
                else:
                    source_image_path = asset_path

                image_scale = item.scale or 1.0
                image_position = item.position or ["50%", "50%"]  # Default to center

                # Store image configuration including frame and rotation settings
                image_rotation = getattr(item, "rotation", 0) or 0
                image_config = {
                    "path": source_image_path,
                    "scale": image_scale,
                    "position": image_position,
                    "frame": getattr(item, "frame", False),  # Capture frame setting
                    "rotation": image_rotation,  # Capture rotation setting
                }
                image_configs.append(image_config)
                logger.info(
                    f"📏 Image: scale={image_scale * 100:.0f}%, "
                    f"position={image_position}, "
                    f"frame={getattr(item, 'frame', False)}, rotation={image_rotation}°"
                )
                # Continue processing more images instead of breaking

            elif item.type == "highlight":
                hl = {
                    "shape": item.shape,
                    "position": item.position,
                    "dimensions": item.dimensions,
                    "border_color": item.border_color,
                    "border_width": item.border_width,
                    "fill_color": item.fill_color,
                    "corner_radius": item.corner_radius,
                    "shadow": item.shadow,
                    "shadow_color": item.shadow_color,
                    "shadow_blur": item.shadow_blur,
                    "shadow_offset": item.shadow_offset,
                    "spotlight": item.spotlight,
                    "spotlight_color": item.spotlight_color,
                    "spotlight_opacity": item.spotlight_opacity,
                    "blur_background": item.blur_background,
                    "blur_radius": item.blur_radius,
                }
                highlight_configs.append(hl)

            elif item.type == "zoom":
                zm = {
                    "source_position": item.source_position,
                    "source_size": item.source_size,
                    "display_position": item.display_position or item.position,
                    "display_size": item.display_size,
                    "shape": item.shape or "circle",
                    "border_color": item.border_color,
                    "border_width": item.border_width,
                    "corner_radius": item.corner_radius,
                    "connector": item.connector,
                    "connector_color": item.connector_color,
                    "connector_width": item.connector_width,
                    "connector_style": item.connector_style,
                    "connector_fill": item.connector_fill,
                    "shadow": item.shadow,
                    "shadow_color": item.shadow_color,
                    "shadow_blur": item.shadow_blur,
                    "shadow_offset": item.shadow_offset,
                    "source_indicator": item.source_indicator,
                    "source_indicator_style": item.source_indicator_style,
                    "zoom_level": item.zoom_level,
                }
                zoom_configs.append(zm)

        # Skip if no images found
        if not image_configs:
            logger.warning(f"No images found for {screenshot_id}")
            return None

        # Validate that all image paths exist
        for img_config in image_configs:
            img_path = str(img_config["path"])
            if not img_path or not Path(img_path).exists():
                logger.error(f"Source image not found: {img_path}")
                if not img_path:
                    raise ConfigurationError("Image asset path is empty or missing")
                else:
                    raise ConfigurationError(f"Image asset not found: {img_path}")

        # Use first image for canvas sizing (backward compatibility)
        # TODO: Could be enhanced to calculate optimal canvas size from all images
        primary_image_config = image_configs[0]
        from PIL import Image

        img_path_str = str(primary_image_config["path"])
        source_image = Image.open(img_path_str)
        original_width, original_height = source_image.size
        scale_raw = primary_image_config["scale"]
        # Ensure scale is a numeric value
        if isinstance(scale_raw, (int, float)):
            image_scale_val = float(scale_raw)
        else:
            image_scale_val = float(str(scale_raw))

        # Calculate scaled image dimensions
        scaled_width = int(original_width * image_scale_val)
        scaled_height = int(original_height * image_scale_val)
        logger.info(
            f"📐 Original: {original_width}×{original_height} → "
            f"Scaled: {scaled_width}×{scaled_height}"
        )

        # Use project-level output_size for canvas dimensions
        if output_size:
            canvas_width, canvas_height = output_size
            logger.info(
                f"📐 Canvas: {canvas_width}×{canvas_height} (project output size)"
            )
        else:
            # Fallback for backward compatibility (shouldn't happen with new config)
            canvas_width, canvas_height = scaled_width + 400, scaled_height + 800
            logger.warning("No output_size specified, using content-based sizing")

        # Check frame setting: None=use default, True=force frame, False=no frame
        frame_setting = getattr(screenshot_def, "frame", None)
        if frame_setting is False:
            should_use_frame = False  # Explicitly disabled
        else:
            should_use_frame = bool(
                device_frame
            )  # Use default logic if frame is None or True

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
                        font_family=getattr(item, "font_family", "Arial") or "Arial",
                        color=item.color,  # Don't default to black if gradient
                        # is provided
                        gradient=item.gradient,  # Pass gradient configuration
                        alignment=getattr(item, "alignment", "center") or "center",
                        anchor="center",  # Use center anchor for
                        # percentage-based positioning
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

        # Create background config with priority: screenshot background >
        # default background > white
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
        # For backward compatibility, use primary image in main config
        img_pos = primary_image_config["position"]
        img_position_list = img_pos if isinstance(img_pos, list) else None

        # Ensure screenshot_id is not None
        if screenshot_id is None:
            screenshot_id = "screenshot"

        scale_raw2 = primary_image_config["scale"]
        # Ensure scale is a numeric value
        if isinstance(scale_raw2, (int, float)):
            scale_val = float(scale_raw2)
        else:
            scale_val = float(str(scale_raw2))

        config = ScreenshotConfig(
            name=screenshot_id,
            source_image=str(primary_image_config["path"]),
            device_frame=device_frame if should_use_frame else None,
            output_size=(canvas_width, canvas_height),  # Dynamic size based on content
            background=background_config,
            text_overlays=text_overlays,
            image_position=img_position_list,
            image_scale=scale_val,
            image_frame=bool(primary_image_config["frame"]),
            output_path=str(
                self._resolve_output_path(output_dir, screenshot_id, config_dir)
            ),
        )

        # Store ALL image configurations as custom attribute
        # for multi-image support
        config._image_configs = image_configs  # type: ignore[attr-defined]
        config._scaled_dimensions = (  # type: ignore[attr-defined]
            scaled_width,
            scaled_height,
        )
        config._highlight_configs = highlight_configs  # type: ignore[attr-defined]
        config._zoom_configs = zoom_configs  # type: ignore[attr-defined]

        return config

    def _convert_position(
        self, position: list[str], canvas_size: tuple[int, int]
    ) -> tuple[int, int]:
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
