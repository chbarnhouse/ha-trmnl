"""Tests for sensor platform."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant

from ..api.models import TRMNLDevice, DeviceStatus, DeviceType
from ..sensor import (
    TRMNLBatterySensor,
    TRMNLLastSeenSensor,
    TRMNLFirmwareVersionSensor,
)


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
    return coordinator


class TestBatterySensor:
    """Test TRMNL battery sensor."""

    def test_battery_sensor_unique_id(self, mock_coordinator: MagicMock) -> None:
        """Test battery sensor unique ID."""
        sensor = TRMNLBatterySensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        assert sensor.unique_id == "device_1_battery"

    def test_battery_sensor_name(self, mock_coordinator: MagicMock) -> None:
        """Test battery sensor friendly name."""
        sensor = TRMNLBatterySensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        assert sensor.name == "Living Room Battery"

    def test_battery_sensor_native_value(self, mock_coordinator: MagicMock) -> None:
        """Test battery sensor returns battery level."""
        sensor = TRMNLBatterySensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        assert sensor.native_value == 75

    def test_battery_sensor_native_value_none(self, mock_coordinator: MagicMock) -> None:
        """Test battery sensor returns None when device not found."""
        sensor = TRMNLBatterySensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        # Clear devices
        mock_coordinator.devices = {}
        assert sensor.native_value is None

    def test_battery_sensor_device_class(self, mock_coordinator: MagicMock) -> None:
        """Test battery sensor has correct device class."""
        sensor = TRMNLBatterySensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        assert sensor._attr_device_class == "battery"

    def test_battery_sensor_unit(self, mock_coordinator: MagicMock) -> None:
        """Test battery sensor has percentage unit."""
        sensor = TRMNLBatterySensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        assert sensor._attr_native_unit_of_measurement == "%"

    def test_battery_sensor_extra_attributes(self, mock_coordinator: MagicMock) -> None:
        """Test battery sensor extra state attributes."""
        sensor = TRMNLBatterySensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        attrs = sensor.extra_state_attributes
        assert "battery_low" in attrs
        assert "status" in attrs
        assert attrs["battery_low"] is False
        assert attrs["status"] == "online"

    def test_battery_sensor_extra_attributes_no_device(self, mock_coordinator: MagicMock) -> None:
        """Test battery sensor extra attributes when device not found."""
        sensor = TRMNLBatterySensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        mock_coordinator.devices = {}
        assert sensor.extra_state_attributes == {}


class TestLastSeenSensor:
    """Test TRMNL last seen sensor."""

    def test_last_seen_sensor_unique_id(self, mock_coordinator: MagicMock) -> None:
        """Test last seen sensor unique ID."""
        sensor = TRMNLLastSeenSensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        assert sensor.unique_id == "device_1_last_seen"

    def test_last_seen_sensor_name(self, mock_coordinator: MagicMock) -> None:
        """Test last seen sensor friendly name."""
        sensor = TRMNLLastSeenSensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        assert sensor.name == "Living Room Last Seen"

    def test_last_seen_sensor_native_value(self, mock_coordinator: MagicMock) -> None:
        """Test last seen sensor returns ISO timestamp."""
        sensor = TRMNLLastSeenSensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        value = sensor.native_value
        assert value == "2025-01-01T12:00:00+00:00"

    def test_last_seen_sensor_native_value_none(self, mock_coordinator: MagicMock) -> None:
        """Test last seen sensor returns None when device not found."""
        sensor = TRMNLLastSeenSensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        mock_coordinator.devices = {}
        assert sensor.native_value is None

    def test_last_seen_sensor_device_class(self, mock_coordinator: MagicMock) -> None:
        """Test last seen sensor has timestamp device class."""
        sensor = TRMNLLastSeenSensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        assert sensor._attr_device_class == "timestamp"

    def test_last_seen_sensor_extra_attributes(self, mock_coordinator: MagicMock) -> None:
        """Test last seen sensor extra state attributes."""
        sensor = TRMNLLastSeenSensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        attrs = sensor.extra_state_attributes
        assert "device_id" in attrs
        assert "device_type" in attrs
        assert attrs["device_id"] == "device_1"
        assert attrs["device_type"] == "og"


class TestFirmwareVersionSensor:
    """Test TRMNL firmware version sensor."""

    def test_firmware_version_sensor_unique_id(self, mock_coordinator: MagicMock) -> None:
        """Test firmware version sensor unique ID."""
        sensor = TRMNLFirmwareVersionSensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        assert sensor.unique_id == "device_1_firmware"

    def test_firmware_version_sensor_name(self, mock_coordinator: MagicMock) -> None:
        """Test firmware version sensor friendly name."""
        sensor = TRMNLFirmwareVersionSensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        assert sensor.name == "Living Room Firmware Version"

    def test_firmware_version_sensor_native_value(self, mock_coordinator: MagicMock) -> None:
        """Test firmware version sensor returns firmware version."""
        sensor = TRMNLFirmwareVersionSensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        assert sensor.native_value == "1.0.0"

    def test_firmware_version_sensor_native_value_none(self, mock_coordinator: MagicMock) -> None:
        """Test firmware version sensor returns None when device not found."""
        sensor = TRMNLFirmwareVersionSensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        mock_coordinator.devices = {}
        assert sensor.native_value is None

    def test_firmware_version_sensor_extra_attributes(self, mock_coordinator: MagicMock) -> None:
        """Test firmware version sensor extra state attributes."""
        sensor = TRMNLFirmwareVersionSensor(mock_coordinator, "device_1", mock_coordinator.devices["device_1"])
        attrs = sensor.extra_state_attributes
        assert "status" in attrs
        assert "battery_level" in attrs
        assert attrs["status"] == "online"
        assert attrs["battery_level"] == 75


class TestSensorSetup:
    """Test sensor platform setup."""

    def test_sensors_created_for_devices(self, mock_coordinator: MagicMock) -> None:
        """Test that sensors are created for each device."""
        device = mock_coordinator.devices["device_1"]

        # Create battery sensor
        battery_sensor = TRMNLBatterySensor(mock_coordinator, "device_1", device)
        assert battery_sensor.unique_id == "device_1_battery"

        # Create last seen sensor
        last_seen_sensor = TRMNLLastSeenSensor(mock_coordinator, "device_1", device)
        assert last_seen_sensor.unique_id == "device_1_last_seen"

        # Create firmware sensor
        firmware_sensor = TRMNLFirmwareVersionSensor(mock_coordinator, "device_1", device)
        assert firmware_sensor.unique_id == "device_1_firmware"

        # All sensors should be properly created
        assert all([battery_sensor, last_seen_sensor, firmware_sensor])
