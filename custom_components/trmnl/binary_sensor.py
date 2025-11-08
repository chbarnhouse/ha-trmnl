"""Binary sensor platform for TRMNL integration."""

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.models import DeviceStatus
from .const import DOMAIN
from .coordinator import TRMNLCoordinator
from .entities.base import TRMNLEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities from config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: TRMNLCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Create binary sensor entities for each device
    entities = []
    for device_id, device in coordinator.devices.items():
        entities.append(TRMNLConnectivityBinarySensor(coordinator, device_id, device))
        entities.append(TRMNLBatteryLowBinarySensor(coordinator, device_id, device))

    async_add_entities(entities)


class TRMNLConnectivityBinarySensor(TRMNLEntity, BinarySensorEntity):
    """Binary sensor for TRMNL device connectivity."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:wifi"

    @property
    def unique_id(self) -> str:
        """Return unique ID for sensor."""
        return f"{self.device_id}_connectivity"

    @property
    def name(self) -> str:
        """Return friendly name."""
        return f"{self.device_name} Connectivity"

    @property
    def is_on(self) -> bool | None:
        """Return True if device is online."""
        device = self.coordinator.devices.get(self.device_id)
        if device is None:
            return None
        return device.is_online

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        device = self.coordinator.devices.get(self.device_id)
        if device is None:
            return {}

        return {
            "status": device.status.value if device.status else None,
            "device_type": device.device_type.value,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        }


class TRMNLBatteryLowBinarySensor(TRMNLEntity, BinarySensorEntity):
    """Binary sensor for TRMNL device low battery alert."""

    _attr_device_class = BinarySensorDeviceClass.BATTERY
    _attr_icon = "mdi:battery-low"

    @property
    def unique_id(self) -> str:
        """Return unique ID for sensor."""
        return f"{self.device_id}_battery_low"

    @property
    def name(self) -> str:
        """Return friendly name."""
        return f"{self.device_name} Battery Low"

    @property
    def is_on(self) -> bool | None:
        """Return True if battery is low."""
        device = self.coordinator.devices.get(self.device_id)
        if device is None:
            return None
        return device.battery_low

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        device = self.coordinator.devices.get(self.device_id)
        if device is None:
            return {}

        return {
            "battery_level": device.battery_level,
            "status": device.status.value if device.status else None,
        }
