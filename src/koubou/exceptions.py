"""Custom exceptions for Koubou."""


class KoubouError(Exception):
    """Base exception for all Koubou errors."""

    pass


class ConfigurationError(KoubouError):
    """Raised when there's an error in the configuration."""

    pass


class RenderError(KoubouError):
    """Raised when there's an error during rendering."""

    pass


class DeviceFrameError(RenderError):
    """Raised when there's an error with device frame processing."""

    pass


class BackgroundRenderError(RenderError):
    """Raised when there's an error rendering backgrounds."""

    pass


class TextRenderError(RenderError):
    """Raised when there's an error rendering text overlays."""

    pass


class TextGradientError(TextRenderError):
    """Raised when there's an error rendering text gradients."""

    pass
