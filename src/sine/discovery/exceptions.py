"""Custom exceptions for pattern discovery."""


class SineError(Exception):
    """Base exception for Sine errors."""

    pass


class PatternDiscoveryError(SineError):
    """Base exception for pattern discovery errors."""

    pass


class PatternStorageError(PatternDiscoveryError):
    """Error during pattern storage operations."""

    pass


class PatternValidationError(PatternDiscoveryError):
    """Error during pattern validation."""

    pass


class AgentError(PatternDiscoveryError):
    """Error during agent execution."""

    pass
