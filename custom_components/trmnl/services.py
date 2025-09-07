"""TRMNL services for Home Assistant - Complete Terminus API Coverage."""
import logging
from typing import Dict, Any, Optional
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, device_registry as dr, entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.exceptions import ServiceValidationError

from .api import TRMNLApi
from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION

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

# === Playlist Configuration Service ===
CONFIGURE_PLAYLISTS_SCHEMA = vol.Schema({
    vol.Required("action"): vol.In(["add", "remove", "set_label", "reset_label", "list"]),
    vol.Optional("playlist_id"): cv.string,
    vol.Optional("label"): cv.string,
})

# === Playlist Naming Services ===
UPDATE_PLAYLIST_NAME_SCHEMA = vol.Schema({
    vol.Required("playlist_id"): cv.string,
    vol.Required("name"): cv.string,
})

RESET_PLAYLIST_NAME_SCHEMA = vol.Schema({
    vol.Required("playlist_id"): cv.string,
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
    
    async def refresh_playlist_selects() -> None:
        """Refresh all TRMNL playlist select entities after playlist changes."""
        try:
            entity_reg = er.async_get(hass)
            # Find all TRMNL playlist select entities
            for entity_entry in entity_reg.entities.values():
                if (entity_entry.platform == DOMAIN and 
                    entity_entry.unique_id and 
                    entity_entry.unique_id.endswith("_playlist")):
                    
                    # Try to get the entity object through the component
                    if "select" in hass.data.get("entity_components", {}):
                        select_component = hass.data["entity_components"]["select"]
                        entity_obj = None
                        
                        # Look through all select entities to find our TRMNL playlist selects
                        for entity in select_component.entities:
                            if (hasattr(entity, 'unique_id') and 
                                entity.unique_id == entity_entry.unique_id):
                                entity_obj = entity
                                break
                        
                        if entity_obj and hasattr(entity_obj, 'async_refresh_playlists'):
                            _LOGGER.debug("Refreshing playlist select entity: %s", entity_entry.entity_id)
                            await entity_obj.async_refresh_playlists()
                        else:
                            _LOGGER.debug("Could not find entity object for %s", entity_entry.entity_id)
        except Exception as e:
            _LOGGER.warning("Error refreshing playlist select entities: %s", e)
    
    async def extract_playlist_id(playlist_input: str) -> str:
        """Extract playlist ID from input string, handling multiple formats."""
        import re
        
        playlist_input = str(playlist_input).strip()
        
        # Check if input is in "Name (ID: X)" format
        id_match = re.search(r'\(ID:\s*(\d+)\)', playlist_input)
        if id_match:
            return id_match.group(1)
        
        # Check if input is a numeric ID
        if playlist_input.isdigit():
            return playlist_input
        
        # If input is a playlist name, try to find the ID by looking up playlists
        try:
            api = get_api_instance()
            playlists = await api.get_playlists()
            
            for playlist in playlists:
                playlist_name = playlist.get('name', f"Playlist {playlist.get('id', '')}")
                if playlist_name.lower() == playlist_input.lower():
                    return str(playlist.get('id', ''))
            
            # If we couldn't find a matching name, assume it's an ID
            return playlist_input
            
        except Exception as e:
            _LOGGER.warning("Could not lookup playlist by name: %s", e)
            # Fallback: assume it's an ID
            return playlist_input
    
    def build_dynamic_playlist_schemas(playlists: list) -> tuple:
        """Build schemas with dynamic playlist options."""
        # Create playlist options for the select field
        playlist_options = []
        for playlist in playlists:
            playlist_id = str(playlist.get('id', ''))
            playlist_name = playlist.get('name', f'Playlist {playlist_id}')
            # Use the name as the option value, but include ID for clarity
            playlist_options.append(f"{playlist_name} (ID: {playlist_id})")
        
        # Fallback options if no playlists available
        if not playlist_options:
            playlist_options = ["Playlist 1 (ID: 1)", "Playlist 2 (ID: 2)", "Playlist 3 (ID: 3)"]
        
        UPDATE_PLAYLIST_NAME_SCHEMA = vol.Schema({
            vol.Required("playlist_id"): vol.In(playlist_options),
            vol.Required("name"): cv.string,
        })
        
        RESET_PLAYLIST_NAME_SCHEMA = vol.Schema({
            vol.Required("playlist_id"): vol.In(playlist_options),
        })
        
        return UPDATE_PLAYLIST_NAME_SCHEMA, RESET_PLAYLIST_NAME_SCHEMA
    
    class PlaylistLabelManager:
        """Manages local playlist label mappings."""
        
        def __init__(self, hass: HomeAssistant):
            self.hass = hass
            self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
            self._labels = {}
            
        async def async_load(self):
            """Load playlist labels from storage."""
            data = await self.store.async_load()
            if data is not None:
                self._labels = data.get("labels", {})
            _LOGGER.debug("Loaded playlist labels: %s", self._labels)
            
        async def async_save(self):
            """Save playlist labels to storage."""
            await self.store.async_save({"labels": self._labels})
            _LOGGER.debug("Saved playlist labels: %s", self._labels)
            
        async def set_label(self, playlist_id: str, label: str):
            """Set a custom label for a playlist."""
            playlist_id = str(playlist_id)
            self._labels[playlist_id] = label
            await self.async_save()
            _LOGGER.info("Set playlist %s label to '%s'", playlist_id, label)
            
        async def remove_label(self, playlist_id: str):
            """Remove a custom label for a playlist."""
            playlist_id = str(playlist_id)
            if playlist_id in self._labels:
                del self._labels[playlist_id]
                await self.async_save()
                _LOGGER.info("Removed custom label for playlist %s", playlist_id)
            
        def get_label(self, playlist_id: str) -> str:
            """Get the label for a playlist (custom or default)."""
            playlist_id = str(playlist_id)
            return self._labels.get(playlist_id, f"Playlist {playlist_id}")
            
        def get_all_labels(self) -> Dict[str, str]:
            """Get all custom labels."""
            return dict(self._labels)
            
        def get_all_playlists(self) -> Dict[str, str]:
            """Get all configured playlists (same as get_all_labels for now)."""
            return dict(self._labels)
            
        async def add_playlist(self, playlist_id: str, label: str = None):
            """Add a playlist to the configuration."""
            playlist_id = str(playlist_id)
            if label is None:
                label = f"Playlist {playlist_id}"
            self._labels[playlist_id] = label
            await self.async_save()
            _LOGGER.info("Added playlist %s with label '%s'", playlist_id, label)
            
        async def remove_playlist(self, playlist_id: str):
            """Remove a playlist from the configuration."""
            playlist_id = str(playlist_id)
            if playlist_id in self._labels:
                del self._labels[playlist_id]
                await self.async_save()
                _LOGGER.info("Removed playlist %s from configuration", playlist_id)
    
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
        device_friendly_id = get_device_friendly_id(call.data["device_id"])
        
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
    
    # === PLAYLIST NAMING SERVICES ===
    
    async def handle_update_playlist_name(call: ServiceCall) -> None:
        """Update a playlist name."""
        api = get_api_instance()
        playlist_input = call.data["playlist_id"]
        new_name = call.data["name"]
        
        # Parse playlist ID from the input (handles multiple formats including playlist names)
        playlist_id = await extract_playlist_id(playlist_input)
        
        success = await api.update_playlist(playlist_id, {"label": new_name})
        if not success:
            raise ServiceValidationError(f"Failed to update playlist {playlist_id} name")
        
        # Refresh playlist select entities to show updated names
        await refresh_playlist_selects()
        
        _LOGGER.info("Successfully updated playlist %s name to '%s'", playlist_id, new_name)
    
    async def handle_reset_playlist_name(call: ServiceCall) -> None:
        """Reset a playlist name to default format."""
        api = get_api_instance()
        playlist_input = call.data["playlist_id"]
        
        # Parse playlist ID from the input (handles multiple formats including playlist names)
        playlist_id = await extract_playlist_id(playlist_input)
        default_name = f"Playlist {playlist_id}"
        
        success = await api.update_playlist(playlist_id, {"label": default_name})
        if not success:
            raise ServiceValidationError(f"Failed to reset playlist {playlist_id} name")
        
        # Refresh playlist select entities to show updated names
        await refresh_playlist_selects()
        
        _LOGGER.info("Successfully reset playlist %s name to '%s'", playlist_id, default_name)
    
    # === PLAYLIST LABEL MANAGEMENT SERVICES ===
    
    # Initialize the label manager
    label_manager = PlaylistLabelManager(hass)
    await label_manager.async_load()
    
    # Store label manager globally for API access
    hass.data.setdefault(f"{DOMAIN}_label_manager", label_manager)
    
    async def handle_configure_playlists(call: ServiceCall) -> None:
        """Configure Home Assistant playlists - comprehensive playlist management."""
        try:
            action = call.data["action"]
            playlist_id = call.data.get("playlist_id")
            label = call.data.get("label")
            
            _LOGGER.debug("Configure playlists called with action=%s, playlist_id=%s, label=%s", action, playlist_id, label)
            
            # Get the label manager from hass.data
            current_label_manager = hass.data.get(f"{DOMAIN}_label_manager")
            if not current_label_manager:
                raise ServiceValidationError("Playlist label manager not initialized")
                
        except Exception as e:
            _LOGGER.error("Error in configure_playlists service: %s", e, exc_info=True)
            raise
        
        if action == "add":
            if not playlist_id:
                raise ServiceValidationError("playlist_id is required for add action")
            await current_label_manager.add_playlist(playlist_id, label)
            await refresh_playlist_selects()
            _LOGGER.info("Added playlist %s%s to Home Assistant", playlist_id, f" with label '{label}'" if label else "")
            
        elif action == "remove":
            if not playlist_id:
                raise ServiceValidationError("playlist_id is required for remove action")
            await current_label_manager.remove_playlist(playlist_id)
            await refresh_playlist_selects()
            _LOGGER.info("Removed playlist %s from Home Assistant", playlist_id)
            
        elif action == "set_label":
            if not playlist_id or not label:
                raise ServiceValidationError("Both playlist_id and label are required for set_label action")
            await current_label_manager.set_label(playlist_id, label)
            await refresh_playlist_selects()
            _LOGGER.info("Set playlist %s label to '%s'", playlist_id, label)
            
        elif action == "reset_label":
            if not playlist_id:
                raise ServiceValidationError("playlist_id is required for reset_label action")
            await current_label_manager.remove_label(playlist_id)
            await refresh_playlist_selects()
            _LOGGER.info("Reset playlist %s label to default", playlist_id)
            
        elif action == "list":
            playlists = current_label_manager.get_all_playlists()
            _LOGGER.info("Current configured playlists: %s", playlists)
            
            # Create a persistent notification with the playlist configuration
            notification_message = "**Home Assistant Playlist Configuration:**\n"
            if playlists:
                for playlist_id, playlist_label in playlists.items():
                    notification_message += f"- Playlist {playlist_id}: {playlist_label}\n"
            else:
                notification_message += "No playlists configured in Home Assistant.\nOnly playlists detected from your TRMNL devices will be shown."
            
            # Check if persistent_notification component is available
            if hasattr(hass.components, 'persistent_notification') and hass.components.persistent_notification:
                hass.components.persistent_notification.create(
                    notification_message,
                    title="TRMNL Playlist Configuration",
                    notification_id="trmnl_playlist_configuration"
                )
            else:
                # Fallback: just log the message
                _LOGGER.info("Playlist Configuration: %s", notification_message)
    
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
        
        # Playlist Configuration
        ("configure_playlists", handle_configure_playlists, CONFIGURE_PLAYLISTS_SCHEMA),
        
        # Playlist Naming - TEMPORARILY DISABLED due to Terminus API limitations
        # The /api/playlists/{id} endpoints return HTTP 404, indicating these
        # features are not supported by the current Terminus server
        # ("update_playlist_name", handle_update_playlist_name, None),
        # ("reset_playlist_name", handle_reset_playlist_name, None),
    ]
    
    # Playlist naming services temporarily disabled - skip dynamic schema building
    # Get playlist data for dynamic schemas
    # try:
    #     api = get_api_instance()
    #     playlists = await api.get_playlists()
    #     _LOGGER.debug("Retrieved %d playlists for service registration", len(playlists))
    # except Exception as e:
    #     _LOGGER.warning("Could not get playlists for service registration: %s", e)
    #     playlists = []
    # 
    # # Build dynamic schemas for playlist naming services
    # dynamic_update_schema, dynamic_reset_schema = build_dynamic_playlist_schemas(playlists)
    
    for service_name, handler, schema in services:
        # Playlist naming services are disabled, no special handling needed
        # if service_name == "update_playlist_name":
        #     schema = dynamic_update_schema
        # elif service_name == "reset_playlist_name":
        #     schema = dynamic_reset_schema
            
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
        # Playlist Naming
        "update_playlist_name", "reset_playlist_name",
    ]
    
    for service in services:
        hass.services.async_remove(DOMAIN, service)
    
    _LOGGER.info("Unloaded all TRMNL services")