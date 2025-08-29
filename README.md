# TRMNL Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

**Control your TRMNL e-paper display directly from Home Assistant with real browser screenshot capabilities.**

![TRMNL Integration](https://raw.githubusercontent.com/chbarnhouse/ha-trmnl/main/images/trmnl-hero.png)

## Features

✅ **Real Browser Screenshots** - Capture actual Home Assistant dashboards using Puppeteer  
✅ **Display Customization** - Configure margins, alignment, zoom, and wait times  
✅ **Multiple Dashboard Support** - Create collections of screens from different dashboards  
✅ **TRMNL Device Control** - Update screens and manage your TRMNL device  
✅ **Service Integration** - Easy-to-use Home Assistant services  
✅ **Playlist Support** - Automatically create playlists from dashboard collections  

## Quick Start

### Prerequisites
- Home Assistant 2023.1+
- TRMNL device with local Terminus server
- Screenshot service deployed (see setup guide)

### Installation via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=chbarnhouse&repository=ha-trmnl&category=integration)

1. Install via HACS:
   - Go to HACS → Integrations
   - Click "Explore & Download Repositories"  
   - Search for "TRMNL"
   - Install the integration
2. Restart Home Assistant
3. Go to Settings → Devices & Services
4. Click "Add Integration"
5. Search for "TRMNL" and configure

### Manual Installation

1. Copy the `custom_components/trmnl` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via the UI

## Configuration

### Initial Setup
When adding the integration, you'll need:
- **TRMNL Server URL**: Your local Terminus server (e.g., `http://192.168.1.5:3000`)
- **API Key**: From your TRMNL dashboard
- **Screenshot Service URL**: Your screenshot service endpoint (e.g., `http://192.168.1.5:3002`)

### Screenshot Service Setup
The integration requires a screenshot service to capture real browser screenshots. See the [Screenshot Service Guide](docs/screenshot-service.md) for deployment instructions.

## Services

### `trmnl.create_dashboard_screen`
Create a single screen from a Home Assistant dashboard.

```yaml
service: trmnl.create_dashboard_screen
data:
  device_id: "YOUR_DEVICE_ID"
  dashboard_url: "/lovelace/home"
  screen_name: "Home Dashboard"
  margins:
    top: 20
    right: 20
    bottom: 20
    left: 20
  alignment: "center"
  zoom: 1.0
  wait_time: 2000
```

### `trmnl.create_dashboard_collection`
Create multiple screens and an optional playlist.

```yaml
service: trmnl.create_dashboard_collection
data:
  device_id: "YOUR_DEVICE_ID"
  create_playlist: true
  dashboards:
    - url: "/lovelace/home"
      name: "Home Dashboard"
      zoom: 0.8
    - url: "/lovelace/energy"
      name: "Energy Dashboard"
      alignment: "left"
```

### `trmnl.update_dashboard_screen`
Update an existing screen with new content.

```yaml
service: trmnl.update_dashboard_screen
data:
  screen_id: 123
  dashboard_url: "/lovelace/updated-dashboard"
  zoom: 1.2
```

## Dashboard URLs

Use relative paths for your dashboards:
- Main dashboard: `/lovelace` or `/lovelace/0`
- Named dashboards: `/lovelace/dashboard-name`
- Admin dashboards: `/config/dashboard`

## Display Customization

### Margins
Control spacing around your dashboard content:
```yaml
margins:
  top: 20     # Top margin in pixels
  right: 20   # Right margin in pixels  
  bottom: 20  # Bottom margin in pixels
  left: 20    # Left margin in pixels
```

### Alignment
Position your content:
- `left` - Align to left edge
- `center` - Center content (default)
- `right` - Align to right edge

### Zoom
Scale your dashboard:
- `0.5` - 50% size (fit more content)
- `1.0` - Original size (default)
- `1.5` - 150% size (larger text/elements)

### Wait Time
Time to wait before taking screenshot (in milliseconds):
- `2000` - 2 seconds (default)
- `5000` - 5 seconds (for slow-loading dashboards)

### CSS Selectors
Target specific dashboard elements:
```yaml
selector: ".panel-view"          # Screenshot main panel
selector: "#energy-card"         # Screenshot specific card
selector: ".type-custom\\:button-card"  # Screenshot button cards
```

## Automation Examples

### Daily Dashboard Update
```yaml
automation:
  - alias: "Update TRMNL with Morning Dashboard"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      service: trmnl.create_dashboard_screen
      data:
        device_id: "YOUR_DEVICE_ID"
        dashboard_url: "/lovelace/morning"
        screen_name: "Morning Brief"
```

### Weather-Based Dashboard
```yaml
automation:
  - alias: "TRMNL Weather Dashboard"
    trigger:
      platform: state
      entity_id: weather.home
    action:
      service: trmnl.create_dashboard_screen
      data:
        device_id: "YOUR_DEVICE_ID"
        dashboard_url: "/lovelace/weather"
        screen_name: "Weather Update"
        wait_time: 3000
```

## Troubleshooting

### Common Issues

**Screenshots are blank or fail:**
- Verify screenshot service is running and accessible
- Check dashboard URL is correct and accessible
- Increase `wait_time` for slow-loading dashboards

**Content is cut off:**
- Adjust `zoom` level (try 0.8 or 0.9)
- Modify `margins` to give more space
- Use CSS `selector` to target specific elements

**Service calls fail:**
- Verify TRMNL server URL and API key
- Check device ID is correct
- Ensure Home Assistant can reach TRMNL server

### Debug Mode
Enable debug logging:
```yaml
logger:
  logs:
    custom_components.trmnl: debug
```

## Contributing

Issues and feature requests are welcome! Please check the [issue tracker](https://github.com/chbarnhouse/ha-trmnl/issues).

## Support

- [Community Forum](https://community.home-assistant.io/)
- [Discord](https://discord.gg/home-assistant)
- [Issue Tracker](https://github.com/chbarnhouse/ha-trmnl/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<a href="https://www.buymeacoffee.com/chbarnhouse" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

[releases-shield]: https://img.shields.io/github/release/chbarnhouse/ha-trmnl.svg?style=for-the-badge
[releases]: https://github.com/chbarnhouse/ha-trmnl/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/chbarnhouse/ha-trmnl.svg?style=for-the-badge
[commits]: https://github.com/chbarnhouse/ha-trmnl/commits/main
[license-shield]: https://img.shields.io/github/license/chbarnhouse/ha-trmnl.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40chbarnhouse-blue.svg?style=for-the-badge
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[buymecoffee]: https://www.buymeacoffee.com/chbarnhouse
[discord]: https://discord.gg/home-assistant
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/