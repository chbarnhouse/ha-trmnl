"""TRMNL integration for Home Assistant."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS, CONF_HOST, CONF_PORT, SERVICE_UPDATE_SCREEN, SERVICE_REFRESH_DEVICE
from .api import TRMNLApi

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the TRMNL integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TRMNL from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 2300)
    
    _LOGGER.info("Setting up TRMNL: %s:%s", host, port)
    
    api = TRMNLApi(host, port)
    
    # Test connection and discover devices
    try:
        if not await api.test_connection():
            _LOGGER.error("Cannot connect to TRMNL server")
            return False
            
        devices = await api.get_devices()
        _LOGGER.info("Found %d TRMNL devices", len(devices))
        
        # Log device details
        for device in devices:
            _LOGGER.info("Device: %s (%s) - Battery: %sV, WiFi: %s dBm", 
                        device.get('friendly_id'), device.get('label'), 
                        device.get('battery'), device.get('wifi'))
        
    except Exception as e:
        _LOGGER.error("Failed to setup TRMNL connection: %s", e)
        return False
    
    # Store data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "host": host,
        "port": port,
        "devices": devices,
    }
    
    # Register services
    await _register_services(hass, entry)
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("TRMNL setup complete - managing %d devices", len(devices))
    return True


async def _register_services(hass: HomeAssistant, entry: ConfigEntry):
    """Register TRMNL services."""
    
    async def update_screen_service(call: ServiceCall):
        """Handle update screen service call."""
        device_id = call.data.get("device")
        screen_id = call.data.get("screen_id")
        
        _LOGGER.info("Update screen service called: device=%s, screen=%s", device_id, screen_id)
        
        # Find the API instance for this device
        api = hass.data[DOMAIN][entry.entry_id]["api"]
        
        # For now, just log the request since screen updates are complex
        _LOGGER.info("Screen update requested but not yet implemented")
        
    async def refresh_device_service(call: ServiceCall):
        """Handle refresh device service call."""
        device_id = call.data.get("device")
        
        _LOGGER.info("Refresh device service called: device=%s", device_id)
        
        api = hass.data[DOMAIN][entry.entry_id]["api"]
        
        try:
            success = await api.refresh_device(device_id)
            if success:
                _LOGGER.info("Successfully refreshed device %s", device_id)
            else:
                _LOGGER.error("Failed to refresh device %s", device_id)
        except Exception as e:
            _LOGGER.error("Error refreshing device %s: %s", device_id, e)
    
    # Register services
    hass.services.async_register(DOMAIN, SERVICE_UPDATE_SCREEN, update_screen_service)
    hass.services.async_register(DOMAIN, SERVICE_REFRESH_DEVICE, refresh_device_service)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove services
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_SCREEN)
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_DEVICE)
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Close API session
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        if "api" in entry_data:
            await entry_data["api"].close()
        
    return unload_ok