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
            elif method.upper() == "PATCH" and data:
                async with session.patch(url, json=data) as response:
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
        if response.status == 200:
            try:
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

    async def refresh_device(self, device_id: str) -> bool:
        """Trigger a device refresh by updating its data."""
        try:
            _LOGGER.info("Refreshing device: %s", device_id)
            
            # Get all devices to find the target device
            devices = await self.get_devices()
            device_data = None
            numeric_id = None
            
            for device in devices:
                if device.get('friendly_id') == device_id or str(device.get('id')) == str(device_id):
                    device_data = device.copy()
                    numeric_id = device.get('id')
                    break
            
            if not device_data or not numeric_id:
                _LOGGER.error("Device %s not found", device_id)
                return False
            
            # Update device with same data to trigger refresh
            url = f"/api/devices/{numeric_id}"
            payload = {"device": device_data}
            
            result = await self._make_request(url, method="PATCH", data=payload)
            
            if result:
                _LOGGER.info("Successfully refreshed device %s", device_id)
                return True
            else:
                _LOGGER.error("Failed to refresh device %s", device_id)
                return False
                
        except Exception as e:
            _LOGGER.error("Error refreshing device %s: %s", device_id, e)
            return False