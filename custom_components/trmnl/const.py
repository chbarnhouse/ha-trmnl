"""Constants for TRMNL integration."""

from enum import Enum

# Domain
DOMAIN = "trmnl"

# Config entry keys
CONF_SERVER_TYPE = "server_type"
CONF_API_KEY = "api_key"
CONF_SERVER_URL = "server_url"
CONF_AUTH_TYPE = "auth_type"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_DEVICES = "devices"
CONF_TOKEN_SECRET = "token_secret"

# Server types
SERVER_TYPE_CLOUD = "cloud"
SERVER_TYPE_BYOS = "byos"

# BYOS Auth types
AUTH_TYPE_API_KEY = "api_key"
AUTH_TYPE_BASIC = "basic"
AUTH_TYPE_NONE = "none"

# TRMNL Cloud API
TRMNL_CLOUD_API_BASE = "https://usetrmnl.com/api"
TRMNL_CLOUD_ENDPOINT_DEVICES = "/devices"
TRMNL_CLOUD_ENDPOINT_PLUGIN_VARS = "/custom_plugins/{plugin_id}/variables"

# Default coordinator update interval (minutes)
COORDINATOR_UPDATE_INTERVAL = 5

# Token management
TOKEN_TTL_HOURS = 24
TOKEN_ROTATION_THRESHOLD_HOURS = 6
TOKEN_PREFIX = "token"
TOKEN_SEPARATOR = "_"

# Entity defaults
ENTITY_BATTERY_LOW_THRESHOLD = 20
ENTITY_LAST_SEEN_THRESHOLD = 3600  # 1 hour in seconds

# Device classes
DEVICE_CLASS_BATTERY = "battery"
DEVICE_CLASS_TIMESTAMP = "timestamp"
DEVICE_CLASS_CONNECTIVITY = "connectivity"

# Attributes
ATTR_DEVICE_ID = "device_id"
ATTR_IMAGE_URL = "image_url"
ATTR_TOKEN = "token"
ATTR_BATTERY = "battery"
ATTR_LAST_SEEN = "last_seen"
ATTR_FIRMWARE = "firmware"
ATTR_CONNECTION = "connection"
ATTR_BATTERY_LOW = "battery_low"

# Service names
SERVICE_UPDATE_SCREENSHOT = "update_screenshot"
SERVICE_TRIGGER_REFRESH = "trigger_refresh"

# WebSocket command types
WS_TYPE_GET_DEVICES = "trmnl/get_devices"
WS_TYPE_GENERATE_TOKEN = "trmnl/generate_token"
WS_TYPE_UPDATE_SCREENSHOT = "trmnl/update_screenshot"

# WebSocket response fields
WS_RESULT_SUCCESS = "success"
WS_RESULT_ERROR = "error"
WS_RESULT_DEVICES = "devices"
WS_RESULT_TOKEN = "token"
WS_RESULT_EXPIRES_AT = "expires_at"


class ServerType(str, Enum):
    """Server type enumeration."""

    CLOUD = SERVER_TYPE_CLOUD
    BYOS = SERVER_TYPE_BYOS


class AuthType(str, Enum):
    """Authentication type enumeration."""

    API_KEY = AUTH_TYPE_API_KEY
    BASIC = AUTH_TYPE_BASIC
    NONE = AUTH_TYPE_NONE


# Error messages
ERROR_INVALID_API_KEY = "Invalid API key"
ERROR_INVALID_SERVER_URL = "Invalid server URL"
ERROR_DEVICE_DISCOVERY_FAILED = "Device discovery failed"
ERROR_UPDATE_SCREENSHOT_FAILED = "Failed to update screenshot"
ERROR_INVALID_TOKEN = "Invalid or expired token"
ERROR_API_UNAVAILABLE = "TRMNL API is unavailable"
