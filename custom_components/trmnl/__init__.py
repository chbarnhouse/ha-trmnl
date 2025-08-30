"""TRMNL integration for Home Assistant."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS, CONF_HOST, CONF_PORT
from .api import TRMNLApi
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the TRMNL integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TRMNL from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 2300)
    
    _LOGGER.info("Setting up TRMNL: %s:%s", host, port)
    
    # Update entry title if using old format
    expected_title = f"Terminus Server ({host}:{port})"
    if entry.title != expected_title:
        _LOGGER.info("Updating entry title from '%s' to '%s'", entry.title, expected_title)
        hass.config_entries.async_update_entry(entry, title=expected_title)
    
    api = TRMNLApi(host, port)
    
    # Test connection and discover devices
    try:
        if not await api.test_connection():
            _LOGGER.error("Cannot connect to TRMNL server")
            return False
            
        devices = await api.get_devices()
        _LOGGER.info("Found %d TRMNL devices", len(devices))
        
        # Get model mappings to resolve model_id to actual model names
        models = await api.get_models()
        _LOGGER.info("Loaded %d TRMNL model mappings", len(models))
        
        # Log device details
        for device in devices:
            _LOGGER.info("Device: %s (%s) - Battery: %sV, WiFi: %s dBm", 
                        device.get('friendly_id'), device.get('label'), 
                        device.get('battery'), device.get('wifi'))
            _LOGGER.info("DEVICE FIELDS for model detection: %s", list(device.keys()))
            _LOGGER.debug("Full device data: %s", device)
        
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
        "models": models,
    }
    
    # Register services
    await async_setup_services(hass)
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info("TRMNL setup complete - managing %d devices", len(devices))
    return True




async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove services
    await async_unload_services(hass)
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Close API session
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        if "api" in entry_data:
            await entry_data["api"].close()
        
    return unload_ok