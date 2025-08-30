"""Support for TRMNL number entities."""
import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
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
    """Set up TRMNL number entities from a config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    api = entry_data["api"]
    devices = entry_data["devices"]
    models = entry_data.get("models", {})
    
    numbers = []
    for device in devices:
        device_id = device.get('friendly_id', str(device.get('id')))
        numbers.extend([
            TRMNLRefreshRateNumber(api, device, device_id, models),
            TRMNLImageTimeoutNumber(api, device, device_id, models),
        ])
    
    async_add_entities(numbers)


class TRMNLNumberBase(NumberEntity):
    """Base class for TRMNL number entities."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the number entity."""
        self._api = api
        self._device = device
        self._device_id = device_id
        self._models = models or {}
        self._attr_has_entity_name = True
        self._attr_mode = NumberMode.BOX
    
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
        if 'firmware_version' in self._device and self._device['firmware_version']:
            return str(self._device['firmware_version'])
        
        version_fields = ['firmware', 'fw_version', 'version', 'software_version', 'sw_version']
        
        for field in version_fields:
            if field in self._device and self._device[field]:
                return str(self._device[field])
        
        return f"TRMNL v{self._device.get('id', 'Unknown')}"
    
    def _get_device_model(self) -> str:
        """Get device model from device data with fallbacks."""
        if 'model_id' in self._device and self._device['model_id']:
            model_id = str(self._device['model_id'])
            if model_id in self._models:
                return self._models[model_id]
            if not model_id.isdigit():
                return model_id
        
        model_fields = ['model', 'device_model', 'product_model', 'hardware_model']
        for field in model_fields:
            if field in self._device and self._device[field]:
                return str(self._device[field])
        
        if 'model_id' in self._device and self._device['model_id']:
            return f"TRMNL Model {self._device['model_id']}"
        
        return "TRMNL Device"


class TRMNLRefreshRateNumber(TRMNLNumberBase):
    """TRMNL refresh rate number entity."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the refresh rate number entity."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Refresh Rate"
        self._attr_unique_id = f"{device_id}_refresh_rate"
        self._attr_icon = "mdi:timer"
        self._attr_native_min_value = 60  # 1 minute
        self._attr_native_max_value = 86400  # 24 hours
        self._attr_native_step = 60  # 1 minute steps
        self._attr_native_unit_of_measurement = "s"
    
    @property
    def native_value(self) -> float:
        """Return the current refresh rate."""
        return self._device.get('refresh_rate', 3600)  # Default 1 hour
    
    async def async_set_native_value(self, value: float) -> None:
        """Set the refresh rate."""
        success = await self._api.set_device_refresh_rate(self._device_id, int(value))
        if success:
            self._device['refresh_rate'] = int(value)
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to set refresh rate for %s", self._device_id)


class TRMNLImageTimeoutNumber(TRMNLNumberBase):
    """TRMNL image timeout number entity."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the image timeout number entity."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Image Timeout"
        self._attr_unique_id = f"{device_id}_image_timeout"
        self._attr_icon = "mdi:clock-outline"
        self._attr_native_min_value = 30  # 30 seconds
        self._attr_native_max_value = 3600  # 1 hour
        self._attr_native_step = 30  # 30 second steps
        self._attr_native_unit_of_measurement = "s"
    
    @property
    def native_value(self) -> float:
        """Return the current image timeout."""
        return self._device.get('image_timeout', 300)  # Default 5 minutes
    
    async def async_set_native_value(self, value: float) -> None:
        """Set the image timeout."""
        success = await self._api.set_device_image_timeout(self._device_id, int(value))
        if success:
            self._device['image_timeout'] = int(value)
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to set image timeout for %s", self._device_id)