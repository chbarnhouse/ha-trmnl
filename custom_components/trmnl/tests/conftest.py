"""Pytest configuration and fixtures for TRMNL integration tests."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Generator

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.config_entries import ConfigEntry

from ..const import (
    DOMAIN,
    CONF_SERVER_TYPE,
    CONF_API_KEY,
    CONF_DEVICES,
    CONF_TOKEN_SECRET,
    SERVER_TYPE_CLOUD,
)
from ..api.models import TRMNLDevice, DeviceType, DeviceStatus


@pytest.fixture
def hass():
    """Return Home Assistant instance."""
    # This will be mocked in actual tests
    pass


@pytest.fixture
def config_entry() -> ConfigEntry:
    """Return a mock config entry."""
    return MagicMock(spec=ConfigEntry)


@pytest.fixture
def mock_cloud_api():
    """Return a mock Cloud API client."""
    mock = AsyncMock()
    mock.validate_credentials = AsyncMock(return_value=True)
    mock.get_devices = AsyncMock(return_value=[
        TRMNLDevice(
            id="device1",
            name="Living Room",
            device_type=DeviceType.OG,
            battery_level=85,
            status=DeviceStatus.ONLINE,
        ),
        TRMNLDevice(
            id="device2",
            name="Bedroom",
            device_type=DeviceType.X,
            battery_level=45,
            status=DeviceStatus.ONLINE,
        ),
    ])
    mock.get_plugin = AsyncMock(return_value=None)
    mock.update_plugin_variables = AsyncMock(return_value=True)
    mock.trigger_refresh = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_byos_api():
    """Return a mock BYOS API client."""
    mock = AsyncMock()
    mock.validate_credentials = AsyncMock(return_value=True)
    mock.get_devices = AsyncMock(return_value=[
        TRMNLDevice(
            id="device3",
            name="Local Device",
            device_type=DeviceType.OG,
            battery_level=70,
            status=DeviceStatus.ONLINE,
        ),
    ])
    mock.get_plugin = AsyncMock(return_value=None)
    mock.update_plugin_variables = AsyncMock(return_value=True)
    mock.trigger_refresh = AsyncMock(return_value=False)  # BYOS may not support this
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_coordinator():
    """Return a mock data coordinator."""
    mock = AsyncMock()
    mock.async_request_refresh = AsyncMock()
    mock.async_config_entry_first_refresh = AsyncMock()
    mock.data = {
        "devices": [
            TRMNLDevice(
                id="device1",
                name="Living Room",
                device_type=DeviceType.OG,
                battery_level=85,
                status=DeviceStatus.ONLINE,
            ),
        ]
    }
    return mock


@pytest.fixture
def cloud_config() -> dict:
    """Return Cloud configuration."""
    return {
        CONF_SERVER_TYPE: SERVER_TYPE_CLOUD,
        CONF_API_KEY: "test_api_key_12345",
        CONF_DEVICES: ["device1", "device2"],
        CONF_TOKEN_SECRET: "test_token_secret_32_bytes_long_enough",
    }


@pytest.fixture
def byos_config() -> dict:
    """Return BYOS configuration."""
    return {
        CONF_SERVER_TYPE: "byos",
        "server_url": "http://192.168.1.100:8000",
        "auth_type": "api_key",
        CONF_API_KEY: "test_api_key",
        CONF_DEVICES: ["device3"],
        CONF_TOKEN_SECRET: "test_token_secret_32_bytes_long_enough",
    }


@pytest.fixture
def sample_device() -> TRMNLDevice:
    """Return a sample device."""
    return TRMNLDevice(
        id="test_device_123",
        name="Test Device",
        device_type=DeviceType.OG,
        battery_level=75,
        last_seen=datetime.now(),
        firmware_version="1.2.3",
        status=DeviceStatus.ONLINE,
    )


@pytest.fixture
def sample_devices() -> list[TRMNLDevice]:
    """Return sample devices."""
    return [
        TRMNLDevice(
            id="device1",
            name="Living Room",
            device_type=DeviceType.OG,
            battery_level=85,
            last_seen=datetime.now() - timedelta(minutes=5),
            firmware_version="1.2.3",
            status=DeviceStatus.ONLINE,
        ),
        TRMNLDevice(
            id="device2",
            name="Bedroom",
            device_type=DeviceType.X,
            battery_level=45,
            last_seen=datetime.now() - timedelta(hours=2),
            firmware_version="1.2.4",
            status=DeviceStatus.ONLINE,
        ),
        TRMNLDevice(
            id="device3",
            name="Offline Device",
            device_type=DeviceType.OG,
            battery_level=10,
            last_seen=datetime.now() - timedelta(days=1),
            firmware_version="1.1.0",
            status=DeviceStatus.OFFLINE,
        ),
    ]


@pytest.fixture
def sample_merge_vars() -> dict:
    """Return sample merge variables."""
    now = datetime.now()
    expires = now + timedelta(hours=24)
    return {
        "ha_image_url": "https://ha.example.com/api/trmnl/screenshot/device1",
        "ha_auth_token": "token_device1_1699284000_abcd1234efgh5678",
        "ha_token_expires": expires.isoformat(),
        "last_updated": now.isoformat(),
        "device_id": "device1",
    }


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
