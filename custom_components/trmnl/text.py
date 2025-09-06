"""Support for TRMNL text entities."""
import logging
from typing import Any

from homeassistant.components.text import TextEntity
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
    """Set up TRMNL text entities from a config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    api = entry_data["api"]
    devices = entry_data["devices"]
    models = entry_data.get("models", {})
    
    texts = []
    for device in devices:
        device_id = device.get('friendly_id', str(device.get('id')))
        texts.append(TRMNLPlaylistNameText(api, device, device_id, models))
    
    async_add_entities(texts)


class TRMNLTextBase(TextEntity):
    """Base class for TRMNL text entities."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the text entity."""
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


class TRMNLPlaylistNameText(TRMNLTextBase):
    """TRMNL playlist name text input entity."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the playlist name text entity."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Playlist Name"
        self._attr_unique_id = f"{device_id}_playlist_name"
        self._attr_icon = "mdi:playlist-edit"
        self._attr_mode = "text"
        self._attr_native_max = 100
        self._current_playlist_id = None
        self._stored_names = {}  # Store custom names per playlist ID
        
    @property
    def native_value(self) -> str:
        """Return the current text value."""
        current_playlist_id = self._device.get('playlist_id')
        if current_playlist_id:
            # Return stored custom name or default format
            return self._stored_names.get(str(current_playlist_id), f"Playlist {current_playlist_id}")
        return ""
    
    async def async_set_value(self, value: str) -> None:
        """Set the text value."""
        current_playlist_id = self._device.get('playlist_id')
        if current_playlist_id:
            # Store the custom name for this playlist
            self._stored_names[str(current_playlist_id)] = value
            _LOGGER.info("Stored custom name '%s' for playlist %s", value, current_playlist_id)
        
        # Update the state
        self.async_write_ha_state()
    
    def get_stored_name(self, playlist_id: str) -> str:
        """Get the stored custom name for a playlist ID."""
        return self._stored_names.get(playlist_id, f"Playlist {playlist_id}")
    
    def clear_stored_name(self, playlist_id: str) -> None:
        """Clear the stored custom name for a playlist ID."""
        self._stored_names.pop(playlist_id, None)
        self.async_write_ha_state()