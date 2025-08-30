"""Support for TRMNL buttons."""
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
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
    """Set up TRMNL buttons from a config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    api = entry_data["api"]
    devices = entry_data["devices"]
    models = entry_data.get("models", {})
    
    buttons = []
    for device in devices:
        device_id = device.get('friendly_id', str(device.get('id')))
        buttons.append(TRMNLRefreshButton(api, device, device_id, models))
    
    async_add_entities(buttons)


class TRMNLButtonBase(ButtonEntity):
    """Base class for TRMNL buttons."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the button."""
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


class TRMNLRefreshButton(TRMNLButtonBase):
    """TRMNL refresh button."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the refresh button."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Refresh"
        self._attr_unique_id = f"{device_id}_refresh"
        self._attr_icon = "mdi:refresh"
    
    async def async_press(self) -> None:
        """Press the refresh button."""
        _LOGGER.info("Refreshing device %s via button press", self._device_id)
        success = await self._api.refresh_device(self._device_id)
        if not success:
            _LOGGER.error("Failed to refresh device %s", self._device_id)