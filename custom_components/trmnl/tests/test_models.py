"""Tests for TRMNL API models."""

import pytest
from datetime import datetime, timedelta

from ..api.models import (
    TRMNLDevice,
    TRMNLPlugin,
    MergeVars,
    DeviceUpdateRequest,
    DevicePlaylist,
    APIResponse,
    DeviceType,
    DeviceStatus,
)


class TestTRMNLDevice:
    """Test TRMNLDevice model."""

    def test_device_creation(self, sample_device):
        """Test creating a device."""
        assert sample_device.id == "test_device_123"
        assert sample_device.name == "Test Device"
        assert sample_device.device_type == DeviceType.OG

    def test_device_unique_id(self, sample_device):
        """Test device unique ID generation."""
        assert sample_device.unique_id == "trmnl_test_device_123"

    def test_device_is_online(self):
        """Test device online status."""
        online = TRMNLDevice(
            id="dev1",
            name="Online",
            device_type=DeviceType.OG,
            status=DeviceStatus.ONLINE,
        )
        offline = TRMNLDevice(
            id="dev2",
            name="Offline",
            device_type=DeviceType.OG,
            status=DeviceStatus.OFFLINE,
        )
        assert online.is_online is True
        assert offline.is_online is False

    def test_device_battery_low(self):
        """Test battery low detection."""
        high_battery = TRMNLDevice(
            id="dev1",
            name="High Battery",
            device_type=DeviceType.OG,
            battery_level=50,
        )
        low_battery = TRMNLDevice(
            id="dev2",
            name="Low Battery",
            device_type=DeviceType.OG,
            battery_level=15,
        )
        assert high_battery.battery_low is False
        assert low_battery.battery_low is True

    def test_device_battery_low_none(self):
        """Test battery low when battery level is None."""
        device = TRMNLDevice(
            id="dev1",
            name="No Battery",
            device_type=DeviceType.OG,
            battery_level=None,
        )
        assert device.battery_low is False

    def test_device_to_dict(self, sample_device):
        """Test device to_dict conversion."""
        device_dict = sample_device.to_dict()
        assert device_dict["id"] == "test_device_123"
        assert device_dict["name"] == "Test Device"
        assert device_dict["device_type"] == "og"
        assert device_dict["battery_level"] == 75
        assert device_dict["status"] == "online"


class TestTRMNLPlugin:
    """Test TRMNLPlugin model."""

    def test_plugin_creation(self):
        """Test creating a plugin."""
        plugin = TRMNLPlugin(
            uuid="plugin_uuid_123",
            name="Test Plugin",
            version="0.1.0",
            description="Test description",
        )
        assert plugin.uuid == "plugin_uuid_123"
        assert plugin.name == "Test Plugin"
        assert plugin.version == "0.1.0"

    def test_plugin_supported_devices(self):
        """Test plugin supported devices."""
        plugin = TRMNLPlugin(
            uuid="plugin_uuid_123",
            name="Test Plugin",
            version="0.1.0",
        )
        assert "og" in plugin.supported_devices
        assert "x" in plugin.supported_devices

    def test_plugin_to_dict(self):
        """Test plugin to_dict conversion."""
        plugin = TRMNLPlugin(
            uuid="plugin_uuid_123",
            name="Test Plugin",
            version="0.1.0",
        )
        plugin_dict = plugin.to_dict()
        assert plugin_dict["uuid"] == "plugin_uuid_123"
        assert plugin_dict["name"] == "Test Plugin"
        assert plugin_dict["version"] == "0.1.0"


class TestMergeVars:
    """Test MergeVars model."""

    def test_merge_vars_creation(self, sample_merge_vars):
        """Test creating merge variables."""
        merge_vars = MergeVars(**sample_merge_vars)
        assert merge_vars.device_id == "device1"
        assert merge_vars.ha_image_url == "https://ha.example.com/api/trmnl/screenshot/device1"

    def test_merge_vars_to_dict(self, sample_merge_vars):
        """Test merge variables to_dict conversion."""
        merge_vars = MergeVars(**sample_merge_vars)
        vars_dict = merge_vars.to_dict()
        assert vars_dict["device_id"] == "device1"
        assert "ha_image_url" in vars_dict
        assert "ha_auth_token" in vars_dict


class TestDeviceUpdateRequest:
    """Test DeviceUpdateRequest model."""

    def test_update_request_creation(self):
        """Test creating update request."""
        request = DeviceUpdateRequest(
            device_id="device1",
            image_url="https://example.com/image.png",
            token="test_token_123",
        )
        assert request.device_id == "device1"
        assert request.image_url == "https://example.com/image.png"
        assert request.token == "test_token_123"

    def test_update_request_to_dict(self):
        """Test update request to_dict conversion."""
        request = DeviceUpdateRequest(
            device_id="device1",
            image_url="https://example.com/image.png",
            token="test_token_123",
        )
        request_dict = request.to_dict()
        assert request_dict["device_id"] == "device1"
        assert request_dict["image_url"] == "https://example.com/image.png"
        assert request_dict["token"] == "test_token_123"

    def test_update_request_without_token(self):
        """Test update request without token."""
        request = DeviceUpdateRequest(
            device_id="device1",
            image_url="https://example.com/image.png",
        )
        request_dict = request.to_dict()
        assert "token" not in request_dict


class TestAPIResponse:
    """Test APIResponse model."""

    def test_success_response(self):
        """Test success response."""
        response = APIResponse(
            status="success",
            data={"result": "ok"},
            message="Operation completed",
        )
        assert response.is_success() is True
        assert response.status == "success"

    def test_error_response(self):
        """Test error response."""
        response = APIResponse(
            status="error",
            error="Invalid API key",
            message="Authentication failed",
        )
        assert response.is_success() is False
        assert response.error == "Invalid API key"

    def test_response_to_dict(self):
        """Test response to_dict conversion."""
        response = APIResponse(
            status="success",
            data={"result": "ok"},
        )
        response_dict = response.to_dict()
        assert response_dict["status"] == "success"
        assert response_dict["data"] == {"result": "ok"}


class TestDevicePlaylist:
    """Test DevicePlaylist model."""

    def test_playlist_creation(self):
        """Test creating playlist."""
        playlist = DevicePlaylist(
            device_id="device1",
            plugins=["plugin1", "plugin2"],
            refresh_interval=15,
        )
        assert playlist.device_id == "device1"
        assert len(playlist.plugins) == 2
        assert playlist.refresh_interval == 15

    def test_playlist_default_interval(self):
        """Test playlist default refresh interval."""
        playlist = DevicePlaylist(device_id="device1")
        assert playlist.refresh_interval == 15

    def test_playlist_to_dict(self):
        """Test playlist to_dict conversion."""
        playlist = DevicePlaylist(
            device_id="device1",
            plugins=["plugin1"],
        )
        playlist_dict = playlist.to_dict()
        assert playlist_dict["device_id"] == "device1"
        assert playlist_dict["plugins"] == ["plugin1"]
