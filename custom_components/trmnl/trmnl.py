"""TRMNL API client for Home Assistant integration."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import async_timeout

from .const import (
    API_BASE_URL,
    API_ENDPOINT,
    CONNECTION_TIMEOUT,
    DEVICE_STATE_ERROR,
    DEVICE_STATE_OFFLINE,
    DEVICE_STATE_ONLINE,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class TRMNLClient:
    """TRMNL API client."""

    def __init__(
        self,
        device_ip: str,
        api_key: str,
        device_id: str,
        update_interval: int = 30,
        webhook_port: int = 8123,
    ) -> None:
        """Initialize the TRMNL client."""
        self.device_ip = device_ip
        self.api_key = api_key
        self.device_id = device_id
        self.update_interval = update_interval
        self.webhook_port = webhook_port
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._last_update: Optional[datetime] = None

    async def async_connect(self) -> None:
        """Connect to TRMNL API."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=CONNECTION_TIMEOUT)
            )

        # Test connection by getting device info
        try:
            await self.async_get_device_info()
            self._connected = True
            _LOGGER.info("Successfully connected to TRMNL API")
        except Exception as ex:
            _LOGGER.error("Failed to connect to TRMNL API: %s", ex)
            self._connected = False
            raise

    async def async_disconnect(self) -> None:
        """Disconnect from TRMNL API."""
        if self.session:
            await self.session.close()
            self.session = None
        self._connected = False

    @property
    def connected(self) -> bool:
        """Return connection status."""
        return self._connected

    async def _async_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """Make an API request."""
        if not self.session:
            raise RuntimeError("Not connected to TRMNL API")

        url = f"http://{self.device_ip}{endpoint}"
        headers = {
            "ID": self.device_id,
            "Access-Token": self.api_key,
        }

        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self.session.request(
                    method, url, headers=headers, **kwargs
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request to {endpoint} timed out")
        except aiohttp.ClientResponseError as ex:
            _LOGGER.error("API request failed: %s", ex)
            raise
        except Exception as ex:
            _LOGGER.error("Unexpected error during API request: %s", ex)
            raise

    async def async_get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        endpoint = API_ENDPOINT
        return await self._async_request("GET", endpoint)

    async def async_get_device_status(self) -> Dict[str, Any]:
        """Get current device status."""
        endpoint = API_ENDPOINT
        return await self._async_request("GET", endpoint)

    async def async_get_screens(self) -> List[Dict[str, Any]]:
        """Get all screens for the device."""
        endpoint = f"devices/{self.device_id}/screens"
        return await self._async_request("GET", endpoint)

    async def async_get_screen(self, screen_id: str) -> Dict[str, Any]:
        """Get specific screen information."""
        endpoint = f"devices/{self.device_id}/screens/{screen_id}"
        return await self._async_request("GET", endpoint)

    async def async_update_screen(
        self, screen_id: str, content: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """Update screen content."""
        endpoint = f"devices/{self.device_id}/screens/{screen_id}"
        data = {"content": content, **kwargs}
        return await self._async_request("PUT", endpoint, json=data)

    async def async_get_plugins(self) -> List[Dict[str, Any]]:
        """Get all plugins for the device."""
        endpoint = f"devices/{self.device_id}/plugins"
        return await self._async_request("GET", endpoint)

    async def async_install_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Install a plugin on the device."""
        endpoint = f"devices/{self.device_id}/plugins"
        data = {"plugin_id": plugin_id}
        return await self._async_request("POST", endpoint, json=data)

    async def async_uninstall_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Uninstall a plugin from the device."""
        endpoint = f"devices/{self.device_id}/plugins/{plugin_id}"
        return await self._async_request("DELETE", endpoint)

    async def async_restart_device(self) -> Dict[str, Any]:
        """Restart the device."""
        endpoint = f"devices/{self.device_id}/restart"
        return await self._async_request("POST", endpoint)

    async def async_get_device_metrics(self) -> Dict[str, Any]:
        """Get device metrics and statistics."""
        endpoint = f"devices/{self.device_id}/metrics"
        return await self._async_request("GET", endpoint)

    async def async_set_brightness(self, brightness: int) -> Dict[str, Any]:
        """Set device screen brightness."""
        endpoint = f"devices/{self.device_id}/brightness"
        data = {"brightness": brightness}
        return await self._async_request("PUT", endpoint, json=data)

    async def async_get_webhook_config(self) -> Dict[str, Any]:
        """Get webhook configuration."""
        endpoint = f"devices/{self.device_id}/webhooks"
        return await self._async_request("GET", endpoint)

    async def async_setup_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Setup webhook for the device."""
        endpoint = f"devices/{self.device_id}/webhooks"
        data = {"webhook_url": webhook_url}
        return await self._async_request("POST", endpoint, json=data)

    def get_device_state(self, status_data: Dict[str, Any]) -> str:
        """Determine device state from status data."""
        if not status_data:
            return DEVICE_STATE_ERROR

        # Check if device is online based on last seen time
        last_seen = status_data.get("last_seen")
        if last_seen:
            try:
                last_seen_dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
                if datetime.now(last_seen_dt.tzinfo) - last_seen_dt < timedelta(
                    minutes=5
                ):
                    return DEVICE_STATE_ONLINE
            except (ValueError, TypeError):
                pass

        return DEVICE_STATE_OFFLINE

    async def async_poll_device(self) -> Dict[str, Any]:
        """Poll device for updates."""
        try:
            device_info = await self.async_get_device_info()
            device_status = await self.async_get_device_status()
            
            # Combine the data
            result = {
                "device_info": device_info,
                "device_status": device_status,
                "state": self.get_device_state(device_status),
                "last_update": datetime.now().isoformat(),
            }
            
            self._last_update = datetime.now()
            return result
            
        except Exception as ex:
            _LOGGER.error("Failed to poll device: %s", ex)
            return {
                "device_info": {},
                "device_status": {},
                "state": DEVICE_STATE_ERROR,
                "last_update": datetime.now().isoformat(),
                "error": str(ex),
            }

    @property
    def last_update(self) -> Optional[datetime]:
        """Return last update time."""
        return self._last_update
