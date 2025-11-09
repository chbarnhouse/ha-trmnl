"""Config flow for TRMNL integration."""

import logging
import secrets
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.config_validation import multi_select
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CloudAPIClient, BYOSAPIClient
from .api.exceptions import InvalidAPIKeyError, DeviceDiscoveryError
from .const import (
    CONF_API_KEY,
    CONF_AUTH_TYPE,
    CONF_DEVICES,
    CONF_PASSWORD,
    CONF_SERVER_TYPE,
    CONF_SERVER_URL,
    CONF_TOKEN_SECRET,
    CONF_USERNAME,
    AUTH_TYPE_API_KEY,
    AUTH_TYPE_BASIC,
    AUTH_TYPE_NONE,
    DOMAIN,
    SERVER_TYPE_BYOS,
    SERVER_TYPE_CLOUD,
    ServerType,
)

_LOGGER = logging.getLogger(__name__)


class TRMNLConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TRMNL."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step (server type selection)."""
        if user_input is not None:
            server_type = user_input[CONF_SERVER_TYPE]
            if server_type == SERVER_TYPE_CLOUD:
                return await self.async_step_cloud_auth()
            else:
                return await self.async_step_byos_config()

        server_type_schema = vol.Schema(
            {
                vol.Required(CONF_SERVER_TYPE): vol.In(
                    {
                        SERVER_TYPE_CLOUD: "TRMNL Cloud (usetrmnl.com)",
                        SERVER_TYPE_BYOS: "BYOS (Self-hosted)",
                    }
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=server_type_schema,
            description_placeholders={},
        )

    async def async_step_cloud_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Cloud authentication step."""
        errors = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]

            try:
                session = async_get_clientsession(self.hass)
                api_client = CloudAPIClient(api_key=api_key, session=session)

                # Validate credentials
                if not await api_client.validate_credentials():
                    errors[CONF_API_KEY] = "invalid_api_key"
                else:
                    return await self.async_step_device_discovery(
                        server_type=SERVER_TYPE_CLOUD,
                        server_config={CONF_API_KEY: api_key},
                    )

            except InvalidAPIKeyError:
                errors[CONF_API_KEY] = "invalid_api_key"
            except Exception as err:
                _LOGGER.error("Cloud authentication error: %s", err)
                errors["base"] = "connection_error"

        cloud_auth_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="cloud_auth",
            data_schema=cloud_auth_schema,
            errors=errors,
            description_placeholders={},
        )

    async def async_step_byos_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle BYOS server configuration step."""
        errors = {}

        if user_input is not None:
            return await self.async_step_byos_auth(
                server_url=user_input[CONF_SERVER_URL],
                auth_type=user_input[CONF_AUTH_TYPE],
            )

        byos_config_schema = vol.Schema(
            {
                vol.Required(CONF_SERVER_URL): str,
                vol.Required(CONF_AUTH_TYPE): vol.In(
                    {
                        AUTH_TYPE_API_KEY: "API Key",
                        AUTH_TYPE_BASIC: "Basic Auth (Username/Password)",
                        AUTH_TYPE_NONE: "No Authentication",
                    }
                ),
            }
        )

        return self.async_show_form(
            step_id="byos_config",
            data_schema=byos_config_schema,
            errors=errors,
            description_placeholders={},
        )

    async def async_step_byos_auth(
        self, server_url: str, auth_type: str, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle BYOS authentication step."""
        errors = {}

        if user_input is not None:
            credentials = {}

            if auth_type == AUTH_TYPE_API_KEY:
                credentials[CONF_API_KEY] = user_input[CONF_API_KEY]
            elif auth_type == AUTH_TYPE_BASIC:
                credentials[CONF_USERNAME] = user_input[CONF_USERNAME]
                credentials[CONF_PASSWORD] = user_input[CONF_PASSWORD]

            try:
                session = async_get_clientsession(self.hass)
                api_client = BYOSAPIClient(
                    server_url=server_url,
                    auth_type=auth_type,
                    credentials=credentials,
                    session=session,
                )

                # Validate credentials
                if not await api_client.validate_credentials():
                    errors["base"] = "cannot_connect"
                else:
                    return await self.async_step_device_discovery(
                        server_type=SERVER_TYPE_BYOS,
                        server_config={
                            CONF_SERVER_URL: server_url,
                            CONF_AUTH_TYPE: auth_type,
                            **credentials,
                        },
                    )

            except Exception as err:
                _LOGGER.error("BYOS authentication error: %s", err)
                errors["base"] = "cannot_connect"

        # Build schema based on auth type
        schema_dict = {}

        if auth_type == AUTH_TYPE_API_KEY:
            schema_dict[vol.Required(CONF_API_KEY)] = str
        elif auth_type == AUTH_TYPE_BASIC:
            schema_dict[vol.Required(CONF_USERNAME)] = str
            schema_dict[vol.Required(CONF_PASSWORD)] = str

        byos_auth_schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="byos_auth",
            data_schema=byos_auth_schema,
            errors=errors,
            description_placeholders={},
        )

    async def async_step_device_discovery(
        self,
        server_type: str,
        server_config: dict[str, Any],
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle device discovery step."""
        errors = {}
        device_options = {}

        # Discover devices from API
        try:
            session = async_get_clientsession(self.hass)

            if server_type == SERVER_TYPE_CLOUD:
                api_client = CloudAPIClient(
                    api_key=server_config[CONF_API_KEY],
                    session=session,
                )
            else:  # BYOS
                credentials = {}
                auth_type = server_config.get(CONF_AUTH_TYPE, AUTH_TYPE_NONE)

                if auth_type == AUTH_TYPE_API_KEY:
                    credentials[CONF_API_KEY] = server_config[CONF_API_KEY]
                elif auth_type == AUTH_TYPE_BASIC:
                    credentials[CONF_USERNAME] = server_config.get(CONF_USERNAME, "")
                    credentials[CONF_PASSWORD] = server_config.get(CONF_PASSWORD, "")

                api_client = BYOSAPIClient(
                    server_url=server_config[CONF_SERVER_URL],
                    auth_type=auth_type,
                    credentials=credentials,
                    session=session,
                )

            # Fetch devices
            devices = await api_client.get_devices()

            if not devices:
                _LOGGER.warning("No devices discovered from %s", server_type)
                errors["base"] = "no_devices_found"
            else:
                # Ensure device IDs are strings for proper validation
                device_options = {str(device.id): device.name for device in devices}
                _LOGGER.debug("Discovered device options: %s", device_options)

        except Exception as err:
            _LOGGER.error("Device discovery error: %s", err)
            errors["base"] = "device_discovery_error"

        if user_input is not None:
            selected_devices = user_input.get(CONF_DEVICES, [])

            # Ensure selected devices are strings
            selected_devices = [str(d) for d in selected_devices]

            if not selected_devices:
                errors[CONF_DEVICES] = "no_devices_selected"
            elif device_options and not all(d in device_options for d in selected_devices):
                _LOGGER.error("Invalid device selection: %s not in %s", selected_devices, device_options)
                errors[CONF_DEVICES] = "invalid_devices"
            elif not errors:
                # Generate random token secret (32 bytes = 256 bits)
                token_secret = secrets.token_hex(32)

                return self.async_create_entry(
                    title=f"TRMNL ({server_type.upper()})",
                    data={
                        CONF_SERVER_TYPE: server_type,
                        **server_config,
                        CONF_DEVICES: selected_devices,
                        CONF_TOKEN_SECRET: token_secret,
                    },
                )

        if not device_options and not errors:
            errors["base"] = "no_devices_found"

        device_discovery_schema = vol.Schema(
            {
                vol.Required(CONF_DEVICES): multi_select(device_options),
            }
        )

        return self.async_show_form(
            step_id="device_discovery",
            data_schema=device_discovery_schema,
            errors=errors,
            description_placeholders={},
        )
