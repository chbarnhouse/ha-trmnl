"""API exceptions for TRMNL integration."""


class TRMNLAPIError(Exception):
    """Base exception for TRMNL API errors."""


class InvalidAPIKeyError(TRMNLAPIError):
    """Exception raised when API key is invalid."""


class InvalidServerURLError(TRMNLAPIError):
    """Exception raised when server URL is invalid."""


class DeviceDiscoveryError(TRMNLAPIError):
    """Exception raised when device discovery fails."""


class UpdateScreenshotError(TRMNLAPIError):
    """Exception raised when screenshot update fails."""


class ConnectionError(TRMNLAPIError):
    """Exception raised when connection to API fails."""


class InvalidTokenError(TRMNLAPIError):
    """Exception raised when token is invalid or expired."""
