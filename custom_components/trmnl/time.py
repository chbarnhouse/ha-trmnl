"""Support for TRMNL time entities."""
import logging
from datetime import time
from typing import Any

from homeassistant.components.time import TimeEntity
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
    """Set up TRMNL time entities from a config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    api = entry_data["api"]
    devices = entry_data["devices"]
    models = entry_data.get("models", {})
    
    times = []
    for device in devices:
        device_id = device.get('friendly_id', str(device.get('id')))
        times.extend([
            TRMNLSleepStartTime(api, device, device_id, models),
            TRMNLSleepStopTime(api, device, device_id, models),
        ])
    
    async_add_entities(times)


class TRMNLTimeBase(TimeEntity):
    """Base class for TRMNL time entities."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the time entity."""
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
    
    def _parse_time_string(self, time_str: str) -> time:
        """Parse time string in HH:MM format to time object."""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return time(hours, minutes)
        except (ValueError, AttributeError):
            return None


class TRMNLSleepStartTime(TRMNLTimeBase):
    """TRMNL sleep start time entity."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the sleep start time entity."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Sleep Start Time"
        self._attr_unique_id = f"{device_id}_sleep_start"
        self._attr_icon = "mdi:sleep"
    
    @property
    def native_value(self) -> time:
        """Return the current sleep start time."""
        sleep_start = self._device.get('sleep_start_at')
        if sleep_start:
            return self._parse_time_string(sleep_start)
        return None
    
    async def async_set_value(self, value: time) -> None:
        """Set the sleep start time."""
        time_str = value.strftime("%H:%M")
        sleep_stop = self._device.get('sleep_stop_at', "07:00")
        
        success = await self._api.set_device_sleep_schedule(self._device_id, time_str, sleep_stop)
        if success:
            self._device['sleep_start_at'] = time_str
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to set sleep start time for %s", self._device_id)


class TRMNLSleepStopTime(TRMNLTimeBase):
    """TRMNL sleep stop time entity."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the sleep stop time entity."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Sleep Stop Time"
        self._attr_unique_id = f"{device_id}_sleep_stop"
        self._attr_icon = "mdi:alarm"
    
    @property
    def native_value(self) -> time:
        """Return the current sleep stop time."""
        sleep_stop = self._device.get('sleep_stop_at')
        if sleep_stop:
            return self._parse_time_string(sleep_stop)
        return None
    
    async def async_set_value(self, value: time) -> None:
        """Set the sleep stop time."""
        time_str = value.strftime("%H:%M")
        sleep_start = self._device.get('sleep_start_at', "23:00")
        
        success = await self._api.set_device_sleep_schedule(self._device_id, sleep_start, time_str)
        if success:
            self._device['sleep_stop_at'] = time_str
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to set sleep stop time for %s", self._device_id)