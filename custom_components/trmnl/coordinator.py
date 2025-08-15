"""Data coordinator for TRMNL integration."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_UPDATE_INTERVAL
from .trmnl import TRMNLClient

_LOGGER = logging.getLogger(__name__)


class TRMNLDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching TRMNL data."""

    def __init__(self, hass: HomeAssistant, client: TRMNLClient) -> None:
        """Initialize."""
        self.client = client
        self.device_id = client.device_id
        self._webhook_data: Dict[str, Any] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=f"TRMNL {self.device_id}",
            update_interval=timedelta(seconds=client.update_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via TRMNL client."""
        try:
            data = await self.client.async_poll_device()
            
            # Merge with any webhook data
            if self._webhook_data:
                data.update(self._webhook_data)
                self._webhook_data = {}  # Clear after merging
                
            return data
        except Exception as ex:
            _LOGGER.error("Error updating TRMNL data: %s", ex)
            raise UpdateFailed(f"Error updating TRMNL data: {ex}") from ex

    async def async_webhook_handler(self, hass: HomeAssistant, webhook_id: str, request) -> None:
        """Handle incoming webhook from TRMNL."""
        try:
            webhook_data = await request.json()
            _LOGGER.debug("Received webhook data: %s", webhook_data)
            
            # Store webhook data for next update
            self._webhook_data.update(webhook_data)
            
            # Trigger immediate update if needed
            if webhook_data.get("requires_immediate_update", False):
                await self.async_request_refresh()
                
        except Exception as ex:
            _LOGGER.error("Error processing webhook: %s", ex)

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        await self.client.async_disconnect()

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device info."""
        data = self.data
        if not data:
            return {}
        
        device_info = data.get("device_info", {})
        return {
            "identifiers": {("trmnl", self.device_id)},
            "name": device_info.get("name", f"TRMNL {self.device_id}"),
            "manufacturer": "TRMNL",
            "model": device_info.get("model", "TRMNL Device"),
            "sw_version": device_info.get("firmware_version", "Unknown"),
            "configuration_url": f"https://docs.usetrmnl.com/go",
        }

    @property
    def device_state(self) -> str:
        """Return current device state."""
        data = self.data
        if not data:
            return "unknown"
        return data.get("state", "unknown")

    @property
    def last_update(self) -> Optional[datetime]:
        """Return last update time."""
        data = self.data
        if not data:
            return None
        
        last_update_str = data.get("last_update")
        if last_update_str:
            try:
                return datetime.fromisoformat(last_update_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        return None

    @property
    def screens(self) -> list:
        """Return list of screens."""
        data = self.data
        if not data:
            return []
        
        device_info = data.get("device_info", {})
        return device_info.get("screens", [])

    @property
    def plugins(self) -> list:
        """Return list of plugins."""
        data = self.data
        if not data:
            return []
        
        device_info = data.get("device_info", {})
        return device_info.get("plugins", [])

    @property
    def metrics(self) -> Dict[str, Any]:
        """Return device metrics."""
        data = self.data
        if not data:
            return {}
        
        return data.get("metrics", {})

    def get_screen(self, screen_id: str) -> Optional[Dict[str, Any]]:
        """Get specific screen by ID."""
        screens = self.screens
        for screen in screens:
            if screen.get("id") == screen_id:
                return screen
        return None

    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get specific plugin by ID."""
        plugins = self.plugins
        for plugin in plugins:
            if plugin.get("id") == plugin_id:
                return plugin
        return None

    async def async_update_screen(self, screen_id: str, content: str, **kwargs: Any) -> bool:
        """Update a screen and refresh data."""
        try:
            await self.client.async_update_screen(screen_id, content, **kwargs)
            await self.async_request_refresh()
            return True
        except Exception as ex:
            _LOGGER.error("Failed to update screen: %s", ex)
            return False

    async def async_install_plugin(self, plugin_id: str) -> bool:
        """Install a plugin and refresh data."""
        try:
            await self.client.async_install_plugin(plugin_id)
            await self.async_request_refresh()
            return True
        except Exception as ex:
            _LOGGER.error("Failed to install plugin: %s", ex)
            return False

    async def async_uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin and refresh data."""
        try:
            await self.client.async_uninstall_plugin(plugin_id)
            await self.async_request_refresh()
            return True
        except Exception as ex:
            _LOGGER.error("Failed to uninstall plugin: %s", ex)
            return False

    async def async_restart_device(self) -> bool:
        """Restart the device."""
        try:
            await self.client.async_restart_device()
            return True
        except Exception as ex:
            _LOGGER.error("Failed to restart device: %s", ex)
            return False

    async def async_set_brightness(self, brightness: int) -> bool:
        """Set device brightness and refresh data."""
        try:
            await self.client.async_set_brightness(brightness)
            await self.async_request_refresh()
            return True
        except Exception as ex:
            _LOGGER.error("Failed to set brightness: %s", ex)
            return False
