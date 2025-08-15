"""Light platform for TRMNL integration."""

import logging
from typing import Any, Optional

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TRMNLDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TRMNL lights based on a config entry."""
    coordinator: TRMNLDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Add screen brightness light
    screens = coordinator.screens
    for screen in screens:
        screen_id = screen.get("id")
        if screen_id:
            async_add_entities([TRMNLScreenLight(coordinator, entry, screen_id)])


class TRMNLScreenLight(CoordinatorEntity, LightEntity):
    """Representation of a TRMNL screen light."""

    def __init__(
        self,
        coordinator: TRMNLDataUpdateCoordinator,
        entry: ConfigEntry,
        screen_id: str,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self.screen_id = screen_id
        self._attr_name = f"{entry.data.get(CONF_NAME, 'TRMNL')} Screen {screen_id} Light"
        self._attr_unique_id = f"{entry.entry_id}_screen_{screen_id}_light"
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_icon = "mdi:monitor"

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        screen = self.coordinator.get_screen(self.screen_id)
        if not screen:
            return False
        return screen.get("active", False)

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness of the light."""
        screen = self.coordinator.get_screen(self.screen_id)
        if not screen:
            return None
        
        brightness = screen.get("brightness", 0)
        # Convert percentage to 0-255 range
        if brightness is not None:
            return int((brightness / 100) * 255)
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        try:
            # Update screen to active state
            await self.coordinator.async_update_screen(
                self.screen_id, 
                content="", 
                active=True
            )
            
            # Set brightness if provided
            if ATTR_BRIGHTNESS in kwargs:
                brightness_pct = int((kwargs[ATTR_BRIGHTNESS] / 255) * 100)
                await self.coordinator.async_set_brightness(brightness_pct)
                
        except Exception as ex:
            _LOGGER.error("Failed to turn on screen light: %s", ex)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            await self.coordinator.async_update_screen(
                self.screen_id, 
                content="", 
                active=False
            )
        except Exception as ex:
            _LOGGER.error("Failed to turn off screen light: %s", ex)

    async def async_set_brightness(self, **kwargs: Any) -> None:
        """Set the brightness of the light."""
        if ATTR_BRIGHTNESS in kwargs:
            try:
                brightness_pct = int((kwargs[ATTR_BRIGHTNESS] / 255) * 100)
                await self.coordinator.async_set_brightness(brightness_pct)
            except Exception as ex:
                _LOGGER.error("Failed to set brightness: %s", ex)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info
