"""Base entity class for TRMNL."""

from typing import Any, Optional

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..api.models import TRMNLDevice


class TRMNLEntity(CoordinatorEntity):
    """Base class for TRMNL entities."""

    def __init__(self, coordinator: Any, device_id: str, device: Any) -> None:
        """Initialize the entity.

        Args:
            coordinator: Data update coordinator
            device_id: Device ID
            device: TRMNL device object
        """
        super().__init__(coordinator)
        self._device_id = device_id
        self._device = device

    @property
    def device_id(self) -> str:
        """Return device ID."""
        return self._device_id

    @property
    def device_name(self) -> str:
        """Return device name."""
        if hasattr(self._device, 'name'):
            return self._device.name
        # Fallback if device not yet loaded
        return f"Device {self._device_id}"

    @property
    def entity_type(self) -> str:
        """Return entity type (to be overridden by subclasses)."""
        return "unknown"

    @property
    def device_info(self) -> dict:
        """Return device information."""
        device_name = self.device_name
        device_type = "unknown"

        if hasattr(self._device, 'device_type'):
            device_type = self._device.device_type.value

        return {
            "identifiers": {("trmnl", self._device_id)},
            "name": device_name,
            "manufacturer": "TRMNL",
            "model": device_type,
        }
