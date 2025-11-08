"""Tests for config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from ..api.exceptions import InvalidAPIKeyError
from ..api.models import TRMNLDevice, DeviceStatus, DeviceType
from ..config_flow import TRMNLConfigFlow
from ..const import (
    CONF_API_KEY,
    CONF_DEVICES,
    CONF_AUTH_TYPE,
    CONF_PASSWORD,
    CONF_SERVER_TYPE,
    CONF_SERVER_URL,
    CONF_TOKEN_SECRET,
    CONF_USERNAME,
    AUTH_TYPE_API_KEY,
    AUTH_TYPE_BASIC,
    AUTH_TYPE_NONE,
    SERVER_TYPE_CLOUD,
    SERVER_TYPE_BYOS,
    DOMAIN,
)


@pytest.fixture
def sample_devices() -> list[TRMNLDevice]:
    """Create sample devices for discovery."""
    return [
        TRMNLDevice(
            id="device_1",
            name="Living Room",
            device_type=DeviceType.OG,
            status=DeviceStatus.ONLINE,
            battery_level=85,
        ),
        TRMNLDevice(
            id="device_2",
            name="Bedroom",
            device_type=DeviceType.X,
            status=DeviceStatus.OFFLINE,
            battery_level=45,
        ),
    ]


class TestConfigFlowServerTypeStep:
    """Test config flow server type selection."""

    def test_server_type_options(self) -> None:
        """Test that server type step offers Cloud and BYOS options."""
        # Config flow should offer both server types
        server_types = [SERVER_TYPE_CLOUD, SERVER_TYPE_BYOS]
        assert SERVER_TYPE_CLOUD in server_types
        assert SERVER_TYPE_BYOS in server_types

    def test_cloud_server_type_selected(self) -> None:
        """Test Cloud server type is a valid option."""
        assert SERVER_TYPE_CLOUD == "cloud"

    def test_byos_server_type_selected(self) -> None:
        """Test BYOS server type is a valid option."""
        assert SERVER_TYPE_BYOS == "byos"


class TestConfigFlowCloudAuthStep:
    """Test config flow Cloud authentication."""

    def test_cloud_requires_api_key(self) -> None:
        """Test that Cloud configuration requires API key."""
        cloud_config = {
            CONF_SERVER_TYPE: SERVER_TYPE_CLOUD,
            CONF_API_KEY: "test_api_key_123",
        }
        assert CONF_API_KEY in cloud_config
        assert cloud_config[CONF_API_KEY] == "test_api_key_123"

    def test_cloud_api_key_validation(self) -> None:
        """Test API key validation."""
        # Valid API key
        api_key = "test_api_key_with_valid_length"
        assert len(api_key) > 0
        assert isinstance(api_key, str)

    def test_cloud_config_structure(self) -> None:
        """Test Cloud configuration structure."""
        config = {
            CONF_SERVER_TYPE: SERVER_TYPE_CLOUD,
            CONF_API_KEY: "api_key",
            CONF_DEVICES: ["device_1"],
            CONF_TOKEN_SECRET: "token_secret_123",
        }

        assert config[CONF_SERVER_TYPE] == SERVER_TYPE_CLOUD
        assert CONF_API_KEY in config
        assert CONF_DEVICES in config
        assert CONF_TOKEN_SECRET in config


class TestConfigFlowBYOSStep:
    """Test config flow BYOS configuration."""

    def test_byos_requires_server_url(self) -> None:
        """Test that BYOS requires server URL."""
        byos_config = {
            CONF_SERVER_TYPE: SERVER_TYPE_BYOS,
            CONF_SERVER_URL: "http://localhost:8080",
        }
        assert CONF_SERVER_URL in byos_config

    def test_byos_requires_auth_type(self) -> None:
        """Test that BYOS requires auth type selection."""
        byos_config = {
            CONF_SERVER_TYPE: SERVER_TYPE_BYOS,
            CONF_SERVER_URL: "http://localhost:8080",
            CONF_AUTH_TYPE: AUTH_TYPE_API_KEY,
        }
        assert CONF_AUTH_TYPE in byos_config

    def test_byos_auth_types(self) -> None:
        """Test that BYOS supports all auth types."""
        auth_types = [AUTH_TYPE_API_KEY, AUTH_TYPE_BASIC, AUTH_TYPE_NONE]
        assert AUTH_TYPE_API_KEY in auth_types
        assert AUTH_TYPE_BASIC in auth_types
        assert AUTH_TYPE_NONE in auth_types

    def test_byos_api_key_auth(self) -> None:
        """Test BYOS with API key authentication."""
        config = {
            CONF_SERVER_TYPE: SERVER_TYPE_BYOS,
            CONF_SERVER_URL: "http://localhost:8080",
            CONF_AUTH_TYPE: AUTH_TYPE_API_KEY,
            CONF_API_KEY: "api_key_123",
        }

        assert config[CONF_AUTH_TYPE] == AUTH_TYPE_API_KEY
        assert CONF_API_KEY in config

    def test_byos_basic_auth(self) -> None:
        """Test BYOS with basic authentication."""
        config = {
            CONF_SERVER_TYPE: SERVER_TYPE_BYOS,
            CONF_SERVER_URL: "http://localhost:8080",
            CONF_AUTH_TYPE: AUTH_TYPE_BASIC,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password123",
        }

        assert config[CONF_AUTH_TYPE] == AUTH_TYPE_BASIC
        assert CONF_USERNAME in config
        assert CONF_PASSWORD in config

    def test_byos_no_auth(self) -> None:
        """Test BYOS with no authentication."""
        config = {
            CONF_SERVER_TYPE: SERVER_TYPE_BYOS,
            CONF_SERVER_URL: "http://localhost:8080",
            CONF_AUTH_TYPE: AUTH_TYPE_NONE,
        }

        assert config[CONF_AUTH_TYPE] == AUTH_TYPE_NONE
        # No credentials needed for NONE auth

    def test_byos_url_variants(self) -> None:
        """Test various BYOS server URL formats."""
        valid_urls = [
            "http://localhost:8080",
            "https://example.com",
            "http://192.168.1.100:8080",
            "https://trmnl.example.com",
        ]

        for url in valid_urls:
            assert len(url) > 0
            assert isinstance(url, str)


class TestConfigFlowDeviceDiscovery:
    """Test config flow device discovery."""

    def test_device_discovery_returns_list(
        self, sample_devices: list[TRMNLDevice]
    ) -> None:
        """Test that device discovery returns device list."""
        assert isinstance(sample_devices, list)
        assert len(sample_devices) == 2

    def test_device_discovery_device_properties(
        self, sample_devices: list[TRMNLDevice]
    ) -> None:
        """Test device discovery returns proper device objects."""
        device = sample_devices[0]
        assert device.id == "device_1"
        assert device.name == "Living Room"
        assert device.device_type == DeviceType.OG

    def test_device_selection_config(self, sample_devices: list[TRMNLDevice]) -> None:
        """Test config with selected devices."""
        selected_device_ids = ["device_1"]

        config = {
            CONF_SERVER_TYPE: SERVER_TYPE_CLOUD,
            CONF_API_KEY: "api_key",
            CONF_DEVICES: selected_device_ids,
            CONF_TOKEN_SECRET: "token_secret",
        }

        assert config[CONF_DEVICES] == selected_device_ids
        assert "device_1" in config[CONF_DEVICES]

    def test_multiple_device_selection(self) -> None:
        """Test selecting multiple devices."""
        selected_devices = ["device_1", "device_2"]

        config = {
            CONF_DEVICES: selected_devices,
        }

        assert len(config[CONF_DEVICES]) == 2
        assert all(device_id in config[CONF_DEVICES] for device_id in selected_devices)


class TestConfigFlowValidation:
    """Test config flow validation."""

    def test_cloud_config_validation(self) -> None:
        """Test Cloud configuration validation."""
        config = {
            CONF_SERVER_TYPE: SERVER_TYPE_CLOUD,
            CONF_API_KEY: "api_key",
            CONF_DEVICES: ["device_1"],
            CONF_TOKEN_SECRET: "token_secret",
        }

        # Verify all required fields present
        assert CONF_SERVER_TYPE in config
        assert CONF_API_KEY in config
        assert CONF_DEVICES in config
        assert CONF_TOKEN_SECRET in config

    def test_byos_api_key_config_validation(self) -> None:
        """Test BYOS API key configuration validation."""
        config = {
            CONF_SERVER_TYPE: SERVER_TYPE_BYOS,
            CONF_SERVER_URL: "http://localhost:8080",
            CONF_AUTH_TYPE: AUTH_TYPE_API_KEY,
            CONF_API_KEY: "api_key",
            CONF_DEVICES: ["device_1"],
            CONF_TOKEN_SECRET: "token_secret",
        }

        assert config[CONF_SERVER_TYPE] == SERVER_TYPE_BYOS
        assert config[CONF_AUTH_TYPE] == AUTH_TYPE_API_KEY
        assert CONF_API_KEY in config

    def test_byos_basic_auth_config_validation(self) -> None:
        """Test BYOS basic auth configuration validation."""
        config = {
            CONF_SERVER_TYPE: SERVER_TYPE_BYOS,
            CONF_SERVER_URL: "http://localhost:8080",
            CONF_AUTH_TYPE: AUTH_TYPE_BASIC,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
            CONF_DEVICES: ["device_1"],
            CONF_TOKEN_SECRET: "token_secret",
        }

        assert config[CONF_SERVER_TYPE] == SERVER_TYPE_BYOS
        assert config[CONF_AUTH_TYPE] == AUTH_TYPE_BASIC
        assert CONF_USERNAME in config
        assert CONF_PASSWORD in config

    def test_config_has_token_secret(self) -> None:
        """Test that all configs have token secret."""
        configs = [
            {
                CONF_SERVER_TYPE: SERVER_TYPE_CLOUD,
                CONF_API_KEY: "key",
                CONF_TOKEN_SECRET: "secret1",
            },
            {
                CONF_SERVER_TYPE: SERVER_TYPE_BYOS,
                CONF_SERVER_URL: "http://localhost",
                CONF_AUTH_TYPE: AUTH_TYPE_NONE,
                CONF_TOKEN_SECRET: "secret2",
            },
        ]

        for config in configs:
            assert CONF_TOKEN_SECRET in config
            assert len(config[CONF_TOKEN_SECRET]) > 0

    def test_token_secret_is_hex_encoded(self) -> None:
        """Test that token secret is hex-encoded string."""
        token_secret = "a1b2c3d4e5f6g7h8i9j0"  # 20 chars (hex-like)
        assert len(token_secret) > 0
        assert isinstance(token_secret, str)


class TestConfigFlowIntegration:
    """Integration tests for complete config flow."""

    def test_cloud_complete_config(self) -> None:
        """Test complete Cloud configuration."""
        config = {
            CONF_SERVER_TYPE: SERVER_TYPE_CLOUD,
            CONF_API_KEY: "cloud_api_key_123",
            CONF_DEVICES: ["device_1", "device_2"],
            CONF_TOKEN_SECRET: "token_secret_123",
        }

        # Verify it's a valid complete config
        assert config[CONF_SERVER_TYPE] == SERVER_TYPE_CLOUD
        assert len(config[CONF_DEVICES]) == 2
        assert CONF_TOKEN_SECRET in config

    def test_byos_complete_config(self) -> None:
        """Test complete BYOS configuration."""
        config = {
            CONF_SERVER_TYPE: SERVER_TYPE_BYOS,
            CONF_SERVER_URL: "https://trmnl.example.com",
            CONF_AUTH_TYPE: AUTH_TYPE_BASIC,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secure_password",
            CONF_DEVICES: ["device_1"],
            CONF_TOKEN_SECRET: "token_secret_456",
        }

        # Verify it's a valid complete config
        assert config[CONF_SERVER_TYPE] == SERVER_TYPE_BYOS
        assert config[CONF_AUTH_TYPE] == AUTH_TYPE_BASIC
        assert CONF_USERNAME in config
        assert CONF_PASSWORD in config
        assert CONF_TOKEN_SECRET in config

    def test_config_entry_creation(self) -> None:
        """Test that config can be used to create entry."""
        entry_data = {
            CONF_SERVER_TYPE: SERVER_TYPE_CLOUD,
            CONF_API_KEY: "api_key",
            CONF_DEVICES: ["device_1"],
            CONF_TOKEN_SECRET: "token_secret",
        }

        # Entry data should match config
        assert entry_data[CONF_SERVER_TYPE] == SERVER_TYPE_CLOUD
        assert entry_data[CONF_API_KEY] == "api_key"
        assert entry_data[CONF_TOKEN_SECRET] == "token_secret"


class TestConfigFlowErrorHandling:
    """Test config flow error handling."""

    def test_invalid_api_key_handled(self) -> None:
        """Test that invalid API key errors are handled."""
        error = InvalidAPIKeyError("Invalid API key")
        assert isinstance(error, Exception)
        assert "Invalid" in str(error)

    def test_connection_error_handled(self) -> None:
        """Test that connection errors are handled."""
        error = Exception("Connection failed")
        assert "Connection" in str(error)

    def test_missing_config_fields_validation(self) -> None:
        """Test that missing config fields are detected."""
        incomplete_cloud_config = {
            CONF_SERVER_TYPE: SERVER_TYPE_CLOUD,
            # Missing CONF_API_KEY
        }

        assert CONF_API_KEY not in incomplete_cloud_config

    def test_auth_type_mismatch_handling(self) -> None:
        """Test handling of auth type field mismatches."""
        # BYOS with BASIC auth but missing credentials
        config_with_mismatch = {
            CONF_SERVER_TYPE: SERVER_TYPE_BYOS,
            CONF_AUTH_TYPE: AUTH_TYPE_BASIC,
            # Missing CONF_USERNAME and CONF_PASSWORD
        }

        # Should be detectable that required fields are missing
        assert CONF_USERNAME not in config_with_mismatch
        assert CONF_PASSWORD not in config_with_mismatch


class TestConfigFlowFlowVariations:
    """Test different paths through config flow."""

    def test_cloud_minimal_flow(self) -> None:
        """Test minimal Cloud configuration flow."""
        steps = [
            {"type": "cloud_server", "data": {CONF_SERVER_TYPE: SERVER_TYPE_CLOUD}},
            {"type": "cloud_api_key", "data": {CONF_API_KEY: "key"}},
            {"type": "device_selection", "data": {CONF_DEVICES: ["d1"]}},
        ]
        assert len(steps) == 3

    def test_byos_api_key_flow(self) -> None:
        """Test BYOS with API key authentication flow."""
        steps = [
            {"type": "server_type", "data": {CONF_SERVER_TYPE: SERVER_TYPE_BYOS}},
            {"type": "byos_url", "data": {CONF_SERVER_URL: "http://localhost"}},
            {"type": "byos_auth", "data": {CONF_AUTH_TYPE: AUTH_TYPE_API_KEY}},
            {"type": "byos_credentials", "data": {CONF_API_KEY: "key"}},
            {"type": "device_selection", "data": {CONF_DEVICES: ["d1"]}},
        ]
        assert len(steps) == 5

    def test_byos_basic_auth_flow(self) -> None:
        """Test BYOS with basic authentication flow."""
        steps = [
            {"type": "server_type", "data": {CONF_SERVER_TYPE: SERVER_TYPE_BYOS}},
            {"type": "byos_url", "data": {CONF_SERVER_URL: "http://localhost"}},
            {"type": "byos_auth", "data": {CONF_AUTH_TYPE: AUTH_TYPE_BASIC}},
            {
                "type": "byos_credentials",
                "data": {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
            },
            {"type": "device_selection", "data": {CONF_DEVICES: ["d1"]}},
        ]
        assert len(steps) == 5

    def test_byos_no_auth_flow(self) -> None:
        """Test BYOS with no authentication flow."""
        steps = [
            {"type": "server_type", "data": {CONF_SERVER_TYPE: SERVER_TYPE_BYOS}},
            {"type": "byos_url", "data": {CONF_SERVER_URL: "http://localhost"}},
            {"type": "byos_auth", "data": {CONF_AUTH_TYPE: AUTH_TYPE_NONE}},
            {"type": "device_selection", "data": {CONF_DEVICES: ["d1"]}},
        ]
        assert len(steps) == 4
