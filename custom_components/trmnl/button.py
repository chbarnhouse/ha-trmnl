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
        buttons.extend([
            TRMNLRefreshButton(api, device, device_id, models),
            TRMNLSavePlaylistNameButton(api, device, device_id, models),
            TRMNLResetPlaylistNameButton(api, device, device_id, models),
        ])
    
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
        try:
            _LOGGER.error("BUTTON PRESSED! Refreshing device %s via button press", self._device_id)
            print(f"TRMNL DEBUG: Button pressed for device {self._device_id}")
            success = await self._api.refresh_device(self._device_id)
            if success:
                _LOGGER.error("BUTTON SUCCESS! Device %s refresh completed successfully", self._device_id)
                print(f"TRMNL DEBUG: Refresh successful for {self._device_id}")
            else:
                _LOGGER.error("BUTTON FAILED! Device %s refresh failed", self._device_id)
                print(f"TRMNL DEBUG: Refresh failed for {self._device_id}")
        except Exception as e:
            _LOGGER.error("BUTTON EXCEPTION! Error in async_press for device %s: %s", self._device_id, e)
            print(f"TRMNL DEBUG: Exception in button press: {e}")
            raise


class TRMNLSavePlaylistNameButton(TRMNLButtonBase):
    """Save playlist name button."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the save playlist name button."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Save Playlist Name"
        self._attr_unique_id = f"{device_id}_save_playlist_name"
        self._attr_icon = "mdi:content-save"
    
    async def async_press(self) -> None:
        """Save the current playlist name from text entity."""
        try:
            from homeassistant.helpers import entity_registry as er
            
            # Get the text entity for playlist name
            ent_reg = er.async_get(self.hass)
            text_entity_id = f"text.trmnl_{self._device_id.lower()}_playlist_name"
            text_entity = ent_reg.async_get(text_entity_id)
            
            if not text_entity:
                _LOGGER.warning("Could not find playlist name text entity: %s", text_entity_id)
                return
            
            # Get the current value from the text entity
            text_state = self.hass.states.get(text_entity_id)
            if not text_state:
                _LOGGER.warning("Could not get state for text entity: %s", text_entity_id)
                return
            
            new_name = text_state.state
            current_playlist_id = self._device.get('playlist_id')
            
            if not current_playlist_id:
                _LOGGER.warning("No playlist assigned to device %s", self._device_id)
                return
            
            # Update the playlist name via API
            success = await self._api.update_playlist(str(current_playlist_id), {"label": new_name})
            
            if success:
                _LOGGER.info("Successfully saved playlist name '%s' for playlist %s", new_name, current_playlist_id)
                
                # Update the select entity options
                select_entity_id = f"select.trmnl_{self._device_id.lower()}_playlist"
                await self._update_select_entity_options(select_entity_id, current_playlist_id, new_name)
                
            else:
                _LOGGER.error("Failed to save playlist name for playlist %s", current_playlist_id)
                
        except Exception as e:
            _LOGGER.error("Error saving playlist name for device %s: %s", self._device_id, e)
    
    async def _update_select_entity_options(self, select_entity_id: str, playlist_id: int, new_name: str) -> None:
        """Update the select entity options with the new playlist name."""
        try:
            # This would need to trigger a refresh of the select entity
            # For now, just log the change
            _LOGGER.info("Playlist %s renamed to '%s' - select entity will update on next refresh", playlist_id, new_name)
        except Exception as e:
            _LOGGER.error("Error updating select entity options: %s", e)


class TRMNLResetPlaylistNameButton(TRMNLButtonBase):
    """Reset playlist name button."""
    
    def __init__(self, api: TRMNLApi, device: dict, device_id: str, models: dict = None) -> None:
        """Initialize the reset playlist name button."""
        super().__init__(api, device, device_id, models)
        self._attr_name = "Reset Playlist Name"
        self._attr_unique_id = f"{device_id}_reset_playlist_name"
        self._attr_icon = "mdi:undo"
    
    async def async_press(self) -> None:
        """Reset the current playlist name to default format."""
        try:
            current_playlist_id = self._device.get('playlist_id')
            
            if not current_playlist_id:
                _LOGGER.warning("No playlist assigned to device %s", self._device_id)
                return
            
            # Reset to default name format
            default_name = f"Playlist {current_playlist_id}"
            
            # Update the playlist name via API
            success = await self._api.update_playlist(str(current_playlist_id), {"label": default_name})
            
            if success:
                _LOGGER.info("Successfully reset playlist %s name to '%s'", current_playlist_id, default_name)
                
                # Update the text entity to show the reset name
                from homeassistant.helpers import entity_registry as er
                
                ent_reg = er.async_get(self.hass)
                text_entity_id = f"text.trmnl_{self._device_id.lower()}_playlist_name"
                
                # Trigger an update to the text entity
                await self.hass.services.async_call(
                    "text", "set_value",
                    {"entity_id": text_entity_id, "value": default_name}
                )
                
            else:
                _LOGGER.error("Failed to reset playlist name for playlist %s", current_playlist_id)
                
        except Exception as e:
            _LOGGER.error("Error resetting playlist name for device %s: %s", self._device_id, e)