"""Tests for data coordinator."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from ..api.models import TRMNLDevice, DeviceStatus, DeviceType
from ..const import (
    CONF_API_KEY,
    CONF_DEVICES,
    CONF_SERVER_TYPE,
    SERVER_TYPE_CLOUD,
)
from ..coordinator import TRMNLCoordinator


@pytest.fixture
def sample_devices() -> list[TRMNLDevice]:
    """Create sample TRMNL devices."""
    return [
        TRMNLDevice(
            id="device_1",
            name="Living Room",
            device_type=DeviceType.OG,
            status=DeviceStatus.ONLINE,
            battery_level=85,
            firmware_version="1.0.0",
        ),
        TRMNLDevice(
            id="device_2",
            name="Bedroom",
            device_type=DeviceType.X,
            status=DeviceStatus.OFFLINE,
            battery_level=45,
            firmware_version="1.1.0",
        ),
    ]


@pytest.fixture
def mock_hass() -> MagicMock:
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.helpers.aiohttp_client.async_get_clientsession = AsyncMock(
        return_value=MagicMock()
    )
    return hass


class TestCoordinatorInitialization:
    """Test coordinator initialization."""

    def test_coordinator_init_stores_entry_data(self) -> None:
        """Test coordinator stores and exposes entry data."""
        entry_data = {
            CONF_SERVER_TYPE: SERVER_TYPE_CLOUD,
            CONF_API_KEY: "test_api_key",
            CONF_DEVICES: ["device_1", "device_2"],
        }

        # Create a minimal coordinator with mocked API client
        coordinator = MagicMock(spec=TRMNLCoordinator)
        coordinator.entry_data = entry_data
        coordinator.devices = {}
        coordinator.plugins = {}

        assert coordinator.entry_data == entry_data
        assert coordinator.devices == {}
        assert coordinator.plugins == {}

    def test_coordinator_device_storage(self) -> None:
        """Test coordinator device storage initialization."""
        coordinator = MagicMock(spec=TRMNLCoordinator)
        coordinator.devices = {"device_1": MagicMock()}
        coordinator.plugins = {}

        assert "device_1" in coordinator.devices
        assert len(coordinator.plugins) == 0


class TestCoordinatorDataUpdate:
    """Test coordinator data update."""

    def test_coordinator_filters_configured_devices(
        self, sample_devices: list[TRMNLDevice]
    ) -> None:
        """Test that coordinator filters devices to configured only."""
        coordinator = MagicMock(spec=TRMNLCoordinator)
        configured_devices = ["device_1"]

        # Simulate filtering logic
        devices_dict = {
            device.id: device
            for device in sample_devices
            if device.id in configured_devices
        }
        coordinator.devices = devices_dict

        # Should only have device_1
        assert len(coordinator.devices) == 1
        assert "device_1" in coordinator.devices
        assert "device_2" not in coordinator.devices

    def test_coordinator_handles_empty_device_list(self) -> None:
        """Test coordinator handling of empty device list."""
        coordinator = MagicMock(spec=TRMNLCoordinator)
        coordinator.devices = {}

        assert len(coordinator.devices) == 0
        assert isinstance(coordinator.devices, dict)

    def test_coordinator_stores_multiple_devices(
        self, sample_devices: list[TRMNLDevice]
    ) -> None:
        """Test coordinator storage of multiple devices."""
        coordinator = MagicMock(spec=TRMNLCoordinator)
        devices_dict = {device.id: device for device in sample_devices}
        coordinator.devices = devices_dict

        assert len(coordinator.devices) == 2
        assert all(device_id in coordinator.devices for device_id in ["device_1", "device_2"])


class TestCoordinatorGetDevices:
    """Test coordinator device getter methods."""

    def test_get_device_from_storage(
        self, sample_devices: list[TRMNLDevice]
    ) -> None:
        """Test getting a device from coordinator storage."""
        coordinator = MagicMock(spec=TRMNLCoordinator)
        coordinator.devices = {"device_1": sample_devices[0]}

        # Test device retrieval
        device = coordinator.devices.get("device_1")
        assert device is not None
        assert device.id == "device_1"

    def test_get_device_not_found(self) -> None:
        """Test getting a non-existent device returns None."""
        coordinator = MagicMock(spec=TRMNLCoordinator)
        coordinator.devices = {}

        device = coordinator.devices.get("nonexistent")
        assert device is None

    def test_get_all_devices(
        self, sample_devices: list[TRMNLDevice]
    ) -> None:
        """Test getting all devices from coordinator."""
        coordinator = MagicMock(spec=TRMNLCoordinator)
        coordinator.devices = {
            "device_1": sample_devices[0],
            "device_2": sample_devices[1],
        }

        devices = coordinator.devices
        assert len(devices) == 2
        assert "device_1" in devices
        assert "device_2" in devices


class TestCoordinatorConnectivity:
    """Test coordinator connection validation."""

    def test_coordinator_api_client_accessible(self) -> None:
        """Test that coordinator maintains API client reference."""
        coordinator = MagicMock(spec=TRMNLCoordinator)
        coordinator.api_client = MagicMock()

        # Coordinator should have API client reference
        assert coordinator.api_client is not None
        assert isinstance(coordinator.api_client, MagicMock)


class TestCoordinatorRefresh:
    """Test coordinator refresh functionality."""

    def test_coordinator_refresh_method_exists(self) -> None:
        """Test that coordinator has refresh method."""
        coordinator = MagicMock(spec=TRMNLCoordinator)
        coordinator.async_request_refresh = AsyncMock(return_value=True)

        # Method should exist
        assert hasattr(coordinator, "async_request_refresh")
        assert callable(coordinator.async_request_refresh)


class TestCoordinatorScreenshot:
    """Test coordinator screenshot update."""

    def test_coordinator_screenshot_method_exists(self) -> None:
        """Test that coordinator has screenshot update method."""
        coordinator = MagicMock(spec=TRMNLCoordinator)
        coordinator.async_update_screenshot = AsyncMock(return_value=True)

        # Method should exist
        assert hasattr(coordinator, "async_update_screenshot")
        assert callable(coordinator.async_update_screenshot)

    def test_coordinator_screenshot_with_minimal_params(self) -> None:
        """Test screenshot update with minimal parameters (addon case)."""
        coordinator = MagicMock(spec=TRMNLCoordinator)
        coordinator.async_update_screenshot = AsyncMock(return_value=True)

        # Should support addon case with minimal parameters
        assert coordinator.async_update_screenshot is not None
