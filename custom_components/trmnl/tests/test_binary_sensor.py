"""Tests for binary sensor platform."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from ..api.models import TRMNLDevice, DeviceStatus, DeviceType
from ..binary_sensor import (
    TRMNLConnectivityBinarySensor,
    TRMNLBatteryLowBinarySensor,
)


@pytest.fixture
def mock_coordinator() -> MagicMock:
    """Create a mock coordinator."""
    coordinator = MagicMock()

    # Sample device - online with good battery
    device = TRMNLDevice(
        id="device_1",
        name="Living Room",
        device_type=DeviceType.OG,
        status=DeviceStatus.ONLINE,
        battery_level=85,
        firmware_version="1.0.0",
    )

    coordinator.devices = {"device_1": device}
    return coordinator


class TestConnectivityBinarySensor:
    """Test TRMNL connectivity binary sensor."""

    def test_connectivity_sensor_unique_id(self, mock_coordinator: MagicMock) -> None:
        """Test connectivity sensor unique ID."""
        sensor = TRMNLConnectivityBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert sensor.unique_id == "device_1_connectivity"

    def test_connectivity_sensor_name(self, mock_coordinator: MagicMock) -> None:
        """Test connectivity sensor friendly name."""
        sensor = TRMNLConnectivityBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert sensor.name == "Living Room Connectivity"

    def test_connectivity_sensor_is_on_online(self, mock_coordinator: MagicMock) -> None:
        """Test connectivity sensor is on when device is online."""
        sensor = TRMNLConnectivityBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert sensor.is_on is True

    def test_connectivity_sensor_is_on_offline(self, mock_coordinator: MagicMock) -> None:
        """Test connectivity sensor is off when device is offline."""
        device = mock_coordinator.devices["device_1"]
        device.status = DeviceStatus.OFFLINE
        sensor = TRMNLConnectivityBinarySensor(
            mock_coordinator, "device_1", device
        )
        assert sensor.is_on is False

    def test_connectivity_sensor_is_on_none(self, mock_coordinator: MagicMock) -> None:
        """Test connectivity sensor returns None when device not found."""
        sensor = TRMNLConnectivityBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        mock_coordinator.devices = {}
        assert sensor.is_on is None

    def test_connectivity_sensor_device_class(self, mock_coordinator: MagicMock) -> None:
        """Test connectivity sensor has correct device class."""
        sensor = TRMNLConnectivityBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert sensor._attr_device_class == "connectivity"

    def test_connectivity_sensor_extra_attributes(self, mock_coordinator: MagicMock) -> None:
        """Test connectivity sensor extra state attributes."""
        sensor = TRMNLConnectivityBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        attrs = sensor.extra_state_attributes
        assert "status" in attrs
        assert "device_type" in attrs
        assert "last_seen" in attrs
        assert attrs["status"] == "online"
        assert attrs["device_type"] == "og"

    def test_connectivity_sensor_extra_attributes_no_device(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test connectivity sensor extra attributes when device not found."""
        sensor = TRMNLConnectivityBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        mock_coordinator.devices = {}
        assert sensor.extra_state_attributes == {}


class TestBatteryLowBinarySensor:
    """Test TRMNL battery low binary sensor."""

    def test_battery_low_sensor_unique_id(self, mock_coordinator: MagicMock) -> None:
        """Test battery low sensor unique ID."""
        sensor = TRMNLBatteryLowBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert sensor.unique_id == "device_1_battery_low"

    def test_battery_low_sensor_name(self, mock_coordinator: MagicMock) -> None:
        """Test battery low sensor friendly name."""
        sensor = TRMNLBatteryLowBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert sensor.name == "Living Room Battery Low"

    def test_battery_low_sensor_is_on_false(self, mock_coordinator: MagicMock) -> None:
        """Test battery low sensor is off when battery is above threshold."""
        sensor = TRMNLBatteryLowBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert sensor.is_on is False

    def test_battery_low_sensor_is_on_true(self, mock_coordinator: MagicMock) -> None:
        """Test battery low sensor is on when battery is below threshold."""
        device = mock_coordinator.devices["device_1"]
        device.battery_level = 15  # Below 20% threshold
        sensor = TRMNLBatteryLowBinarySensor(
            mock_coordinator, "device_1", device
        )
        assert sensor.is_on is True

    def test_battery_low_sensor_is_on_at_threshold(self, mock_coordinator: MagicMock) -> None:
        """Test battery low sensor is on at exactly 20% threshold."""
        device = mock_coordinator.devices["device_1"]
        device.battery_level = 20  # Exactly at threshold
        sensor = TRMNLBatteryLowBinarySensor(
            mock_coordinator, "device_1", device
        )
        # Should be False since 20 is not < 20
        assert sensor.is_on is False

    def test_battery_low_sensor_is_on_below_threshold(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test battery low sensor is on just below threshold."""
        device = mock_coordinator.devices["device_1"]
        device.battery_level = 19  # Just below 20% threshold
        sensor = TRMNLBatteryLowBinarySensor(
            mock_coordinator, "device_1", device
        )
        assert sensor.is_on is True

    def test_battery_low_sensor_is_on_none(self, mock_coordinator: MagicMock) -> None:
        """Test battery low sensor returns None when device not found."""
        sensor = TRMNLBatteryLowBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        mock_coordinator.devices = {}
        assert sensor.is_on is None

    def test_battery_low_sensor_device_class(self, mock_coordinator: MagicMock) -> None:
        """Test battery low sensor has correct device class."""
        sensor = TRMNLBatteryLowBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        assert sensor._attr_device_class == "battery"

    def test_battery_low_sensor_extra_attributes(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test battery low sensor extra state attributes."""
        sensor = TRMNLBatteryLowBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        attrs = sensor.extra_state_attributes
        assert "battery_level" in attrs
        assert "status" in attrs
        assert attrs["battery_level"] == 85
        assert attrs["status"] == "online"

    def test_battery_low_sensor_extra_attributes_no_device(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test battery low sensor extra attributes when device not found."""
        sensor = TRMNLBatteryLowBinarySensor(
            mock_coordinator, "device_1", mock_coordinator.devices["device_1"]
        )
        mock_coordinator.devices = {}
        assert sensor.extra_state_attributes == {}


class TestBinarySensorSetup:
    """Test binary sensor platform setup."""

    def test_binary_sensors_created_for_device(self, mock_coordinator: MagicMock) -> None:
        """Test that binary sensors are created for a device."""
        device = mock_coordinator.devices["device_1"]

        # Create connectivity sensor
        connectivity_sensor = TRMNLConnectivityBinarySensor(
            mock_coordinator, "device_1", device
        )
        assert connectivity_sensor.unique_id == "device_1_connectivity"

        # Create battery low sensor
        battery_low_sensor = TRMNLBatteryLowBinarySensor(
            mock_coordinator, "device_1", device
        )
        assert battery_low_sensor.unique_id == "device_1_battery_low"

        # Both sensors should be properly created
        assert all([connectivity_sensor, battery_low_sensor])

    def test_binary_sensors_created_for_multiple_devices(
        self, mock_coordinator: MagicMock
    ) -> None:
        """Test that binary sensors are created for multiple devices."""
        device2 = TRMNLDevice(
            id="device_2",
            name="Bedroom",
            device_type=DeviceType.X,
            status=DeviceStatus.OFFLINE,
            battery_level=45,
        )
        mock_coordinator.devices["device_2"] = device2

        # Create sensors for both devices
        sensors = []
        for device_id, device in mock_coordinator.devices.items():
            sensors.append(
                TRMNLConnectivityBinarySensor(mock_coordinator, device_id, device)
            )
            sensors.append(
                TRMNLBatteryLowBinarySensor(mock_coordinator, device_id, device)
            )

        # Should have 4 sensors (2 per device)
        assert len(sensors) == 4
        unique_ids = [s.unique_id for s in sensors]
        assert "device_1_connectivity" in unique_ids
        assert "device_1_battery_low" in unique_ids
        assert "device_2_connectivity" in unique_ids
        assert "device_2_battery_low" in unique_ids
