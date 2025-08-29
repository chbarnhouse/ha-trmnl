"""Support for TRMNL sensors."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TRMNLDataUpdateCoordinator
from .const import (
    DOMAIN,
    SENSOR_TYPES,
    MANUFACTURER,
    MODEL,
    CONF_DEVICE_ID,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TRMNL sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data[CONF_DEVICE_ID]

    sensors = []
    for sensor_type in SENSOR_TYPES:
        sensors.append(TRMNLSensor(coordinator, device_id, sensor_type))

    async_add_entities(sensors)


class TRMNLSensor(CoordinatorEntity, SensorEntity):
    """Representation of a TRMNL sensor."""

    def __init__(
        self,
        coordinator: TRMNLDataUpdateCoordinator,
        device_id: str,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._sensor_type = sensor_type
        self._attr_name = f"TRMNL {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_unique_id = f"{device_id}_{sensor_type}"
        self._attr_icon = SENSOR_TYPES[sensor_type].get("icon")

        # Set device class and unit of measurement
        if "device_class" in SENSOR_TYPES[sensor_type]:
            if SENSOR_TYPES[sensor_type]["device_class"] == "battery":
                self._attr_device_class = SensorDeviceClass.BATTERY
                self._attr_native_unit_of_measurement = PERCENTAGE
                self._attr_state_class = SensorStateClass.MEASUREMENT
            elif SENSOR_TYPES[sensor_type]["device_class"] == "signal_strength":
                self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
                self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
                self._attr_state_class = SensorStateClass.MEASUREMENT
            elif SENSOR_TYPES[sensor_type]["device_class"] == "timestamp":
                self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": f"TRMNL {self._device_id}",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": self.coordinator.data.get("firmware_version", "Unknown") if self.coordinator.data else "Unknown",
        }

    @property
    def native_value(self) -> Optional[Any]:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        data = self.coordinator.data

        if self._sensor_type == "battery":
            # Convert voltage to percentage (approximate)
            voltage = data.get("battery", 0)
            if voltage > 4.0:
                return 100
            elif voltage > 3.7:
                return int((voltage - 3.7) / 0.3 * 100)
            else:
                return 0

        elif self._sensor_type == "wifi_signal":
            return data.get("wifi_signal", -100)

        elif self._sensor_type == "firmware_version":
            return data.get("firmware_version", "Unknown")

        elif self._sensor_type == "last_seen":
            last_seen = data.get("last_seen")
            if last_seen:
                try:
                    return datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    return None
            return None

        elif self._sensor_type == "device_status":
            return data.get("device_status", "unknown")

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None

        attributes = {}
        data = self.coordinator.data

        if self._sensor_type == "battery":
            attributes["voltage"] = data.get("battery", 0)

        elif self._sensor_type == "device_status":
            attributes["mac_address"] = data.get("mac_address", "")
            attributes["uptime"] = data.get("uptime", 0)
            attributes["last_update"] = data.get("last_seen", "")

        return attributes