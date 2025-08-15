"""Config flow for TRMNL integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_DEVICE_IP,
    CONF_DEVICE_ID,
    CONF_UPDATE_INTERVAL,
    CONF_WEBHOOK_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_WEBHOOK_PORT,
    DOMAIN,
)
from .trmnl import TRMNLClient

_LOGGER = logging.getLogger(__name__)


class TRMNLConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TRMNL."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate the connection
                client = TRMNLClient(
                    device_ip=user_input[CONF_DEVICE_IP],
                    api_key=user_input[CONF_API_KEY],
                    device_id=user_input[CONF_DEVICE_ID],
                    update_interval=user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                    webhook_port=user_input.get(CONF_WEBHOOK_PORT, DEFAULT_WEBHOOK_PORT),
                )
                
                await client.async_connect()
                await client.async_disconnect()

                # Check if device ID is already configured
                await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, f"TRMNL {user_input[CONF_DEVICE_ID]}"),
                    data=user_input,
                )

            except Exception as ex:
                _LOGGER.error("Failed to connect to TRMNL: %s", ex)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_IP): str,
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(CONF_DEVICE_ID): str,
                    vol.Optional(CONF_NAME): str,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                    ): int,
                    vol.Optional(
                        CONF_WEBHOOK_PORT, default=DEFAULT_WEBHOOK_PORT
                    ): int,
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, import_info: Dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidDevice(HomeAssistantError):
    """Error to indicate there is an invalid device ID."""
