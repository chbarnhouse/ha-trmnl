"""Tests for TRMNL Cloud API client."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

from aiohttp import ClientError

from ..api.cloud import CloudAPIClient
from ..api.models import TRMNLDevice, TRMNLPlugin, MergeVars, DeviceType, DeviceStatus
from ..api.exceptions import (
    InvalidAPIKeyError,
    DeviceDiscoveryError,
    UpdateScreenshotError,
    ConnectionError as TRMNLConnectionError,
)

pytestmark = pytest.mark.asyncio


def create_mock_response(status, json_data=None):
    """Create a mock aiohttp response."""
    mock_response = MagicMock()
    mock_response.status = status
    if json_data is not None:
        mock_response.json = AsyncMock(return_value=json_data)
    return mock_response


def create_mock_session_method(response_or_error):
    """Create a mock session.get or session.post method that returns the response."""
    @asynccontextmanager
    async def context_manager(*args, **kwargs):
        if isinstance(response_or_error, Exception):
            raise response_or_error
        yield response_or_error

    return MagicMock(side_effect=context_manager)


class TestCloudAPIClientCredentials:
    """Test CloudAPIClient credential validation."""

    async def test_validate_credentials_success(self):
        """Test validating credentials with valid API key."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response = create_mock_response(200)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        result = await client.validate_credentials()

        assert result is True
        mock_session.get.assert_called_once()

    async def test_validate_credentials_invalid_api_key(self):
        """Test validating credentials with invalid API key."""
        client = CloudAPIClient(api_key="invalid_key")

        mock_response = create_mock_response(401)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        with pytest.raises(InvalidAPIKeyError):
            await client.validate_credentials()

    async def test_validate_credentials_server_error(self):
        """Test validating credentials with server error."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response = create_mock_response(500)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        with pytest.raises(TRMNLConnectionError):
            await client.validate_credentials()

    async def test_validate_credentials_connection_error(self):
        """Test validating credentials with connection error."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(ClientError("Connection failed"))
        client.session = mock_session

        with pytest.raises(TRMNLConnectionError):
            await client.validate_credentials()


class TestCloudAPIClientGetDevices:
    """Test CloudAPIClient device discovery."""

    async def test_get_devices_success(self):
        """Test successful device discovery."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response_data = {
            "devices": [
                {
                    "id": "device1",
                    "name": "Living Room",
                    "device_type": "og",
                    "battery_level": 85,
                    "last_seen": "2025-01-01T12:00:00",
                    "firmware_version": "1.0.0",
                    "status": "online",
                    "attributes": {},
                },
                {
                    "id": "device2",
                    "name": "Bedroom",
                    "device_type": "x",
                    "battery_level": 50,
                    "last_seen": "2025-01-01T11:00:00",
                    "firmware_version": "1.0.0",
                    "status": "offline",
                    "attributes": {},
                },
            ]
        }

        mock_response = create_mock_response(200, mock_response_data)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        devices = await client.get_devices()

        assert len(devices) == 2
        assert devices[0].id == "device1"
        assert devices[0].name == "Living Room"
        assert devices[0].device_type == DeviceType.OG
        assert devices[0].battery_level == 85
        assert devices[0].status == DeviceStatus.ONLINE

        assert devices[1].id == "device2"
        assert devices[1].device_type == DeviceType.X
        assert devices[1].status == DeviceStatus.OFFLINE

    async def test_get_devices_empty(self):
        """Test device discovery with no devices."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response_data = {"devices": []}

        mock_response = create_mock_response(200, mock_response_data)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        devices = await client.get_devices()

        assert len(devices) == 0

    async def test_get_devices_invalid_api_key(self):
        """Test device discovery with invalid API key."""
        client = CloudAPIClient(api_key="invalid_key")

        mock_response = create_mock_response(401)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        with pytest.raises(InvalidAPIKeyError):
            await client.get_devices()

    async def test_get_devices_server_error(self):
        """Test device discovery with server error."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response = create_mock_response(500)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        with pytest.raises(DeviceDiscoveryError):
            await client.get_devices()

    async def test_get_devices_connection_error(self):
        """Test device discovery with connection error."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(ClientError("Connection failed"))
        client.session = mock_session

        with pytest.raises(DeviceDiscoveryError):
            await client.get_devices()

    async def test_get_devices_malformed_response(self):
        """Test device discovery with malformed response."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response_data = {
            "devices": [
                {
                    # Missing required 'id' field
                    "name": "Invalid Device",
                    "device_type": "og",
                }
            ]
        }

        mock_response = create_mock_response(200, mock_response_data)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        # Should skip malformed device and return empty list
        devices = await client.get_devices()
        assert len(devices) == 0


class TestCloudAPIClientGetPlugin:
    """Test CloudAPIClient plugin retrieval."""

    async def test_get_plugin_success(self):
        """Test successful plugin retrieval."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response_data = {
            "uuid": "plugin_uuid_123",
            "name": "Home Assistant Screenshot",
            "version": "0.1.0",
            "description": "Display HA screenshots on TRMNL",
        }

        mock_response = create_mock_response(200, mock_response_data)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        plugin = await client.get_plugin("plugin_uuid_123")

        assert plugin is not None
        assert plugin.uuid == "plugin_uuid_123"
        assert plugin.name == "Home Assistant Screenshot"
        assert plugin.version == "0.1.0"

    async def test_get_plugin_not_found(self):
        """Test plugin retrieval when plugin not found."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response = create_mock_response(404)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        plugin = await client.get_plugin("nonexistent_plugin")

        assert plugin is None

    async def test_get_plugin_invalid_api_key(self):
        """Test plugin retrieval with invalid API key."""
        client = CloudAPIClient(api_key="invalid_key")

        mock_response = create_mock_response(401)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        with pytest.raises(InvalidAPIKeyError):
            await client.get_plugin("plugin_uuid_123")

    async def test_get_plugin_server_error(self):
        """Test plugin retrieval with server error."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response = create_mock_response(500)
        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(mock_response)
        client.session = mock_session

        plugin = await client.get_plugin("plugin_uuid_123")

        assert plugin is None

    async def test_get_plugin_connection_error(self):
        """Test plugin retrieval with connection error."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_session = MagicMock()
        mock_session.get = create_mock_session_method(ClientError("Connection failed"))
        client.session = mock_session

        plugin = await client.get_plugin("plugin_uuid_123")

        assert plugin is None


class TestCloudAPIClientUpdateVariables:
    """Test CloudAPIClient plugin variable updates."""

    async def test_update_variables_success(self):
        """Test successful variable update."""
        client = CloudAPIClient(api_key="test_api_key_123")

        merge_vars = MergeVars(
            device_id="device1",
            ha_image_url="https://example.com/image.png",
            ha_auth_token="test_token_123",
            ha_token_expires="2025-01-02T12:00:00",
            last_updated="2025-01-01T12:00:00",
        )

        mock_response = create_mock_response(200)
        mock_session = MagicMock()
        mock_session.post = create_mock_session_method(mock_response)
        client.session = mock_session

        result = await client.update_plugin_variables(
            plugin_uuid="plugin_uuid_123",
            device_id="device1",
            merge_vars=merge_vars,
        )

        assert result is True
        mock_session.post.assert_called_once()
        # Verify the payload includes merge_vars
        call_args = mock_session.post.call_args
        assert call_args[1]["json"]["device_id"] == "device1"

    async def test_update_variables_plugin_not_found(self):
        """Test variable update when plugin not found."""
        client = CloudAPIClient(api_key="test_api_key_123")

        merge_vars = MergeVars(
            device_id="device1",
            ha_image_url="https://example.com/image.png",
            ha_auth_token="test_token_123",
            ha_token_expires="2025-01-02T12:00:00",
            last_updated="2025-01-01T12:00:00",
        )

        mock_response = create_mock_response(404)
        mock_session = MagicMock()
        mock_session.post = create_mock_session_method(mock_response)
        client.session = mock_session

        with pytest.raises(UpdateScreenshotError):
            await client.update_plugin_variables(
                plugin_uuid="nonexistent_plugin",
                device_id="device1",
                merge_vars=merge_vars,
            )

    async def test_update_variables_invalid_api_key(self):
        """Test variable update with invalid API key."""
        client = CloudAPIClient(api_key="invalid_key")

        merge_vars = MergeVars(
            device_id="device1",
            ha_image_url="https://example.com/image.png",
            ha_auth_token="test_token_123",
            ha_token_expires="2025-01-02T12:00:00",
            last_updated="2025-01-01T12:00:00",
        )

        mock_response = create_mock_response(401)
        mock_session = MagicMock()
        mock_session.post = create_mock_session_method(mock_response)
        client.session = mock_session

        with pytest.raises(InvalidAPIKeyError):
            await client.update_plugin_variables(
                plugin_uuid="plugin_uuid_123",
                device_id="device1",
                merge_vars=merge_vars,
            )

    async def test_update_variables_server_error(self):
        """Test variable update with server error."""
        client = CloudAPIClient(api_key="test_api_key_123")

        merge_vars = MergeVars(
            device_id="device1",
            ha_image_url="https://example.com/image.png",
            ha_auth_token="test_token_123",
            ha_token_expires="2025-01-02T12:00:00",
            last_updated="2025-01-01T12:00:00",
        )

        mock_response = create_mock_response(500)
        mock_session = MagicMock()
        mock_session.post = create_mock_session_method(mock_response)
        client.session = mock_session

        with pytest.raises(UpdateScreenshotError):
            await client.update_plugin_variables(
                plugin_uuid="plugin_uuid_123",
                device_id="device1",
                merge_vars=merge_vars,
            )

    async def test_update_variables_connection_error(self):
        """Test variable update with connection error."""
        client = CloudAPIClient(api_key="test_api_key_123")

        merge_vars = MergeVars(
            device_id="device1",
            ha_image_url="https://example.com/image.png",
            ha_auth_token="test_token_123",
            ha_token_expires="2025-01-02T12:00:00",
            last_updated="2025-01-01T12:00:00",
        )

        mock_session = MagicMock()
        mock_session.post = create_mock_session_method(ClientError("Connection failed"))
        client.session = mock_session

        with pytest.raises(UpdateScreenshotError):
            await client.update_plugin_variables(
                plugin_uuid="plugin_uuid_123",
                device_id="device1",
                merge_vars=merge_vars,
            )


class TestCloudAPIClientTriggerRefresh:
    """Test CloudAPIClient device refresh."""

    async def test_trigger_refresh_success(self):
        """Test successful refresh trigger."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response = create_mock_response(200)
        mock_session = MagicMock()
        mock_session.post = create_mock_session_method(mock_response)
        client.session = mock_session

        result = await client.trigger_refresh(device_id="device1")

        assert result is True
        mock_session.post.assert_called_once()

    async def test_trigger_refresh_device_not_found(self):
        """Test refresh trigger when device not found."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response = create_mock_response(404)
        mock_session = MagicMock()
        mock_session.post = create_mock_session_method(mock_response)
        client.session = mock_session

        result = await client.trigger_refresh(device_id="nonexistent_device")

        assert result is False

    async def test_trigger_refresh_invalid_api_key(self):
        """Test refresh trigger with invalid API key."""
        client = CloudAPIClient(api_key="invalid_key")

        mock_response = create_mock_response(401)
        mock_session = MagicMock()
        mock_session.post = create_mock_session_method(mock_response)
        client.session = mock_session

        with pytest.raises(InvalidAPIKeyError):
            await client.trigger_refresh(device_id="device1")

    async def test_trigger_refresh_server_error(self):
        """Test refresh trigger with server error."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_response = create_mock_response(500)
        mock_session = MagicMock()
        mock_session.post = create_mock_session_method(mock_response)
        client.session = mock_session

        result = await client.trigger_refresh(device_id="device1")

        assert result is False

    async def test_trigger_refresh_connection_error(self):
        """Test refresh trigger with connection error."""
        client = CloudAPIClient(api_key="test_api_key_123")

        mock_session = MagicMock()
        mock_session.post = create_mock_session_method(ClientError("Connection failed"))
        client.session = mock_session

        result = await client.trigger_refresh(device_id="device1")

        assert result is False


class TestCloudAPIClientHeaders:
    """Test CloudAPIClient header building."""

    def test_build_headers(self):
        """Test building request headers."""
        client = CloudAPIClient(api_key="test_api_key_123")

        headers = client._build_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_api_key_123"
        assert headers["Content-Type"] == "application/json"
        assert "User-Agent" in headers

    def test_build_headers_different_api_key(self):
        """Test building headers with different API key."""
        api_key = "different_key_456"
        client = CloudAPIClient(api_key=api_key)

        headers = client._build_headers()

        assert headers["Authorization"] == f"Bearer {api_key}"


class TestCloudAPIClientContextManager:
    """Test CloudAPIClient context manager support."""

    async def test_context_manager(self):
        """Test using CloudAPIClient as context manager."""
        async with CloudAPIClient(api_key="test_api_key_123") as client:
            assert client is not None
            assert client.api_key == "test_api_key_123"

    async def test_context_manager_closes_session(self):
        """Test that context manager closes owned session."""
        client = CloudAPIClient(api_key="test_api_key_123")

        # Manually create a session (simulating _get_session behavior)
        mock_session = MagicMock()
        mock_session.close = AsyncMock()
        client.session = mock_session
        client._session_owned = True

        await client.close()

        mock_session.close.assert_called_once()
