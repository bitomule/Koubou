"""Configuration models using Pydantic for type safety and validation."""

import json
import re
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator


def load_appstore_sizes() -> Dict[str, Dict[str, Union[int, str]]]:
    """Load App Store standard sizes from JSON file."""
    sizes_file = Path(__file__).parent / "appstore_sizes.json"
    with open(sizes_file, "r") as f:
        data: Dict[str, Dict[str, Union[int, str]]] = json.load(f)
        return data


def resolve_output_size(size: Union[str, Tuple[int, int]]) -> Tuple[int, int]:
    """Resolve output size from named App Store size or custom tuple.

    Args:
        size: Either a named size (e.g., "iPhone6_9") or custom tuple (width, height)

    Returns:
        Tuple of (width, height)

    Raises:
        ValueError: If named size not found or dimensions invalid
    """
    if isinstance(size, tuple):
        width, height = size
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions: {width}x{height}")
        return size

    # Named size - look up in App Store sizes
    appstore_sizes = load_appstore_sizes()
    if size not in appstore_sizes:
        available = ", ".join(appstore_sizes.keys())
        raise ValueError(
            f"Unknown App Store size '{size}'. Available sizes: {available}"
        )

    size_info = appstore_sizes[size]
    width = int(size_info["width"])
    height = int(size_info["height"])
    return (width, height)


# Hex color validation pattern: #RGB, #RRGGBB, or #RRGGBBAA
HEX_COLOR_PATTERN = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")


def validate_hex_color(color: str, field_name: str = "Color") -> None:
    """Validate that a color string is a valid hex color.

    Args:
        color: Color string to validate (e.g., "#FF0000")
        field_name: Name of the field for error messages

    Raises:
        ValueError: If color is not a valid hex color
    """
    if not HEX_COLOR_PATTERN.match(color):
        raise ValueError(
            f"{field_name} must be in hex format: #RGB, #RRGGBB, or #RRGGBBAA "
            f"(e.g., #FFF, #FFFFFF, or #FFFFFF80). Got: {color}"
        )


class GradientConfig(BaseModel):
    """Universal gradient configuration for text and backgrounds."""

    type: Literal["solid", "linear", "radial", "conic"] = Field(
        ..., description="Gradient type"
    )
    colors: List[str] = Field(..., description="List of hex colors")
    positions: Optional[List[float]] = Field(
        default=None, description="Color stop positions (0.0-1.0)"
    )
    direction: Optional[float] = Field(
        default=0, description="Gradient direction in degrees (linear gradients)"
    )
    center: Optional[Tuple[str, str]] = Field(
        default=None, description="Center point for radial/conic gradients"
    )
    radius: Optional[str] = Field(
        default=None, description="Radius for radial gradients (e.g., '50%', '100px')"
    )
    start_angle: Optional[float] = Field(
        default=0, description="Starting angle in degrees (conic gradients)"
    )

    @field_validator("colors")
    @classmethod
    def validate_colors(cls, v: List[str], info: ValidationInfo) -> List[str]:
        gradient_type = info.data.get("type")

        # Validate minimum colors based on type
        if gradient_type == "solid" and len(v) != 1:
            raise ValueError("Solid backgrounds require exactly 1 color")
        elif gradient_type in ["linear", "radial", "conic"] and len(v) < 2:
            raise ValueError("Gradients require at least 2 colors")
        elif not v:
            raise ValueError("At least one color is required")

        # Validate color format
        for i, color in enumerate(v):
            try:
                validate_hex_color(color, f"Color at index {i}")
            except ValueError as e:
                # Re-raise with more context
                raise ValueError(str(e)) from None
        return v

    @field_validator("positions")
    @classmethod
    def validate_positions(
        cls, v: Optional[List[float]], info: ValidationInfo
    ) -> Optional[List[float]]:
        if v is None:
            return v

        colors = info.data.get("colors", [])
        if len(v) != len(colors):
            raise ValueError("Positions array must match colors array length")

        if not all(0.0 <= pos <= 1.0 for pos in v):
            raise ValueError("Color stop positions must be between 0.0 and 1.0")

        if v != sorted(v):
            raise ValueError("Color stop positions must be in ascending order")

        return v

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0 or v >= 360):
            raise ValueError("Direction must be between 0 and 359 degrees")
        return v

    @field_validator("start_angle")
    @classmethod
    def validate_start_angle(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0 or v >= 360):
            raise ValueError("Start angle must be between 0 and 359 degrees")
        return v


class TextOverlay(BaseModel):
    """Configuration for text overlays on screenshots."""

    content: str = Field(..., description="The text content to display")
    position: Tuple[int, int] = Field(..., description="X, Y position in pixels")
    font_size: int = Field(default=24, description="Font size in pixels")
    font_family: str = Field(default="Arial", description="Font family name")
    font_weight: str = Field(default="normal", description="Font weight (normal, bold)")

    # Text fill options (mutually exclusive)
    color: Optional[str] = Field(
        default=None, description="Solid text color in hex format"
    )
    gradient: Optional[GradientConfig] = Field(
        default=None, description="Text gradient configuration"
    )

    alignment: Literal["left", "center", "right"] = Field(default="center")
    anchor: Literal[
        "top-left",
        "top-center",
        "top-right",
        "center-left",
        "center",
        "center-right",
        "bottom-left",
        "bottom-center",
        "bottom-right",
    ] = Field(default="center", description="Anchor point for position")
    max_width: Optional[int] = Field(
        default=None, description="Maximum width for text wrapping"
    )
    max_lines: Optional[int] = Field(
        default=None, description="Maximum number of lines for text wrapping"
    )
    min_font_size: Optional[int] = Field(
        default=None, description="Minimum font size for auto-sizing"
    )
    max_height: Optional[int] = Field(
        default=None,
        description="Max height in pixels for the text block",
    )
    line_height: float = Field(default=1.2, description="Line height multiplier")
    stroke_width: Optional[int] = Field(default=None, description="Text stroke width")

    # Stroke options (mutually exclusive)
    stroke_color: Optional[str] = Field(default=None, description="Solid stroke color")
    stroke_gradient: Optional[GradientConfig] = Field(
        default=None, description="Stroke gradient configuration"
    )
    rotation: Optional[float] = Field(
        default=0, description="Rotation angle in degrees (clockwise)"
    )

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v:
            validate_hex_color(v, "Color")
        return v

    @field_validator("stroke_color")
    @classmethod
    def validate_stroke_color(cls, v: Optional[str]) -> Optional[str]:
        if v:
            validate_hex_color(v, "Stroke color")
        return v

    @field_validator("gradient")
    @classmethod
    def validate_fill_options(
        cls, v: Optional[GradientConfig], info: ValidationInfo
    ) -> Optional[GradientConfig]:
        color = info.data.get("color")

        # Validation only - ensure both color and gradient are not specified
        if color is not None and v is not None:
            raise ValueError(
                "Cannot specify both 'color' and 'gradient'. Choose exactly one."
            )

        return v

    @model_validator(mode="after")
    def validate_stroke_options(self):
        """Validate stroke configuration after all fields are set."""
        if self.stroke_width is not None and self.stroke_width > 0:
            if self.stroke_color is not None and self.stroke_gradient is not None:
                raise ValueError(
                    "Cannot specify both 'stroke_color' and 'stroke_gradient'. "
                    "Choose exactly one."
                )
            elif self.stroke_color is None and self.stroke_gradient is None:
                raise ValueError(
                    "When 'stroke_width' is specified, must provide either "
                    "'stroke_color' or 'stroke_gradient'."
                )
        return self


class ScreenshotConfig(BaseModel):
    """Configuration for a single screenshot generation."""

    name: str = Field(..., description="Name/identifier for this screenshot")
    source_image: str = Field(..., description="Path to source screenshot image")
    device_frame: Optional[str] = Field(
        default=None, description="Device frame to apply"
    )
    output_size: Union[str, Tuple[int, int]] = Field(
        ...,
        description=(
            "Final output size. Either App Store named size (e.g., 'iPhone6_9') "
            "or custom tuple [width, height]"
        ),
    )
    output_path: Optional[str] = Field(default=None, description="Custom output path")
    background: Optional[GradientConfig] = Field(
        default=None, description="Background configuration"
    )
    text_overlays: List[TextOverlay] = Field(
        default=[], description="List of text overlays"
    )
    image_position: Optional[List[str]] = Field(
        default=None, description="Image position as [x%, y%] relative to canvas"
    )
    image_scale: Optional[float] = Field(default=None, description="Image scale factor")
    image_frame: Optional[bool] = Field(
        default=False,
        description="Apply device frame to image at image position and scale",
    )
    image_rotation: Optional[float] = Field(
        default=0, description="Image rotation angle in degrees (clockwise)"
    )

    @field_validator("source_image")
    @classmethod
    def validate_source_image(cls, v: str) -> str:
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Source image not found: {v}")
        return v

    @field_validator("output_size")
    @classmethod
    def validate_output_size(cls, v: Union[str, Tuple[int, int]]) -> Tuple[int, int]:
        """Validate and resolve output size to tuple."""
        # Resolve named size or validate custom tuple
        resolved = resolve_output_size(v)
        width, height = resolved

        if width > 10000 or height > 10000:
            raise ValueError("Output size too large (max 10000x10000)")
        return resolved


class ContentItem(BaseModel):
    """Individual content item in a screenshot."""

    type: Literal["text", "image", "highlight", "zoom"] = Field(
        ..., description="Type of content item"
    )
    content: Optional[str] = Field(default=None, description="Text content")
    asset: Optional[Union[str, Dict[str, str]]] = Field(
        default=None,
        description=(
            "Image asset path. Supports two formats:\n"
            "1. String: Simple path or convention-based localized path "
            "(e.g., 'screenshots/hero.png' resolves to "
            "'screenshots/{lang}/hero.png')\n"
            "2. Dict: Explicit per-language paths with optional "
            "'default' fallback "
            "(e.g., {'en': 'path/en.png', 'es': 'path/es.png', "
            "'default': 'path/fallback.png'})"
        ),
    )
    position: Tuple[str, str] = Field(
        default=("50%", "50%"), description="Position as percentage or pixels"
    )
    size: Optional[int] = Field(default=24, description="Font size for text")
    max_width: Optional[int] = Field(
        default=None, description="Maximum width for text wrapping"
    )
    max_lines: Optional[int] = Field(
        default=None, description="Maximum number of lines"
    )
    max_height: Optional[int] = Field(
        default=None,
        description="Max height in pixels for the text block",
    )
    min_size: Optional[int] = Field(
        default=None, description="Minimum font size for auto-sizing"
    )

    # Text fill options (mutually exclusive)
    color: Optional[str] = Field(default=None, description="Solid text color")
    gradient: Optional[GradientConfig] = Field(
        default=None, description="Text gradient"
    )

    weight: Optional[str] = Field(default="normal", description="Font weight")
    font_family: Optional[str] = Field(default="Arial", description="Font family name")
    alignment: Optional[str] = Field(
        default="center", description="Text alignment (left, center, right)"
    )

    # Stroke options
    stroke_width: Optional[int] = Field(default=None, description="Text stroke width")
    stroke_color: Optional[str] = Field(default=None, description="Solid stroke color")
    stroke_gradient: Optional[GradientConfig] = Field(
        default=None, description="Stroke gradient"
    )

    scale: Optional[float] = Field(default=1.0, description="Image scale factor")
    frame: Optional[bool] = Field(
        default=False, description="Apply device frame to image"
    )
    rotation: Optional[float] = Field(
        default=0, description="Rotation angle in degrees (clockwise)"
    )

    # Highlight/Zoom shared fields
    shape: Optional[Literal["circle", "rounded_rect", "rect"]] = Field(
        default=None, description="Shape for highlight or zoom callout"
    )
    dimensions: Optional[Tuple[str, str]] = Field(
        default=None, description="Width, height for highlight (% or px)"
    )
    border_color: Optional[str] = Field(
        default=None, description="Border color in hex format"
    )
    border_width: Optional[int] = Field(default=3, description="Border width in pixels")
    fill_color: Optional[str] = Field(
        default=None, description="Fill color in hex format (supports alpha)"
    )
    corner_radius: Optional[int] = Field(
        default=16, description="Corner radius for rounded_rect shape"
    )

    # Shadow (shared highlight + zoom)
    shadow: Optional[bool] = Field(default=False, description="Enable drop shadow")
    shadow_color: Optional[str] = Field(
        default="#00000040", description="Shadow color with alpha"
    )
    shadow_blur: Optional[int] = Field(
        default=15, description="Gaussian blur radius for shadow"
    )
    shadow_offset: Optional[Tuple[str, str]] = Field(
        default=("0", "6"), description="Shadow X, Y offset in px"
    )

    # Spotlight (highlight only)
    spotlight: Optional[bool] = Field(
        default=False, description="Enable spotlight mode (dim background)"
    )
    spotlight_color: Optional[str] = Field(
        default="#000000", description="Spotlight overlay color"
    )
    spotlight_opacity: Optional[float] = Field(
        default=0.5, description="Spotlight overlay opacity 0.0-1.0"
    )

    # Blur background (highlight only)
    blur_background: Optional[bool] = Field(
        default=False, description="Blur non-highlighted area"
    )
    blur_radius: Optional[int] = Field(
        default=20, description="Gaussian blur radius for background blur"
    )

    # Zoom-specific fields
    source_position: Optional[Tuple[str, str]] = Field(
        default=None, description="Center of area to magnify (% or px)"
    )
    source_size: Optional[Tuple[str, str]] = Field(
        default=None, description="Size of source crop region (% or px)"
    )
    display_position: Optional[Tuple[str, str]] = Field(
        default=None, description="Where magnified view appears (% or px)"
    )
    display_size: Optional[Tuple[str, str]] = Field(
        default=None, description="Size of magnified bubble (% or px)"
    )
    zoom_level: Optional[float] = Field(
        default=None,
        description="Auto-calculate display_size as source_size * zoom_level",
    )

    # Source indicator (zoom only)
    source_indicator: Optional[bool] = Field(
        default=True, description="Show outline on source region"
    )
    source_indicator_style: Optional[Literal["border", "dashed", "fill"]] = Field(
        default="border", description="Source indicator style"
    )

    # Connector fields (zoom only)
    connector: Optional[bool] = Field(
        default=False, description="Draw connector line from source to display"
    )
    connector_color: Optional[str] = Field(
        default=None, description="Connector line color (defaults to border_color)"
    )
    connector_width: Optional[int] = Field(
        default=2, description="Connector line width in pixels"
    )
    connector_style: Optional[Literal["straight", "curved", "facing"]] = Field(
        default="straight", description="Connector rendering style"
    )
    connector_fill: Optional[str] = Field(
        default=None, description="Fill color between facing connector lines"
    )

    @field_validator("color")
    @classmethod
    def validate_color_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            validate_hex_color(v, "Color")
        return v

    @field_validator("stroke_color")
    @classmethod
    def validate_stroke_color_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            validate_hex_color(v, "Stroke color")
        return v

    @field_validator("gradient")
    @classmethod
    def validate_text_fill_options(
        cls, v: Optional[GradientConfig], info: ValidationInfo
    ) -> Optional[GradientConfig]:
        color = info.data.get("color")

        # Validation only - ensure both color and gradient are not specified
        if color is not None and v is not None:
            raise ValueError(
                "Cannot specify both 'color' and 'gradient'. Choose exactly one."
            )

        return v

    @field_validator("stroke_gradient")
    @classmethod
    def validate_stroke_fill_options(
        cls, v: Optional[GradientConfig], info: ValidationInfo
    ) -> Optional[GradientConfig]:
        stroke_color = info.data.get("stroke_color")
        stroke_width = info.data.get("stroke_width")

        # Only validate if stroke is being used
        if stroke_width is not None and stroke_width > 0:
            if stroke_color is not None and v is not None:
                raise ValueError(
                    "Cannot specify both 'stroke_color' and 'stroke_gradient'. "
                    "Choose exactly one."
                )
            elif stroke_color is None and v is None:
                raise ValueError(
                    "When 'stroke_width' is specified, must provide either "
                    "'stroke_color' or 'stroke_gradient'."
                )

        return v

    @field_validator("border_color")
    @classmethod
    def validate_border_color_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            validate_hex_color(v, "Border color")
        return v

    @field_validator("fill_color")
    @classmethod
    def validate_fill_color_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            validate_hex_color(v, "Fill color")
        return v

    @field_validator("connector_color")
    @classmethod
    def validate_connector_color_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            validate_hex_color(v, "Connector color")
        return v

    @field_validator("connector_fill")
    @classmethod
    def validate_connector_fill_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            validate_hex_color(v, "Connector fill")
        return v

    @field_validator("shadow_color")
    @classmethod
    def validate_shadow_color_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            validate_hex_color(v, "Shadow color")
        return v

    @field_validator("spotlight_color")
    @classmethod
    def validate_spotlight_color_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            validate_hex_color(v, "Spotlight color")
        return v

    @field_validator("spotlight_opacity")
    @classmethod
    def validate_spotlight_opacity_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Spotlight opacity must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def validate_type_required_fields(self):
        if self.type == "highlight":
            if self.shape is None:
                raise ValueError("Highlight items require 'shape'")
        elif self.type == "zoom":
            if self.source_position is None:
                raise ValueError("Zoom items require 'source_position'")
            if self.source_size is None:
                raise ValueError("Zoom items require 'source_size'")
            # display_size is optional if zoom_level is set
            if self.display_size is None and self.zoom_level is None:
                raise ValueError("Zoom items require 'display_size' or 'zoom_level'")
        # Validate auto-sizing fields
        if self.min_size is not None:
            if self.max_width is None:
                raise ValueError("min_size requires max_width to be set")
            if self.max_height is None:
                raise ValueError("min_size requires max_height to be set")
            if self.size is not None and self.min_size > self.size:
                raise ValueError(
                    f"min_size ({self.min_size}) must be <= size ({self.size})"
                )
        return self

    @field_validator("asset")
    @classmethod
    def validate_asset_format(
        cls, v: Optional[Union[str, Dict[str, str]]]
    ) -> Optional[Union[str, Dict[str, str]]]:
        """Validate asset field format."""
        if v is None:
            return v

        if isinstance(v, dict):
            if not v:
                raise ValueError("Asset dict cannot be empty")

            # Validate keys are valid language codes (2-3 letters or 'default')
            for key in v.keys():
                if key != "default" and not (2 <= len(key) <= 3 and key.isalpha()):
                    raise ValueError(
                        f"Invalid language code '{key}'. "
                        "Use 2-3 letter codes (e.g., 'en', 'es', 'pt') or 'default'"
                    )

            # Validate all values are non-empty strings
            for lang, path in v.items():
                if not path or not isinstance(path, str):
                    raise ValueError(
                        f"Asset path for '{lang}' must be a non-empty string"
                    )

        return v


class ScreenshotDefinition(BaseModel):
    """Screenshot definition with content items."""

    background: Optional[GradientConfig] = Field(
        default=None,
        description=(
            "Background configuration (optional - uses default if not specified)"
        ),
    )
    content: List[ContentItem] = Field(..., description="List of content items")
    frame: Optional[bool] = Field(
        default=None,
        description=(
            "Whether to use device frame (None=use default, True=force frame, "
            "False=no frame)"
        ),
    )


class LocalizationConfig(BaseModel):
    """Localization configuration for multi-language screenshot generation."""

    base_language: str = Field(
        ..., description="Base/source language code (e.g., 'en')"
    )
    languages: List[str] = Field(..., description="List of target language codes")
    xcstrings_path: str = Field(
        default="Localizable.xcstrings",
        description="Path to xcstrings localization file",
    )

    @field_validator("base_language")
    @classmethod
    def validate_base_language(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Base language cannot be empty")
        return v.strip()

    @field_validator("languages")
    @classmethod
    def validate_languages(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Languages list cannot be empty")

        # Remove duplicates while preserving order
        seen = set()
        unique_languages = []
        for lang in v:
            if lang and lang.strip() and lang.strip() not in seen:
                clean_lang = lang.strip()
                seen.add(clean_lang)
                unique_languages.append(clean_lang)

        if not unique_languages:
            raise ValueError("No valid languages provided")

        return unique_languages

    @field_validator("languages")
    @classmethod
    def validate_base_language_in_languages(
        cls, v: List[str], info: ValidationInfo
    ) -> List[str]:
        base_language = info.data.get("base_language")
        if base_language and base_language not in v:
            raise ValueError(
                f"Base language '{base_language}' must be included in languages list"
            )
        return v


class ProjectInfo(BaseModel):
    """Project information."""

    name: str = Field(..., description="Project name")
    output_dir: str = Field(default="output", description="Output directory")
    device: str = Field(..., description="Target device frame")
    output_size: Tuple[int, int] = Field(
        default=(1320, 2868),  # Default to iPhone6_9 dimensions
        description=(
            "Output size for all screenshots. Either App Store named size "
            "(e.g., 'iPhone6_9') or custom tuple [width, height]"
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_output_size_field(cls, data: dict) -> dict:
        """Resolve output_size from string or list to tuple before validation."""
        if isinstance(data, dict) and "output_size" in data:
            v = data["output_size"]

            # Handle list input (from YAML) - convert to tuple
            if isinstance(v, list) and len(v) == 2:
                try:
                    v = (int(v[0]), int(v[1]))
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid output_size list: {v}") from e

            # Resolve string or tuple to final dimensions
            if isinstance(v, str):
                resolved = resolve_output_size(v)
            elif isinstance(v, tuple) and len(v) == 2:
                resolved = resolve_output_size(v)
            else:
                raise ValueError(
                    f"output_size must be a string (named size) or "
                    f"tuple/list of 2 integers, got: {v}"
                )

            width, height = resolved
            if width > 10000 or height > 10000:
                raise ValueError("Output size too large (max 10000x10000)")

            data["output_size"] = resolved
        elif isinstance(data, dict) and "output_size" not in data:
            # If output_size not provided, use default from appstore sizes
            data["output_size"] = resolve_output_size("iPhone6_9")

        return data


class ProjectConfig(BaseModel):
    """Complete project configuration."""

    project: ProjectInfo = Field(..., description="Project information")
    defaults: Optional[Dict] = Field(default=None, description="Default settings")
    localization: Optional[LocalizationConfig] = Field(
        default=None,
        description="Localization configuration for multi-language screenshots",
    )
    screenshots: Dict[str, ScreenshotDefinition] = Field(
        ..., description="Screenshot definitions mapped by ID"
    )

    @field_validator("project")
    @classmethod
    def create_output_directory(cls, v: "ProjectInfo") -> "ProjectInfo":
        Path(v.output_dir).mkdir(parents=True, exist_ok=True)
        return v
