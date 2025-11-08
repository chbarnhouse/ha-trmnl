"""TRMNL Home Assistant Integration.

Discover and manage TRMNL e-ink devices.
"""

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import TRMNLCoordinator
from .websocket.api import async_setup_websocket_api

_LOGGER: logging.Logger = logging.getLogger(__name__)

PLATFORMS: Final[list[Platform]] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TRMNL from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry for this integration

    Returns:
        True if setup was successful
    """
    hass.data.setdefault(DOMAIN, {})

    # Create coordinator for periodic device updates
    coordinator = TRMNLCoordinator(hass, entry.data)
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # Perform initial device refresh
    await coordinator.async_config_entry_first_refresh()

    # Set up platforms (sensors, binary sensors, buttons)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up WebSocket API for addon communication (Days 18-19)
    async_setup_websocket_api(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to unload

    Returns:
        True if unload was successful
    """
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up entry data
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to reload
    """
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
