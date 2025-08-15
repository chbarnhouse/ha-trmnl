"""Constants for the TRMNL integration."""

DOMAIN = "trmnl"

# Configuration keys
CONF_API_KEY = "api_key"
CONF_DEVICE_ID = "device_id"
CONF_NAME = "name"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_WEBHOOK_PORT = "webhook_port"

# Default values
DEFAULT_UPDATE_INTERVAL = 30
DEFAULT_WEBHOOK_PORT = 8123

# API endpoints
API_BASE_URL = "https://api.usetrmnl.com"
API_VERSION = "v1"

# Device states
DEVICE_STATE_ONLINE = "online"
DEVICE_STATE_OFFLINE = "offline"
DEVICE_STATE_ERROR = "error"

# Screen states
SCREEN_STATE_ACTIVE = "active"
SCREEN_STATE_INACTIVE = "inactive"
SCREEN_STATE_UPDATING = "updating"

# Plugin states
PLUGIN_STATE_RUNNING = "running"
PLUGIN_STATE_STOPPED = "stopped"
PLUGIN_STATE_ERROR = "error"

# Entity attributes
ATTR_DEVICE_ID = "device_id"
ATTR_SCREEN_ID = "screen_id"
ATTR_PLUGIN_ID = "plugin_id"
ATTR_LAST_UPDATE = "last_update"
ATTR_FIRMWARE_VERSION = "firmware_version"
ATTR_SCREEN_CONTENT = "screen_content"
ATTR_BRIGHTNESS = "brightness"
ATTR_PLUGIN_STATUS = "plugin_status"
ATTR_WEBHOOK_URL = "webhook_url"
ATTR_EVENTS = "events"

# Service names
SERVICE_UPDATE_SCREEN = "update_screen"
SERVICE_INSTALL_PLUGIN = "install_plugin"
SERVICE_UNINSTALL_PLUGIN = "uninstall_plugin"
SERVICE_RESTART_DEVICE = "restart_device"
SERVICE_SET_BRIGHTNESS = "set_brightness"
SERVICE_SETUP_WEBHOOK = "setup_webhook"

# Webhook events
WEBHOOK_EVENT_DEVICE_UPDATE = "device_update"
WEBHOOK_EVENT_SCREEN_UPDATE = "screen_update"
WEBHOOK_EVENT_PLUGIN_UPDATE = "plugin_update"
WEBHOOK_EVENT_DEVICE_STATUS = "device_status"

# Update intervals
UPDATE_INTERVAL_FAST = 10
UPDATE_INTERVAL_NORMAL = 30
UPDATE_INTERVAL_SLOW = 60

# Timeouts
CONNECTION_TIMEOUT = 30
REQUEST_TIMEOUT = 10
WEBHOOK_TIMEOUT = 5
