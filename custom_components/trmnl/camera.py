"""Camera platform for TRMNL integration."""

import logging
from typing import Any, Optional

from homeassistant.components.camera import Camera
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
    """Set up TRMNL cameras based on a config entry."""
    coordinator: TRMNLDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Add screen cameras
    screens = coordinator.screens
    for screen in screens:
        screen_id = screen.get("id")
        if screen_id:
            async_add_entities([TRMNLScreenCamera(coordinator, entry, screen_id)])


class TRMNLScreenCamera(CoordinatorEntity, Camera):
    """Representation of a TRMNL screen camera."""

    def __init__(
        self,
        coordinator: TRMNLDataUpdateCoordinator,
        entry: ConfigEntry,
        screen_id: str,
    ) -> None:
        """Initialize the camera."""
        super().__init__(coordinator)
        self.screen_id = screen_id
        self._attr_name = f"{entry.data.get(CONF_NAME, 'TRMNL')} Screen {screen_id} Camera"
        self._attr_unique_id = f"{entry.entry_id}_screen_{screen_id}_camera"
        self._attr_icon = "mdi:monitor-eye"

    @property
    def is_recording(self) -> bool:
        """Return true if the device is recording."""
        return False

    @property
    def is_streaming(self) -> bool:
        """Return true if the device is streaming."""
        screen = self.coordinator.get_screen(self.screen_id)
        if not screen:
            return False
        return screen.get("active", False)

    @property
    def motion_detection_enabled(self) -> bool:
        """Return the camera motion detection status."""
        return False

    @property
    def brand(self) -> Optional[str]:
        """Return the camera brand."""
        return "TRMNL"

    @property
    def model(self) -> Optional[str]:
        """Return the camera model."""
        screen = self.coordinator.get_screen(self.screen_id)
        if not screen:
            return None
        return screen.get("model", "TRMNL Screen")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self.coordinator.device_info

    async def async_camera_image(
        self, width: Optional[int] = None, height: Optional[int] = None
    ) -> Optional[bytes]:
        """Return a still image response from the camera."""
        try:
            # Get screen content
            screen = self.coordinator.get_screen(self.screen_id)
            if not screen:
                return None

            # For now, return a placeholder image
            # In a real implementation, you would fetch the actual screen content
            # from the TRMNL API or generate an image based on the screen data
            _LOGGER.debug("Camera image requested for screen %s", self.screen_id)
            
            # Return None to indicate no image available
            # This will show a placeholder in the UI
            return None
            
        except Exception as ex:
            _LOGGER.error("Failed to get camera image: %s", ex)
            return None

    async def async_turn_on(self) -> None:
        """Turn on the camera."""
        try:
            await self.coordinator.async_update_screen(
                self.screen_id, 
                content="", 
                active=True
            )
        except Exception as ex:
            _LOGGER.error("Failed to turn on camera: %s", ex)

    async def async_turn_off(self) -> None:
        """Turn off the camera."""
        try:
            await self.coordinator.async_update_screen(
                self.screen_id, 
                content="", 
                active=False
            )
        except Exception as ex:
            _LOGGER.error("Failed to turn off camera: %s", ex)
