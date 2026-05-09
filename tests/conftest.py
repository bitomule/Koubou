"""Test configuration and fixtures."""

import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from koubou.config import GradientConfig, ScreenshotConfig, TextOverlay


@pytest.fixture
def system_font_file():
    """Find a real local font file for custom-font integration tests."""
    preferred = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/SFNS.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]
    for path in preferred:
        if path.exists():
            return path

    for root in [
        Path("/System/Library/Fonts"),
        Path("/Library/Fonts"),
        Path("/usr/share/fonts"),
    ]:
        if not root.exists():
            continue
        for suffix in ("*.ttf", "*.otf", "*.ttc"):
            try:
                return next(root.rglob(suffix))
            except StopIteration:
                continue

    pytest.skip("No local TrueType/OpenType font file available")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample test image."""
    image_path = temp_dir / "test_image.png"

    # Create a simple test image
    image = Image.new("RGBA", (100, 200), (255, 0, 0, 255))  # Red image
    image.save(image_path)

    return str(image_path)


@pytest.fixture
def sample_screenshot_config(sample_image):
    """Create a sample screenshot configuration."""
    return ScreenshotConfig(
        name="Test Screenshot",
        source_image=sample_image,
        output_size=(400, 800),
        background=GradientConfig(type="solid", colors=["#0066cc"]),
        text_overlays=[
            TextOverlay(
                content="Test Text", position=(50, 50), font_size=24, color="#ffffff"
            )
        ],
    )


@pytest.fixture
def sample_gradient_background():
    """Create a sample gradient background configuration."""
    return GradientConfig(
        type="linear", colors=["#ff0000", "#00ff00", "#0000ff"], direction=45
    )


@pytest.fixture
def sample_text_overlay():
    """Create a sample text overlay configuration."""
    return TextOverlay(
        content="Hello World",
        position=(100, 100),
        font_size=32,
        color="#ffffff",
        alignment="center",
        max_width=300,
    )
