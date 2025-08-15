"""Services for TRMNL integration."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    ATTR_SCREEN_ID,
    ATTR_PLUGIN_ID,
    ATTR_BRIGHTNESS,
    ATTR_WEBHOOK_URL,
    ATTR_EVENTS,
    DOMAIN,
    SERVICE_UPDATE_SCREEN,
    SERVICE_INSTALL_PLUGIN,
    SERVICE_UNINSTALL_PLUGIN,
    SERVICE_RESTART_DEVICE,
    SERVICE_SET_BRIGHTNESS,
    SERVICE_SETUP_WEBHOOK,
)

_LOGGER = logging.getLogger(__name__)

# Service schemas
UPDATE_SCREEN_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SCREEN_ID): cv.string,
        vol.Required("content"): cv.string,
        vol.Optional("template", default=False): cv.boolean,
    }
)

INSTALL_PLUGIN_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PLUGIN_ID): cv.string,
        vol.Optional("config"): cv.string,
    }
)

UNINSTALL_PLUGIN_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PLUGIN_ID): cv.string,
    }
)

SET_BRIGHTNESS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)

SETUP_WEBHOOK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_WEBHOOK_URL): cv.url,
        vol.Optional(ATTR_EVENTS, default=["device_update", "screen_update", "plugin_update"]): vol.All(
            cv.ensure_list, [cv.string]
        ),
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up TRMNL services."""

    async def async_update_screen(call: ServiceCall) -> None:
        """Update a TRMNL screen."""
        screen_id = call.data[ATTR_SCREEN_ID]
        content = call.data["content"]
        template = call.data.get("template", False)

        # Find the coordinator for this service call
        for entry_id, coordinator in hass.data[DOMAIN].items():
            try:
                success = await coordinator.async_update_screen(
                    screen_id, content, template=template
                )
                if success:
                    _LOGGER.info("Successfully updated screen %s", screen_id)
                else:
                    _LOGGER.error("Failed to update screen %s", screen_id)
                break
            except Exception as ex:
                _LOGGER.error("Error updating screen %s: %s", screen_id, ex)

    async def async_install_plugin(call: ServiceCall) -> None:
        """Install a TRMNL plugin."""
        plugin_id = call.data[ATTR_PLUGIN_ID]
        config = call.data.get("config")

        # Find the coordinator for this service call
        for entry_id, coordinator in hass.data[DOMAIN].items():
            try:
                success = await coordinator.async_install_plugin(plugin_id)
                if success:
                    _LOGGER.info("Successfully installed plugin %s", plugin_id)
                else:
                    _LOGGER.error("Failed to install plugin %s", plugin_id)
                break
            except Exception as ex:
                _LOGGER.error("Error installing plugin %s: %s", plugin_id, ex)

    async def async_uninstall_plugin(call: ServiceCall) -> None:
        """Uninstall a TRMNL plugin."""
        plugin_id = call.data[ATTR_PLUGIN_ID]

        # Find the coordinator for this service call
        for entry_id, coordinator in hass.data[DOMAIN].items():
            try:
                success = await coordinator.async_uninstall_plugin(plugin_id)
                if success:
                    _LOGGER.info("Successfully uninstalled plugin %s", plugin_id)
                else:
                    _LOGGER.error("Failed to uninstall plugin %s", plugin_id)
                break
            except Exception as ex:
                _LOGGER.error("Error uninstalling plugin %s: %s", plugin_id, ex)

    async def async_restart_device(call: ServiceCall) -> None:
        """Restart a TRMNL device."""
        # Find the coordinator for this service call
        for entry_id, coordinator in hass.data[DOMAIN].items():
            try:
                success = await coordinator.async_restart_device()
                if success:
                    _LOGGER.info("Successfully initiated device restart")
                else:
                    _LOGGER.error("Failed to restart device")
                break
            except Exception as ex:
                _LOGGER.error("Error restarting device: %s", ex)

    async def async_set_brightness(call: ServiceCall) -> None:
        """Set TRMNL device brightness."""
        brightness = call.data[ATTR_BRIGHTNESS]

        # Find the coordinator for this service call
        for entry_id, coordinator in hass.data[DOMAIN].items():
            try:
                success = await coordinator.async_set_brightness(brightness)
                if success:
                    _LOGGER.info("Successfully set brightness to %d%%", brightness)
                else:
                    _LOGGER.error("Failed to set brightness to %d%%", brightness)
                break
            except Exception as ex:
                _LOGGER.error("Error setting brightness: %s", ex)

    async def async_setup_webhook(call: ServiceCall) -> None:
        """Setup webhook for TRMNL device."""
        webhook_url = call.data[ATTR_WEBHOOK_URL]
        events = call.data[ATTR_EVENTS]

        # Find the coordinator for this service call
        for entry_id, coordinator in hass.data[DOMAIN].items():
            try:
                success = await coordinator.client.async_setup_webhook(webhook_url)
                if success:
                    _LOGGER.info("Successfully setup webhook: %s", webhook_url)
                else:
                    _LOGGER.error("Failed to setup webhook: %s", webhook_url)
                break
            except Exception as ex:
                _LOGGER.error("Error setting up webhook: %s", ex)

    # Register services
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_SCREEN, async_update_screen, schema=UPDATE_SCREEN_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_INSTALL_PLUGIN, async_install_plugin, schema=INSTALL_PLUGIN_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UNINSTALL_PLUGIN, async_uninstall_plugin, schema=UNINSTALL_PLUGIN_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESTART_DEVICE, async_restart_device
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_BRIGHTNESS, async_set_brightness, schema=SET_BRIGHTNESS_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SETUP_WEBHOOK, async_setup_webhook, schema=SETUP_WEBHOOK_SCHEMA
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload TRMNL services."""
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_SCREEN)
    hass.services.async_remove(DOMAIN, SERVICE_INSTALL_PLUGIN)
    hass.services.async_remove(DOMAIN, SERVICE_UNINSTALL_PLUGIN)
    hass.services.async_remove(DOMAIN, SERVICE_RESTART_DEVICE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_BRIGHTNESS)
    hass.services.async_remove(DOMAIN, SERVICE_SETUP_WEBHOOK)
