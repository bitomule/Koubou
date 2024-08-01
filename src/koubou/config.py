"""Configuration models using Pydantic for type safety and validation."""

from typing import List, Optional, Tuple, Union, Literal, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator


class TextOverlay(BaseModel):
    """Configuration for text overlays on screenshots."""
    
    content: str = Field(..., description="The text content to display")
    position: Tuple[int, int] = Field(..., description="X, Y position in pixels")
    font_size: int = Field(default=24, description="Font size in pixels")
    font_family: str = Field(default="Arial", description="Font family name")
    font_weight: str = Field(default="normal", description="Font weight (normal, bold)")
    color: str = Field(default="#000000", description="Text color in hex format")
    alignment: Literal["left", "center", "right"] = Field(default="center")
    anchor: Literal["top-left", "top-center", "top-right", "center-left", "center", "center-right", "bottom-left", "bottom-center", "bottom-right"] = Field(default="center", description="Anchor point for position")
    max_width: Optional[int] = Field(default=None, description="Maximum width for text wrapping")
    max_lines: Optional[int] = Field(default=None, description="Maximum number of lines for text wrapping")
    line_height: float = Field(default=1.2, description="Line height multiplier")
    stroke_width: Optional[int] = Field(default=None, description="Text stroke width")
    stroke_color: Optional[str] = Field(default=None, description="Text stroke color")
    
    @validator("color", "stroke_color")
    def validate_color(cls, v):
        if v and not v.startswith("#"):
            raise ValueError("Colors must be in hex format (e.g., #FFFFFF)")
        return v


class BackgroundConfig(BaseModel):
    """Configuration for screenshot backgrounds."""
    
    type: Literal["solid", "linear", "radial", "conic"] = Field(..., description="Background type")
    colors: List[str] = Field(..., description="List of hex colors")
    direction: Optional[float] = Field(default=0, description="Gradient direction in degrees")
    center: Optional[Tuple[str, str]] = Field(default=None, description="Center point for radial/conic gradients")
    
    @validator("colors")
    def validate_colors(cls, v):
        if not v:
            raise ValueError("At least one color is required")
        for color in v:
            if not color.startswith("#"):
                raise ValueError("Colors must be in hex format (e.g., #FFFFFF)")
        return v
    
    @validator("colors")
    def validate_gradient_colors(cls, v, values):
        bg_type = values.get("type")
        if bg_type in ["linear", "radial", "conic"] and len(v) < 2:
            raise ValueError("Gradient backgrounds require at least 2 colors")
        return v


class ScreenshotConfig(BaseModel):
    """Configuration for a single screenshot generation."""
    
    name: str = Field(..., description="Name/identifier for this screenshot")
    source_image: str = Field(..., description="Path to source screenshot image")
    device_frame: Optional[str] = Field(default=None, description="Device frame to apply")
    output_size: Tuple[int, int] = Field(..., description="Final output size (width, height)")
    output_path: Optional[str] = Field(default=None, description="Custom output path")
    background: Optional[BackgroundConfig] = Field(default=None, description="Background configuration")
    text_overlays: List[TextOverlay] = Field(default=[], description="List of text overlays")
    image_position: Optional[List[str]] = Field(default=None, description="Image position as [x%, y%] relative to canvas")
    image_scale: Optional[float] = Field(default=None, description="Image scale factor")
    image_frame: Optional[bool] = Field(default=False, description="Apply device frame to image at image position and scale")
    
    @validator("source_image")
    def validate_source_image(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Source image not found: {v}")
        return v
    
    @validator("output_size")
    def validate_output_size(cls, v):
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
    position: Tuple[str, str] = Field(default=("50%", "50%"), description="Position as percentage or pixels")
    size: Optional[int] = Field(default=24, description="Font size for text")
    color: Optional[str] = Field(default="#000000", description="Text color")
    weight: Optional[str] = Field(default="normal", description="Font weight")
    alignment: Optional[str] = Field(default="center", description="Text alignment (left, center, right)")
    scale: Optional[float] = Field(default=1.0, description="Image scale factor")
    frame: Optional[bool] = Field(default=False, description="Apply device frame to image")


class ScreenshotDefinition(BaseModel):
    """Screenshot definition with content items."""
    
    name: str = Field(..., description="Screenshot name")
    content: List[ContentItem] = Field(..., description="List of content items")


class ProjectInfo(BaseModel):
    """Project information."""
    
    name: str = Field(..., description="Project name")
    output_dir: str = Field(default="output", description="Output directory")


class ProjectConfig(BaseModel):
    """Complete project configuration."""
    
    project: ProjectInfo = Field(..., description="Project information")
    devices: List[str] = Field(default=["iPhone 15 Pro Portrait"], description="Target devices")
    defaults: Optional[Dict] = Field(default=None, description="Default settings")
    screenshots: List[ScreenshotDefinition] = Field(..., description="Screenshot definitions")
    
    @validator("project")
    def create_output_directory(cls, v):
        Path(v.output_dir).mkdir(parents=True, exist_ok=True)
        return v


