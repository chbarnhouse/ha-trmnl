"""Tests for WebSocket API."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.components.websocket_api import ActiveConnection, websocket_command

from ..api.exceptions import InvalidTokenError
from ..api.models import TRMNLDevice, DeviceStatus, DeviceType
from ..const import (
    CONF_TOKEN_SECRET,
    DOMAIN,
    WS_TYPE_GENERATE_TOKEN,
    WS_TYPE_GET_DEVICES,
    WS_TYPE_UPDATE_SCREENSHOT,
)
from ..coordinator import TRMNLCoordinator
from ..token_manager import TokenManager
from ..websocket.api import (
    handle_generate_token,
    handle_get_devices,
    handle_update_screenshot,
)


@pytest.fixture
def sample_device() -> TRMNLDevice:
    """Create a sample TRMNL device."""
    return TRMNLDevice(
        id="device_1",
        name="Living Room",
        device_type=DeviceType.OG,
        status=DeviceStatus.ONLINE,
        battery_level=85,
        firmware_version="1.0.0",
        last_seen=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_coordinator(sample_device: TRMNLDevice) -> MagicMock:
    """Create a mock coordinator."""
    coordinator = MagicMock(spec=TRMNLCoordinator)
    coordinator.devices = {"device_1": sample_device}
    coordinator.async_update_screenshot = AsyncMock(return_value=True)
    return coordinator


@pytest.fixture
def mock_hass(mock_coordinator: MagicMock) -> MagicMock:
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)

    # Set up data structure
    entry_id = "test_entry"
    token_secret = "test_secret_1234567890abcdef"

    hass.data = {
        DOMAIN: {
            entry_id: {
                "coordinator": mock_coordinator,
            }
        }
    }

    # Mock config entry
    mock_config_entry = MagicMock()
    mock_config_entry.data = {
        CONF_TOKEN_SECRET: token_secret,
    }

    hass.config_entries.async_get_entry = MagicMock(
        return_value=mock_config_entry
    )

    return hass


@pytest.fixture
def mock_connection() -> MagicMock:
    """Create a mock WebSocket connection."""
    connection = MagicMock(spec=ActiveConnection)
    connection.send_result = MagicMock()
    connection.send_error = MagicMock()
    return connection


class TestHandleGetDevices:
    """Test get_devices WebSocket handler."""

    @pytest.mark.asyncio
    async def test_get_devices_success(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test successful device retrieval."""
        msg = {
            "id": 123,
            "type": WS_TYPE_GET_DEVICES,
            "entry_id": "test_entry",
        }

        await handle_get_devices(mock_hass, mock_connection, msg)

        # Verify response
        assert mock_connection.send_result.called
        call_args = mock_connection.send_result.call_args
        assert call_args[0][0] == 123  # Message ID
        result = call_args[0][1]
        assert "devices" in result
        assert len(result["devices"]) == 1
        assert result["devices"][0]["id"] == "device_1"

    @pytest.mark.asyncio
    async def test_get_devices_missing_entry_id(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test get_devices with missing entry_id."""
        msg = {
            "id": 123,
            "type": WS_TYPE_GET_DEVICES,
        }

        await handle_get_devices(mock_hass, mock_connection, msg)

        # Verify error
        assert mock_connection.send_error.called
        call_args = mock_connection.send_error.call_args
        assert call_args[0][0] == 123  # Message ID

    @pytest.mark.asyncio
    async def test_get_devices_invalid_entry(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test get_devices with invalid entry."""
        msg = {
            "id": 123,
            "type": WS_TYPE_GET_DEVICES,
            "entry_id": "invalid_entry",
        }

        await handle_get_devices(mock_hass, mock_connection, msg)

        # Verify error
        assert mock_connection.send_error.called

    @pytest.mark.asyncio
    async def test_get_devices_device_details(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test that device details are correctly formatted."""
        msg = {
            "id": 123,
            "type": WS_TYPE_GET_DEVICES,
            "entry_id": "test_entry",
        }

        await handle_get_devices(mock_hass, mock_connection, msg)

        call_args = mock_connection.send_result.call_args
        result = call_args[0][1]
        device = result["devices"][0]

        assert device["name"] == "Living Room"
        assert device["device_type"] == "og"  # Enum value is lowercase
        assert device["status"] == "online"  # Enum value is lowercase
        assert device["battery_level"] == 85
        assert device["battery_low"] is False
        assert device["firmware_version"] == "1.0.0"
        assert device["is_online"] is True


class TestHandleGenerateToken:
    """Test generate_token WebSocket handler."""

    @pytest.mark.asyncio
    async def test_generate_token_success(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test successful token generation."""
        msg = {
            "id": 124,
            "type": WS_TYPE_GENERATE_TOKEN,
            "entry_id": "test_entry",
            "device_id": "device_1",
        }

        await handle_generate_token(mock_hass, mock_connection, msg)

        # Verify response
        assert mock_connection.send_result.called
        call_args = mock_connection.send_result.call_args
        assert call_args[0][0] == 124  # Message ID
        result = call_args[0][1]
        assert "token" in result
        assert "expires_at" in result
        assert result["token"].startswith("token_")

    @pytest.mark.asyncio
    async def test_generate_token_missing_entry_id(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test generate_token with missing entry_id."""
        msg = {
            "id": 124,
            "type": WS_TYPE_GENERATE_TOKEN,
            "device_id": "device_1",
        }

        await handle_generate_token(mock_hass, mock_connection, msg)

        # Verify error
        assert mock_connection.send_error.called

    @pytest.mark.asyncio
    async def test_generate_token_missing_device_id(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test generate_token with missing device_id."""
        msg = {
            "id": 124,
            "type": WS_TYPE_GENERATE_TOKEN,
            "entry_id": "test_entry",
        }

        await handle_generate_token(mock_hass, mock_connection, msg)

        # Verify error
        assert mock_connection.send_error.called

    @pytest.mark.asyncio
    async def test_generate_token_invalid_entry(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test generate_token with invalid entry."""
        msg = {
            "id": 124,
            "type": WS_TYPE_GENERATE_TOKEN,
            "entry_id": "invalid_entry",
            "device_id": "device_1",
        }

        await handle_generate_token(mock_hass, mock_connection, msg)

        # Verify error
        assert mock_connection.send_error.called

    @pytest.mark.asyncio
    async def test_generate_token_format(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test that generated token has correct format."""
        msg = {
            "id": 124,
            "type": WS_TYPE_GENERATE_TOKEN,
            "entry_id": "test_entry",
            "device_id": "device_1",
        }

        await handle_generate_token(mock_hass, mock_connection, msg)

        call_args = mock_connection.send_result.call_args
        result = call_args[0][1]
        token = result["token"]

        # Token should have format: token_<payload>_<signature>
        parts = token.split("_")
        assert len(parts) == 3
        assert parts[0] == "token"


class TestHandleUpdateScreenshot:
    """Test update_screenshot WebSocket handler."""

    @pytest.mark.asyncio
    async def test_update_screenshot_success(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test successful screenshot update."""
        # First generate a valid token
        token_manager = TokenManager("test_secret_1234567890abcdef")
        token = token_manager.generate_token("device_1")

        msg = {
            "id": 125,
            "type": WS_TYPE_UPDATE_SCREENSHOT,
            "entry_id": "test_entry",
            "device_id": "device_1",
            "image_url": "https://example.com/image.png",
            "token": token,
        }

        await handle_update_screenshot(mock_hass, mock_connection, msg)

        # Verify response
        assert mock_connection.send_result.called
        call_args = mock_connection.send_result.call_args
        assert call_args[0][0] == 125  # Message ID
        result = call_args[0][1]
        assert "success" in result
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_update_screenshot_invalid_token(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test screenshot update with invalid token."""
        msg = {
            "id": 125,
            "type": WS_TYPE_UPDATE_SCREENSHOT,
            "entry_id": "test_entry",
            "device_id": "device_1",
            "image_url": "https://example.com/image.png",
            "token": "invalid_token",
        }

        await handle_update_screenshot(mock_hass, mock_connection, msg)

        # Verify error - invalid token should send_error
        assert mock_connection.send_error.called

    @pytest.mark.asyncio
    async def test_update_screenshot_token_device_mismatch(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test screenshot update with token for different device."""
        token_manager = TokenManager("test_secret_1234567890abcdef")
        token = token_manager.generate_token("device_2")  # Token for different device

        msg = {
            "id": 125,
            "type": WS_TYPE_UPDATE_SCREENSHOT,
            "entry_id": "test_entry",
            "device_id": "device_1",  # But update device_1
            "image_url": "https://example.com/image.png",
            "token": token,
        }

        await handle_update_screenshot(mock_hass, mock_connection, msg)

        # Verify error
        assert mock_connection.send_error.called

    @pytest.mark.asyncio
    async def test_update_screenshot_missing_fields(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test screenshot update with missing required fields."""
        msg = {
            "id": 125,
            "type": WS_TYPE_UPDATE_SCREENSHOT,
            "entry_id": "test_entry",
            "device_id": "device_1",
            # Missing image_url and token
        }

        await handle_update_screenshot(mock_hass, mock_connection, msg)

        # Verify error
        assert mock_connection.send_error.called

    @pytest.mark.asyncio
    async def test_update_screenshot_calls_coordinator(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test that coordinator.async_update_screenshot is called."""
        token_manager = TokenManager("test_secret_1234567890abcdef")
        token = token_manager.generate_token("device_1")

        msg = {
            "id": 125,
            "type": WS_TYPE_UPDATE_SCREENSHOT,
            "entry_id": "test_entry",
            "device_id": "device_1",
            "image_url": "https://example.com/image.png",
            "token": token,
        }

        await handle_update_screenshot(mock_hass, mock_connection, msg)

        # Verify coordinator was called
        coordinator = mock_hass.data[DOMAIN]["test_entry"]["coordinator"]
        assert coordinator.async_update_screenshot.called
        call_args = coordinator.async_update_screenshot.call_args
        assert call_args[1]["device_id"] == "device_1"
        assert call_args[1]["image_url"] == "https://example.com/image.png"


class TestWebSocketIntegration:
    """Integration tests for WebSocket API."""

    @pytest.mark.asyncio
    async def test_workflow_generate_then_update(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test complete workflow: generate token then update screenshot."""
        # Step 1: Generate token
        gen_msg = {
            "id": 124,
            "type": WS_TYPE_GENERATE_TOKEN,
            "entry_id": "test_entry",
            "device_id": "device_1",
        }

        await handle_generate_token(mock_hass, mock_connection, gen_msg)

        # Extract token from response
        gen_call_args = mock_connection.send_result.call_args
        token = gen_call_args[0][1]["token"]

        # Reset mock
        mock_connection.reset_mock()

        # Step 2: Update screenshot with generated token
        update_msg = {
            "id": 125,
            "type": WS_TYPE_UPDATE_SCREENSHOT,
            "entry_id": "test_entry",
            "device_id": "device_1",
            "image_url": "https://example.com/image.png",
            "token": token,
        }

        await handle_update_screenshot(mock_hass, mock_connection, update_msg)

        # Verify success
        assert mock_connection.send_result.called
        result = mock_connection.send_result.call_args[0][1]
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_multiple_devices(
        self, mock_hass: MagicMock, mock_connection: MagicMock
    ) -> None:
        """Test handling multiple devices."""
        # Add another device
        device2 = TRMNLDevice(
            id="device_2",
            name="Bedroom",
            device_type=DeviceType.X,
            status=DeviceStatus.ONLINE,
            battery_level=45,
            firmware_version="1.1.0",
            last_seen=datetime.now(timezone.utc),
        )

        coordinator = mock_hass.data[DOMAIN]["test_entry"]["coordinator"]
        coordinator.devices["device_2"] = device2

        # Get devices
        get_msg = {
            "id": 123,
            "type": WS_TYPE_GET_DEVICES,
            "entry_id": "test_entry",
        }

        await handle_get_devices(mock_hass, mock_connection, get_msg)

        # Verify both devices returned
        call_args = mock_connection.send_result.call_args
        result = call_args[0][1]
        assert len(result["devices"]) == 2

        device_ids = [d["id"] for d in result["devices"]]
        assert "device_1" in device_ids
        assert "device_2" in device_ids
