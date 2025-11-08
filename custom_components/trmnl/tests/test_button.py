"""Tests for button platform."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from ..api.models import TRMNLDevice, DeviceStatus, DeviceType
from ..button import TRMNLRefreshButton


@pytest.fixture
def mock_coordinator() -> MagicMock:
    """Create a mock coordinator."""
    coordinator = MagicMock()

    # Sample device
    device = TRMNLDevice(
        id="device_1",
        name="Living Room",
        device_type=DeviceType.OG,
        status=DeviceStatus.ONLINE,
        battery_level=75,
        firmware_version="1.0.0",
        last_seen=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )

    coordinator.devices = {"device_1": device}
    coordinator.async_request_refresh = AsyncMock(return_value=True)

    return coordinator


class TestRefreshButton:
    """Test TRMNL refresh button."""

    def test_refresh_button_unique_id(self, mock_coordinator: MagicMock) -> None:
        """Test refresh button unique ID."""
        button = TRMNLRefreshButton(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert button.unique_id == "device_1_refresh"

    def test_refresh_button_name(self, mock_coordinator: MagicMock) -> None:
        """Test refresh button friendly name."""
        button = TRMNLRefreshButton(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert button.name == "Living Room Refresh"

    def test_refresh_button_device_class(self, mock_coordinator: MagicMock) -> None:
        """Test refresh button has correct device class."""
        button = TRMNLRefreshButton(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert button._attr_device_class == "restart"

    def test_refresh_button_icon(self, mock_coordinator: MagicMock) -> None:
        """Test refresh button has correct icon."""
        button = TRMNLRefreshButton(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert button._attr_icon == "mdi:refresh"

    @pytest.mark.asyncio
    async def test_refresh_button_press_success(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test refresh button press triggers refresh."""
        button = TRMNLRefreshButton(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )

        await button.async_press()

        # Verify coordinator refresh was called
        assert mock_coordinator.async_request_refresh.call_count == 2
        # First call with device_id, second without (for coordinator update)

    @pytest.mark.asyncio
    async def test_refresh_button_press_failure(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test refresh button press handles failure."""
        mock_coordinator.async_request_refresh = AsyncMock(return_value=False)
        button = TRMNLRefreshButton(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )

        # Should not raise exception on failure
        await button.async_press()

        assert mock_coordinator.async_request_refresh.called

    def test_refresh_button_extra_attributes(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test refresh button extra state attributes."""
        button = TRMNLRefreshButton(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        attrs = button.extra_state_attributes
        assert "status" in attrs
        assert "battery_level" in attrs
        assert "last_seen" in attrs
        assert attrs["status"] == "online"
        assert attrs["battery_level"] == 75

    def test_refresh_button_extra_attributes_no_device(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test refresh button extra attributes when device not found."""
        button = TRMNLRefreshButton(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        mock_coordinator.devices = {}
        assert button.extra_state_attributes == {}


class TestButtonSetup:
    """Test button platform setup."""

    def test_button_created_for_device(self, mock_coordinator: MagicMock) -> None:
        """Test that button is created for a device."""
        device = mock_coordinator.devices["device_1"]

        # Create refresh button
        button = TRMNLRefreshButton(mock_coordinator, "device_1", device)
        assert button.unique_id == "device_1_refresh"
        assert button.name == "Living Room Refresh"

    def test_buttons_created_for_multiple_devices(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test that buttons are created for multiple devices."""
        device2 = TRMNLDevice(
            id="device_2",
            name="Bedroom",
            device_type=DeviceType.X,
            status=DeviceStatus.OFFLINE,
            battery_level=45,
        )
        mock_coordinator.devices["device_2"] = device2

        # Create buttons for both devices
        buttons = []
        for device_id, device in mock_coordinator.devices.items():
            buttons.append(TRMNLRefreshButton(mock_coordinator, device_id, device))

        # Should have 2 buttons (1 per device)
        assert len(buttons) == 2
        unique_ids = [b.unique_id for b in buttons]
        assert "device_1_refresh" in unique_ids
        assert "device_2_refresh" in unique_ids
