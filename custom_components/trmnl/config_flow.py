"""Config flow for TRMNL integration."""
import voluptuous as vol
import asyncio
import logging
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import TRMNLApi
from .const import DOMAIN, CONF_HOST, CONF_PORT

_LOGGER = logging.getLogger(__name__)


async def validate_connection(hass: HomeAssistant, host: str, port: int) -> dict:
    """Validate connection to Terminus server and discover devices."""
    _LOGGER.info("Testing connection to %s:%s", host, port)
    api = TRMNLApi(host, port)
    
    try:
        if not await api.test_connection():
            raise CannotConnect(f"Cannot connect to {host}:{port}")
        
        # Get devices from server
        devices = await api.get_devices()
        _LOGGER.info("Found %d TRMNL devices", len(devices))
        
        return {
            "title": f"TRMNL ({host}:{port})",
            "devices": devices,
            "host": host,
            "port": port
        }
    finally:
        await api.close()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TRMNL."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        if user_input is None:
            # Auto-discover known Terminus server
            known_servers = [
                ("192.168.1.56", 2300),
            ]
            
            _LOGGER.info("Auto-discovering TRMNL Terminus server...")
            
            for host, port in known_servers:
                try:
                    info = await validate_connection(self.hass, host, port)
                    
                    # Check if already configured
                    await self.async_set_unique_id(f"{host}:{port}")
                    self._abort_if_unique_id_configured()
                    
                    # Create entry immediately
                    return self.async_create_entry(
                        title=info["title"], 
                        data={CONF_HOST: host, CONF_PORT: port}
                    )
                    
                except CannotConnect:
                    _LOGGER.debug("Cannot connect to %s:%s", host, port)
                    continue
                except Exception as e:
                    _LOGGER.debug("Error testing %s:%s: %s", host, port, e)
                    continue
            
            # If auto-discovery fails, show manual form
            errors["base"] = "cannot_connect_auto"
            
        else:
            # Manual configuration
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            
            try:
                info = await validate_connection(self.hass, host, port)
                
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show manual configuration form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default="192.168.1.56"): str,
                vol.Required(CONF_PORT, default=2300): int,
            }),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""