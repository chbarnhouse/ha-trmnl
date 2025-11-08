"""Sensor platform for TRMNL integration."""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TRMNLCoordinator
from .entities.base import TRMNLEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: TRMNLCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Create sensor entities for each device
    entities = []
    for device_id, device in coordinator.devices.items():
        entities.append(TRMNLBatterySensor(coordinator, device_id, device))
        entities.append(TRMNLLastSeenSensor(coordinator, device_id, device))
        entities.append(TRMNLFirmwareVersionSensor(coordinator, device_id, device))

    async_add_entities(entities)


class TRMNLBatterySensor(TRMNLEntity, SensorEntity):
    """Sensor for TRMNL device battery level."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:battery"

    @property
    def unique_id(self) -> str:
        """Return unique ID for sensor."""
        return f"{self.device_id}_battery"

    @property
    def name(self) -> str:
        """Return friendly name."""
        return f"{self.device_name} Battery"

    @property
    def native_value(self) -> int | None:
        """Return the current battery level percentage."""
        device = self.coordinator.devices.get(self.device_id)
        if device is None:
            return None
        return device.battery_level

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        device = self.coordinator.devices.get(self.device_id)
        if device is None:
            return {}

        return {
            "battery_low": device.battery_low,
            "status": device.status.value if device.status else None,
        }


class TRMNLLastSeenSensor(TRMNLEntity, SensorEntity):
    """Sensor for TRMNL device last seen timestamp."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock"

    @property
    def unique_id(self) -> str:
        """Return unique ID for sensor."""
        return f"{self.device_id}_last_seen"

    @property
    def name(self) -> str:
        """Return friendly name."""
        return f"{self.device_name} Last Seen"

    @property
    def native_value(self) -> str | None:
        """Return the last seen timestamp."""
        device = self.coordinator.devices.get(self.device_id)
        if device is None or device.last_seen is None:
            return None
        return device.last_seen.isoformat()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        device = self.coordinator.devices.get(self.device_id)
        if device is None:
            return {}

        return {
            "device_id": device.id,
            "device_type": device.device_type.value,
        }


class TRMNLFirmwareVersionSensor(TRMNLEntity, SensorEntity):
    """Sensor for TRMNL device firmware version."""

    _attr_icon = "mdi:information"

    @property
    def unique_id(self) -> str:
        """Return unique ID for sensor."""
        return f"{self.device_id}_firmware"

    @property
    def name(self) -> str:
        """Return friendly name."""
        return f"{self.device_name} Firmware Version"

    @property
    def native_value(self) -> str | None:
        """Return the firmware version."""
        device = self.coordinator.devices.get(self.device_id)
        if device is None:
            return None
        return device.firmware_version

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        device = self.coordinator.devices.get(self.device_id)
        if device is None:
            return {}

        return {
            "status": device.status.value if device.status else None,
            "battery_level": device.battery_level,
        }
