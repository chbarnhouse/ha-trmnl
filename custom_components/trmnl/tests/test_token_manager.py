"""Tests for token manager."""

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from ..api.exceptions import InvalidTokenError
from ..token_manager import TokenManager


class TestTokenManagerInitialization:
    """Test token manager initialization."""

    def test_init_with_valid_secret(self) -> None:
        """Test initialization with valid token secret."""
        manager = TokenManager("test_secret_1234567890abcdef")
        assert manager is not None
        assert manager._token_secret == "test_secret_1234567890abcdef"

    def test_init_with_empty_secret(self) -> None:
        """Test initialization with empty token secret."""
        with pytest.raises(ValueError, match="token_secret must be a non-empty string"):
            TokenManager("")

    def test_init_with_none_secret(self) -> None:
        """Test initialization with None token secret."""
        with pytest.raises(ValueError, match="token_secret must be a non-empty string"):
            TokenManager(None)  # type: ignore

    def test_init_with_non_string_secret(self) -> None:
        """Test initialization with non-string token secret."""
        with pytest.raises(ValueError, match="token_secret must be a non-empty string"):
            TokenManager(12345)  # type: ignore


class TestTokenGeneration:
    """Test token generation."""

    @pytest.fixture
    def manager(self) -> TokenManager:
        """Create token manager for tests."""
        return TokenManager("test_secret_1234567890abcdef")

    def test_generate_token(self, manager: TokenManager) -> None:
        """Test basic token generation."""
        token = manager.generate_token("device_1")
        assert token is not None
        assert isinstance(token, str)
        assert token.startswith("token_")

    def test_generate_token_format(self, manager: TokenManager) -> None:
        """Test token format is correct."""
        token = manager.generate_token("device_1")
        parts = token.split("_")
        assert len(parts) == 3
        assert parts[0] == "token"
        # parts[1] is base64 payload, parts[2] is hex signature

    def test_generate_token_contains_device_id(self, manager: TokenManager) -> None:
        """Test generated token contains device ID."""
        device_id = "device_123"
        token = manager.generate_token(device_id)

        # Extract payload
        parts = token.split("_")
        payload_b64 = parts[1]
        payload_json = base64.b64decode(payload_b64).decode()
        payload_data = json.loads(payload_json)

        assert payload_data["device_id"] == device_id

    def test_generate_token_with_expiration(self, manager: TokenManager) -> None:
        """Test generated token contains expiration."""
        token = manager.generate_token("device_1")

        # Extract payload
        parts = token.split("_")
        payload_b64 = parts[1]
        payload_json = base64.b64decode(payload_b64).decode()
        payload_data = json.loads(payload_json)

        assert "expires_at" in payload_data
        expires_at = datetime.fromisoformat(payload_data["expires_at"])
        now = datetime.now(timezone.utc)
        # Token should expire in ~24 hours
        assert (expires_at - now).total_seconds() > 86000  # ~24h - 1h buffer
        assert (expires_at - now).total_seconds() < 86400 + 3600  # ~24h + 1h buffer

    def test_generate_token_invalid_device_id(self, manager: TokenManager) -> None:
        """Test token generation with invalid device ID."""
        with pytest.raises(ValueError, match="device_id must be a non-empty string"):
            manager.generate_token("")

    def test_generate_token_none_device_id(self, manager: TokenManager) -> None:
        """Test token generation with None device ID."""
        with pytest.raises(ValueError, match="device_id must be a non-empty string"):
            manager.generate_token(None)  # type: ignore

    def test_generate_token_non_string_device_id(self, manager: TokenManager) -> None:
        """Test token generation with non-string device ID."""
        with pytest.raises(ValueError, match="device_id must be a non-empty string"):
            manager.generate_token(12345)  # type: ignore

    def test_generate_different_tokens_same_device(self, manager: TokenManager) -> None:
        """Test that multiple tokens for same device have different timestamps."""
        token1 = manager.generate_token("device_1")
        token2 = manager.generate_token("device_1")

        # Tokens should be different due to issued_at timestamp
        assert token1 != token2

    def test_generate_token_includes_issued_at(self, manager: TokenManager) -> None:
        """Test generated token includes issued_at timestamp."""
        token = manager.generate_token("device_1")

        # Extract payload
        parts = token.split("_")
        payload_b64 = parts[1]
        payload_json = base64.b64decode(payload_b64).decode()
        payload_data = json.loads(payload_json)

        assert "issued_at" in payload_data


class TestTokenValidation:
    """Test token validation."""

    @pytest.fixture
    def manager(self) -> TokenManager:
        """Create token manager for tests."""
        return TokenManager("test_secret_1234567890abcdef")

    def test_validate_valid_token(self, manager: TokenManager) -> None:
        """Test validation of a valid token."""
        token = manager.generate_token("device_1")
        assert manager.validate_token(token) is True

    def test_validate_invalid_token_format(self, manager: TokenManager) -> None:
        """Test validation of token with invalid format."""
        with pytest.raises(InvalidTokenError, match="Invalid token format"):
            manager.validate_token("invalid_token")

    def test_validate_token_wrong_prefix(self, manager: TokenManager) -> None:
        """Test validation of token with wrong prefix."""
        with pytest.raises(InvalidTokenError, match="Invalid token prefix"):
            manager.validate_token("wrong_payload_signature")

    def test_validate_token_invalid_signature(self, manager: TokenManager) -> None:
        """Test validation of token with invalid signature."""
        token = manager.generate_token("device_1")
        parts = token.split("_")
        # Modify the signature
        invalid_token = f"{parts[0]}_{parts[1]}_invalidsignature"

        with pytest.raises(InvalidTokenError, match="Invalid token signature"):
            manager.validate_token(invalid_token)

    def test_validate_expired_token(self, manager: TokenManager) -> None:
        """Test validation of an expired token."""
        # Create a token with past expiration
        payload_data = {
            "device_id": "device_1",
            "expires_at": (
                datetime.now(timezone.utc) - timedelta(hours=1)
            ).isoformat(),
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }
        payload_json = json.dumps(payload_data)
        payload_b64 = base64.b64encode(payload_json.encode()).decode()

        # Generate signature
        signature = hmac.new(
            "test_secret_1234567890abcdef".encode(),
            payload_b64.encode(),
            hashlib.sha256,
        ).hexdigest()

        token = f"token_{payload_b64}_{signature}"

        with pytest.raises(InvalidTokenError, match="Token has expired"):
            manager.validate_token(token)

    def test_validate_empty_token(self, manager: TokenManager) -> None:
        """Test validation of empty token."""
        with pytest.raises(InvalidTokenError, match="Token must be a non-empty string"):
            manager.validate_token("")

    def test_validate_none_token(self, manager: TokenManager) -> None:
        """Test validation of None token."""
        with pytest.raises(InvalidTokenError, match="Token must be a non-empty string"):
            manager.validate_token(None)  # type: ignore

    def test_validate_corrupted_payload(self, manager: TokenManager) -> None:
        """Test validation of token with corrupted payload."""
        token = manager.generate_token("device_1")
        parts = token.split("_")
        # Replace payload with invalid base64
        invalid_token = f"{parts[0]}_invalid_base64__{parts[2]}"

        with pytest.raises(InvalidTokenError, match="Invalid token format"):
            manager.validate_token(invalid_token)

    def test_validate_missing_required_field(self, manager: TokenManager) -> None:
        """Test validation of token missing required field."""
        # Create a token without expires_at
        payload_data = {
            "device_id": "device_1",
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }
        payload_json = json.dumps(payload_data)
        payload_b64 = base64.b64encode(payload_json.encode()).decode()

        signature = hmac.new(
            "test_secret_1234567890abcdef".encode(),
            payload_b64.encode(),
            hashlib.sha256,
        ).hexdigest()

        token = f"token_{payload_b64}_{signature}"

        with pytest.raises(InvalidTokenError):
            manager.validate_token(token)


class TestTokenRotation:
    """Test token rotation threshold checking."""

    @pytest.fixture
    def manager(self) -> TokenManager:
        """Create token manager for tests."""
        return TokenManager("test_secret_1234567890abcdef")

    def test_should_not_rotate_new_token(self, manager: TokenManager) -> None:
        """Test that new tokens don't need rotation."""
        token = manager.generate_token("device_1")
        assert manager.should_rotate_token(token) is False

    def test_should_rotate_near_expiration(self, manager: TokenManager) -> None:
        """Test that tokens near expiration should be rotated."""
        # Create a token expiring in 5 hours (less than 6-hour threshold)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=5)
        payload_data = {
            "device_id": "device_1",
            "expires_at": expires_at.isoformat(),
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }
        payload_json = json.dumps(payload_data)
        payload_b64 = base64.b64encode(payload_json.encode()).decode()

        signature = hmac.new(
            "test_secret_1234567890abcdef".encode(),
            payload_b64.encode(),
            hashlib.sha256,
        ).hexdigest()

        token = f"token_{payload_b64}_{signature}"

        assert manager.should_rotate_token(token) is True

    def test_should_rotate_at_threshold(self, manager: TokenManager) -> None:
        """Test that tokens exactly at threshold should be rotated."""
        # Create a token expiring exactly at the 6-hour threshold
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=TOKEN_ROTATION_THRESHOLD_HOURS
        )
        payload_data = {
            "device_id": "device_1",
            "expires_at": expires_at.isoformat(),
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }
        payload_json = json.dumps(payload_data)
        payload_b64 = base64.b64encode(payload_json.encode()).decode()

        signature = hmac.new(
            "test_secret_1234567890abcdef".encode(),
            payload_b64.encode(),
            hashlib.sha256,
        ).hexdigest()

        token = f"token_{payload_b64}_{signature}"

        # At threshold, rotation should be triggered
        assert manager.should_rotate_token(token) is True

    def test_rotation_with_invalid_token(self, manager: TokenManager) -> None:
        """Test rotation check with invalid token."""
        with pytest.raises(InvalidTokenError, match="Invalid token format"):
            manager.should_rotate_token("invalid_token")

    def test_rotation_with_empty_token(self, manager: TokenManager) -> None:
        """Test rotation check with empty token."""
        with pytest.raises(InvalidTokenError, match="Token must be a non-empty string"):
            manager.should_rotate_token("")

    def test_rotation_with_none_token(self, manager: TokenManager) -> None:
        """Test rotation check with None token."""
        with pytest.raises(InvalidTokenError, match="Token must be a non-empty string"):
            manager.should_rotate_token(None)  # type: ignore


class TestTokenInfo:
    """Test token info extraction."""

    @pytest.fixture
    def manager(self) -> TokenManager:
        """Create token manager for tests."""
        return TokenManager("test_secret_1234567890abcdef")

    def test_get_token_info_valid_token(self, manager: TokenManager) -> None:
        """Test getting info from a valid token."""
        token = manager.generate_token("device_123")
        info = manager.get_token_info(token)

        assert info["device_id"] == "device_123"
        assert "issued_at" in info
        assert "expires_at" in info

    def test_get_token_info_all_fields(self, manager: TokenManager) -> None:
        """Test that token info contains all expected fields."""
        token = manager.generate_token("device_1")
        info = manager.get_token_info(token)

        assert "device_id" in info
        assert "issued_at" in info
        assert "expires_at" in info
        assert len(info) == 3

    def test_get_token_info_invalid_format(self, manager: TokenManager) -> None:
        """Test getting info from invalidly formatted token."""
        with pytest.raises(InvalidTokenError, match="Invalid token format"):
            manager.get_token_info("invalid_token")

    def test_get_token_info_empty_token(self, manager: TokenManager) -> None:
        """Test getting info from empty token."""
        with pytest.raises(InvalidTokenError, match="Token must be a non-empty string"):
            manager.get_token_info("")

    def test_get_token_info_none_token(self, manager: TokenManager) -> None:
        """Test getting info from None token."""
        with pytest.raises(InvalidTokenError, match="Token must be a non-empty string"):
            manager.get_token_info(None)  # type: ignore


class TestTokenManagerSignature:
    """Test HMAC signature generation."""

    @pytest.fixture
    def manager(self) -> TokenManager:
        """Create token manager for tests."""
        return TokenManager("test_secret_1234567890abcdef")

    def test_signature_deterministic(self, manager: TokenManager) -> None:
        """Test that same payload produces same signature."""
        payload = "test_payload"
        sig1 = manager._generate_signature(payload)
        sig2 = manager._generate_signature(payload)

        assert sig1 == sig2

    def test_signature_different_payloads(self, manager: TokenManager) -> None:
        """Test that different payloads produce different signatures."""
        sig1 = manager._generate_signature("payload_1")
        sig2 = manager._generate_signature("payload_2")

        assert sig1 != sig2

    def test_signature_different_secrets(self) -> None:
        """Test that different secrets produce different signatures."""
        manager1 = TokenManager("secret_1")
        manager2 = TokenManager("secret_2")

        payload = "test_payload"
        sig1 = manager1._generate_signature(payload)
        sig2 = manager2._generate_signature(payload)

        assert sig1 != sig2

    def test_signature_hex_format(self, manager: TokenManager) -> None:
        """Test that signature is hex-formatted."""
        signature = manager._generate_signature("payload")
        # Should be valid hex string
        try:
            int(signature, 16)
        except ValueError:
            pytest.fail("Signature is not valid hex")


class TestTokenManagerIntegration:
    """Integration tests for token manager."""

    @pytest.fixture
    def manager(self) -> TokenManager:
        """Create token manager for tests."""
        return TokenManager("test_secret_1234567890abcdef")

    def test_generate_and_validate_cycle(self, manager: TokenManager) -> None:
        """Test complete generate-validate cycle."""
        device_id = "device_456"
        token = manager.generate_token(device_id)
        assert manager.validate_token(token) is True

        info = manager.get_token_info(token)
        assert info["device_id"] == device_id

    def test_multiple_devices_same_manager(self, manager: TokenManager) -> None:
        """Test managing tokens for multiple devices."""
        token1 = manager.generate_token("device_1")
        token2 = manager.generate_token("device_2")
        token3 = manager.generate_token("device_3")

        # All should be valid
        assert manager.validate_token(token1) is True
        assert manager.validate_token(token2) is True
        assert manager.validate_token(token3) is True

        # Info should be correct
        assert manager.get_token_info(token1)["device_id"] == "device_1"
        assert manager.get_token_info(token2)["device_id"] == "device_2"
        assert manager.get_token_info(token3)["device_id"] == "device_3"

    def test_token_cross_manager_validation(self) -> None:
        """Test that tokens from one manager can't validate in another."""
        manager1 = TokenManager("secret_1")
        manager2 = TokenManager("secret_2")

        token = manager1.generate_token("device_1")

        # Should fail with different secret
        with pytest.raises(InvalidTokenError, match="Invalid token signature"):
            manager2.validate_token(token)

    def test_token_lifetime(self, manager: TokenManager) -> None:
        """Test complete token lifecycle: generate, validate, check rotation."""
        token = manager.generate_token("device_1")

        # Fresh token should be valid and not need rotation
        assert manager.validate_token(token) is True
        assert manager.should_rotate_token(token) is False

        # Token info should be accessible
        info = manager.get_token_info(token)
        assert info["device_id"] == "device_1"


# Import rotation threshold for tests
from ..const import TOKEN_ROTATION_THRESHOLD_HOURS
