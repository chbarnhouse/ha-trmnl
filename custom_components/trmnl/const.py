"""Constants for the TRMNL integration."""

DOMAIN = "trmnl"

# Platforms
PLATFORMS = ["sensor", "switch", "button", "number", "time", "select", "text"]

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"

# Default values
DEFAULT_PORT = 2300
DEFAULT_NAME = "TRMNL"

# Services are now handled in services.py