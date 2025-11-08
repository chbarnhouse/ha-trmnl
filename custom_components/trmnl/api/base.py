"""Base API client for TRMNL."""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Any
from aiohttp import ClientSession

from .models import TRMNLDevice, TRMNLPlugin, MergeVars, DevicePlaylist
from .exceptions import TRMNLAPIError

_LOGGER = logging.getLogger(__name__)


class BaseTRMNLAPI(ABC):
    """Abstract base class for TRMNL API clients.

    This defines the interface that all API client implementations
    (Cloud, BYOS, etc.) must follow.
    """

    def __init__(self, session: Optional[ClientSession] = None) -> None:
        """Initialize API client.

        Args:
            session: Optional aiohttp ClientSession. If not provided,
                    a new one will be created.
        """
        self.session = session
        self._session_owned = session is None

    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session.

        Returns:
            ClientSession instance
        """
        if self.session is None:
            self.session = ClientSession()
        return self.session

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate API credentials.

        This should test authentication without making any state changes.

        Returns:
            True if credentials are valid

        Raises:
            InvalidAPIKeyError: If API key is invalid
            ConnectionError: If connection to API fails
        """

    @abstractmethod
    async def get_devices(self) -> list[TRMNLDevice]:
        """Get list of all TRMNL devices.

        Returns:
            List of TRMNLDevice objects discovered from API

        Raises:
            DeviceDiscoveryError: If device discovery fails
            ConnectionError: If connection to API fails
        """

    async def get_device(self, device_id: str) -> Optional[TRMNLDevice]:
        """Get specific TRMNL device by ID.

        Default implementation: fetch all devices and filter.
        Subclasses may override for efficiency.

        Args:
            device_id: ID of device to retrieve

        Returns:
            TRMNLDevice or None if not found

        Raises:
            ConnectionError: If connection to API fails
        """
        devices = await self.get_devices()
        for device in devices:
            if device.id == device_id:
                return device
        return None

    @abstractmethod
    async def get_plugin(self, plugin_uuid: str) -> Optional[TRMNLPlugin]:
        """Get plugin information.

        Args:
            plugin_uuid: UUID of the plugin to retrieve

        Returns:
            TRMNLPlugin if found, None otherwise

        Raises:
            ConnectionError: If connection to API fails
        """

    @abstractmethod
    async def update_plugin_variables(
        self, plugin_uuid: str, device_id: str, merge_vars: MergeVars
    ) -> bool:
        """Update plugin merge variables (screenshot update).

        This tells TRMNL what image to display next time it refreshes.

        Args:
            plugin_uuid: UUID of the plugin
            device_id: ID of the device to update
            merge_vars: Variables to update (image URL, token, etc.)

        Returns:
            True if update was successful

        Raises:
            UpdateScreenshotError: If update fails
            ConnectionError: If connection to API fails
        """

    async def get_playlist(self, device_id: str) -> Optional[DevicePlaylist]:
        """Get device playlist (collection of plugins).

        Default implementation: returns None.
        Subclasses may override if API supports it.

        Args:
            device_id: ID of the device

        Returns:
            DevicePlaylist or None

        Raises:
            ConnectionError: If connection to API fails
        """
        return None

    @abstractmethod
    async def trigger_refresh(self, device_id: str) -> bool:
        """Trigger immediate device refresh.

        Tells TRMNL to refresh the device display immediately
        instead of waiting for the scheduled refresh.

        Args:
            device_id: ID of the device to refresh

        Returns:
            True if refresh was triggered successfully.
            False if API doesn't support this feature.

        Raises:
            ConnectionError: If connection to API fails
        """

    async def close(self) -> None:
        """Close API client and cleanup resources.

        Closes the ClientSession if it was created by this client.
        """
        if self._session_owned and self.session:
            await self.session.close()

    async def __aenter__(self) -> "BaseTRMNLAPI":
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        await self.close()
