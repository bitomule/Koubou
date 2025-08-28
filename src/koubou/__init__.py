"""Koubou (工房) - The artisan workshop for App Store screenshots."""

__version__ = "0.1.1"
__author__ = "David Collado"
__email__ = "your-email@example.com"

from .config import GradientConfig, ScreenshotConfig, TextOverlay
from .exceptions import ConfigurationError, KoubouError, RenderError, TextGradientError
from .generator import ScreenshotGenerator

__all__ = [
    "ScreenshotConfig",
    "TextOverlay",
    "GradientConfig",
    "ScreenshotGenerator",
    "KoubouError",
    "ConfigurationError",
    "RenderError",
    "TextGradientError",
]
