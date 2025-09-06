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
        
        # Try comprehensive list of possible API endpoints
        endpoints_to_try = [
            "/api/playlists", 
            "/playlists.json",
            "/admin/playlists.json",
            "/admin/api/playlists",
            "/api/v1/playlists",
            "/admin/playlists",
            "/playlists"  # Even though this returns HTML, let's see the full response
        ]
        
        for endpoint in endpoints_to_try:
            _LOGGER.error("PLAYLIST DEBUG: Trying endpoint %s", endpoint)
            
            try:
                # Make raw request to see headers and content type
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    _LOGGER.error("PLAYLIST DEBUG: %s - Status: %d, Content-Type: %s", 
                                endpoint, response.status, response.headers.get('content-type', 'unknown'))
                    
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        
                        if 'json' in content_type.lower():
                            result = await response.json()
                            _LOGGER.error("PLAYLIST DEBUG: JSON response from %s: %s", endpoint, result)
                            
                            # Check if it's a direct array or wrapped in "data"
                            if isinstance(result, list):
                                _LOGGER.error("PLAYLIST DEBUG: Found %d playlists (direct array)", len(result))
                                return result
                            elif isinstance(result, dict) and "data" in result:
                                playlists = result["data"]
                                _LOGGER.error("PLAYLIST DEBUG: Found %d playlists (data wrapper)", len(playlists))
                                return playlists
                        else:
                            # For HTML responses, let's see if we can parse playlist info
                            text = await response.text()
                            _LOGGER.error("PLAYLIST DEBUG: Non-JSON response from %s (first 200 chars): %s", 
                                        endpoint, text[:200])
                            
                            # Try to extract playlist references from HTML
                            import re
                            playlist_matches = re.findall(r'playlist["\s]*:\s*["\s]*(\d+)["\s]*[,}]', text, re.IGNORECASE)
                            name_matches = re.findall(r'name["\s]*:\s*["\s]*([^"]+)["\s]*[,}]', text, re.IGNORECASE)
                            
                            if playlist_matches:
                                _LOGGER.error("PLAYLIST DEBUG: Found playlist IDs in HTML: %s", playlist_matches)
                            if name_matches:
                                _LOGGER.error("PLAYLIST DEBUG: Found names in HTML: %s", name_matches)
                    else:
                        _LOGGER.error("PLAYLIST DEBUG: %s returned status %d", endpoint, response.status)
                        
            except Exception as e:
                _LOGGER.error("PLAYLIST DEBUG: Error with endpoint %s: %s", endpoint, e)
        
        # Try to get screens and see if they contain playlist info
        _LOGGER.error("PLAYLIST DEBUG: Checking screens for playlist information")
        screens = await self.get_screens()
        _LOGGER.error("PLAYLIST DEBUG: Got %d screens: %s", len(screens), screens)
        
        # Fallback: Since devices contain playlist_id, create generic playlists
        # But try to get ALL possible playlist IDs (not just from current device)
        _LOGGER.error("PLAYLIST DEBUG: Falling back to creating generic playlists")
        
        # Assume playlists 1-10 exist (common range) and let user select
        fallback_playlists = []
        for i in range(1, 11):
            fallback_playlists.append({
                'id': i,
                'name': f"Playlist {i}"
            })
        
        _LOGGER.error("PLAYLIST DEBUG: Created %d fallback playlists", len(fallback_playlists))
        return fallback_playlists

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

    # Display API - Direct device display updates
    async def update_display(self, device_id: str, display_data: Dict) -> bool:
        """Update device display content directly via Display API."""
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
                return False
            
            # Make request with MAC address as ID header (as per TRMNL API spec)
            session = await self._get_session()
            headers = {
                'ID': mac_address,
                'Content-Type': 'application/json'
            }
            
            # Add base64 encoding header if requested
            if display_data.get('base64_image'):
                headers['BASE64'] = 'true'
            
            # POST display update
            async with session.post(f"{self.base_url}/api/display", 
                                  headers=headers, 
                                  json=display_data) as response:
                result = await self._handle_response(response, f"{self.base_url}/api/display")
                if result:
                    _LOGGER.info("Updated display for device %s (MAC: %s)", device_id, mac_address)
                    return True
                return False
                
        except Exception as e:
            _LOGGER.error("Error updating display for device %s: %s", device_id, e)
            return False
    
    # Playlist Management Methods
    async def create_playlist(self, playlist_data: Dict) -> Optional[Dict]:
        """Create a new playlist in Terminus."""
        try:
            _LOGGER.info("Creating playlist: %s", playlist_data.get('name', 'unknown'))
            result = await self._make_request("/api/playlists", method="POST", data={"playlist": playlist_data})
            if result:
                _LOGGER.info("Successfully created playlist")
                return result.get("data")
            return None
        except Exception as e:
            _LOGGER.error("Error creating playlist: %s", e)
            return None

    async def update_playlist(self, playlist_id: str, playlist_data: Dict) -> bool:
        """Update a playlist in Terminus."""
        try:
            _LOGGER.info("Updating playlist %s", playlist_id)
            result = await self._make_request(f"/api/playlists/{playlist_id}", method="PATCH", data={"playlist": playlist_data})
            if result:
                _LOGGER.info("Successfully updated playlist %s", playlist_id)
                return True
            return False
        except Exception as e:
            _LOGGER.error("Error updating playlist %s: %s", playlist_id, e)
            return False

    async def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist from Terminus."""
        try:
            _LOGGER.info("Deleting playlist %s", playlist_id)
            result = await self._make_request(f"/api/playlists/{playlist_id}", method="DELETE")
            if result:
                _LOGGER.info("Successfully deleted playlist %s", playlist_id)
                return True
            return False
        except Exception as e:
            _LOGGER.error("Error deleting playlist %s: %s", playlist_id, e)
            return False

    async def add_screen_to_playlist(self, playlist_id: str, screen_id: str, position: Optional[int] = None) -> bool:
        """Add a screen to a playlist at optional position."""
        try:
            _LOGGER.info("Adding screen %s to playlist %s", screen_id, playlist_id)
            data = {"screen_id": screen_id}
            if position is not None:
                data["position"] = position
            
            result = await self._make_request(f"/api/playlists/{playlist_id}/screens", method="POST", data=data)
            if result:
                _LOGGER.info("Successfully added screen %s to playlist %s", screen_id, playlist_id)
                return True
            return False
        except Exception as e:
            _LOGGER.error("Error adding screen %s to playlist %s: %s", screen_id, playlist_id, e)
            return False

    async def remove_screen_from_playlist(self, playlist_id: str, screen_id: str) -> bool:
        """Remove a screen from a playlist."""
        try:
            _LOGGER.info("Removing screen %s from playlist %s", screen_id, playlist_id)
            result = await self._make_request(f"/api/playlists/{playlist_id}/screens/{screen_id}", method="DELETE")
            if result:
                _LOGGER.info("Successfully removed screen %s from playlist %s", screen_id, playlist_id)
                return True
            return False
        except Exception as e:
            _LOGGER.error("Error removing screen %s from playlist %s: %s", screen_id, playlist_id, e)
            return False

    # Log Management
    async def send_device_log(self, device_id: str, log_data: Dict) -> bool:
        """Send log data from a device."""
        try:
            # Find device to get MAC address for proper log correlation
            devices = await self.get_devices()
            mac_address = None
            
            for device in devices:
                if device.get('friendly_id') == device_id or str(device.get('id')) == str(device_id):
                    mac_address = device.get('mac_address')
                    break
            
            # Enhance log data with device info
            enhanced_log = {
                "device_id": device_id,
                "timestamp": log_data.get("timestamp"),
                "level": log_data.get("level", "info"),
                "message": log_data.get("message", ""),
                "component": log_data.get("component", "home_assistant"),
            }
            
            if mac_address:
                enhanced_log["mac_address"] = mac_address
            
            # Add any additional data
            if "additional_data" in log_data:
                enhanced_log.update(log_data["additional_data"])
            
            _LOGGER.debug("Sending log data for device %s", device_id)
            result = await self._make_request("/api/log", method="POST", data=enhanced_log)
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

    async def setup_device(self, device_id: str, force_setup: bool = False) -> Optional[Dict]:
        """Trigger device setup process."""
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
            
            # Make setup request with MAC address as ID header
            session = await self._get_session()
            headers = {
                'ID': mac_address,
                'Content-Type': 'application/json'
            }
            
            setup_data = {"force": force_setup}
            
            async with session.post(f"{self.base_url}/api/setup", 
                                  headers=headers, 
                                  json=setup_data) as response:
                result = await self._handle_response(response, f"{self.base_url}/api/setup")
                if result:
                    _LOGGER.info("Setup initiated for device %s (MAC: %s)", device_id, mac_address)
                    return result
                return None
                
        except Exception as e:
            _LOGGER.error("Error setting up device %s: %s", device_id, e)
            return None