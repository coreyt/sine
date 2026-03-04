"""Custom exceptions for pattern discovery."""


class LookoutError(Exception):
    """Base exception for Lookout errors."""

    pass


class PatternDiscoveryError(LookoutError):
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
