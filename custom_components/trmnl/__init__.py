"""The TRMNL integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_DEVICE_ID,
    CONF_UPDATE_INTERVAL,
    CONF_WEBHOOK_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_WEBHOOK_PORT,
    DOMAIN,
)
from .coordinator import TRMNLDataUpdateCoordinator
from .trmnl import TRMNLClient
from . import services

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_DEVICE_ID): cv.string,
                vol.Optional(CONF_NAME): cv.string,
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): cv.positive_int,
                vol.Optional(
                    CONF_WEBHOOK_PORT, default=DEFAULT_WEBHOOK_PORT
                ): cv.port,
            }
        )
    }
)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.LIGHT,
    Platform.CAMERA,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TRMNL from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create TRMNL client
    client = TRMNLClient(
        api_key=entry.data[CONF_API_KEY],
        device_id=entry.data[CONF_DEVICE_ID],
        update_interval=entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        webhook_port=entry.data.get(CONF_WEBHOOK_PORT, DEFAULT_WEBHOOK_PORT),
    )

    # Test connection
    try:
        await client.async_connect()
    except Exception as ex:
        _LOGGER.error("Failed to connect to TRMNL: %s", ex)
        raise ConfigEntryNotReady from ex

    # Create coordinator
    coordinator = TRMNLDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up webhook
    if entry.data.get(CONF_WEBHOOK_PORT):
        hass.http.register_webhook(
            f"/api/webhook/{DOMAIN}/{entry.entry_id}",
            coordinator.async_webhook_handler,
        )

    # Set up services
    await services.async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: TRMNLDataUpdateCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

        # Unload services if this is the last entry
        if not hass.data[DOMAIN]:
            await services.async_unload_services(hass)

    return unload_ok
