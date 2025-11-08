"""WebSocket API for TRMNL integration addon communication."""

import logging
from typing import Any, Callable

from homeassistant.core import HomeAssistant, callback
from homeassistant.components.websocket_api import (
    ERR_INVALID_FORMAT,
    ERR_UNAUTHORIZED,
    ActiveConnection,
    async_response,
    websocket_command,
)

from ..api.exceptions import InvalidTokenError, TRMNLAPIError
from ..const import (
    CONF_TOKEN_SECRET,
    DOMAIN,
    WS_TYPE_GENERATE_TOKEN,
    WS_TYPE_GET_DEVICES,
    WS_TYPE_UPDATE_SCREENSHOT,
)
from ..coordinator import TRMNLCoordinator
from ..token_manager import TokenManager

_LOGGER = logging.getLogger(__name__)


def async_setup_websocket_api(hass: HomeAssistant) -> None:
    """Set up WebSocket API for TRMNL integration.

    Args:
        hass: Home Assistant instance
    """

    @websocket_command({"type": WS_TYPE_GET_DEVICES})
    @async_response
    async def handle_get_devices_impl(
        hass_inner: HomeAssistant,
        connection: ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        """WebSocket command handler for get_devices."""
        await handle_get_devices(hass_inner, connection, msg)

    @websocket_command({"type": WS_TYPE_GENERATE_TOKEN})
    @async_response
    async def handle_generate_token_impl(
        hass_inner: HomeAssistant,
        connection: ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        """WebSocket command handler for generate_token."""
        await handle_generate_token(hass_inner, connection, msg)

    @websocket_command({"type": WS_TYPE_UPDATE_SCREENSHOT})
    @async_response
    async def handle_update_screenshot_impl(
        hass_inner: HomeAssistant,
        connection: ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        """WebSocket command handler for update_screenshot."""
        await handle_update_screenshot(hass_inner, connection, msg)

    _LOGGER.debug("WebSocket API setup complete")


async def handle_get_devices(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle get_devices WebSocket command.

    Returns list of TRMNL devices for the configured entry.

    Args:
        hass: Home Assistant instance
        connection: WebSocket connection
        msg: WebSocket message

    Example:
        Incoming: {"id": 123, "type": "trmnl/get_devices", "entry_id": "abc123"}
        Outgoing: {
            "id": 123,
            "type": "result",
            "success": true,
            "result": {
                "devices": [
                    {
                        "id": "device_1",
                        "name": "Living Room",
                        "device_type": "OG",
                        "status": "ONLINE",
                        "battery_level": 85,
                        "battery_low": false,
                        "firmware_version": "1.0.0",
                        "last_seen": "2025-01-01T12:00:00Z"
                    }
                ]
            }
        }
    """
    try:
        entry_id = msg.get("entry_id")
        if not entry_id:
            connection.send_error(msg["id"], ERR_INVALID_FORMAT, "entry_id required")
            return

        # Get coordinator for the entry
        coordinator = _get_coordinator(hass, entry_id)
        if not coordinator:
            connection.send_error(
                msg["id"],
                "unauthorized",
                "No coordinator for this entry",
            )
            return

        # Get devices
        devices = []
        for device_id, device in coordinator.devices.items():
            devices.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "device_type": device.device_type.value,
                    "status": device.status.value if device.status else None,
                    "battery_level": device.battery_level,
                    "battery_low": device.battery_low,
                    "firmware_version": device.firmware_version,
                    "is_online": device.is_online,
                    "last_seen": device.last_seen.isoformat()
                    if device.last_seen
                    else None,
                }
            )

        connection.send_result(
            msg["id"],
            {
                "devices": devices,
            },
        )
        _LOGGER.debug("Returned %d devices via WebSocket", len(devices))

    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Error in get_devices handler: %s", err)
        connection.send_error(msg["id"], "internal_error", str(err))


async def handle_generate_token(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle generate_token WebSocket command.

    Generates an HMAC-signed token for authenticating screenshot requests.

    Args:
        hass: Home Assistant instance
        connection: WebSocket connection
        msg: WebSocket message

    Example:
        Incoming: {
            "id": 124,
            "type": "trmnl/generate_token",
            "entry_id": "abc123",
            "device_id": "device_1"
        }
        Outgoing: {
            "id": 124,
            "type": "result",
            "success": true,
            "result": {
                "token": "token_eyJ..._abc123def456",
                "expires_at": "2025-01-02T12:00:00Z"
            }
        }
    """
    try:
        entry_id = msg.get("entry_id")
        device_id = msg.get("device_id")

        if not entry_id or not device_id:
            connection.send_error(
                msg["id"],
                ERR_INVALID_FORMAT,
                "entry_id and device_id required",
            )
            return

        # Get coordinator for the entry
        coordinator = _get_coordinator(hass, entry_id)
        if not coordinator:
            connection.send_error(
                msg["id"],
                "unauthorized",
                "No coordinator for this entry",
            )
            return

        # Get token manager
        token_manager = _get_token_manager(hass, entry_id, coordinator)
        if not token_manager:
            connection.send_error(
                msg["id"],
                "internal_error",
                "No token manager for this entry",
            )
            return

        # Generate token
        token = token_manager.generate_token(device_id)
        token_info = token_manager.get_token_info(token)

        connection.send_result(
            msg["id"],
            {
                "token": token,
                "expires_at": token_info.get("expires_at"),
            },
        )
        _LOGGER.debug("Generated token for device %s via WebSocket", device_id)

    except ValueError as err:
        _LOGGER.warning("Invalid token generation request: %s", err)
        connection.send_error(msg["id"], ERR_INVALID_FORMAT, str(err))
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Error in generate_token handler: %s", err)
        connection.send_error(msg["id"], "internal_error", str(err))


async def handle_update_screenshot(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle update_screenshot WebSocket command.

    Updates TRMNL device with a new screenshot URL and authentication token.
    This command requires valid authentication token to prevent unauthorized updates.

    Args:
        hass: Home Assistant instance
        connection: WebSocket connection
        msg: WebSocket message

    Example:
        Incoming: {
            "id": 125,
            "type": "trmnl/update_screenshot",
            "entry_id": "abc123",
            "device_id": "device_1",
            "image_url": "https://homeassistant.local/api/trmnl/screenshot",
            "token": "token_eyJ..._abc123def456"
        }
        Outgoing: {
            "id": 125,
            "type": "result",
            "success": true,
            "result": {
                "success": true,
                "message": "Screenshot updated successfully"
            }
        }
    """
    try:
        entry_id = msg.get("entry_id")
        device_id = msg.get("device_id")
        image_url = msg.get("image_url")
        token = msg.get("token")

        if not all([entry_id, device_id, image_url, token]):
            connection.send_error(
                msg["id"],
                ERR_INVALID_FORMAT,
                "entry_id, device_id, image_url, and token required",
            )
            return

        # Get coordinator for the entry
        coordinator = _get_coordinator(hass, entry_id)
        if not coordinator:
            connection.send_error(
                msg["id"],
                "unauthorized",
                "No coordinator for this entry",
            )
            return

        # Get token manager and validate token
        token_manager = _get_token_manager(hass, entry_id, coordinator)
        if not token_manager:
            connection.send_error(
                msg["id"],
                "internal_error",
                "No token manager for this entry",
            )
            return

        try:
            # Validate token signature and expiration
            token_manager.validate_token(token)
            token_info = token_manager.get_token_info(token)

            # Ensure token is for the requested device
            if token_info.get("device_id") != device_id:
                _LOGGER.warning(
                    "Token device mismatch: token is for %s, request is for %s",
                    token_info.get("device_id"),
                    device_id,
                )
                connection.send_error(
                    msg["id"],
                    "unauthorized",
                    "Token is not valid for this device",
                )
                return

        except InvalidTokenError as err:
            _LOGGER.warning("Invalid token in screenshot update: %s", err)
            connection.send_error(msg["id"], "unauthorized", str(err))
            return

        # Update screenshot
        try:
            success = await coordinator.async_update_screenshot(
                device_id=device_id,
                image_url=image_url,
                token=token,
            )

            if success:
                connection.send_result(
                    msg["id"],
                    {
                        "success": True,
                        "message": "Screenshot updated successfully",
                    },
                )
                _LOGGER.info(
                    "Screenshot updated for device %s via WebSocket", device_id
                )
            else:
                connection.send_result(
                    msg["id"],
                    {
                        "success": False,
                        "message": "Failed to update screenshot",
                    },
                )
                _LOGGER.warning("Screenshot update failed for device %s", device_id)

        except TRMNLAPIError as err:
            _LOGGER.error("API error updating screenshot: %s", err)
            connection.send_result(
                msg["id"],
                {
                    "success": False,
                    "message": f"API error: {err}",
                },
            )

    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Error in update_screenshot handler: %s", err)
        connection.send_error(msg["id"], "internal_error", str(err))


def _get_coordinator(hass: HomeAssistant, entry_id: str) -> TRMNLCoordinator | None:
    """Get the coordinator for a config entry.

    Args:
        hass: Home Assistant instance
        entry_id: Config entry ID

    Returns:
        Coordinator instance or None if not found
    """
    try:
        entry_data = hass.data.get(DOMAIN, {}).get(entry_id, {})
        return entry_data.get("coordinator")
    except (KeyError, AttributeError):
        return None


def _get_token_manager(
    hass: HomeAssistant, entry_id: str, coordinator: TRMNLCoordinator
) -> TokenManager | None:
    """Get the token manager for a config entry.

    Creates a new TokenManager if one doesn't exist yet.

    Args:
        hass: Home Assistant instance
        entry_id: Config entry ID
        coordinator: Coordinator instance

    Returns:
        TokenManager instance or None if token secret not found
    """
    try:
        # Check if token manager already exists
        entry_data = hass.data.get(DOMAIN, {}).get(entry_id, {})
        if "token_manager" in entry_data:
            return entry_data["token_manager"]

        # Get token secret from config entry
        config_entry = hass.config_entries.async_get_entry(entry_id)
        if not config_entry:
            return None

        token_secret = config_entry.data.get(CONF_TOKEN_SECRET)
        if not token_secret:
            return None

        # Create and cache token manager
        token_manager = TokenManager(token_secret)
        hass.data[DOMAIN][entry_id]["token_manager"] = token_manager
        return token_manager

    except (KeyError, AttributeError, ValueError):
        return None
