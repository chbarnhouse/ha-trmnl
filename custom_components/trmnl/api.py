"""API client for TRMNL Terminus server."""
import asyncio
import logging
from typing import Dict, List, Optional
import aiohttp

_LOGGER = logging.getLogger(__name__)


class TRMNLApi:
    """API client for TRMNL Terminus server."""
    
    def __init__(self, host: str, port: int = 2300):
        """Initialize the API client."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session
        
    async def close(self):
        """Close the session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _make_request(self, endpoint: str, method: str = "GET", data: dict = None) -> Optional[Dict]:
        """Make an async HTTP request to the API."""
        try:
            url = f"{self.base_url}{endpoint}"
            _LOGGER.debug("Making request to: %s", url)
            
            session = await self._get_session()
            
            if method.upper() == "GET":
                async with session.get(url) as response:
                    return await self._handle_response(response, url)
            elif method.upper() == "POST":
                async with session.post(url, json=data) as response:
                    return await self._handle_response(response, url)
            elif method.upper() == "PATCH":
                async with session.patch(url, json=data) as response:
                    return await self._handle_response(response, url)
            elif method.upper() == "DELETE":
                async with session.delete(url) as response:
                    return await self._handle_response(response, url)
            else:
                _LOGGER.error("Unsupported HTTP method: %s", method)
                return None
                
        except aiohttp.ClientError as e:
            _LOGGER.error("HTTP client error requesting %s: %s", url, e)
            return None
        except Exception as e:
            _LOGGER.error("Unexpected error requesting %s: %s", url, e, exc_info=True)
            return None
            
    async def _handle_response(self, response, url: str) -> Optional[Dict]:
        """Handle HTTP response."""
        if response.status in [200, 201, 204]:
            try:
                # Handle empty responses for DELETE operations
                if response.status == 204:
                    return {"status": "ok"}
                data = await response.json()
                _LOGGER.debug("Request successful to %s", url)
                return data
            except Exception:
                _LOGGER.debug("Response is not JSON from %s", url)
                return {"status": "ok", "content_type": "text"}
        else:
            _LOGGER.warning("HTTP %s from %s", response.status, url)
            return None
            
    async def get_devices(self) -> List[Dict]:
        """Get all devices from Terminus."""
        _LOGGER.debug("Fetching devices from %s", self.base_url)
        result = await self._make_request("/api/devices")
        
        if result and "data" in result:
            devices = result["data"]
            _LOGGER.info("Found %d TRMNL devices", len(devices))
            # Log each device's available fields for model detection debugging
            for i, device in enumerate(devices):
                _LOGGER.info("Device %d available fields: %s", i, list(device.keys()))
                _LOGGER.info("Device %d full data: %s", i, device)
            return devices
        else:
            _LOGGER.error("No devices found or API error")
            return []
            
    async def get_screens(self) -> List[Dict]:
        """Get all screens from Terminus."""
        _LOGGER.debug("Fetching screens from %s", self.base_url)
        result = await self._make_request("/api/screens")
        
        if result and "data" in result:
            screens = result["data"]
            _LOGGER.debug("Found %d screens", len(screens))
            return screens
        else:
            _LOGGER.error("No screens found or API error")
            return []

    async def get_playlists(self) -> List[Dict]:
        """Get all playlists from Terminus."""
        _LOGGER.error("PLAYLIST DEBUG: Fetching playlists from %s", self.base_url)
        
        # Since devices contain playlist_id, let's extract unique playlists from device data
        try:
            devices = await self.get_devices()
            _LOGGER.error("PLAYLIST DEBUG: Got %d devices to analyze for playlists", len(devices))
            
            unique_playlists = {}
            for device in devices:
                _LOGGER.error("PLAYLIST DEBUG: Device data: %s", device)
                
                playlist_id = device.get('playlist_id')
                if playlist_id and playlist_id not in unique_playlists:
                    # Create playlist entry from device data
                    playlist_name = f"Playlist {playlist_id}"
                    
                    # Try to get more info from device attributes that might contain playlist info
                    if 'playlist_name' in device:
                        playlist_name = device['playlist_name']
                    elif 'playlist_label' in device:
                        playlist_name = device['playlist_label']
                    
                    unique_playlists[playlist_id] = {
                        'id': playlist_id,
                        'name': playlist_name
                    }
                    _LOGGER.error("PLAYLIST DEBUG: Found playlist ID %s (name: %s)", playlist_id, playlist_name)
            
            playlists_list = list(unique_playlists.values())
            _LOGGER.error("PLAYLIST DEBUG: Extracted %d unique playlists from devices", len(playlists_list))
            
            if playlists_list:
                return playlists_list
            
        except Exception as e:
            _LOGGER.error("PLAYLIST DEBUG: Error extracting playlists from devices: %s", e)
        
        # Fallback: try API endpoints
        endpoints_to_try = ["/playlists", "/api/playlists", "/admin/playlists", "/playlists.json"]
        
        for endpoint in endpoints_to_try:
            _LOGGER.error("PLAYLIST DEBUG: Trying endpoint %s", endpoint)
            result = await self._make_request(endpoint)
            
            if result:
                _LOGGER.error("PLAYLIST DEBUG: Response from %s: %s", endpoint, result)
                
                # Check if it's a direct array or wrapped in "data"
                if isinstance(result, list):
                    _LOGGER.error("PLAYLIST DEBUG: Found %d playlists (direct array)", len(result))
                    return result
                elif isinstance(result, dict) and "data" in result:
                    playlists = result["data"]
                    _LOGGER.error("PLAYLIST DEBUG: Found %d playlists (data wrapper)", len(playlists))
                    return playlists
                else:
                    _LOGGER.error("PLAYLIST DEBUG: Unexpected response format from %s", endpoint)
            else:
                _LOGGER.error("PLAYLIST DEBUG: No response from %s", endpoint)
        
        _LOGGER.error("PLAYLIST DEBUG: No playlists found from any method")
        return []

    async def assign_device_to_playlist(self, device_id: str, playlist_id: str) -> bool:
        """Assign a device to a specific playlist."""
        try:
            _LOGGER.info("Assigning device %s to playlist %s", device_id, playlist_id)
            
            # Find the device's numeric ID
            devices = await self.get_devices()
            numeric_id = None
            
            for device in devices:
                if device.get('friendly_id') == device_id or str(device.get('id')) == str(device_id):
                    numeric_id = device.get('id')
                    break
            
            if not numeric_id:
                _LOGGER.error("Device %s not found", device_id)
                return False
            
            # Update device to assign to playlist
            # Note: The exact field name may need to be adjusted based on Terminus API
            result = await self._make_request(
                f"/api/devices/{numeric_id}", 
                method="PATCH", 
                data={"device": {"playlist_id": playlist_id}}
            )
            
            if result:
                _LOGGER.info("Successfully assigned device %s to playlist %s", device_id, playlist_id)
                return True
            else:
                _LOGGER.error("Failed to assign device %s to playlist %s", device_id, playlist_id)
                return False
                
        except Exception as e:
            _LOGGER.error("Error assigning device %s to playlist %s: %s", device_id, playlist_id, e)
            return False
            
    async def get_models(self) -> Dict[str, str]:
        """Get all models from Terminus and return as ID->name mapping."""
        _LOGGER.debug("Fetching models from %s", self.base_url)
        result = await self._make_request("/api/models")
        
        models_map = {}
        if result and "data" in result:
            models = result["data"]
            _LOGGER.info("Found %d TRMNL models", len(models))
            for model in models:
                # Map model ID to model display name (prefer label, then description, then name)
                model_id = str(model.get('id', ''))
                model_name = model.get('label', model.get('description', model.get('name', f'Model {model_id}')))
                if model_id:
                    models_map[model_id] = model_name
                    _LOGGER.info("Model mapping: ID %s -> Name '%s'", model_id, model_name)
        else:
            _LOGGER.warning("No models found or API error")
            
        return models_map
            
    async def test_connection(self) -> bool:
        """Test connection to Terminus server."""
        try:
            _LOGGER.debug("Testing connection to %s:%s", self.host, self.port)
            
            # Try simple HTTP request first
            result = await self._make_request("/")
            if result is not None:
                _LOGGER.info("HTTP connection successful to %s:%s", self.host, self.port)
                return True
            
            # Fallback to TCP connection test
            _LOGGER.debug("HTTP failed, trying TCP connection")
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=5
            )
            writer.close()
            await writer.wait_closed()
            _LOGGER.info("TCP connection successful to %s:%s", self.host, self.port)
            return True
            
        except Exception as e:
            _LOGGER.warning("Connection failed to %s:%s - %s", self.host, self.port, e)
            return False

    # Device Management Methods
    async def create_device(self, device_data: Dict) -> Optional[Dict]:
        """Create a new device in Terminus."""
        try:
            _LOGGER.info("Creating device: %s", device_data.get('friendly_id', 'unknown'))
            result = await self._make_request("/api/devices", method="POST", data={"device": device_data})
            if result:
                _LOGGER.info("Successfully created device")
                return result.get("data")
            return None
        except Exception as e:
            _LOGGER.error("Error creating device: %s", e)
            return None

    async def update_device(self, device_id: str, updates: Dict) -> bool:
        """Update device configuration."""
        try:
            _LOGGER.info("Updating device %s with: %s", device_id, updates)
            
            devices = await self.get_devices()
            numeric_id = None
            
            for device in devices:
                if device.get('friendly_id') == device_id or str(device.get('id')) == str(device_id):
                    numeric_id = device.get('id')
                    break
            
            if not numeric_id:
                _LOGGER.error("Device %s not found", device_id)
                return False
            
            result = await self._make_request(f"/api/devices/{numeric_id}", method="PATCH", data={"device": updates})
            
            if result:
                _LOGGER.info("Successfully updated device %s", device_id)
                return True
            return False
                
        except Exception as e:
            _LOGGER.error("Error updating device %s: %s", device_id, e)
            return False

    async def delete_device(self, device_id: str) -> bool:
        """Delete a device from Terminus."""
        try:
            _LOGGER.info("Deleting device: %s", device_id)
            
            devices = await self.get_devices()
            numeric_id = None
            
            for device in devices:
                if device.get('friendly_id') == device_id or str(device.get('id')) == str(device_id):
                    numeric_id = device.get('id')
                    break
            
            if not numeric_id:
                _LOGGER.error("Device %s not found", device_id)
                return False
            
            result = await self._make_request(f"/api/devices/{numeric_id}", method="DELETE")
            
            if result:
                _LOGGER.info("Successfully deleted device %s", device_id)
                return True
            return False
                
        except Exception as e:
            _LOGGER.error("Error deleting device %s: %s", device_id, e)
            return False

    async def get_device(self, device_id: str) -> Optional[Dict]:
        """Get a specific device by ID."""
        try:
            devices = await self.get_devices()
            
            for device in devices:
                if device.get('friendly_id') == device_id or str(device.get('id')) == str(device_id):
                    return device
            
            _LOGGER.error("Device %s not found", device_id)
            return None
                
        except Exception as e:
            _LOGGER.error("Error getting device %s: %s", device_id, e)
            return None

    async def set_device_sleep_schedule(self, device_id: str, sleep_start: str, sleep_stop: str) -> bool:
        """Set device sleep schedule (format: HH:MM)."""
        return await self.update_device(device_id, {
            "sleep_start_at": sleep_start,
            "sleep_stop_at": sleep_stop
        })

    async def set_device_refresh_rate(self, device_id: str, refresh_rate: int) -> bool:
        """Set device refresh rate in seconds."""
        return await self.update_device(device_id, {"refresh_rate": refresh_rate})

    async def set_device_image_timeout(self, device_id: str, timeout: int) -> bool:
        """Set device image timeout in seconds."""
        return await self.update_device(device_id, {"image_timeout": timeout})

    async def enable_firmware_update(self, device_id: str, enable: bool = True) -> bool:
        """Enable or disable firmware updates for device."""
        return await self.update_device(device_id, {"firmware_update": enable})

    async def refresh_device(self, device_id: str) -> bool:
        """Refresh device by pre-generating fresh content for next polling cycle."""
        try:
            _LOGGER.info("Refreshing device %s - preparing fresh content", device_id)
            
            # Find device data
            devices = await self.get_devices()
            device_data = None
            
            for device in devices:
                if device.get('friendly_id') == device_id or str(device.get('id')) == str(device_id):
                    device_data = device.copy()
                    break
            
            if not device_data:
                _LOGGER.error("Device %s not found", device_id)
                return False
            
            current_rate = device_data.get('refresh_rate', 3600)
            
            # Pre-generate fresh display content
            display_result = await self.get_device_display(device_id)
            
            if display_result and 'image_url' in display_result:
                _LOGGER.info("Fresh content prepared for device %s: %s", device_id, display_result.get('filename', 'unknown'))
                _LOGGER.info("Device will update on next polling cycle (within %s seconds)", current_rate)
                return True
            else:
                _LOGGER.error("Failed to prepare fresh content for device %s", device_id)
                return False
                
        except Exception as e:
            _LOGGER.error("Error refreshing device %s: %s", device_id, e)
            return False

    # Screen Management Methods
    async def create_screen(self, screen_data: Dict) -> Optional[Dict]:
        """Create a new screen in Terminus."""
        try:
            _LOGGER.info("Creating screen: %s", screen_data.get('name', 'unknown'))
            result = await self._make_request("/api/screens", method="POST", data={"image": screen_data})
            if result:
                _LOGGER.info("Successfully created screen")
                return result.get("data")
            return None
        except Exception as e:
            _LOGGER.error("Error creating screen: %s", e)
            return None

    async def update_screen(self, screen_id: str, screen_data: Dict) -> bool:
        """Update a screen in Terminus."""
        try:
            _LOGGER.info("Updating screen %s", screen_id)
            result = await self._make_request(f"/api/screens/{screen_id}", method="PATCH", data={"image": screen_data})
            if result:
                _LOGGER.info("Successfully updated screen %s", screen_id)
                return True
            return False
        except Exception as e:
            _LOGGER.error("Error updating screen %s: %s", screen_id, e)
            return False

    async def delete_screen(self, screen_id: str) -> bool:
        """Delete a screen from Terminus."""
        try:
            _LOGGER.info("Deleting screen %s", screen_id)
            result = await self._make_request(f"/api/screens/{screen_id}", method="DELETE")
            if result:
                _LOGGER.info("Successfully deleted screen %s", screen_id)
                return True
            return False
        except Exception as e:
            _LOGGER.error("Error deleting screen %s: %s", screen_id, e)
            return False

    async def get_screen(self, screen_id: str) -> Optional[Dict]:
        """Get a specific screen by ID."""
        try:
            result = await self._make_request(f"/api/screens/{screen_id}")
            if result and "data" in result:
                return result["data"]
            return None
        except Exception as e:
            _LOGGER.error("Error getting screen %s: %s", screen_id, e)
            return None

    # Model Management Methods
    async def create_model(self, model_data: Dict) -> Optional[Dict]:
        """Create a new model in Terminus."""
        try:
            _LOGGER.info("Creating model: %s", model_data.get('name', 'unknown'))
            result = await self._make_request("/api/models", method="POST", data={"model": model_data})
            if result:
                _LOGGER.info("Successfully created model")
                return result.get("data")
            return None
        except Exception as e:
            _LOGGER.error("Error creating model: %s", e)
            return None

    async def update_model(self, model_id: str, model_data: Dict) -> bool:
        """Update a model in Terminus."""
        try:
            _LOGGER.info("Updating model %s", model_id)
            result = await self._make_request(f"/api/models/{model_id}", method="PATCH", data={"model": model_data})
            if result:
                _LOGGER.info("Successfully updated model %s", model_id)
                return True
            return False
        except Exception as e:
            _LOGGER.error("Error updating model %s: %s", model_id, e)
            return False

    async def delete_model(self, model_id: str) -> bool:
        """Delete a model from Terminus."""
        try:
            _LOGGER.info("Deleting model %s", model_id)
            result = await self._make_request(f"/api/models/{model_id}", method="DELETE")
            if result:
                _LOGGER.info("Successfully deleted model %s", model_id)
                return True
            return False
        except Exception as e:
            _LOGGER.error("Error deleting model %s: %s", model_id, e)
            return False

    async def get_model(self, model_id: str) -> Optional[Dict]:
        """Get a specific model by ID."""
        try:
            result = await self._make_request(f"/api/models/{model_id}")
            if result and "data" in result:
                return result["data"]
            return None
        except Exception as e:
            _LOGGER.error("Error getting model %s: %s", model_id, e)
            return None

    # Display and Content Management
    async def get_device_display(self, device_id: str) -> Optional[Dict]:
        """Get the current display content for a device using its MAC address."""
        try:
            # Find device to get MAC address
            devices = await self.get_devices()
            mac_address = None
            
            for device in devices:
                if device.get('friendly_id') == device_id or str(device.get('id')) == str(device_id):
                    mac_address = device.get('mac_address')
                    break
            
            if not mac_address:
                _LOGGER.error("Could not find MAC address for device %s", device_id)
                return None
            
            # Make request with MAC address as ID header (as per TRMNL API spec)
            session = await self._get_session()
            headers = {
                'ID': mac_address,
                'Content-Type': 'application/json'
            }
            
            async with session.get(f"{self.base_url}/api/display", headers=headers) as response:
                result = await self._handle_response(response, f"{self.base_url}/api/display")
                if result:
                    _LOGGER.debug("Retrieved display content for device %s (MAC: %s)", device_id, mac_address)
                    return result
                return None
                
        except Exception as e:
            _LOGGER.error("Error getting display for device %s: %s", device_id, e)
            return None

    async def send_device_log(self, device_id: str, log_data: Dict) -> bool:
        """Send log data from a device."""
        try:
            _LOGGER.debug("Sending log data for device %s", device_id)
            result = await self._make_request("/api/log", method="POST", data=log_data)
            if result:
                return True
            return False
        except Exception as e:
            _LOGGER.error("Error sending log for device %s: %s", device_id, e)
            return False

    # Setup and Configuration
    async def get_setup_info(self) -> Optional[Dict]:
        """Get setup information from Terminus."""
        try:
            result = await self._make_request("/api/setup")
            if result:
                _LOGGER.debug("Retrieved setup information")
                return result
            return None
        except Exception as e:
            _LOGGER.error("Error getting setup info: %s", e)
            return None