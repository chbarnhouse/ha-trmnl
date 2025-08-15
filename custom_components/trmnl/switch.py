"""Switch platform for TRMNL integration."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TRMNLDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TRMNL switches based on a config entry."""
    coordinator: TRMNLDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Add device restart switch
    async_add_entities([TRMNLDeviceRestartSwitch(coordinator, entry)])

    # Add plugin control switches
    plugins = coordinator.plugins
    for plugin in plugins:
        plugin_id = plugin.get("id")
        if plugin_id:
            async_add_entities([TRMNLPluginControlSwitch(coordinator, entry, plugin_id)])


class TRMNLDeviceRestartSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a TRMNL device restart switch."""

    def __init__(
        self, coordinator: TRMNLDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = f"{entry.data.get(CONF_NAME, 'TRMNL')} Device Restart"
        self._attr_unique_id = f"{entry.entry_id}_device_restart"
        self._attr_icon = "mdi:restart"
        self._attr_assumed_state = True

    @property
    def is_on(self) -> bool:
        """Return true if the device is restarting."""
        # This switch is always off (momentary switch)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (restart device)."""
        try:
            await self.coordinator.async_restart_device()
            _LOGGER.info("Device restart initiated")
        except Exception as ex:
            _LOGGER.error("Failed to restart device: %s", ex)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (no action needed)."""
        # No action needed for turn off
        pass

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info


class TRMNLPluginControlSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a TRMNL plugin control switch."""

    def __init__(
        self,
        coordinator: TRMNLDataUpdateCoordinator,
        entry: ConfigEntry,
        plugin_id: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.plugin_id = plugin_id
        self._attr_name = f"{entry.data.get(CONF_NAME, 'TRMNL')} Plugin {plugin_id} Control"
        self._attr_unique_id = f"{entry.entry_id}_plugin_{plugin_id}_control"
        self._attr_icon = "mdi:plugin"

    @property
    def is_on(self) -> bool:
        """Return true if the plugin is installed."""
        plugin = self.coordinator.get_plugin(self.plugin_id)
        return plugin is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (install plugin)."""
        try:
            success = await self.coordinator.async_install_plugin(self.plugin_id)
            if success:
                _LOGGER.info("Plugin %s installed successfully", self.plugin_id)
            else:
                _LOGGER.error("Failed to install plugin %s", self.plugin_id)
        except Exception as ex:
            _LOGGER.error("Failed to install plugin %s: %s", self.plugin_id, ex)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (uninstall plugin)."""
        try:
            success = await self.coordinator.async_uninstall_plugin(self.plugin_id)
            if success:
                _LOGGER.info("Plugin %s uninstalled successfully", self.plugin_id)
            else:
                _LOGGER.error("Failed to uninstall plugin %s", self.plugin_id)
        except Exception as ex:
            _LOGGER.error("Failed to uninstall plugin %s: %s", self.plugin_id, ex)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info
