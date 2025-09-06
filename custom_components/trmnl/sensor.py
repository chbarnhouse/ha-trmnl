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
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, UnitOfElectricPotential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

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
    models = entry_data.get("models", {})
    
    sensors = []
    for device in devices:
        device_id = device.get('friendly_id', str(device.get('id')))
        sensors.extend([
            # Core device sensors
            TRMNLBatterySensor(api, device, device_id, models),
            TRMNLWiFiSensor(api, device, device_id, models),
            
            # Configuration sensors
            TRMNLRefreshRateSensor(api, device, device_id, models),
            TRMNLImageTimeoutSensor(api, device, device_id, models),
            
            # Status sensors
            TRMNLLastUpdateSensor(api, device, device_id, models),
            TRMNLMacAddressSensor(api, device, device_id, models),
            TRMNLApiKeySensor(api, device, device_id, models),
            
            # Display configuration sensors
            TRMNLWidthSensor(api, device, device_id, models),
            TRMNLHeightSensor(api, device, device_id, models),
            TRMNLModelIdSensor(api, device, device_id, models),
            TRMNLPlaylistIdSensor(api, device, device_id, models),
        ])
    
    async_add_entities(sensors)


class TRMNLSensorBase(SensorEntity):
    """Base class for TRMNL sensors."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the sensor."""
        self._api = api
        self._device = device
        self._device_id = device_id
        self._models = models or {}
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
        # Based on BYOS documentation, firmware_version is the correct field
        if 'firmware_version' in self._device and self._device['firmware_version']:
            return str(self._device['firmware_version'])
        
        # Try other fallback field names
        version_fields = [
            'firmware',
            'fw_version', 
            'version',
            'software_version',
            'sw_version'
        ]
        
        for field in version_fields:
            if field in self._device and self._device[field]:
                return str(self._device[field])
        
        # If no firmware version found, return a descriptive fallback
        return f"TRMNL v{self._device.get('id', 'Unknown')}"
    
    def _get_device_model(self) -> str:
        """Get device model from device data with fallbacks."""
        # Based on BYOS documentation, model information might be in model_id
        # But model_id is likely a reference that needs to be resolved to actual model name
        
        # Log all available device fields for debugging
        _LOGGER.info("Available device fields for model detection: %s", list(self._device.keys()))
        
        # First try to resolve model_id using the models mapping
        if 'model_id' in self._device and self._device['model_id']:
            model_id = str(self._device['model_id'])
            _LOGGER.info("Found model_id: %s", model_id)
            
            # Try to resolve model_id to actual model name using models mapping
            if model_id in self._models:
                model_name = self._models[model_id]
                _LOGGER.info("Resolved model_id %s to model name: %s", model_id, model_name)
                return model_name
            
            # If model_id looks like it contains useful info directly, use it
            if not model_id.isdigit():  # Not just a numeric ID
                return model_id
        
        # Try other potential model field names
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
        
        for field in model_fields:
            if field in self._device and self._device[field]:
                model_value = str(self._device[field])
                _LOGGER.info("Found device model in field '%s': %s", field, model_value)
                return model_value
        
        # If model_id was numeric, use it with TRMNL prefix
        if 'model_id' in self._device and self._device['model_id']:
            model_id = str(self._device['model_id'])
            _LOGGER.info("Using numeric model_id as fallback: %s", model_id)
            return f"TRMNL Model {model_id}"
        
        # Log that no model was found
        _LOGGER.warning("No device model found in device data, using fallback")
        
        # Fallback to a generic model name
        return "TRMNL Device"


class TRMNLBatterySensor(TRMNLSensorBase):
    """TRMNL battery sensor."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the battery sensor."""
        super().__init__(api, device, device_id, models)
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
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the WiFi sensor."""
        super().__init__(api, device, device_id, models)
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


class TRMNLRefreshRateSensor(TRMNLSensorBase):
    """TRMNL refresh rate sensor."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the refresh rate sensor."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Refresh Rate"
        self._attr_unique_id = f"{device_id}_refresh_rate"
        self._attr_native_unit_of_measurement = "minutes"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:timer"
    
    @property
    def native_value(self) -> Optional[int]:
        """Return refresh rate in minutes."""
        return self._device.get('refresh_rate')


class TRMNLImageTimeoutSensor(TRMNLSensorBase):
    """TRMNL image timeout sensor."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the image timeout sensor."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Image Timeout"
        self._attr_unique_id = f"{device_id}_image_timeout"
        self._attr_native_unit_of_measurement = "seconds"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:timer-outline"
    
    @property
    def native_value(self) -> Optional[int]:
        """Return image timeout in seconds."""
        return self._device.get('image_timeout')


class TRMNLLastUpdateSensor(TRMNLSensorBase):
    """TRMNL last update sensor."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the last update sensor."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Last Update"
        self._attr_unique_id = f"{device_id}_last_update"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-outline"
    
    @property
    def native_value(self) -> Optional[datetime]:
        """Return last update timestamp."""
        timestamp_str = self._device.get('updated_at')
        if timestamp_str:
            try:
                # Parse ISO format timestamp
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                _LOGGER.warning("Could not parse timestamp: %s", timestamp_str)
                return None
        return None


class TRMNLMacAddressSensor(TRMNLSensorBase):
    """TRMNL MAC address sensor."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the MAC address sensor."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "MAC Address"
        self._attr_unique_id = f"{device_id}_mac_address"
        self._attr_icon = "mdi:network"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> Optional[str]:
        """Return MAC address."""
        return self._device.get('mac_address')


class TRMNLApiKeySensor(TRMNLSensorBase):
    """TRMNL API key sensor (partially masked for security)."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the API key sensor."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "API Key"
        self._attr_unique_id = f"{device_id}_api_key"
        self._attr_icon = "mdi:key"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> Optional[str]:
        """Return partially masked API key for security."""
        api_key = self._device.get('api_key')
        if api_key and len(api_key) > 8:
            # Show first 4 and last 4 characters, mask the middle
            return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"
        return api_key


class TRMNLWidthSensor(TRMNLSensorBase):
    """TRMNL display width sensor."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the width sensor."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Display Width"
        self._attr_unique_id = f"{device_id}_width"
        self._attr_native_unit_of_measurement = "pixels"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:monitor-screenshot"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> Optional[int]:
        """Return display width."""
        return self._device.get('width')


class TRMNLHeightSensor(TRMNLSensorBase):
    """TRMNL display height sensor."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the height sensor."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Display Height"
        self._attr_unique_id = f"{device_id}_height"
        self._attr_native_unit_of_measurement = "pixels"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:monitor-screenshot"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> Optional[int]:
        """Return display height."""
        return self._device.get('height')


class TRMNLModelIdSensor(TRMNLSensorBase):
    """TRMNL model ID sensor."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the model ID sensor."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Model ID"
        self._attr_unique_id = f"{device_id}_model_id"
        self._attr_icon = "mdi:information"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> Optional[int]:
        """Return model ID."""
        return self._device.get('model_id')
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional model information."""
        model_id = self._device.get('model_id')
        if model_id and str(model_id) in self._models:
            return {
                "model_name": self._models[str(model_id)]
            }
        return {}


class TRMNLPlaylistIdSensor(TRMNLSensorBase):
    """TRMNL playlist ID sensor."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the playlist ID sensor."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Playlist ID"
        self._attr_unique_id = f"{device_id}_playlist_id"
        self._attr_icon = "mdi:playlist-play"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
    
    @property
    def native_value(self) -> Optional[int]:
        """Return current playlist ID."""
        return self._device.get('playlist_id')