"""TRMNL API client module."""

from .base import BaseTRMNLAPI
from .cloud import CloudAPIClient
from .byos import BYOSAPIClient
from .exceptions import (
    TRMNLAPIError,
    InvalidAPIKeyError,
    InvalidServerURLError,
    DeviceDiscoveryError,
    UpdateScreenshotError,
    ConnectionError,
    InvalidTokenError,
)
from .models import (
    TRMNLDevice,
    TRMNLPlugin,
    MergeVars,
    DeviceUpdateRequest,
    DevicePlaylist,
    APIResponse,
    DeviceType,
    DeviceStatus,
)

__all__ = [
    # Clients
    "BaseTRMNLAPI",
    "CloudAPIClient",
    "BYOSAPIClient",
    # Exceptions
    "TRMNLAPIError",
    "InvalidAPIKeyError",
    "InvalidServerURLError",
    "DeviceDiscoveryError",
    "UpdateScreenshotError",
    "ConnectionError",
    "InvalidTokenError",
    # Models
    "TRMNLDevice",
    "TRMNLPlugin",
    "MergeVars",
    "DeviceUpdateRequest",
    "DevicePlaylist",
    "APIResponse",
    "DeviceType",
    "DeviceStatus",
]
