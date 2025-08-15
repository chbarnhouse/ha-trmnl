"""Sensor platform for TRMNL integration."""

import logging
from datetime import datetime
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_NAME,
    DEVICE_CLASS_TIMESTAMP,
    STATE_UNKNOWN,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DEVICE_ID,
    ATTR_FIRMWARE_VERSION,
    ATTR_LAST_UPDATE,
    ATTR_SCREEN_CONTENT,
    ATTR_PLUGIN_STATUS,
    DOMAIN,
)
from .coordinator import TRMNLDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TRMNL sensor based on a config entry."""
    coordinator: TRMNLDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Add device status sensor
    async_add_entities([TRMNLDeviceStatusSensor(coordinator, entry)])

    # Add screen sensors
    screens = coordinator.screens
    for screen in screens:
        screen_id = screen.get("id")
        if screen_id:
            async_add_entities([TRMNLScreenSensor(coordinator, entry, screen_id)])

    # Add plugin sensors
    plugins = coordinator.plugins
    for plugin in plugins:
        plugin_id = plugin.get("id")
        if plugin_id:
            async_add_entities([TRMNLPluginSensor(coordinator, entry, plugin_id)])


class TRMNLDeviceStatusSensor(CoordinatorEntity, SensorEntity):
    """Representation of a TRMNL device status sensor."""

    def __init__(
        self, coordinator: TRMNLDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{entry.data.get(CONF_NAME, 'TRMNL')} Device Status"
        self._attr_unique_id = f"{entry.entry_id}_device_status"
        self._attr_device_class = "trmnl__device_status"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.coordinator.device_state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        data = self.coordinator.data
        if not data:
            return {}

        device_info = data.get("device_info", {})
        device_status = data.get("device_status", {})

        return {
            ATTR_DEVICE_ID: self.coordinator.device_id,
            ATTR_FIRMWARE_VERSION: device_info.get("firmware_version"),
            ATTR_LAST_UPDATE: self.coordinator.last_update.isoformat() if self.coordinator.last_update else None,
            "model": device_info.get("model"),
            "manufacturer": device_info.get("manufacturer"),
            "last_seen": device_status.get("last_seen"),
            "uptime": device_status.get("uptime"),
            "temperature": device_status.get("temperature"),
            "memory_usage": device_status.get("memory_usage"),
            "cpu_usage": device_status.get("cpu_usage"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info


class TRMNLScreenSensor(CoordinatorEntity, SensorEntity):
    """Representation of a TRMNL screen sensor."""

    def __init__(
        self,
        coordinator: TRMNLDataUpdateCoordinator,
        entry: ConfigEntry,
        screen_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.screen_id = screen_id
        self._attr_name = f"{entry.data.get(CONF_NAME, 'TRMNL')} Screen {screen_id}"
        self._attr_unique_id = f"{entry.entry_id}_screen_{screen_id}"
        self._attr_device_class = "trmnl__screen"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        screen = self.coordinator.get_screen(self.screen_id)
        if not screen:
            return STATE_UNKNOWN
        return screen.get("state", STATE_UNKNOWN)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        screen = self.coordinator.get_screen(self.screen_id)
        if not screen:
            return {}

        return {
            ATTR_SCREEN_ID: self.screen_id,
            ATTR_SCREEN_CONTENT: screen.get("content"),
            "resolution": screen.get("resolution"),
            "orientation": screen.get("orientation"),
            "brightness": screen.get("brightness"),
            "active": screen.get("active", False),
            "last_updated": screen.get("last_updated"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info


class TRMNLPluginSensor(CoordinatorEntity, SensorEntity):
    """Representation of a TRMNL plugin sensor."""

    def __init__(
        self,
        coordinator: TRMNLDataUpdateCoordinator,
        entry: ConfigEntry,
        plugin_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.plugin_id = plugin_id
        self._attr_name = f"{entry.data.get(CONF_NAME, 'TRMNL')} Plugin {plugin_id}"
        self._attr_unique_id = f"{entry.entry_id}_plugin_{plugin_id}"
        self._attr_device_class = "trmnl__plugin"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        plugin = self.coordinator.get_plugin(self.plugin_id)
        if not plugin:
            return STATE_UNKNOWN
        return plugin.get("status", STATE_UNKNOWN)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        plugin = self.coordinator.get_plugin(self.plugin_id)
        if not plugin:
            return {}

        return {
            ATTR_PLUGIN_ID: self.plugin_id,
            ATTR_PLUGIN_STATUS: plugin.get("status"),
            "version": plugin.get("version"),
            "description": plugin.get("description"),
            "author": plugin.get("author"),
            "repository": plugin.get("repository"),
            "installed_at": plugin.get("installed_at"),
            "last_updated": plugin.get("last_updated"),
            "config": plugin.get("config"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info
