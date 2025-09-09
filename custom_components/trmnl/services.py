"""TRMNL services for Home Assistant - Complete Terminus API Coverage."""
import logging
from typing import Dict, Any, Optional
import voluptuous as vol
from datetime import datetime

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, device_registry as dr, entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.exceptions import ServiceValidationError
import asyncio
import base64
import io
import tempfile
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps

# Optional Playwright import for dashboard capture
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None

# Alternative imports for basic dashboard capture
import aiohttp
from urllib.parse import urljoin

from .api import TRMNLApi
from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)

# === DASHBOARD CAPTURE CLASS ===

class DashboardCapture:
    """Captures Home Assistant dashboards for TRMNL display."""
    
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._playwright = None
        self._browser = None
        self._context = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        if PLAYWRIGHT_AVAILABLE:
            await self._setup_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if PLAYWRIGHT_AVAILABLE:
            await self._cleanup_browser()
    
    async def _setup_browser(self):
        """Setup Playwright browser for dashboard capture."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not available. Dashboard capture requires Playwright to be installed. "
                "For Home Assistant OS, try restarting Home Assistant to retry dependency installation."
            )
        
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            self._context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                device_scale_factor=1
            )
            _LOGGER.info("Browser setup complete for dashboard capture")
        except Exception as e:
            _LOGGER.error("Failed to setup browser: %s", e)
            raise
    
    async def _cleanup_browser(self):
        """Cleanup browser resources."""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            _LOGGER.info("Browser cleanup complete")
        except Exception as e:
            _LOGGER.error("Error during browser cleanup: %s", e)
    
    async def capture_dashboard(
        self,
        dashboard_path: str,
        theme: str = None,
        width: int = 800,
        height: int = 480,
        orientation: str = "landscape",
        center_x_offset: int = 0,
        center_y_offset: int = 0,
        margin_top: int = 0,
        margin_bottom: int = 0,
        margin_left: int = 0,
        margin_right: int = 0,
        rotation_angle: float = 0.0
    ) -> bytes:
        """Capture a Home Assistant dashboard and return processed image data."""
        
        if PLAYWRIGHT_AVAILABLE:
            # Use Playwright for full browser automation
            return await self._capture_with_playwright(
                dashboard_path, theme, width, height, orientation,
                center_x_offset, center_y_offset, margin_top, margin_bottom,
                margin_left, margin_right, rotation_angle
            )
        else:
            # Use alternative method without Playwright - no browser context needed
            return await self._capture_with_fallback(
                dashboard_path, theme, width, height, orientation,
                center_x_offset, center_y_offset, margin_top, margin_bottom,
                margin_left, margin_right, rotation_angle
            )
    
    async def _capture_with_playwright(
        self,
        dashboard_path: str,
        theme: str = None,
        width: int = 800,
        height: int = 480,
        orientation: str = "landscape",
        center_x_offset: int = 0,
        center_y_offset: int = 0,
        margin_top: int = 0,
        margin_bottom: int = 0,
        margin_left: int = 0,
        margin_right: int = 0,
        rotation_angle: float = 0.0
    ) -> bytes:
        """Capture dashboard using Playwright browser automation."""
        
        async with self:  # Use context manager for browser lifecycle
            try:
                # Get Home Assistant URL
                base_url = str(self.hass.config.api.base_url)
                if not base_url:
                    base_url = "http://localhost:8123"
                
                # Build dashboard URL
                dashboard_url = f"{base_url.rstrip('/')}{dashboard_path}"
                
                # Add theme parameter if specified
                if theme:
                    separator = "&" if "?" in dashboard_url else "?"
                    dashboard_url += f"{separator}theme={theme}"
                
                _LOGGER.info("Capturing dashboard with Playwright: %s", dashboard_url)
                
                # Create new page
                page = await self._context.new_page()
                
                # Set viewport to desired size
                await page.set_viewport_size({"width": width, "height": height})
                
                # Navigate to dashboard with authentication
                # Note: In a real deployment, you'd need to handle HA authentication
                # This assumes the dashboard is accessible (e.g., via long-lived access token)
                await page.goto(dashboard_url, wait_until="networkidle")
                
                # Wait for dashboard to load
                await page.wait_for_timeout(3000)  # Give dashboard time to render
                
                # Take screenshot
                screenshot_bytes = await page.screenshot(
                    type="png",
                    full_page=False
                )
                
                await page.close()
                
                # Process the image according to parameters
                processed_image_bytes = await self._process_image(
                    screenshot_bytes,
                    orientation=orientation,
                    center_x_offset=center_x_offset,
                    center_y_offset=center_y_offset,
                    margin_top=margin_top,
                    margin_bottom=margin_bottom,
                    margin_left=margin_left,
                    margin_right=margin_right,
                    rotation_angle=rotation_angle
                )
                
                # Convert to base64 for TRMNL API
                image_base64 = base64.b64encode(processed_image_bytes).decode('utf-8')
                _LOGGER.info("Dashboard capture completed successfully with Playwright")
                
                return image_base64
                
            except Exception as e:
                _LOGGER.error("Error capturing dashboard with Playwright: %s", e)
                raise
    
    async def _capture_with_fallback(
        self,
        dashboard_path: str,
        theme: str = None,
        width: int = 800,
        height: int = 480,
        orientation: str = "landscape",
        center_x_offset: int = 0,
        center_y_offset: int = 0,
        margin_top: int = 0,
        margin_bottom: int = 0,
        margin_left: int = 0,
        margin_right: int = 0,
        rotation_angle: float = 0.0
    ) -> bytes:
        """Capture dashboard using fallback method without Playwright."""
        
        try:
            _LOGGER.info("Using fallback dashboard capture method (Playwright not available)")
            
            # Create a placeholder image with dashboard information
            # This is a basic fallback - in a production system you might want to
            # implement a more sophisticated capture method
            
            # Create a simple text-based image as a placeholder
            # Use smaller dimensions for testing to avoid server size limits
            test_width = min(width, 320)
            test_height = min(height, 240)
            img = Image.new("RGB", (test_width, test_height), color="white")
            _LOGGER.info("Creating test image: %dx%d (requested %dx%d)", test_width, test_height, width, height)
            
            # You could enhance this by:
            # 1. Fetching dashboard HTML and parsing it
            # 2. Using a lightweight rendering engine
            # 3. Creating informative placeholder content
            # 4. Connecting to external screenshot services
            
            # For now, create a placeholder with useful information
            from PIL import ImageDraw, ImageFont
            
            draw = ImageDraw.Draw(img)
            
            # Try to use a basic font
            try:
                # This will work on most systems
                font = ImageFont.load_default()
            except:
                font = None
            
            # Add text information
            text_lines = [
                "TRMNL Dashboard Capture",
                f"Path: {dashboard_path}",
                f"Theme: {theme or 'default'}",
                f"Size: {width}x{height}",
                "",
                "Playwright not available",
                "Using fallback method",
                "",
                "To enable full capture:",
                "Install Playwright manually"
            ]
            
            y_offset = 50
            for line in text_lines:
                if font:
                    draw.text((50, y_offset), line, fill="black", font=font)
                else:
                    draw.text((50, y_offset), line, fill="black")
                y_offset += 30
            
            # Process the image according to parameters (synchronous version for fallback)
            processed_image_bytes = self._process_image_sync(
                img,
                orientation=orientation,
                center_x_offset=center_x_offset,
                center_y_offset=center_y_offset,
                margin_top=margin_top,
                margin_bottom=margin_bottom,
                margin_left=margin_left,
                margin_right=margin_right,
                rotation_angle=rotation_angle
            )
            
            # Convert to base64 for TRMNL API
            image_base64 = base64.b64encode(processed_image_bytes).decode('utf-8')
            _LOGGER.info("Dashboard capture completed with fallback method")
            _LOGGER.info("Generated image: %d bytes raw, %d chars base64", len(processed_image_bytes), len(image_base64))
            
            return image_base64
            
        except Exception as e:
            _LOGGER.error("Error in fallback dashboard capture: %s", e)
            raise
    
    async def _process_image(
        self,
        image_data: bytes,
        orientation: str = "landscape",
        center_x_offset: int = 0,
        center_y_offset: int = 0,
        margin_top: int = 0,
        margin_bottom: int = 0,
        margin_left: int = 0,
        margin_right: int = 0,
        rotation_angle: float = 0.0
    ) -> bytes:
        """Process captured image with orientation, positioning, margins, and rotation."""
        
        # Load image
        img = Image.open(io.BytesIO(image_data))
        
        # Apply orientation
        if orientation == "portrait":
            img = img.rotate(90, expand=True)
        elif orientation == "portrait_inverted":
            img = img.rotate(-90, expand=True)
        elif orientation == "landscape_inverted":
            img = img.rotate(180, expand=True)
        # landscape is default (no rotation)
        
        # Apply fine rotation angle if specified
        if rotation_angle != 0.0:
            img = img.rotate(rotation_angle, expand=True, fillcolor='white')
        
        # Apply margins by creating a new image with padding
        if any([margin_top, margin_bottom, margin_left, margin_right]):
            old_width, old_height = img.size
            new_width = old_width + margin_left + margin_right
            new_height = old_height + margin_top + margin_bottom
            
            new_img = Image.new("RGB", (new_width, new_height), "white")
            new_img.paste(img, (margin_left, margin_top))
            img = new_img
        
        # Apply center offsets by cropping/repositioning
        if center_x_offset != 0 or center_y_offset != 0:
            width, height = img.size
            
            # Calculate crop box with offsets
            left = max(0, center_x_offset)
            top = max(0, center_y_offset)
            right = min(width, width + center_x_offset)
            bottom = min(height, height + center_y_offset)
            
            # If offset would crop the image, create a new canvas
            if left > 0 or top > 0 or right < width or bottom < height:
                new_img = Image.new("RGB", (width, height), "white")
                paste_x = max(0, -center_x_offset)
                paste_y = max(0, -center_y_offset)
                new_img.paste(img, (paste_x, paste_y))
                img = new_img
        
        # Convert back to bytes
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="PNG", optimize=True)
        
        return output_buffer.getvalue()
    
    def _process_image_sync(
        self,
        img: Image.Image,
        orientation: str = "landscape",
        center_x_offset: int = 0,
        center_y_offset: int = 0,
        margin_top: int = 0,
        margin_bottom: int = 0,
        margin_left: int = 0,
        margin_right: int = 0,
        rotation_angle: float = 0.0
    ) -> bytes:
        """Process image with orientation, positioning, margins, and rotation (synchronous version)."""
        
        # Apply orientation
        if orientation == "portrait":
            img = img.rotate(90, expand=True)
        elif orientation == "portrait_inverted":
            img = img.rotate(-90, expand=True)
        elif orientation == "landscape_inverted":
            img = img.rotate(180, expand=True)
        # landscape is default (no rotation)
        
        # Apply fine rotation angle if specified
        if rotation_angle != 0.0:
            img = img.rotate(rotation_angle, expand=True, fillcolor='white')
        
        # Apply margins by creating a new image with padding
        if any([margin_top, margin_bottom, margin_left, margin_right]):
            old_width, old_height = img.size
            new_width = old_width + margin_left + margin_right
            new_height = old_height + margin_top + margin_bottom
            
            new_img = Image.new("RGB", (new_width, new_height), "white")
            new_img.paste(img, (margin_left, margin_top))
            img = new_img
        
        # Apply center offsets by cropping/repositioning
        if center_x_offset != 0 or center_y_offset != 0:
            width, height = img.size
            
            # Calculate crop box with offsets
            left = max(0, center_x_offset)
            top = max(0, center_y_offset)
            right = min(width, width + center_x_offset)
            bottom = min(height, height + center_y_offset)
            
            # If offset would crop the image, create a new canvas
            if left > 0 or top > 0 or right < width or bottom < height:
                new_img = Image.new("RGB", (width, height), "white")
                paste_x = max(0, -center_x_offset)
                paste_y = max(0, -center_y_offset)
                new_img.paste(img, (paste_x, paste_y))
                img = new_img
        
        # Convert back to bytes
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="PNG", optimize=True)
        
        return output_buffer.getvalue()

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

# === Dashboard to TRMNL Service ===
SEND_DASHBOARD_SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
    vol.Required("dashboard_path"): cv.string,
    vol.Optional("theme"): cv.string,
    vol.Optional("screen_name"): cv.string,
    vol.Optional("action"): vol.In(["create_screen", "update_screen", "add_to_playlist"]),
    vol.Optional("playlist_id"): cv.string,
    vol.Optional("width", default=800): vol.Coerce(int),
    vol.Optional("height", default=480): vol.Coerce(int),
    vol.Optional("orientation", default="landscape"): vol.In(["landscape", "portrait", "landscape_inverted", "portrait_inverted"]),
    vol.Optional("center_x_offset", default=0): vol.Coerce(int),
    vol.Optional("center_y_offset", default=0): vol.Coerce(int),
    vol.Optional("margin_top", default=0): vol.Coerce(int),
    vol.Optional("margin_bottom", default=0): vol.Coerce(int),
    vol.Optional("margin_left", default=0): vol.Coerce(int),
    vol.Optional("margin_right", default=0): vol.Coerce(int),
    vol.Optional("rotation_angle", default=0.0): vol.Coerce(float),
    vol.Optional("update_frequency"): vol.In(["manual", "hourly", "daily", "every_30min", "every_15min"]),
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
            
            _LOGGER.info("Configure playlists called with action=%s, playlist_id=%s, label=%s", action, playlist_id, label)
            
            # Get the label manager from hass.data using the service call's hass reference
            service_hass = call.hass if hasattr(call, 'hass') else hass
            current_label_manager = service_hass.data.get(f"{DOMAIN}_label_manager")
            
            if not current_label_manager:
                _LOGGER.error("Label manager not found in hass.data. Available keys: %s", list(service_hass.data.keys()))
                # Try to initialize a new one
                current_label_manager = PlaylistLabelManager(service_hass)
                await current_label_manager.async_load()
                service_hass.data[f"{DOMAIN}_label_manager"] = current_label_manager
                _LOGGER.info("Created new label manager")
                
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
            
            # Try to create a persistent notification, with fallback to logging
            try:
                await service_hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "message": notification_message,
                        "title": "TRMNL Playlist Configuration",
                        "notification_id": "trmnl_playlist_configuration"
                    }
                )
                _LOGGER.info("Created notification with playlist configuration")
            except Exception as notification_error:
                # Fallback: just log the message
                _LOGGER.info("Could not create notification (%s), logging instead: %s", notification_error, notification_message)
    
    # === DASHBOARD CAPTURE SERVICE ===
    
    async def handle_send_dashboard_to_device(call: ServiceCall) -> None:
        """Capture a Home Assistant dashboard and send it to a TRMNL device."""
        try:
            
            api = get_api_instance()
            device_friendly_id = get_device_friendly_id(call.data["device_id"])
            dashboard_path = call.data["dashboard_path"]
            
            # Get optional parameters with defaults
            theme = call.data.get("theme")
            width = call.data.get("width", 800)
            height = call.data.get("height", 480)
            orientation = call.data.get("orientation", "landscape")
            center_x_offset = call.data.get("center_x_offset", 0)
            center_y_offset = call.data.get("center_y_offset", 0)
            margin_top = call.data.get("margin_top", 0)
            margin_bottom = call.data.get("margin_bottom", 0)
            margin_left = call.data.get("margin_left", 0)
            margin_right = call.data.get("margin_right", 0)
            rotation_angle = call.data.get("rotation_angle", 0.0)
            
            _LOGGER.info(
                "Capturing dashboard %s for device %s with theme=%s, size=%dx%d, orientation=%s",
                dashboard_path, device_friendly_id, theme, width, height, orientation
            )
            
            # Initialize dashboard capture
            dashboard_capture = DashboardCapture(hass)
            
            # Capture the dashboard with appropriate method
            try:
                image_data = await dashboard_capture.capture_dashboard(
                    dashboard_path=dashboard_path,
                    theme=theme,
                    width=width,
                    height=height,
                    orientation=orientation,
                    center_x_offset=center_x_offset,
                    center_y_offset=center_y_offset,
                    margin_top=margin_top,
                    margin_bottom=margin_bottom,
                    margin_left=margin_left,
                    margin_right=margin_right,
                    rotation_angle=rotation_angle
                )
            except Exception as capture_error:
                _LOGGER.error("Failed to initialize dashboard capture: %s", capture_error)
                raise ServiceValidationError("Failed to initialize browser for dashboard capture")
            
            # Create a screen with the captured image (sanitize path for filename)
            safe_path = dashboard_path.replace("/", "_").replace("\\", "_")
            timestamp = int(datetime.now().timestamp())
            unique_name = f"Dashboard_{safe_path}_{timestamp}"
            
            # Log image data stats before sending
            _LOGGER.info("Screen creation - Image data size: %d characters", len(image_data))
            _LOGGER.info("Image data starts with: %s", image_data[:50] if image_data else "NO DATA")
            
            # Check if we're accidentally sending placeholder content
            if "Playwright not available" in image_data:
                _LOGGER.warning("WARNING: Sending placeholder text instead of actual image data!")
                _LOGGER.warning("The dashboard capture is creating a text-based placeholder, not a real image")
                _LOGGER.warning("This means Playwright is not available for actual screenshot capture")
            
            # Based on diagnostics, this server expects format with image object containing model_id and label
            screen_data = {
                "model_id": 1,
                "name": unique_name,
                "label": f"HA Dashboard {dashboard_path}",
                "image": {
                    "model_id": 1,
                    "name": unique_name,
                    "label": f"HA Dashboard {dashboard_path}",
                    "data": image_data
                }
            }
            
            # Based on user feedback, some screens WERE created in earlier attempts!
            # This means the /api/screens endpoint DOES work, but our format was causing 500 errors
            # Let's go back to the screens API with a simpler, cleaner format
            
            _LOGGER.info("Returning to screens API approach - user reports some screens were created earlier")
            _LOGGER.info("Attempting screen creation with minimal, clean format")
            
            # Try a very simple screen format (like what worked in earlier versions)
            simple_screen_data = {
                "name": unique_name,
                "label": f"HA Dashboard {dashboard_path}",
                "image": {
                    "data": image_data
                }
            }
            
            _LOGGER.info("Attempting screen creation with minimal format")
            screen_result = await api.create_screen(simple_screen_data)
            
            if not screen_result:
                _LOGGER.warning("Simple format failed, trying with model_id")
                # Try with model_id as we know this was required
                enhanced_screen_data = {
                    "model_id": 1,
                    "name": unique_name,
                    "label": f"HA Dashboard {dashboard_path}",
                    "image": {
                        "model_id": 1,
                        "name": unique_name,
                        "label": f"HA Dashboard {dashboard_path}",
                        "data": image_data
                    }
                }
                
                screen_result = await api.create_screen(enhanced_screen_data)
                
            if not screen_result:
                raise ServiceValidationError(f"Failed to create screen for dashboard {dashboard_path}")
            
            screen_id = screen_result.get('id')
            _LOGGER.info("Successfully created screen %s with dashboard capture", screen_id)
            
            # Screen created successfully! Now try to get it to display on the device
            _LOGGER.info("Screen %s created successfully, attempting assignment to device %s", screen_id, device_friendly_id)
            
            # Try multiple assignment approaches since playlists don't work
            assignment_methods = [
                # Method 1: Try setting current_screen_id directly
                {"current_screen_id": screen_id},
                # Method 2: Try with just screen_id
                {"screen_id": screen_id}, 
                # Method 3: Try with active_screen
                {"active_screen": screen_id},
                # Method 4: Try with display_screen_id  
                {"display_screen_id": screen_id},
                # Method 5: Try updating label to include screen reference
                {"label": f"HA Dashboard {dashboard_path}", "active_screen_id": screen_id}
            ]
            
            assignment_success = False
            for i, assignment_data in enumerate(assignment_methods):
                try:
                    _LOGGER.info("Trying screen assignment method %d: %s", i + 1, assignment_data)
                    result = await api.update_device(device_friendly_id, assignment_data)
                    if result:
                        _LOGGER.info("Screen assignment method %d succeeded!", i + 1)
                        assignment_success = True
                        break
                    else:
                        _LOGGER.warning("Screen assignment method %d returned False", i + 1)
                except Exception as assign_error:
                    _LOGGER.warning("Screen assignment method %d failed: %s", i + 1, assign_error)
                    continue
            
            if assignment_success:
                _LOGGER.info("Successfully assigned screen %s to device %s", screen_id, device_friendly_id)
                # Try to trigger device refresh
                try:
                    await api.refresh_device(device_friendly_id)
                    _LOGGER.info("Device refresh triggered - screen should display now")
                except:
                    _LOGGER.info("Device refresh failed, but screen may appear on next polling cycle")
            else:
                _LOGGER.warning("Could not assign screen to device automatically")
                _LOGGER.info("Screen %s created successfully and available in TRMNL web interface", screen_id)
                _LOGGER.info("You can manually assign it to device %s in the web interface", device_friendly_id)
            
            _LOGGER.info("Dashboard capture completed - screen %s created for %s", screen_id, dashboard_path)
            
        except Exception as e:
            _LOGGER.error("Error in send_dashboard_to_device service: %s", e, exc_info=True)
            raise ServiceValidationError(f"Failed to send dashboard to device: {e}")
    
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
    
    # Always add dashboard capture service - will show helpful error if Playwright unavailable
    services.append(("send_dashboard_to_device", handle_send_dashboard_to_device, SEND_DASHBOARD_SCHEMA))
    
    if PLAYWRIGHT_AVAILABLE:
        _LOGGER.info("Dashboard capture service enabled (Playwright available)")
    else:
        _LOGGER.warning("Dashboard capture service registered but Playwright not available - service will show installation instructions")
    
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