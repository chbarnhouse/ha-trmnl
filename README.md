# TRMNL Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40chbarnhouse-blue.svg)](https://github.com/chbarnhouse)
[![GitHub release](https://img.shields.io/github/v/release/chbarnhouse/ha-trmnl.svg)](https://github.com/chbarnhouse/ha-trmnl/releases)

A custom integration for Home Assistant that integrates with TRMNL devices and services.

## Features

- **Device Discovery**: Automatically discover and configure TRMNL devices
- **Real-time Updates**: Get live updates from your TRMNL devices
- **Screen Management**: Control and configure TRMNL screens
- **Plugin Integration**: Manage TRMNL plugins through Home Assistant
- **Webhook Support**: Receive webhooks from TRMNL services

## Installation

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Add this repository as a custom repository in HACS
3. Search for "TRMNL" in the integrations section
4. Click "Download"
5. Restart Home Assistant
6. Go to **Settings** → **Devices & Services** → **Add Integration**
7. Search for "TRMNL" and configure it

### Manual Installation

1. Download the latest release
2. Extract the `trmnl` folder to your `config/custom_components/` directory
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for "TRMNL" and configure it

## Configuration

### Required Configuration

- **API Key**: Your TRMNL API key from the [TRMNL dashboard](https://docs.usetrmnl.com/go)
- **Device ID**: Your TRMNL device identifier

### Optional Configuration

- **Update Interval**: How often to poll for updates (default: 30 seconds)
- **Webhook Port**: Port for receiving webhooks (default: 8123)

## Usage

After configuration, the integration will:

1. **Discover Devices**: Automatically find your TRMNL devices
2. **Create Entities**: Generate Home Assistant entities for each device
3. **Enable Control**: Allow you to control devices through Home Assistant
4. **Provide Sensors**: Show device status, screen content, and more

## Services

The integration provides several services:

- `trmnl.update_screen`: Update a TRMNL screen
- `trmnl.install_plugin`: Install a plugin on a device
- `trmnl.uninstall_plugin`: Remove a plugin from a device
- `trmnl.restart_device`: Restart a TRMNL device

## Entities

### Device Entities

- **Status**: Online/offline status
- **Last Seen**: Last communication time
- **Firmware Version**: Current firmware version

### Screen Entities

- **Current Screen**: Active screen identifier
- **Screen Content**: Current display content
- **Brightness**: Screen brightness level

### Plugin Entities

- **Installed Plugins**: List of installed plugins
- **Plugin Status**: Running/stopped status

## Troubleshooting

### Common Issues

1. **Integration won't load**: Check your API key and restart Home Assistant
2. **Devices not discovered**: Verify your device ID and network connectivity
3. **Webhooks not working**: Check firewall settings and port configuration

### Logs

Enable debug logging by adding to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.trmnl: debug
```

## Development

This integration is open source. Contributions are welcome!

### Local Development

1. Clone this repository
2. Copy the `trmnl` folder to your `config/custom_components/` directory
3. Make your changes
4. Restart Home Assistant to test

## Support

- **Issues**: [GitHub Issues](https://github.com/chbarnhouse/ha-trmnl/issues)
- **Documentation**: [TRMNL Docs](https://docs.usetrmnl.com/go)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- Built for [TRMNL](https://usetrmnl.com/)
- Compatible with [Home Assistant](https://www.home-assistant.io/)
- Installable through [HACS](https://hacs.xyz/)
