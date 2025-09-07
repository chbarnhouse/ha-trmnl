"""Support for TRMNL select entities."""
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
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
    """Set up TRMNL select entities from a config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    api = entry_data["api"]
    devices = entry_data["devices"]
    models = entry_data.get("models", {})
    
    # Get playlists with custom labels
    playlists = await api.get_playlists(hass)
    
    selects = []
    for device in devices:
        device_id = device.get('friendly_id', str(device.get('id')))
        selects.append(TRMNLPlaylistSelect(api, device, device_id, models, playlists))
    
    async_add_entities(selects)


class TRMNLSelectBase(SelectEntity):
    """Base class for TRMNL select entities."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the select entity."""
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


class TRMNLPlaylistSelect(TRMNLSelectBase):
    """TRMNL playlist selection entity."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None, playlists: list = None) -> None:
        """Initialize the playlist select entity."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Playlist"
        self._attr_unique_id = f"{device_id}_playlist"
        self._attr_icon = "mdi:playlist-play"
        self._playlists = playlists or []
        
        # Build options from playlists
        self._update_options()
            
        _LOGGER.info("Created playlist select for device %s with options: %s", device_id, self._attr_options)
    
    def _update_options(self):
        """Update the available options and playlist mapping."""
        self._attr_options = []
        self._playlist_map = {}  # Maps display names to IDs
        
        if self._playlists:
            for playlist in self._playlists:
                playlist_id = str(playlist.get('id', ''))
                playlist_name = playlist.get('name', f'Playlist {playlist_id}')
                self._attr_options.append(playlist_name)
                self._playlist_map[playlist_name] = playlist_id
        else:
            self._attr_options = ["No playlists available"]
    
    async def async_refresh_playlists(self):
        """Refresh the playlist options from the server."""
        try:
            _LOGGER.debug("Refreshing playlists for device %s", self._device_id)
            self._playlists = await self._api.get_playlists(self.hass)
            self._update_options()
            self.async_write_ha_state()
            _LOGGER.info("Refreshed playlists for device %s: %s", self._device_id, self._attr_options)
        except Exception as e:
            _LOGGER.error("Error refreshing playlists for device %s: %s", self._device_id, e)
    
    @property
    def current_option(self) -> str:
        """Return the currently selected playlist."""
        # Try to get current playlist from device data
        current_playlist_id = self._device.get('playlist_id')
        
        if current_playlist_id:
            # Find playlist name by ID
            for name, pid in self._playlist_map.items():
                if pid == str(current_playlist_id):
                    return name
        
        # Default to first option if no current playlist or not found
        return self._attr_options[0] if self._attr_options else None
    
    async def async_select_option(self, option: str) -> None:
        """Select a playlist option."""
        if option in self._playlist_map:
            playlist_id = self._playlist_map[option]
            _LOGGER.info("Assigning device %s to playlist '%s' (ID: %s)", self._device_id, option, playlist_id)
            
            success = await self._api.assign_device_to_playlist(self._device_id, playlist_id)
            if success:
                # Update device data cache
                self._device['playlist_id'] = playlist_id
                self.async_write_ha_state()
                _LOGGER.info("Successfully assigned device %s to playlist '%s'", self._device_id, option)
            else:
                _LOGGER.error("Failed to assign device %s to playlist '%s'", self._device_id, option)
        else:
            _LOGGER.error("Invalid playlist option '%s' for device %s", option, self._device_id)