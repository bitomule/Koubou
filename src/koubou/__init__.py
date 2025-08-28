"""Koubou (工房) - The artisan workshop for App Store screenshots."""

# Modern version detection using importlib.metadata (Python 3.8+)
try:
    from importlib.metadata import version

    __version__ = version("koubou")
except ImportError:
    # Python < 3.8 fallback
    try:
        from importlib_metadata import version

        __version__ = version("koubou")
    except ImportError:
        __version__ = "dev"
except Exception:
    # Development fallback when package not installed
    __version__ = "dev"
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
