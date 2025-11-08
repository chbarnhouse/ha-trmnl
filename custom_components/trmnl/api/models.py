"""Data models for TRMNL API."""

from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    """TRMNL device types."""

    OG = "og"
    X = "x"


class DeviceStatus(str, Enum):
    """Device connection status."""

    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class TRMNLDevice:
    """Represents a TRMNL device."""

    id: str
    name: str
    device_type: DeviceType
    battery_level: Optional[int] = None
    last_seen: Optional[datetime] = None
    firmware_version: Optional[str] = None
    status: DeviceStatus = DeviceStatus.UNKNOWN
    attributes: dict = field(default_factory=dict)

    @property
    def unique_id(self) -> str:
        """Return unique ID for the device."""
        return f"trmnl_{self.id}"

    @property
    def is_online(self) -> bool:
        """Check if device is online."""
        return self.status == DeviceStatus.ONLINE

    @property
    def battery_low(self) -> bool:
        """Check if battery is low."""
        if self.battery_level is None:
            return False
        return self.battery_level < 20

    def to_dict(self) -> dict[str, Any]:
        """Convert device to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "device_type": self.device_type.value,
            "battery_level": self.battery_level,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "firmware_version": self.firmware_version,
            "status": self.status.value,
        }


@dataclass
class TRMNLPlugin:
    """Represents a TRMNL plugin."""

    uuid: str
    name: str
    version: str
    description: Optional[str] = None
    supported_devices: list[str] = field(default_factory=lambda: ["og", "x"])
    attributes: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert plugin to dictionary."""
        return {
            "uuid": self.uuid,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "supported_devices": self.supported_devices,
        }


@dataclass
class MergeVars:
    """Plugin merge variables for screenshot display."""

    ha_image_url: str
    ha_auth_token: str
    ha_token_expires: str
    last_updated: str
    device_id: str
    attributes: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert merge vars to dictionary."""
        return {
            "ha_image_url": self.ha_image_url,
            "ha_auth_token": self.ha_auth_token,
            "ha_token_expires": self.ha_token_expires,
            "last_updated": self.last_updated,
            "device_id": self.device_id,
        }


@dataclass
class DeviceUpdateRequest:
    """Request to update device screenshot."""

    device_id: str
    image_url: str
    token: Optional[str] = None
    attributes: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert request to dictionary."""
        data = {
            "device_id": self.device_id,
            "image_url": self.image_url,
        }
        if self.token:
            data["token"] = self.token
        return data


@dataclass
class DevicePlaylist:
    """Represents a device's playlist (collection of plugins)."""

    device_id: str
    plugins: list[str] = field(default_factory=list)  # Plugin UUIDs
    refresh_interval: int = 15  # Minutes
    attributes: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert playlist to dictionary."""
        return {
            "device_id": self.device_id,
            "plugins": self.plugins,
            "refresh_interval": self.refresh_interval,
        }


@dataclass
class APIResponse:
    """API response wrapper."""

    status: str  # "success" or "error"
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

    def is_success(self) -> bool:
        """Check if response indicates success."""
        return self.status == "success"

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "message": self.message,
        }
