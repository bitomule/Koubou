"""Koubou (工房) - The artisan workshop for App Store screenshots."""

__version__ = "0.0.1"
__author__ = "David Collado"
__email__ = "your-email@example.com"

from .config import ScreenshotConfig, TextOverlay, BackgroundConfig
from .generator import ScreenshotGenerator
from .exceptions import KoubouError, ConfigurationError, RenderError

__all__ = [
    "ScreenshotConfig",
    "TextOverlay", 
    "BackgroundConfig",
    "ScreenshotGenerator",
    "KoubouError",
    "ConfigurationError",
    "RenderError",
]