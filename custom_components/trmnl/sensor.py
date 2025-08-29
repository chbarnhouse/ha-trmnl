"""Support for TRMNL sensors."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, UnitOfElectricPotential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .api import TRMNLApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TRMNL sensors from a config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    api = entry_data["api"]
    devices = entry_data["devices"]
    
    sensors = []
    for device in devices:
        device_id = device.get('friendly_id', str(device.get('id')))
        sensors.extend([
            TRMNLBatterySensor(api, device, device_id),
            TRMNLWiFiSensor(api, device, device_id),
        ])
    
    async_add_entities(sensors)


class TRMNLSensorBase(SensorEntity):
    """Base class for TRMNL sensors."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str) -> None:
        """Initialize the sensor."""
        self._api = api
        self._device = device
        self._device_id = device_id
        self._attr_has_entity_name = True
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=f"{self._device.get('label', self._device_id)} ({self._device.get('friendly_id', self._device_id)})",
            manufacturer="TRMNL",
            model=self._get_device_model(),
            sw_version=self._get_firmware_version(),
        )
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True
    
    def _get_firmware_version(self) -> str:
        """Get firmware version from device data with fallbacks."""
        # Try multiple common field names for firmware version
        version_fields = [
            'firmware',
            'fw_version', 
            'version',
            'software_version',
            'sw_version',
            'firmware_version'
        ]
        
        for field in version_fields:
            if field in self._device and self._device[field]:
                return str(self._device[field])
        
        # If no firmware version found, return a descriptive fallback
        return f"TRMNL v{self._device.get('id', 'Unknown')}"
    
    def _get_device_model(self) -> str:
        """Get device model from device data with fallbacks."""
        # Try multiple common field names for device model
        model_fields = [
            'model',
            'device_model', 
            'product_model',
            'hardware_model',
            'device_type',
            'product_type',
            'type',
            'variant',
            'sku',
            'part_number'
        ]
        
        # Log all available device fields for debugging
        _LOGGER.debug("Available device fields for model detection: %s", list(self._device.keys()))
        
        for field in model_fields:
            if field in self._device and self._device[field]:
                model_value = str(self._device[field])
                _LOGGER.debug("Found device model in field '%s': %s", field, model_value)
                return model_value
        
        # Log that no model was found
        _LOGGER.warning("No device model found in device data, using fallback")
        
        # Fallback to a generic model name
        return "TRMNL Device"


class TRMNLBatterySensor(TRMNLSensorBase):
    """TRMNL battery sensor."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str) -> None:
        """Initialize the battery sensor."""
        super().__init__(api, device, device_id)
        self._attr_name = "Battery"
        self._attr_unique_id = f"{device_id}_battery"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:battery"
    
    @property
    def native_value(self) -> Optional[float]:
        """Return battery voltage."""
        return self._device.get('battery')
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes."""
        voltage = self._device.get('battery', 0)
        # Convert voltage to approximate percentage
        if voltage >= 4.0:
            percentage = 100
        elif voltage >= 3.7:
            percentage = int((voltage - 3.7) / 0.3 * 100)
        else:
            percentage = 0
            
        return {
            "voltage": voltage,
            "percentage": percentage,
        }


class TRMNLWiFiSensor(TRMNLSensorBase):
    """TRMNL WiFi signal sensor."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str) -> None:
        """Initialize the WiFi sensor."""
        super().__init__(api, device, device_id)
        self._attr_name = "WiFi Signal"
        self._attr_unique_id = f"{device_id}_wifi"
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:wifi"
    
    @property
    def native_value(self) -> Optional[int]:
        """Return WiFi signal strength."""
        return self._device.get('wifi')