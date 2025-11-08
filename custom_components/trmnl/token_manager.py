"""Token manager for TRMNL integration with HMAC-SHA256 signing."""

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from .api.exceptions import InvalidTokenError
from .const import (
    CONF_TOKEN_SECRET,
    TOKEN_PREFIX,
    TOKEN_ROTATION_THRESHOLD_HOURS,
    TOKEN_SEPARATOR,
    TOKEN_TTL_HOURS,
)

_LOGGER = logging.getLogger(__name__)


class TokenManager:
    """Manager for generating and validating HMAC-signed tokens."""

    def __init__(self, token_secret: str) -> None:
        """Initialize token manager.

        Args:
            token_secret: Secret key for HMAC signing (hex-encoded)

        Raises:
            ValueError: If token_secret is invalid
        """
        if not token_secret or not isinstance(token_secret, str):
            raise ValueError("token_secret must be a non-empty string")

        self._token_secret = token_secret
        self._token_ttl_hours = TOKEN_TTL_HOURS
        self._rotation_threshold_hours = TOKEN_ROTATION_THRESHOLD_HOURS

    def generate_token(self, device_id: str) -> str:
        """Generate a new HMAC-signed token for a device.

        Args:
            device_id: Device ID to generate token for

        Returns:
            Token string in format: token_<payload>_<signature>

        Raises:
            ValueError: If device_id is invalid
        """
        if not device_id or not isinstance(device_id, str):
            raise ValueError("device_id must be a non-empty string")

        # Generate expiration time
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self._token_ttl_hours
        )

        # Create payload
        payload_data = {
            "device_id": device_id,
            "expires_at": expires_at.isoformat(),
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }

        # Encode payload as base64
        payload_json = json.dumps(payload_data)
        payload_b64 = base64.b64encode(payload_json.encode()).decode()

        # Generate HMAC signature
        signature = self._generate_signature(payload_b64)

        # Combine into token
        token = f"{TOKEN_PREFIX}{TOKEN_SEPARATOR}{payload_b64}{TOKEN_SEPARATOR}{signature}"

        _LOGGER.debug("Generated token for device %s (expires at %s)", device_id, expires_at)

        return token

    def validate_token(self, token: str) -> bool:
        """Validate a token's signature and expiration.

        Args:
            token: Token to validate

        Returns:
            True if token is valid

        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        if not token or not isinstance(token, str):
            raise InvalidTokenError("Token must be a non-empty string")

        try:
            # Parse token
            parts = token.split(TOKEN_SEPARATOR)
            if len(parts) != 3:
                raise InvalidTokenError("Invalid token format")

            prefix, payload_b64, signature = parts

            if prefix != TOKEN_PREFIX:
                raise InvalidTokenError("Invalid token prefix")

            # Validate signature
            expected_signature = self._generate_signature(payload_b64)
            if not hmac.compare_digest(signature, expected_signature):
                raise InvalidTokenError("Invalid token signature")

            # Decode and parse payload
            payload_json = base64.b64decode(payload_b64).decode()
            payload_data = json.loads(payload_json)

            # Check expiration
            expires_at = datetime.fromisoformat(payload_data["expires_at"])
            if datetime.now(timezone.utc) >= expires_at:
                raise InvalidTokenError("Token has expired")

            _LOGGER.debug("Validated token for device %s", payload_data.get("device_id"))

            return True

        except (ValueError, KeyError, json.JSONDecodeError) as err:
            raise InvalidTokenError(f"Invalid token format: {err}") from err

    def should_rotate_token(self, token: str) -> bool:
        """Check if a token should be rotated based on expiration threshold.

        Args:
            token: Token to check

        Returns:
            True if token should be rotated

        Raises:
            InvalidTokenError: If token is invalid
        """
        if not token or not isinstance(token, str):
            raise InvalidTokenError("Token must be a non-empty string")

        try:
            # Parse token
            parts = token.split(TOKEN_SEPARATOR)
            if len(parts) != 3:
                raise InvalidTokenError("Invalid token format")

            _, payload_b64, _ = parts

            # Decode and parse payload
            payload_json = base64.b64decode(payload_b64).decode()
            payload_data = json.loads(payload_json)

            # Check if expiration is within rotation threshold
            expires_at = datetime.fromisoformat(payload_data["expires_at"])
            rotation_threshold = datetime.now(timezone.utc) + timedelta(
                hours=self._rotation_threshold_hours
            )

            should_rotate = expires_at <= rotation_threshold
            if should_rotate:
                _LOGGER.debug(
                    "Token for device %s is near expiration (expires at %s)",
                    payload_data.get("device_id"),
                    expires_at,
                )

            return should_rotate

        except (ValueError, KeyError, json.JSONDecodeError) as err:
            raise InvalidTokenError(f"Invalid token format: {err}") from err

    def get_token_info(self, token: str) -> dict:
        """Get information from a token without validating signature.

        Args:
            token: Token to extract info from

        Returns:
            Dictionary with device_id, issued_at, expires_at

        Raises:
            InvalidTokenError: If token format is invalid
        """
        if not token or not isinstance(token, str):
            raise InvalidTokenError("Token must be a non-empty string")

        try:
            # Parse token
            parts = token.split(TOKEN_SEPARATOR)
            if len(parts) != 3:
                raise InvalidTokenError("Invalid token format")

            _, payload_b64, _ = parts

            # Decode and parse payload
            payload_json = base64.b64decode(payload_b64).decode()
            payload_data = json.loads(payload_json)

            return {
                "device_id": payload_data.get("device_id"),
                "issued_at": payload_data.get("issued_at"),
                "expires_at": payload_data.get("expires_at"),
            }

        except (ValueError, KeyError, json.JSONDecodeError) as err:
            raise InvalidTokenError(f"Invalid token format: {err}") from err

    def _generate_signature(self, payload: str) -> str:
        """Generate HMAC-SHA256 signature for payload.

        Args:
            payload: Payload to sign

        Returns:
            Hex-encoded signature
        """
        signature = hmac.new(
            self._token_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return signature
