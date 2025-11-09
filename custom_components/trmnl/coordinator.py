"""Data coordinator for TRMNL integration."""

import logging
from datetime import timedelta
from typing import Any, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CloudAPIClient, BYOSAPIClient
from .const import (
    CONF_API_KEY,
    CONF_AUTH_TYPE,
    CONF_DEVICES,
    CONF_PASSWORD,
    CONF_SERVER_TYPE,
    CONF_SERVER_URL,
    CONF_USERNAME,
    AUTH_TYPE_API_KEY,
    AUTH_TYPE_BASIC,
    COORDINATOR_UPDATE_INTERVAL,
    DOMAIN,
    SERVER_TYPE_CLOUD,
    SERVER_TYPE_BYOS,
)

_LOGGER = logging.getLogger(__name__)


class TRMNLCoordinator(DataUpdateCoordinator):
    """Coordinator for TRMNL data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_data: dict[str, Any],
    ) -> None:
        """Initialize coordinator.

        Args:
            hass: Home Assistant instance
            entry_data: Config entry data with server configuration
        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=COORDINATOR_UPDATE_INTERVAL),
        )

        self.entry_data = entry_data
        self.devices: dict[str, Any] = {}
        self.plugins: dict[str, Any] = {}
        self.api_client: CloudAPIClient | BYOSAPIClient | None = None

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh and set up API client."""
        # Initialize API client (deferred to async context)
        self.api_client = await self._async_create_api_client()

        # Now perform the first refresh
        await super().async_config_entry_first_refresh()

    async def _async_create_api_client(self) -> CloudAPIClient | BYOSAPIClient:
        """Create appropriate API client based on config.

        Returns:
            CloudAPIClient or BYOSAPIClient instance
        """
        from homeassistant.helpers.aiohttp_client import async_get_clientsession

        session = async_get_clientsession(self.hass)
        server_type = self.entry_data.get(CONF_SERVER_TYPE)

        if server_type == SERVER_TYPE_CLOUD:
            api_key = self.entry_data.get(CONF_API_KEY)
            return CloudAPIClient(api_key=api_key, session=session)
        else:  # BYOS
            server_url = self.entry_data.get(CONF_SERVER_URL)
            auth_type = self.entry_data.get(CONF_AUTH_TYPE, AUTH_TYPE_API_KEY)
            credentials = {}

            if auth_type == AUTH_TYPE_API_KEY:
                credentials[CONF_API_KEY] = self.entry_data.get(CONF_API_KEY, "")
            elif auth_type == AUTH_TYPE_BASIC:
                credentials[CONF_USERNAME] = self.entry_data.get(CONF_USERNAME, "")
                credentials[CONF_PASSWORD] = self.entry_data.get(CONF_PASSWORD, "")

            return BYOSAPIClient(
                server_url=server_url,
                auth_type=auth_type,
                credentials=credentials,
                session=session,
            )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from TRMNL API.

        Returns:
            Dictionary with devices and plugins

        Raises:
            UpdateFailed: If update fails
        """
        try:
            # Ensure API client is initialized
            if self.api_client is None:
                _LOGGER.error("API client is not initialized in coordinator!")
                raise UpdateFailed("API client not initialized")

            # Fetch all devices
            all_devices = await self.api_client.get_devices()

            _LOGGER.debug("Fetched %d devices from API", len(all_devices))
            for device in all_devices:
                _LOGGER.debug("Device: id=%s (type: %s), name=%s", device.id, type(device.id).__name__, device.name)

            # Filter to only configured devices
            configured_device_ids = self.entry_data.get(CONF_DEVICES, [])
            _LOGGER.debug("Configured device IDs: %s (type: %s)", configured_device_ids, type(configured_device_ids).__name__)
            if configured_device_ids:
                _LOGGER.debug("First configured ID: %s (type: %s)", configured_device_ids[0], type(configured_device_ids[0]).__name__)

            # Ensure all device IDs are strings for comparison
            devices = {
                device.id: device
                for device in all_devices
                if str(device.id) in [str(cid) for cid in configured_device_ids]
            }

            if not devices:
                _LOGGER.warning(
                    "No configured devices found. Expected: %s, Got API devices: %s",
                    configured_device_ids,
                    [device.id for device in all_devices],
                )

            # Store devices for entities to access
            self.devices = devices

            _LOGGER.debug("Updated %d devices from API", len(devices))

            return {
                "devices": devices,
            }

        except Exception as err:
            _LOGGER.error("Error updating TRMNL data: %s", err)
            raise UpdateFailed(f"Failed to update TRMNL data: {err}") from err

    async def get_device(self, device_id: str) -> Optional[Any]:
        """Get a specific device.

        Args:
            device_id: Device ID to retrieve

        Returns:
            Device object or None if not found
        """
        return self.devices.get(device_id)

    async def get_devices(self) -> dict[str, Any]:
        """Get all configured devices.

        Returns:
            Dictionary of device_id -> device object
        """
        return self.devices

    async def async_validate_connection(self) -> bool:
        """Validate connection to TRMNL server.

        Returns:
            True if connection successful
        """
        try:
            return await self.api_client.validate_credentials()
        except Exception as err:
            _LOGGER.error("Connection validation failed: %s", err)
            return False

    async def async_request_refresh(self, device_id: str) -> bool:
        """Request immediate device refresh.

        Args:
            device_id: Device to refresh

        Returns:
            True if refresh triggered
        """
        try:
            return await self.api_client.trigger_refresh(device_id)
        except Exception as err:
            _LOGGER.error("Failed to trigger refresh for %s: %s", device_id, err)
            return False

    async def async_update_screenshot(
        self,
        device_id: str,
        image_url: str,
        token: str,
        plugin_uuid: Optional[str] = None,
        auth_token: Optional[str] = None,
        token_expires: Optional[str] = None,
    ) -> bool:
        """Update device screenshot via plugin variables.

        Can be called in two ways:
        1. With token only (from WebSocket addon):
           device_id, image_url, token
        2. With full parameters (internal use):
           device_id, image_url, token, plugin_uuid, auth_token, token_expires

        Args:
            device_id: Device to update
            image_url: Screenshot image URL
            token: Auth token (for WebSocket addon cases) or timestamp
            plugin_uuid: Plugin UUID (optional, for internal use)
            auth_token: Authentication token for image access (optional)
            token_expires: Token expiration datetime (optional)

        Returns:
            True if update successful
        """
        from datetime import datetime

        from .api.models import MergeVars

        try:
            # If plugin_uuid not provided, try to get from device config
            if not plugin_uuid:
                # For addon WebSocket calls, we'll log a warning but continue
                # The device's plugin will pull the URL from somewhere else
                _LOGGER.debug(
                    "No plugin_uuid provided for screenshot update on device %s. "
                    "Variables will not be updated. Device plugin must be configured "
                    "to pull images from configured addon URL.",
                    device_id,
                )
                return True

            # Full update with all parameters
            merge_vars = MergeVars(
                device_id=device_id,
                ha_image_url=image_url,
                ha_auth_token=auth_token or token,
                ha_token_expires=token_expires or datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
            )

            return await self.api_client.update_plugin_variables(
                plugin_uuid=plugin_uuid,
                device_id=device_id,
                merge_vars=merge_vars,
            )
        except Exception as err:
            _LOGGER.error(
                "Failed to update screenshot for device %s: %s", device_id, err
            )
            return False
