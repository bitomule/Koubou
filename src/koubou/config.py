"""Configuration models using Pydantic for type safety and validation."""

from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field, model_validator, validator


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

    @validator("colors")
    def validate_colors(cls, v: List[str], values: Dict) -> List[str]:
        gradient_type = values.get("type")

        # Validate minimum colors based on type
        if gradient_type == "solid" and len(v) != 1:
            raise ValueError("Solid backgrounds require exactly 1 color")
        elif gradient_type in ["linear", "radial", "conic"] and len(v) < 2:
            raise ValueError("Gradients require at least 2 colors")
        elif not v:
            raise ValueError("At least one color is required")

        # Validate color format
        for color in v:
            if not color.startswith("#"):
                raise ValueError("Colors must be in hex format (e.g., #FFFFFF)")
        return v

    @validator("positions")
    def validate_positions(
        cls, v: Optional[List[float]], values: Dict
    ) -> Optional[List[float]]:
        if v is None:
            return v

        colors = values.get("colors", [])
        if len(v) != len(colors):
            raise ValueError("Positions array must match colors array length")

        if not all(0.0 <= pos <= 1.0 for pos in v):
            raise ValueError("Color stop positions must be between 0.0 and 1.0")

        if v != sorted(v):
            raise ValueError("Color stop positions must be in ascending order")

        return v

    @validator("direction")
    def validate_direction(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0 or v >= 360):
            raise ValueError("Direction must be between 0 and 359 degrees")
        return v

    @validator("start_angle")
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
    line_height: float = Field(default=1.2, description="Line height multiplier")
    stroke_width: Optional[int] = Field(default=None, description="Text stroke width")

    # Stroke options (mutually exclusive)
    stroke_color: Optional[str] = Field(default=None, description="Solid stroke color")
    stroke_gradient: Optional[GradientConfig] = Field(
        default=None, description="Stroke gradient configuration"
    )

    @validator("color")
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("#"):
            raise ValueError("Colors must be in hex format (e.g., #FFFFFF)")
        return v

    @validator("stroke_color")
    def validate_stroke_color(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("#"):
            raise ValueError("Stroke colors must be in hex format (e.g., #FFFFFF)")
        return v

    @validator("gradient")
    def validate_fill_options(
        cls, v: Optional[GradientConfig], values: Dict
    ) -> Optional[GradientConfig]:
        color = values.get("color")

        if color is None and v is None:
            # Set default color if neither is specified
            values["color"] = "#000000"
        elif color is not None and v is not None:
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
    output_size: Tuple[int, int] = Field(
        ..., description="Final output size (width, height)"
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

    @validator("source_image")
    def validate_source_image(cls, v: str) -> str:
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Source image not found: {v}")
        return v

    @validator("output_size")
    def validate_output_size(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        width, height = v
        if width <= 0 or height <= 0:
            raise ValueError("Output size must be positive")
        if width > 10000 or height > 10000:
            raise ValueError("Output size too large (max 10000x10000)")
        return v


class ContentItem(BaseModel):
    """Individual content item in a screenshot."""

    type: Literal["text", "image"] = Field(..., description="Type of content item")
    content: Optional[str] = Field(default=None, description="Text content")
    asset: Optional[str] = Field(default=None, description="Image asset path")
    position: Tuple[str, str] = Field(
        default=("50%", "50%"), description="Position as percentage or pixels"
    )
    size: Optional[int] = Field(default=24, description="Font size for text")

    # Text fill options (mutually exclusive)
    color: Optional[str] = Field(default=None, description="Solid text color")
    gradient: Optional[GradientConfig] = Field(
        default=None, description="Text gradient"
    )

    weight: Optional[str] = Field(default="normal", description="Font weight")
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

    @validator("color")
    def validate_color_format(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("#"):
            raise ValueError("Colors must be in hex format (e.g., #FFFFFF)")
        return v

    @validator("stroke_color")
    def validate_stroke_color_format(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("#"):
            raise ValueError("Stroke colors must be in hex format (e.g., #FFFFFF)")
        return v

    @validator("gradient")
    def validate_text_fill_options(
        cls, v: Optional[GradientConfig], values: Dict
    ) -> Optional[GradientConfig]:
        color = values.get("color")

        if color is None and v is None:
            # Set default color if neither is specified
            values["color"] = "#000000"
        elif color is not None and v is not None:
            raise ValueError(
                "Cannot specify both 'color' and 'gradient'. Choose exactly one."
            )

        return v

    @validator("stroke_gradient")
    def validate_stroke_fill_options(
        cls, v: Optional[GradientConfig], values: Dict
    ) -> Optional[GradientConfig]:
        stroke_color = values.get("stroke_color")
        stroke_width = values.get("stroke_width")

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
        description="Whether to use device frame (None=use default, True=force frame, False=no frame)",
    )


class ProjectInfo(BaseModel):
    """Project information."""

    name: str = Field(..., description="Project name")
    output_dir: str = Field(default="output", description="Output directory")


class ProjectConfig(BaseModel):
    """Complete project configuration."""

    project: ProjectInfo = Field(..., description="Project information")
    devices: List[str] = Field(
        default=["iPhone 15 Pro Portrait"], description="Target devices"
    )
    defaults: Optional[Dict] = Field(default=None, description="Default settings")
    screenshots: Dict[str, ScreenshotDefinition] = Field(
        ..., description="Screenshot definitions mapped by ID"
    )

    @validator("project")
    def create_output_directory(cls, v: "ProjectInfo") -> "ProjectInfo":
        Path(v.output_dir).mkdir(parents=True, exist_ok=True)
        return v
