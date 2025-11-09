"""TRMNL BYOS (Self-Hosted) API client implementation with graceful degradation."""

import logging
import asyncio
from typing import Optional, Any
from datetime import datetime
import base64

from aiohttp import ClientSession, ClientError

from .base import BaseTRMNLAPI
from .models import TRMNLDevice, TRMNLPlugin, MergeVars, DeviceType, DeviceStatus
from .exceptions import (
    InvalidServerURLError,
    DeviceDiscoveryError,
    UpdateScreenshotError,
    ConnectionError as TRMNLConnectionError,
)

_LOGGER = logging.getLogger(__name__)


class BYOSAPIClient(BaseTRMNLAPI):
    """TRMNL BYOS (Self-Hosted) API client with graceful degradation.

    This client supports multiple server implementations and authentication
    methods. If an endpoint is not available, it gracefully degrades to
    provide alternative functionality or returns sensible defaults.
    """

    def __init__(
        self,
        server_url: str,
        auth_type: str,
        credentials: Optional[dict] = None,
        session: Optional[ClientSession] = None,
    ) -> None:
        """Initialize BYOS API client.

        Args:
            server_url: URL of the BYOS TRMNL server (e.g., http://192.168.1.100:8000)
            auth_type: Authentication type ("api_key", "basic", "none")
            credentials: Optional credentials dict (varies by auth_type)
            session: Optional aiohttp ClientSession
        """
        super().__init__(session)
        self.server_url = server_url.rstrip("/")
        self.auth_type = auth_type
        self.credentials = credentials or {}
        self._endpoint_cache = {}

    async def validate_credentials(self) -> bool:
        """Validate BYOS server connection and credentials.

        Attempts to connect to the server and validate credentials without
        making any state changes.

        Returns:
            True if connection successful, False if server unreachable
        """
        session = await self._get_session()
        headers = self._build_headers()

        # Try to discover endpoints (also validates connection)
        try:
            endpoints = await self._discover_endpoints()
            if endpoints:
                _LOGGER.debug("BYOS server connection validated")
                return True
        except (ClientError, TRMNLConnectionError) as err:
            _LOGGER.warning("BYOS server connection failed: %s", err)

        return False

    async def get_devices(self) -> list[TRMNLDevice]:
        """Get devices from BYOS server with fallback endpoints.

        Tries multiple endpoint variations to support different server
        implementations. Returns empty list if all endpoints unavailable.

        Returns:
            List of devices (empty list if endpoint not available)

        Raises:
            DeviceDiscoveryError: Only if server unreachable entirely
        """
        session = await self._get_session()
        headers = self._build_headers()
        endpoints = await self._discover_endpoints()

        # Try primary endpoint
        if "devices" in endpoints:
            url = f"{self.server_url}{endpoints['devices']}"
            devices = await self._try_get_devices(session, headers, url)
            if devices is not None:
                return devices

        # Try fallback endpoints
        fallback_urls = [
            f"{self.server_url}/api/devices",
            f"{self.server_url}/devices",
            f"{self.server_url}/api/list/devices",
        ]

        for url in fallback_urls:
            devices = await self._try_get_devices(session, headers, url)
            if devices is not None:
                return devices

        _LOGGER.warning("No device endpoints available on BYOS server")
        return []

    async def get_plugin(self, plugin_uuid: str) -> Optional[TRMNLPlugin]:
        """Get plugin from BYOS server with graceful degradation.

        Returns None if plugin endpoint not available rather than failing.

        Args:
            plugin_uuid: UUID of the plugin

        Returns:
            TRMNLPlugin if available, None if endpoint doesn't exist
        """
        session = await self._get_session()
        headers = self._build_headers()
        endpoints = await self._discover_endpoints()

        # Try primary endpoint
        if "plugins" in endpoints:
            url = f"{self.server_url}{endpoints['plugins']}/{plugin_uuid}"
            plugin = await self._try_get_plugin(session, headers, url)
            if plugin is not None:
                return plugin

        # Try fallback endpoints
        fallback_urls = [
            f"{self.server_url}/api/plugins/{plugin_uuid}",
            f"{self.server_url}/plugins/{plugin_uuid}",
            f"{self.server_url}/api/custom_plugins/{plugin_uuid}",
        ]

        for url in fallback_urls:
            plugin = await self._try_get_plugin(session, headers, url)
            if plugin is not None:
                return plugin

        _LOGGER.debug("Plugin %s not available on BYOS server", plugin_uuid)
        return None

    async def update_plugin_variables(
        self, plugin_uuid: str, device_id: str, merge_vars: MergeVars
    ) -> bool:
        """Update plugin variables on BYOS server with fallback.

        Returns False if endpoint not available rather than raising an error,
        allowing users to manually configure via TRMNL UI.

        Args:
            plugin_uuid: UUID of the plugin
            device_id: ID of the device
            merge_vars: Variables to update

        Returns:
            True if update successful, False if endpoint not available
        """
        session = await self._get_session()
        headers = self._build_headers()
        endpoints = await self._discover_endpoints()

        payload = {
            "device_id": device_id,
            "merge_vars": merge_vars.to_dict(),
        }

        # Try primary endpoint
        if "plugins" in endpoints:
            url = f"{self.server_url}{endpoints['plugins']}/{plugin_uuid}/variables"
            if await self._try_update_variables(session, headers, url, payload):
                return True

        # Try fallback endpoints
        fallback_urls = [
            f"{self.server_url}/api/custom_plugins/{plugin_uuid}/variables",
            f"{self.server_url}/api/plugins/{plugin_uuid}/variables",
        ]

        for url in fallback_urls:
            if await self._try_update_variables(session, headers, url, payload):
                return True

        _LOGGER.debug("Plugin variables update not supported on BYOS server")
        return False

    async def trigger_refresh(self, device_id: str) -> bool:
        """Trigger device refresh with graceful degradation.

        Returns False if not supported rather than raising an error,
        allowing users to manually refresh on device.

        Args:
            device_id: ID of the device

        Returns:
            True if triggered, False if not supported
        """
        session = await self._get_session()
        headers = self._build_headers()
        endpoints = await self._discover_endpoints()

        # Try primary endpoint
        if "devices" in endpoints:
            url = f"{self.server_url}{endpoints['devices']}/{device_id}/refresh"
            if await self._try_trigger_refresh(session, headers, url):
                return True

        # Try fallback endpoints
        fallback_urls = [
            f"{self.server_url}/api/devices/{device_id}/refresh",
            f"{self.server_url}/devices/{device_id}/refresh",
        ]

        for url in fallback_urls:
            if await self._try_trigger_refresh(session, headers, url):
                return True

        _LOGGER.debug("Device refresh not supported on BYOS server")
        return False

    async def _discover_endpoints(self) -> dict[str, str]:
        """Auto-discover available endpoints on BYOS server.

        Caches successful endpoints for future use.

        Returns:
            Dictionary of available endpoints (may be empty if none found)
        """
        if self._endpoint_cache:
            return self._endpoint_cache

        session = await self._get_session()
        headers = self._build_headers()

        # Try to probe common endpoints to discover server type
        probe_urls = [
            f"{self.server_url}/api/devices",
            f"{self.server_url}/devices",
            f"{self.server_url}/api/custom_plugins",
        ]

        endpoints = {}
        for url in probe_urls:
            try:
                async with session.head(url, headers=headers, timeout=5) as response:
                    if response.status in (200, 204, 404):  # Server responds (not 404 doesn't matter for HEAD)
                        if "/devices" in url:
                            endpoints["devices"] = url.replace(self.server_url, "")
                        elif "/custom_plugins" in url or "/plugins" in url:
                            endpoints["plugins"] = url.replace(self.server_url, "")
                        _LOGGER.debug("Discovered endpoint: %s", url)
            except (ClientError, asyncio.TimeoutError):
                continue

        # Cache even if empty (to avoid repeated probing)
        self._endpoint_cache = endpoints
        return endpoints

    async def _try_get_devices(
        self,
        session: ClientSession,
        headers: dict,
        url: str,
    ) -> Optional[list[TRMNLDevice]]:
        """Try to fetch devices from a specific URL.

        Returns None if endpoint not available (graceful degradation).

        Args:
            session: aiohttp ClientSession
            headers: Request headers with auth
            url: URL to try

        Returns:
            List of devices or None if endpoint not available
        """
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_devices_response(data)
                elif response.status == 404:
                    _LOGGER.debug("Devices endpoint not found: %s", url)
                    return None
                else:
                    _LOGGER.debug("Unexpected status %s fetching devices: %s", response.status, url)
                    return None
        except (ClientError, ValueError) as err:
            _LOGGER.debug("Error fetching devices from %s: %s", url, err)
            return None

    async def _try_get_plugin(
        self,
        session: ClientSession,
        headers: dict,
        url: str,
    ) -> Optional[TRMNLPlugin]:
        """Try to fetch plugin from a specific URL.

        Returns None if endpoint not available (graceful degradation).

        Args:
            session: aiohttp ClientSession
            headers: Request headers with auth
            url: URL to try

        Returns:
            TRMNLPlugin or None if endpoint not available
        """
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_plugin_response(data)
                elif response.status in (404, 405):  # 405 = method not allowed
                    _LOGGER.debug("Plugin endpoint not available: %s", url)
                    return None
                else:
                    _LOGGER.debug("Unexpected status %s fetching plugin: %s", response.status, url)
                    return None
        except (ClientError, ValueError) as err:
            _LOGGER.debug("Error fetching plugin from %s: %s", url, err)
            return None

    async def _try_update_variables(
        self,
        session: ClientSession,
        headers: dict,
        url: str,
        payload: dict,
    ) -> bool:
        """Try to update variables at a specific URL.

        Returns False if endpoint not available (graceful degradation).

        Args:
            session: aiohttp ClientSession
            headers: Request headers with auth
            url: URL to try
            payload: Data to send

        Returns:
            True if successful, False if endpoint not available
        """
        try:
            async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                if response.status == 200:
                    _LOGGER.debug("Successfully updated variables")
                    return True
                elif response.status in (404, 405):  # 405 = method not allowed
                    _LOGGER.debug("Update endpoint not available: %s", url)
                    return False
                else:
                    _LOGGER.debug("Unexpected status %s updating variables: %s", response.status, url)
                    return False
        except (ClientError, ValueError) as err:
            _LOGGER.debug("Error updating variables: %s", err)
            return False

    async def _try_trigger_refresh(
        self,
        session: ClientSession,
        headers: dict,
        url: str,
    ) -> bool:
        """Try to trigger refresh at a specific URL.

        Returns False if endpoint not available (graceful degradation).

        Args:
            session: aiohttp ClientSession
            headers: Request headers with auth
            url: URL to try

        Returns:
            True if triggered, False if endpoint not available
        """
        try:
            async with session.post(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    _LOGGER.debug("Successfully triggered refresh")
                    return True
                elif response.status in (404, 405):  # 405 = method not allowed
                    _LOGGER.debug("Refresh endpoint not available: %s", url)
                    return False
                else:
                    _LOGGER.debug("Unexpected status %s triggering refresh: %s", response.status, url)
                    return False
        except (ClientError, ValueError) as err:
            _LOGGER.debug("Error triggering refresh: %s", err)
            return False

    def _parse_devices_response(self, data: dict[str, Any]) -> list[TRMNLDevice]:
        """Parse devices response, handling various formats.

        Args:
            data: JSON response from devices endpoint

        Returns:
            List of TRMNLDevice objects (empty if parsing fails)
        """
        devices = []

        # Try to extract devices array (different servers may use different formats)
        devices_data = data.get("devices", [])
        if not devices_data and "data" in data:
            devices_data = data.get("data", [])
        if not devices_data and isinstance(data, list):
            devices_data = data

        for device_data in devices_data:
            try:
                # Infer device status based on presence of data
                # If API returns the device, it has recently reported data, so consider it online
                status_str = device_data.get("status", "online")
                if status_str not in ["online", "offline"]:
                    status_str = "online"  # Default to online if device data was returned

                device = TRMNLDevice(
                    id=device_data["id"],
                    name=device_data.get("name", f"Device {device_data['id']}"),
                    device_type=DeviceType(device_data.get("device_type", "og")),
                    battery_level=device_data.get("battery_level"),
                    last_seen=(
                        datetime.fromisoformat(device_data["last_seen"])
                        if device_data.get("last_seen")
                        else None
                    ),
                    firmware_version=device_data.get("firmware_version"),
                    status=DeviceStatus(status_str),
                    attributes=device_data.get("attributes", {}),
                )
                devices.append(device)
            except (KeyError, ValueError) as err:
                _LOGGER.debug("Failed to parse device: %s", err)
                continue

        return devices

    def _parse_plugin_response(self, data: dict[str, Any]) -> Optional[TRMNLPlugin]:
        """Parse plugin response, handling various formats.

        Args:
            data: JSON response from plugin endpoint

        Returns:
            TRMNLPlugin or None if parsing fails
        """
        try:
            plugin = TRMNLPlugin(
                uuid=data.get("uuid", data.get("id", "")),
                name=data.get("name", "Unknown Plugin"),
                version=data.get("version", "0.1.0"),
                description=data.get("description"),
            )
            return plugin
        except (KeyError, ValueError) as err:
            _LOGGER.debug("Failed to parse plugin: %s", err)
            return None

    def _build_headers(self) -> dict:
        """Build HTTP headers with authentication.

        Returns:
            Headers dictionary with auth method
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TRMNL-HA-Integration/0.1.0",
        }

        if self.auth_type == "api_key":
            api_key = self.credentials.get("api_key")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        elif self.auth_type == "basic":
            username = self.credentials.get("username", "")
            password = self.credentials.get("password", "")
            auth_str = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {auth_str}"

        return headers
