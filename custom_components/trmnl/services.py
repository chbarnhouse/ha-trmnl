"""TRMNL services for Home Assistant - Complete Terminus API Coverage."""
import logging
from typing import Dict, Any, Optional
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.exceptions import ServiceValidationError

from .api import TRMNLApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# === Core Device API Services ===
DEVICE_REFRESH_SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
})

DEVICE_UPDATE_SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
    vol.Optional("sleep_start"): cv.string,
    vol.Optional("sleep_stop"): cv.string,
    vol.Optional("refresh_rate"): vol.Coerce(int),
    vol.Optional("image_timeout"): vol.Coerce(int),
    vol.Optional("firmware_update"): cv.boolean,
    vol.Optional("label"): cv.string,
    vol.Optional("proxy"): cv.boolean,
})

DEVICE_CREATE_SCHEMA = vol.Schema({
    vol.Required("friendly_id"): cv.string,
    vol.Required("mac_address"): cv.string,
    vol.Required("model_id"): vol.Coerce(int),
    vol.Optional("label"): cv.string,
    vol.Optional("api_key"): cv.string,
    vol.Optional("playlist_id"): vol.Coerce(int),
})

# === Display API Services ===
DISPLAY_UPDATE_SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
    vol.Optional("content"): cv.string,
    vol.Optional("uri"): cv.string,
    vol.Optional("image_url"): cv.string,
    vol.Optional("base64_image"): cv.string,
    vol.Optional("timeout"): vol.Coerce(int),
    vol.Optional("preprocessed"): cv.boolean,
})

# === Screen Management Services ===
SCREEN_CREATE_SCHEMA = vol.Schema({
    vol.Required("model_id"): vol.Coerce(int),
    vol.Required("name"): cv.string,
    vol.Required("label"): cv.string,
    vol.Optional("content"): cv.string,
    vol.Optional("uri"): cv.string,
    vol.Optional("image_url"): cv.string,
    vol.Optional("data"): dict,
    vol.Optional("preprocessed"): cv.boolean,
    vol.Optional("timeout"): vol.Coerce(int),
})

SCREEN_UPDATE_SCHEMA = vol.Schema({
    vol.Required("screen_id"): cv.string,
    vol.Optional("name"): cv.string,
    vol.Optional("label"): cv.string,
    vol.Optional("content"): cv.string,
    vol.Optional("uri"): cv.string,
    vol.Optional("image_url"): cv.string,
    vol.Optional("data"): dict,
    vol.Optional("preprocessed"): cv.boolean,
    vol.Optional("timeout"): vol.Coerce(int),
})

SCREEN_DELETE_SCHEMA = vol.Schema({
    vol.Required("screen_id"): cv.string,
})

# === Model Management Services ===
MODEL_CREATE_SCHEMA = vol.Schema({
    vol.Required("name"): cv.string,
    vol.Optional("label"): cv.string,
    vol.Optional("description"): cv.string,
    vol.Optional("width"): vol.Coerce(int),
    vol.Optional("height"): vol.Coerce(int),
    vol.Optional("bit_depth"): vol.Coerce(int),
    vol.Optional("color_mode"): cv.string,
})

MODEL_UPDATE_SCHEMA = vol.Schema({
    vol.Required("model_id"): cv.string,
    vol.Optional("name"): cv.string,
    vol.Optional("label"): cv.string,
    vol.Optional("description"): cv.string,
    vol.Optional("width"): vol.Coerce(int),
    vol.Optional("height"): vol.Coerce(int),
    vol.Optional("bit_depth"): vol.Coerce(int),
    vol.Optional("color_mode"): cv.string,
})

MODEL_DELETE_SCHEMA = vol.Schema({
    vol.Required("model_id"): cv.string,
})

# === Playlist Management Services ===
PLAYLIST_CREATE_SCHEMA = vol.Schema({
    vol.Required("name"): cv.string,
    vol.Optional("label"): cv.string,
    vol.Optional("description"): cv.string,
    vol.Optional("screen_ids"): [cv.string],
    vol.Optional("auto_advance"): cv.boolean,
    vol.Optional("advance_interval"): vol.Coerce(int),
})

PLAYLIST_UPDATE_SCHEMA = vol.Schema({
    vol.Required("playlist_id"): cv.string,
    vol.Optional("name"): cv.string,
    vol.Optional("label"): cv.string,
    vol.Optional("description"): cv.string,
    vol.Optional("screen_ids"): [cv.string],
    vol.Optional("auto_advance"): cv.boolean,
    vol.Optional("advance_interval"): vol.Coerce(int),
})

PLAYLIST_DELETE_SCHEMA = vol.Schema({
    vol.Required("playlist_id"): cv.string,
})

PLAYLIST_ASSIGN_SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
    vol.Required("playlist_id"): cv.string,
})

PLAYLIST_ADD_SCREEN_SCHEMA = vol.Schema({
    vol.Required("playlist_id"): cv.string,
    vol.Required("screen_id"): cv.string,
    vol.Optional("position"): vol.Coerce(int),
})

PLAYLIST_REMOVE_SCREEN_SCHEMA = vol.Schema({
    vol.Required("playlist_id"): cv.string,
    vol.Required("screen_id"): cv.string,
})

# === Log Management Services ===
DEVICE_LOG_SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
    vol.Optional("log_level"): cv.string,
    vol.Optional("message"): cv.string,
    vol.Optional("component"): cv.string,
    vol.Optional("additional_data"): dict,
})

# === Setup/Configuration Services ===
DEVICE_SETUP_SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
    vol.Optional("force_setup"): cv.boolean,
})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up comprehensive TRMNL services for all Terminus API endpoints."""
    
    def get_api_instance() -> TRMNLApi:
        """Get the first available API instance from integration entries."""
        for entry_id, entry_data in hass.data[DOMAIN].items():
            if isinstance(entry_data, dict) and "api" in entry_data:
                return entry_data["api"]
        raise ServiceValidationError("No TRMNL integration configured")
    
    def get_device_friendly_id(device_id: str) -> str:
        """Convert HA device ID to TRMNL device friendly_id."""
        device_registry = dr.async_get(hass)
        device = device_registry.async_get(device_id)
        
        if not device:
            raise ServiceValidationError(f"Device {device_id} not found")
        
        # Check if this is a TRMNL device
        trmnl_identifier = None
        for identifier in device.identifiers:
            if identifier[0] == DOMAIN:
                trmnl_identifier = identifier[1]
                break
        
        if not trmnl_identifier:
            raise ServiceValidationError(f"Device {device_id} is not a TRMNL device")
        
        return trmnl_identifier
    
    # === DEVICE MANAGEMENT SERVICES ===
    
    async def handle_refresh_device(call: ServiceCall) -> None:
        """Refresh a specific device to check for new content."""
        api = get_api_instance()
        device_friendly_id = get_device_friendly_id(call.data["device_id"])
        
        success = await api.refresh_device(device_friendly_id)
        if not success:
            raise ServiceValidationError(f"Failed to refresh device {device_friendly_id}")
        _LOGGER.info("Successfully refreshed device %s", device_friendly_id)
    
    async def handle_update_device(call: ServiceCall) -> None:
        """Update device configuration settings."""
        api = get_api_instance()
        device_friendly_id = get_device_friendly_id(call.data["device_id"])
        
        # Build update dictionary from call data
        updates = {}
        field_mappings = {
            "sleep_start": "sleep_start_at",
            "sleep_stop": "sleep_stop_at", 
            "refresh_rate": "refresh_rate",
            "image_timeout": "image_timeout",
            "firmware_update": "firmware_update",
            "label": "label",
            "proxy": "proxy",
        }
        
        for call_field, api_field in field_mappings.items():
            if call_field in call.data:
                updates[api_field] = call.data[call_field]
        
        if not updates:
            raise ServiceValidationError("No update fields provided")
        
        success = await api.update_device(device_friendly_id, updates)
        if not success:
            raise ServiceValidationError(f"Failed to update device {device_friendly_id}")
        _LOGGER.info("Successfully updated device %s", device_friendly_id)
    
    async def handle_create_device(call: ServiceCall) -> None:
        """Create a new device in Terminus."""
        api = get_api_instance()
        
        device_data = {
            "friendly_id": call.data["friendly_id"],
            "mac_address": call.data["mac_address"],
            "model_id": call.data["model_id"],
        }
        
        # Add optional fields
        optional_fields = ["label", "api_key", "playlist_id"]
        for field in optional_fields:
            if field in call.data:
                device_data[field] = call.data[field]
        
        result = await api.create_device(device_data)
        if not result:
            raise ServiceValidationError("Failed to create device")
        _LOGGER.info("Successfully created device %s", call.data["friendly_id"])
    
    # === DISPLAY API SERVICES ===
    
    async def handle_update_display(call: ServiceCall) -> None:
        """Update device display content directly."""
        api = get_api_instance()
        
        # Debug logging
        _LOGGER.error("SERVICE DEBUG: Raw call data: %s", call.data)
        _LOGGER.error("SERVICE DEBUG: device_id from call: %s (type: %s)", call.data.get("device_id"), type(call.data.get("device_id")))
        
        device_friendly_id = get_device_friendly_id(call.data["device_id"])
        _LOGGER.error("SERVICE DEBUG: Converted friendly_id: %s", device_friendly_id)
        
        display_data = {}
        if "content" in call.data:
            display_data["content"] = call.data["content"]
        if "uri" in call.data:
            display_data["uri"] = call.data["uri"]
        if "image_url" in call.data:
            display_data["image_url"] = call.data["image_url"]
        if "base64_image" in call.data:
            display_data["base64_image"] = call.data["base64_image"]
        if "timeout" in call.data:
            display_data["timeout"] = call.data["timeout"]
        if "preprocessed" in call.data:
            display_data["preprocessed"] = call.data["preprocessed"]
        
        success = await api.update_display(device_friendly_id, display_data)
        if not success:
            raise ServiceValidationError(f"Failed to update display for device {device_friendly_id}")
        _LOGGER.info("Successfully updated display for device %s", device_friendly_id)
    
    # === SCREEN MANAGEMENT SERVICES ===
    
    async def handle_create_screen(call: ServiceCall) -> None:
        """Create a new screen template."""
        api = get_api_instance()
        
        screen_data = {
            "model_id": call.data["model_id"],
            "name": call.data["name"],
            "label": call.data["label"],
        }
        
        # Add optional fields
        optional_fields = ["content", "uri", "image_url", "data", "preprocessed", "timeout"]
        for field in optional_fields:
            if field in call.data:
                screen_data[field] = call.data[field]
        
        result = await api.create_screen(screen_data)
        if not result:
            raise ServiceValidationError("Failed to create screen")
        _LOGGER.info("Successfully created screen %s", call.data["name"])
    
    async def handle_update_screen(call: ServiceCall) -> None:
        """Update an existing screen template."""
        api = get_api_instance()
        screen_id = call.data["screen_id"]
        
        # Build update dictionary from call data
        updates = {}
        optional_fields = ["name", "label", "content", "uri", "image_url", "data", "preprocessed", "timeout"]
        for field in optional_fields:
            if field in call.data:
                updates[field] = call.data[field]
        
        if not updates:
            raise ServiceValidationError("No update fields provided")
        
        success = await api.update_screen(screen_id, updates)
        if not success:
            raise ServiceValidationError(f"Failed to update screen {screen_id}")
        _LOGGER.info("Successfully updated screen %s", screen_id)
    
    async def handle_delete_screen(call: ServiceCall) -> None:
        """Delete a screen template."""
        api = get_api_instance()
        screen_id = call.data["screen_id"]
        
        success = await api.delete_screen(screen_id)
        if not success:
            raise ServiceValidationError(f"Failed to delete screen {screen_id}")
        _LOGGER.info("Successfully deleted screen %s", screen_id)
    
    # === MODEL MANAGEMENT SERVICES ===
    
    async def handle_create_model(call: ServiceCall) -> None:
        """Create a new device model definition."""
        api = get_api_instance()
        
        model_data = {"name": call.data["name"]}
        
        # Add optional fields
        optional_fields = ["label", "description", "width", "height", "bit_depth", "color_mode"]
        for field in optional_fields:
            if field in call.data:
                model_data[field] = call.data[field]
        
        result = await api.create_model(model_data)
        if not result:
            raise ServiceValidationError("Failed to create model")
        _LOGGER.info("Successfully created model %s", call.data["name"])
    
    async def handle_update_model(call: ServiceCall) -> None:
        """Update an existing device model definition."""
        api = get_api_instance()
        model_id = call.data["model_id"]
        
        # Build update dictionary from call data
        updates = {}
        optional_fields = ["name", "label", "description", "width", "height", "bit_depth", "color_mode"]
        for field in optional_fields:
            if field in call.data:
                updates[field] = call.data[field]
        
        if not updates:
            raise ServiceValidationError("No update fields provided")
        
        success = await api.update_model(model_id, updates)
        if not success:
            raise ServiceValidationError(f"Failed to update model {model_id}")
        _LOGGER.info("Successfully updated model %s", model_id)
    
    async def handle_delete_model(call: ServiceCall) -> None:
        """Delete a device model definition."""
        api = get_api_instance()
        model_id = call.data["model_id"]
        
        success = await api.delete_model(model_id)
        if not success:
            raise ServiceValidationError(f"Failed to delete model {model_id}")
        _LOGGER.info("Successfully deleted model %s", model_id)
    
    # === PLAYLIST MANAGEMENT SERVICES ===
    
    async def handle_create_playlist(call: ServiceCall) -> None:
        """Create a new playlist."""
        api = get_api_instance()
        
        playlist_data = {"name": call.data["name"]}
        
        # Add optional fields
        optional_fields = ["label", "description", "screen_ids", "auto_advance", "advance_interval"]
        for field in optional_fields:
            if field in call.data:
                playlist_data[field] = call.data[field]
        
        result = await api.create_playlist(playlist_data)
        if not result:
            raise ServiceValidationError("Failed to create playlist")
        _LOGGER.info("Successfully created playlist %s", call.data["name"])
    
    async def handle_update_playlist(call: ServiceCall) -> None:
        """Update an existing playlist."""
        api = get_api_instance()
        playlist_id = call.data["playlist_id"]
        
        # Build update dictionary from call data
        updates = {}
        optional_fields = ["name", "label", "description", "screen_ids", "auto_advance", "advance_interval"]
        for field in optional_fields:
            if field in call.data:
                updates[field] = call.data[field]
        
        if not updates:
            raise ServiceValidationError("No update fields provided")
        
        success = await api.update_playlist(playlist_id, updates)
        if not success:
            raise ServiceValidationError(f"Failed to update playlist {playlist_id}")
        _LOGGER.info("Successfully updated playlist %s", playlist_id)
    
    async def handle_delete_playlist(call: ServiceCall) -> None:
        """Delete a playlist."""
        api = get_api_instance()
        playlist_id = call.data["playlist_id"]
        
        success = await api.delete_playlist(playlist_id)
        if not success:
            raise ServiceValidationError(f"Failed to delete playlist {playlist_id}")
        _LOGGER.info("Successfully deleted playlist %s", playlist_id)
    
    async def handle_assign_playlist(call: ServiceCall) -> None:
        """Assign a playlist to a device."""
        api = get_api_instance()
        device_friendly_id = get_device_friendly_id(call.data["device_id"])
        playlist_id = call.data["playlist_id"]
        
        success = await api.assign_device_to_playlist(device_friendly_id, playlist_id)
        if not success:
            raise ServiceValidationError(f"Failed to assign device {device_friendly_id} to playlist {playlist_id}")
        _LOGGER.info("Successfully assigned device %s to playlist %s", device_friendly_id, playlist_id)
    
    async def handle_playlist_add_screen(call: ServiceCall) -> None:
        """Add a screen to a playlist."""
        api = get_api_instance()
        playlist_id = call.data["playlist_id"]
        screen_id = call.data["screen_id"]
        position = call.data.get("position")
        
        success = await api.add_screen_to_playlist(playlist_id, screen_id, position)
        if not success:
            raise ServiceValidationError(f"Failed to add screen {screen_id} to playlist {playlist_id}")
        _LOGGER.info("Successfully added screen %s to playlist %s", screen_id, playlist_id)
    
    async def handle_playlist_remove_screen(call: ServiceCall) -> None:
        """Remove a screen from a playlist."""
        api = get_api_instance()
        playlist_id = call.data["playlist_id"]
        screen_id = call.data["screen_id"]
        
        success = await api.remove_screen_from_playlist(playlist_id, screen_id)
        if not success:
            raise ServiceValidationError(f"Failed to remove screen {screen_id} from playlist {playlist_id}")
        _LOGGER.info("Successfully removed screen %s from playlist %s", screen_id, playlist_id)
    
    # === LOG MANAGEMENT SERVICES ===
    
    async def handle_device_log(call: ServiceCall) -> None:
        """Send log entry for a device."""
        api = get_api_instance()
        device_friendly_id = get_device_friendly_id(call.data["device_id"])
        
        log_data = {}
        if "log_level" in call.data:
            log_data["level"] = call.data["log_level"]
        if "message" in call.data:
            log_data["message"] = call.data["message"]
        if "component" in call.data:
            log_data["component"] = call.data["component"]
        if "additional_data" in call.data:
            log_data.update(call.data["additional_data"])
        
        success = await api.send_device_log(device_friendly_id, log_data)
        if not success:
            raise ServiceValidationError(f"Failed to send log for device {device_friendly_id}")
        _LOGGER.info("Successfully sent log for device %s", device_friendly_id)
    
    # === SETUP/CONFIGURATION SERVICES ===
    
    async def handle_device_setup(call: ServiceCall) -> None:
        """Trigger device setup process."""
        api = get_api_instance()
        device_friendly_id = get_device_friendly_id(call.data["device_id"])
        force_setup = call.data.get("force_setup", False)
        
        result = await api.setup_device(device_friendly_id, force_setup)
        if not result:
            raise ServiceValidationError(f"Failed to setup device {device_friendly_id}")
        _LOGGER.info("Successfully initiated setup for device %s", device_friendly_id)
    
    # === REGISTER ALL SERVICES ===
    
    services = [
        # Device Management
        ("refresh_device", handle_refresh_device, DEVICE_REFRESH_SCHEMA),
        ("update_device", handle_update_device, DEVICE_UPDATE_SCHEMA),
        ("create_device", handle_create_device, DEVICE_CREATE_SCHEMA),
        
        # Display API
        ("update_display", handle_update_display, DISPLAY_UPDATE_SCHEMA),
        
        # Screen Management
        ("create_screen", handle_create_screen, SCREEN_CREATE_SCHEMA),
        ("update_screen", handle_update_screen, SCREEN_UPDATE_SCHEMA),
        ("delete_screen", handle_delete_screen, SCREEN_DELETE_SCHEMA),
        
        # Model Management
        ("create_model", handle_create_model, MODEL_CREATE_SCHEMA),
        ("update_model", handle_update_model, MODEL_UPDATE_SCHEMA),
        ("delete_model", handle_delete_model, MODEL_DELETE_SCHEMA),
        
        # Playlist Management
        ("create_playlist", handle_create_playlist, PLAYLIST_CREATE_SCHEMA),
        ("update_playlist", handle_update_playlist, PLAYLIST_UPDATE_SCHEMA),
        ("delete_playlist", handle_delete_playlist, PLAYLIST_DELETE_SCHEMA),
        ("assign_playlist", handle_assign_playlist, PLAYLIST_ASSIGN_SCHEMA),
        ("playlist_add_screen", handle_playlist_add_screen, PLAYLIST_ADD_SCREEN_SCHEMA),
        ("playlist_remove_screen", handle_playlist_remove_screen, PLAYLIST_REMOVE_SCREEN_SCHEMA),
        
        # Logging
        ("device_log", handle_device_log, DEVICE_LOG_SCHEMA),
        
        # Setup
        ("device_setup", handle_device_setup, DEVICE_SETUP_SCHEMA),
    ]
    
    for service_name, handler, schema in services:
        hass.services.async_register(DOMAIN, service_name, handler, schema=schema)
        _LOGGER.debug("Registered service: %s", service_name)
    
    _LOGGER.info("Successfully registered %d TRMNL services covering all Terminus API endpoints", len(services))


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload all TRMNL services."""
    services = [
        # Device Management
        "refresh_device", "update_device", "create_device",
        # Display API
        "update_display",
        # Screen Management
        "create_screen", "update_screen", "delete_screen",
        # Model Management
        "create_model", "update_model", "delete_model",
        # Playlist Management
        "create_playlist", "update_playlist", "delete_playlist", 
        "assign_playlist", "playlist_add_screen", "playlist_remove_screen",
        # Logging
        "device_log",
        # Setup
        "device_setup",
    ]
    
    for service in services:
        hass.services.async_remove(DOMAIN, service)
    
    _LOGGER.info("Unloaded all TRMNL services")