class PySysWatchError(Exception):
    """Base exception for all PySysWatch errors."""


class CollectorError(PySysWatchError):
    """Raised when a system metric collector fails."""


class ConfigurationError(PySysWatchError):
    """Raised when there is an invalid configuration."""


class DatabaseError(PySysWatchError):
    """Raised when a database operation fails."""


class PermissionError(PySysWatchError):
    """Raised when the application lacks privileges for an operation."""


class ServiceUnavailableError(PySysWatchError):
    """Raised when an external service or system daemon is unreachable."""
