# TRMNL Home Assistant Integration

[![HACS Default](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/chbarnhouse/trmnl-ha-integration.svg?style=for-the-badge)](https://github.com/chbarnhouse/trmnl-ha-integration/releases)

Home Assistant integration for TRMNL e-ink display devices. Enables automated screenshot capture of your HA dashboard and display on your TRMNL device.

## Features

- 📸 **Automatic Dashboard Screenshots** - Captures your HA dashboard at regular intervals
- 🎨 **E-ink Optimized Images** - Floyd-Steinberg dithering for TRMNL OG, color quantization for TRMNL X
- 🔐 **Secure Token Management** - HMAC-SHA256 signed tokens with automatic rotation
- 🌐 **Cloud & BYOS Support** - Works with both TRMNL cloud and self-hosted servers
- ⚡ **WebSocket Integration** - Real-time communication with the screenshot addon
- 📊 **Device Monitoring** - Battery, signal strength, and device status sensors
- 🎯 **Service Calls** - Trigger immediate screenshot capture via Home Assistant services

## Requirements

- Home Assistant 2024.1.0 or later
- TRMNL device (OG or X)
- [TRMNL Screenshot Addon](https://github.com/chbarnhouse/ha-addons)
- TRMNL cloud account or BYOS server

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Click "Integrations"
3. Click the "+" button
4. Search for "TRMNL"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/chbarnhouse/trmnl-ha-integration/releases)
2. Extract `trmnl` folder to `custom_components` directory
3. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Create Integration**
2. Search for "TRMNL" and select it
3. Enter your configuration:
   - **HA Dashboard URL** - URL of the HA dashboard to capture (e.g., `http://192.168.1.1:8123/lovelace/default`)
   - **HA Access Token** - Long-lived access token (create in Settings → Developer Tools → Personal Access Tokens)
   - **Token Secret** - 32+ character random string used for token signing
   - **Refresh Interval** - How often to capture (seconds, minimum 60)

4. Click Create
5. [Install the Screenshot Addon](https://github.com/chbarnhouse/ha-addons)
6. Configure the addon with matching credentials
7. Your TRMNL device should start receiving updated screenshots!

## Configuration

### Integration Options

In the integration settings, you can configure:

- **Dashboard URL** - Which HA dashboard/lovelace view to capture
- **Token Secret** - Secret for HMAC token signing (keep secure!)
- **Refresh Interval** - Screenshot capture frequency

### Addon Configuration

The companion [Screenshot Addon](https://github.com/chbarnhouse/ha-addons) must be installed on the same Home Assistant instance and configured with:

- **HA_URL** - Home Assistant internal URL
- **HA_TOKEN** - Same token used in integration
- **TOKEN_SECRET** - Same secret as integration
- **LOG_LEVEL** - Logging verbosity (debug, info, warning, error)

## Entities

The integration creates the following entities:

### Sensors
- `sensor.trmnl_device_battery` - Device battery percentage
- `sensor.trmnl_device_signal` - WiFi signal strength
- `sensor.trmnl_last_update` - Timestamp of last screenshot

### Binary Sensors
- `binary_sensor.trmnl_device_charging` - Device charging status
- `binary_sensor.trmnl_device_online` - Device online status

### Buttons
- `button.trmnl_capture_screenshot` - Manual trigger for screenshot capture

## Services

### `trmnl.capture_screenshot`

Manually trigger a screenshot capture for a device.

**Parameters:**
- `device_id` (required) - Your TRMNL device ID
- `force` (optional) - Skip rate limiting (default: false)

**Example:**
```yaml
service: trmnl.capture_screenshot
data:
  device_id: "abc123def456"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Home Assistant Instance                                      │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────────┐         ┌──────────────────────────┐   │
│ │   Integration    │◄────────┤  Screenshot Addon        │   │
│ │   (This Repo)    │         │  (Separate Repo)         │   │
│ │                  │         │                          │   │
│ │ • Config Flow    │         │ • Puppeteer Capture      │   │
│ │ • Device Mgmt    │         │ • Image Optimization     │   │
│ │ • Token Manager  │         │ • HTTP Serving           │   │
│ │ • WebSocket API  │         │ • Rate Limiting          │   │
│ └──────────────────┘         └──────────────────────────┘   │
│         │                              │                     │
└─────────┼──────────────────────────────┼─────────────────────┘
          │                              │
          ├──────────┬───────────────────┤
          │          │                   │
          ▼          ▼                   ▼
    ┌─────────┐ ┌────────────┐  ┌──────────────┐
    │  TRMNL  │ │  TRMNL HA  │  │  Screenshot  │
    │  Cloud  │ │  Device    │  │  Image       │
    │  Server │ │  (E-Ink)   │  │  (Hosted)    │
    └─────────┘ └────────────┘  └──────────────┘
```

## Troubleshooting

### Screenshot not updating
1. Check addon logs for capture errors
2. Verify token is being rotated correctly
3. Ensure dashboard URL is accessible internally
4. Check HA logs for websocket connection issues

### Integration won't install
1. Make sure HACS is up to date
2. Check manifest.json compatibility with your HA version
3. Clear browser cache and try again

### Rate limiting issues
1. Adjust refresh interval (higher = less frequent)
2. Use `force: true` in service calls if manually triggering
3. Check logs for "Rate limit exceeded" messages

## Development

### Requirements
```bash
pip install -r requirements-dev.txt
```

### Testing
```bash
pytest custom_components/trmnl/tests/
pytest custom_components/trmnl/tests/ --cov=custom_components/trmnl/
```

### Code Quality
```bash
black custom_components/trmnl/
pylint custom_components/trmnl/
mypy custom_components/trmnl/ --strict
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

- [GitHub Issues](https://github.com/chbarnhouse/trmnl-ha-integration/issues)
- [TRMNL Community](https://usetrmnl.com/community)
- [Home Assistant Community](https://community.home-assistant.io)

## Related Projects

- [TRMNL Screenshot Addon](https://github.com/chbarnhouse/ha-addons) - Required addon for screenshot capture
- [TRMNL Custom Plugin](https://github.com/chbarnhouse/trmnl-screenshot-plugin) - Optional plugin for advanced features
- [TRMNL Website](https://usetrmnl.com) - Official TRMNL site

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.
