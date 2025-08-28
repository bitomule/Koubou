"""Koubou (工房) - The artisan workshop for App Store screenshots."""

import subprocess
import sys
from pathlib import Path

def _get_version_from_git():
    """Try to get version from git tag."""
    try:
        # Check if we're in a git repository
        repo_root = Path(__file__).parent.parent.parent
        if not (repo_root / '.git').exists():
            return None
            
        # Get the latest git tag
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'], 
            capture_output=True, text=True, cwd=repo_root, timeout=5
        )
        if result.returncode == 0:
            tag = result.stdout.strip()
            # Remove 'v' prefix if present
            return tag.lstrip('v')
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    return None

# Try to get version from git, fallback to hardcoded version
__version__ = _get_version_from_git() or "0.1.0"
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
