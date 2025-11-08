"""Button platform for TRMNL integration."""

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import TRMNLCoordinator
from .entities.base import TRMNLEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities from config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        async_add_entities: Callback to add entities
    """
    coordinator: TRMNLCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Create button entities for each device
    entities = []
    for device_id, device in coordinator.devices.items():
        entities.append(TRMNLRefreshButton(coordinator, device_id, device))

    async_add_entities(entities)


class TRMNLRefreshButton(TRMNLEntity, ButtonEntity):
    """Button to trigger device refresh."""

    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: TRMNLCoordinator, device_id: str, device: Any) -> None:
        """Initialize the button."""
        super().__init__(coordinator, device_id, device)
        self._attr_name = f"{self.device_name} Refresh"

    @property
    def unique_id(self) -> str:
        """Return unique ID for button."""
        return f"{self.device_id}_refresh"

    @property
    def name(self) -> str:
        """Return friendly name."""
        return f"{self.device_name} Refresh"

    async def async_press(self) -> None:
        """Handle button press - trigger device refresh."""
        _LOGGER.debug("Triggering refresh for device %s", self.device_id)

        success = await self.coordinator.async_request_refresh(self.device_id)

        if success:
            _LOGGER.info("Device refresh triggered for %s", self.device_id)
        else:
            _LOGGER.warning("Device refresh failed for %s", self.device_id)

        # Request coordinator update after refresh
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        device = self.coordinator.devices.get(self.device_id)
        if device is None:
            return {}

        return {
            "status": device.status.value if device.status else None,
            "battery_level": device.battery_level,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        }
