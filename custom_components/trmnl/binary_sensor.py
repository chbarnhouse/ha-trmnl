"""Binary sensor platform for TRMNL integration."""

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEVICE_STATE_ONLINE,
    SCREEN_STATE_ACTIVE,
    PLUGIN_STATE_RUNNING,
    DOMAIN,
)
from .coordinator import TRMNLDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TRMNL binary sensors based on a config entry."""
    coordinator: TRMNLDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Add device online sensor
    async_add_entities([TRMNLDeviceOnlineSensor(coordinator, entry)])

    # Add screen active sensors
    screens = coordinator.screens
    for screen in screens:
        screen_id = screen.get("id")
        if screen_id:
            async_add_entities([TRMNLScreenActiveSensor(coordinator, entry, screen_id)])

    # Add plugin running sensors
    plugins = coordinator.plugins
    for plugin in plugins:
        plugin_id = plugin.get("id")
        if plugin_id:
            async_add_entities([TRMNLPluginRunningSensor(coordinator, entry, plugin_id)])


class TRMNLDeviceOnlineSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a TRMNL device online binary sensor."""

    def __init__(
        self, coordinator: TRMNLDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{entry.data.get(CONF_NAME, 'TRMNL')} Device Online"
        self._attr_unique_id = f"{entry.entry_id}_device_online"
        self._attr_device_class = "connectivity"

    @property
    def is_on(self) -> bool:
        """Return true if the device is online."""
        return self.coordinator.device_state == DEVICE_STATE_ONLINE

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info


class TRMNLScreenActiveSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a TRMNL screen active binary sensor."""

    def __init__(
        self,
        coordinator: TRMNLDataUpdateCoordinator,
        entry: ConfigEntry,
        screen_id: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.screen_id = screen_id
        self._attr_name = f"{entry.data.get(CONF_NAME, 'TRMNL')} Screen {screen_id} Active"
        self._attr_unique_id = f"{entry.entry_id}_screen_{screen_id}_active"
        self._attr_device_class = "power"

    @property
    def is_on(self) -> bool:
        """Return true if the screen is active."""
        screen = self.coordinator.get_screen(self.screen_id)
        if not screen:
            return False
        return screen.get("state") == SCREEN_STATE_ACTIVE

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info


class TRMNLPluginRunningSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a TRMNL plugin running binary sensor."""

    def __init__(
        self,
        coordinator: TRMNLDataUpdateCoordinator,
        entry: ConfigEntry,
        plugin_id: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.plugin_id = plugin_id
        self._attr_name = f"{entry.data.get(CONF_NAME, 'TRMNL')} Plugin {plugin_id} Running"
        self._attr_unique_id = f"{entry.entry_id}_plugin_{plugin_id}_running"
        self._attr_device_class = "power"

    @property
    def is_on(self) -> bool:
        """Return true if the plugin is running."""
        plugin = self.coordinator.get_plugin(self.plugin_id)
        if not plugin:
            return False
        return plugin.get("status") == PLUGIN_STATE_RUNNING

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info
