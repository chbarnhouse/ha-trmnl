"""TRMNL services for Home Assistant."""
import logging
from typing import Dict, Any, Optional
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.exceptions import ServiceValidationError

from .api import TRMNLApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Service schemas
DEVICE_UPDATE_SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
    vol.Optional("sleep_start"): cv.string,
    vol.Optional("sleep_stop"): cv.string,
    vol.Optional("refresh_rate"): vol.Coerce(int),
    vol.Optional("image_timeout"): vol.Coerce(int),
    vol.Optional("firmware_update"): cv.boolean,
})

SCREEN_CREATE_SCHEMA = vol.Schema({
    vol.Required("model_id"): vol.Coerce(int),
    vol.Required("name"): cv.string,
    vol.Required("label"): cv.string,
    vol.Optional("content"): cv.string,
    vol.Optional("uri"): cv.string,
    vol.Optional("data"): dict,
    vol.Optional("preprocessed"): cv.boolean,
})

SCREEN_UPDATE_SCHEMA = vol.Schema({
    vol.Required("screen_id"): cv.string,
    vol.Optional("name"): cv.string,
    vol.Optional("label"): cv.string,
    vol.Optional("content"): cv.string,
    vol.Optional("uri"): cv.string,
    vol.Optional("data"): dict,
    vol.Optional("preprocessed"): cv.boolean,
})

MODEL_CREATE_SCHEMA = vol.Schema({
    vol.Required("name"): cv.string,
    vol.Optional("label"): cv.string,
    vol.Optional("description"): cv.string,
    vol.Optional("width"): vol.Coerce(int),
    vol.Optional("height"): vol.Coerce(int),
    vol.Optional("bit_depth"): vol.Coerce(int),
})

PLAYLIST_ASSIGN_SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
    vol.Required("playlist_id"): cv.string,
})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up TRMNL services."""
    
    async def handle_refresh_device(call: ServiceCall) -> None:
        """Handle device refresh service call."""
        device_id = call.data.get("device_id")
        
        # Find the API instance from any integration entry
        api = None
        for entry_id, entry_data in hass.data[DOMAIN].items():
            if isinstance(entry_data, dict) and "api" in entry_data:
                api = entry_data["api"]
                break
        
        if not api:
            raise ServiceValidationError("No TRMNL integration configured")
        
        success = await api.refresh_device(device_id)
        if not success:
            raise ServiceValidationError(f"Failed to refresh device {device_id}")
    
    async def handle_update_device(call: ServiceCall) -> None:
        """Handle device update service call."""
        device_id = call.data.get("device_id")
        
        # Find the API instance
        api = None
        for entry_id, entry_data in hass.data[DOMAIN].items():
            if isinstance(entry_data, dict) and "api" in entry_data:
                api = entry_data["api"]
                break
        
        if not api:
            raise ServiceValidationError("No TRMNL integration configured")
        
        # Build update dictionary from call data
        updates = {}
        if "sleep_start" in call.data:
            updates["sleep_start_at"] = call.data["sleep_start"]
        if "sleep_stop" in call.data:
            updates["sleep_stop_at"] = call.data["sleep_stop"]
        if "refresh_rate" in call.data:
            updates["refresh_rate"] = call.data["refresh_rate"]
        if "image_timeout" in call.data:
            updates["image_timeout"] = call.data["image_timeout"]
        if "firmware_update" in call.data:
            updates["firmware_update"] = call.data["firmware_update"]
        
        if not updates:
            raise ServiceValidationError("No update fields provided")
        
        success = await api.update_device(device_id, updates)
        if not success:
            raise ServiceValidationError(f"Failed to update device {device_id}")
    
    async def handle_create_screen(call: ServiceCall) -> None:
        """Handle screen creation service call."""
        # Find the API instance
        api = None
        for entry_id, entry_data in hass.data[DOMAIN].items():
            if isinstance(entry_data, dict) and "api" in entry_data:
                api = entry_data["api"]
                break
        
        if not api:
            raise ServiceValidationError("No TRMNL integration configured")
        
        screen_data = {
            "model_id": call.data["model_id"],
            "name": call.data["name"],
            "label": call.data["label"],
        }
        
        # Add optional fields
        for field in ["content", "uri", "data", "preprocessed"]:
            if field in call.data:
                screen_data[field] = call.data[field]
        
        result = await api.create_screen(screen_data)
        if not result:
            raise ServiceValidationError("Failed to create screen")
    
    async def handle_update_screen(call: ServiceCall) -> None:
        """Handle screen update service call."""
        screen_id = call.data.get("screen_id")
        
        # Find the API instance
        api = None
        for entry_id, entry_data in hass.data[DOMAIN].items():
            if isinstance(entry_data, dict) and "api" in entry_data:
                api = entry_data["api"]
                break
        
        if not api:
            raise ServiceValidationError("No TRMNL integration configured")
        
        # Build update dictionary from call data
        updates = {}
        for field in ["name", "label", "content", "uri", "data", "preprocessed"]:
            if field in call.data:
                updates[field] = call.data[field]
        
        if not updates:
            raise ServiceValidationError("No update fields provided")
        
        success = await api.update_screen(screen_id, updates)
        if not success:
            raise ServiceValidationError(f"Failed to update screen {screen_id}")
    
    async def handle_delete_screen(call: ServiceCall) -> None:
        """Handle screen deletion service call."""
        screen_id = call.data.get("screen_id")
        
        # Find the API instance
        api = None
        for entry_id, entry_data in hass.data[DOMAIN].items():
            if isinstance(entry_data, dict) and "api" in entry_data:
                api = entry_data["api"]
                break
        
        if not api:
            raise ServiceValidationError("No TRMNL integration configured")
        
        success = await api.delete_screen(screen_id)
        if not success:
            raise ServiceValidationError(f"Failed to delete screen {screen_id}")
    
    async def handle_create_model(call: ServiceCall) -> None:
        """Handle model creation service call."""
        # Find the API instance
        api = None
        for entry_id, entry_data in hass.data[DOMAIN].items():
            if isinstance(entry_data, dict) and "api" in entry_data:
                api = entry_data["api"]
                break
        
        if not api:
            raise ServiceValidationError("No TRMNL integration configured")
        
        model_data = {"name": call.data["name"]}
        
        # Add optional fields
        for field in ["label", "description", "width", "height", "bit_depth"]:
            if field in call.data:
                model_data[field] = call.data[field]
        
        result = await api.create_model(model_data)
        if not result:
            raise ServiceValidationError("Failed to create model")
    
    async def handle_assign_playlist(call: ServiceCall) -> None:
        """Handle playlist assignment service call."""
        device_id = call.data.get("device_id")
        playlist_id = call.data.get("playlist_id")
        
        # Find the API instance
        api = None
        for entry_id, entry_data in hass.data[DOMAIN].items():
            if isinstance(entry_data, dict) and "api" in entry_data:
                api = entry_data["api"]
                break
        
        if not api:
            raise ServiceValidationError("No TRMNL integration configured")
        
        success = await api.assign_device_to_playlist(device_id, playlist_id)
        if not success:
            raise ServiceValidationError(f"Failed to assign device {device_id} to playlist {playlist_id}")
    
    # Register services
    hass.services.async_register(
        DOMAIN, "refresh_device", handle_refresh_device,
        schema=vol.Schema({vol.Required("device_id"): cv.string})
    )
    
    hass.services.async_register(
        DOMAIN, "update_device", handle_update_device,
        schema=DEVICE_UPDATE_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, "create_screen", handle_create_screen,
        schema=SCREEN_CREATE_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, "update_screen", handle_update_screen,
        schema=SCREEN_UPDATE_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, "delete_screen", handle_delete_screen,
        schema=vol.Schema({vol.Required("screen_id"): cv.string})
    )
    
    hass.services.async_register(
        DOMAIN, "create_model", handle_create_model,
        schema=MODEL_CREATE_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, "assign_playlist", handle_assign_playlist,
        schema=PLAYLIST_ASSIGN_SCHEMA
    )
    
    _LOGGER.info("TRMNL services registered")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload TRMNL services."""
    services = [
        "refresh_device",
        "update_device", 
        "create_screen",
        "update_screen",
        "delete_screen",
        "create_model",
        "assign_playlist",
    ]
    
    for service in services:
        hass.services.async_remove(DOMAIN, service)
    
    _LOGGER.info("TRMNL services unloaded")