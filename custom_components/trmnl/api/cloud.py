"""TRMNL Cloud API client implementation."""

import logging
from typing import Optional, Any
from datetime import datetime

from aiohttp import ClientSession, ClientError

from ..const import TRMNL_CLOUD_API_BASE, TRMNL_CLOUD_ENDPOINT_DEVICES
from .base import BaseTRMNLAPI
from .models import TRMNLDevice, TRMNLPlugin, MergeVars, DeviceType, DeviceStatus
from .exceptions import (
    InvalidAPIKeyError,
    DeviceDiscoveryError,
    UpdateScreenshotError,
    ConnectionError as TRMNLConnectionError,
)

_LOGGER = logging.getLogger(__name__)


class CloudAPIClient(BaseTRMNLAPI):
    """TRMNL Cloud API client (usetrmnl.com)."""

    def __init__(self, api_key: str, session: Optional[ClientSession] = None) -> None:
        """Initialize Cloud API client.

        Args:
            api_key: API key for TRMNL Cloud
            session: Optional aiohttp ClientSession
        """
        super().__init__(session)
        self.api_key = api_key
        self.base_url = TRMNL_CLOUD_API_BASE

    async def validate_credentials(self) -> bool:
        """Validate API credentials.

        Makes a GET request to /api/devices to verify the API key is valid.

        Returns:
            True if credentials are valid

        Raises:
            InvalidAPIKeyError: If API key is invalid
            TRMNLConnectionError: If connection to API fails
        """
        session = await self._get_session()
        headers = self._build_headers()
        url = f"{self.base_url}{TRMNL_CLOUD_ENDPOINT_DEVICES}"

        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 401:
                    _LOGGER.error("Invalid API key for TRMNL Cloud")
                    raise InvalidAPIKeyError("Invalid API key")

                if response.status == 200:
                    return True

                _LOGGER.error(
                    "Unexpected status code validating credentials: %s",
                    response.status,
                )
                raise TRMNLConnectionError(
                    f"Unexpected status code: {response.status}"
                )

        except ClientError as err:
            _LOGGER.error("Connection error validating credentials: %s", err)
            raise TRMNLConnectionError(f"Connection error: {err}") from err

    async def get_devices(self) -> list[TRMNLDevice]:
        """Get list of devices from TRMNL Cloud.

        Makes a GET request to /api/devices and parses the response into
        TRMNLDevice objects.

        Returns:
            List of discovered devices (empty list if none found)

        Raises:
            DeviceDiscoveryError: If device discovery fails
            TRMNLConnectionError: If connection to API fails
        """
        session = await self._get_session()
        headers = self._build_headers()
        url = f"{self.base_url}{TRMNL_CLOUD_ENDPOINT_DEVICES}"

        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 401:
                    _LOGGER.error("Invalid API key when fetching devices")
                    raise InvalidAPIKeyError("Invalid API key")

                if response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch devices, status: %s", response.status
                    )
                    raise DeviceDiscoveryError(
                        f"API returned status {response.status}"
                    )

                data = await response.json()
                return self._parse_devices_response(data)

        except ClientError as err:
            _LOGGER.error("Connection error fetching devices: %s", err)
            raise DeviceDiscoveryError(f"Connection error: {err}") from err

    async def get_plugin(self, plugin_uuid: str) -> Optional[TRMNLPlugin]:
        """Get plugin from TRMNL Cloud.

        Makes a GET request to /api/plugins/{plugin_uuid} and returns the plugin
        if found, or None if not found (404).

        Args:
            plugin_uuid: UUID of the plugin

        Returns:
            TRMNLPlugin if found, None if not found (404)

        Raises:
            TRMNLConnectionError: If connection to API fails
        """
        session = await self._get_session()
        headers = self._build_headers()
        url = f"{self.base_url}/plugins/{plugin_uuid}"

        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 404:
                    _LOGGER.debug("Plugin %s not found", plugin_uuid)
                    return None

                if response.status == 401:
                    _LOGGER.error("Invalid API key when fetching plugin")
                    raise InvalidAPIKeyError("Invalid API key")

                if response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch plugin %s, status: %s",
                        plugin_uuid,
                        response.status,
                    )
                    return None

                data = await response.json()
                return self._parse_plugin_response(data)

        except ClientError as err:
            _LOGGER.error("Connection error fetching plugin: %s", err)
            return None

    async def update_plugin_variables(
        self, plugin_uuid: str, device_id: str, merge_vars: MergeVars
    ) -> bool:
        """Update plugin merge variables on TRMNL Cloud.

        Makes a POST request to /api/custom_plugins/{uuid}/variables with the
        merge variables to update.

        Args:
            plugin_uuid: UUID of the plugin
            device_id: ID of the device
            merge_vars: Variables to update

        Returns:
            True if update was successful

        Raises:
            UpdateScreenshotError: If update fails due to API error
            TRMNLConnectionError: If connection to API fails
        """
        session = await self._get_session()
        headers = self._build_headers()
        url = f"{self.base_url}/custom_plugins/{plugin_uuid}/variables"

        payload = {
            "device_id": device_id,
            "merge_vars": merge_vars.to_dict(),
        }

        try:
            async with session.post(
                url, json=payload, headers=headers, timeout=10
            ) as response:
                if response.status == 401:
                    _LOGGER.error("Invalid API key when updating variables")
                    raise InvalidAPIKeyError("Invalid API key")

                if response.status == 404:
                    _LOGGER.error(
                        "Plugin %s not found when updating variables", plugin_uuid
                    )
                    raise UpdateScreenshotError(f"Plugin {plugin_uuid} not found")

                if response.status != 200:
                    _LOGGER.error(
                        "Failed to update variables, status: %s", response.status
                    )
                    raise UpdateScreenshotError(
                        f"API returned status {response.status}"
                    )

                _LOGGER.debug("Successfully updated variables for plugin %s", plugin_uuid)
                return True

        except ClientError as err:
            _LOGGER.error("Connection error updating variables: %s", err)
            raise UpdateScreenshotError(f"Connection error: {err}") from err

    async def trigger_refresh(self, device_id: str) -> bool:
        """Trigger device refresh on TRMNL Cloud.

        Makes a POST request to /api/devices/{id}/refresh to trigger an
        immediate refresh on the device.

        Args:
            device_id: ID of the device

        Returns:
            True if refresh was triggered

        Raises:
            TRMNLConnectionError: If connection to API fails
        """
        session = await self._get_session()
        headers = self._build_headers()
        url = f"{self.base_url}/devices/{device_id}/refresh"

        try:
            async with session.post(url, headers=headers, timeout=10) as response:
                if response.status == 401:
                    _LOGGER.error("Invalid API key when triggering refresh")
                    raise InvalidAPIKeyError("Invalid API key")

                if response.status == 404:
                    _LOGGER.warning("Device %s not found", device_id)
                    return False

                if response.status != 200:
                    _LOGGER.error(
                        "Failed to trigger refresh for device %s, status: %s",
                        device_id,
                        response.status,
                    )
                    return False

                _LOGGER.debug("Successfully triggered refresh for device %s", device_id)
                return True

        except ClientError as err:
            _LOGGER.error("Connection error triggering refresh: %s", err)
            return False

    def _parse_devices_response(self, data: dict[str, Any]) -> list[TRMNLDevice]:
        """Parse devices response from API.

        Args:
            data: JSON response from /api/devices endpoint

        Returns:
            List of TRMNLDevice objects

        Raises:
            DeviceDiscoveryError: If response format is invalid
        """
        try:
            devices_data = data.get("devices", [])
            devices = []

            for device_data in devices_data:
                try:
                    device = TRMNLDevice(
                        id=device_data["id"],
                        name=device_data["name"],
                        device_type=DeviceType(device_data.get("device_type", "og")),
                        battery_level=device_data.get("battery_level"),
                        last_seen=(
                            datetime.fromisoformat(device_data["last_seen"])
                            if device_data.get("last_seen")
                            else None
                        ),
                        firmware_version=device_data.get("firmware_version"),
                        status=DeviceStatus(device_data.get("status", "unknown")),
                        attributes=device_data.get("attributes", {}),
                    )
                    devices.append(device)
                except (KeyError, ValueError) as err:
                    _LOGGER.warning("Failed to parse device: %s", err)
                    continue

            _LOGGER.debug("Parsed %d devices from API response", len(devices))
            return devices

        except Exception as err:
            _LOGGER.error("Error parsing devices response: %s", err)
            raise DeviceDiscoveryError(f"Invalid response format: {err}") from err

    def _parse_plugin_response(self, data: dict[str, Any]) -> Optional[TRMNLPlugin]:
        """Parse plugin response from API.

        Args:
            data: JSON response from /api/plugins/{uuid} endpoint

        Returns:
            TRMNLPlugin object or None if parsing fails
        """
        try:
            plugin = TRMNLPlugin(
                uuid=data["uuid"],
                name=data["name"],
                version=data.get("version", "0.1.0"),
                description=data.get("description"),
            )
            _LOGGER.debug("Parsed plugin: %s", plugin.name)
            return plugin

        except (KeyError, ValueError) as err:
            _LOGGER.error("Failed to parse plugin response: %s", err)
            return None

    def _build_headers(self) -> dict:
        """Build HTTP headers with authentication.

        Returns:
            Headers dictionary with Authorization header
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TRMNL-HA-Integration/0.1.0",
        }
