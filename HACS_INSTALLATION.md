# HACS Installation Guide for TRMNL Integration

This guide explains how to install the TRMNL integration through HACS (Home Assistant Community Store).

## Prerequisites

1. **Home Assistant**: Version 2023.8.0 or newer
2. **HACS**: Must be installed and configured in your Home Assistant instance
3. **TRMNL Account**: API credentials from [TRMNL](https://docs.usetrmnl.com/go)

## HACS Installation

### Step 1: Add Custom Repository

1. Open your Home Assistant instance
2. Go to **HACS** → **Integrations**
3. Click the **⋮** (three dots) menu in the top right
4. Select **Custom repositories**
5. Click **Add**
6. Enter the following information:
   - **Repository**: `chbarnhouse/ha-trmnl`
   - **Category**: `Integration`
7. Click **Add**

### Step 2: Install the Integration

1. In HACS → **Integrations**, search for "TRMNL"
2. Click on the TRMNL integration
3. Click **Download**
4. Wait for the download to complete
5. Click **Restart Home Assistant**

### Step 3: Configure the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "TRMNL"
4. Click on **TRMNL**
5. Enter your configuration:
   - **API Key**: Your TRMNL API key
   - **Device ID**: Your TRMNL device ID
   - **Name** (Optional): Custom name for the integration
   - **Update Interval**: How often to poll for updates (default: 30 seconds)
   - **Webhook Port**: Port for receiving webhooks (default: 8123)
6. Click **Submit**

## Manual Installation (Alternative)

If you prefer not to use HACS, you can install manually:

### Step 1: Download the Integration

1. Go to the [GitHub repository](https://github.com/chbarnhouse/ha-trmnl)
2. Click **Code** → **Download ZIP**
3. Extract the ZIP file

### Step 2: Copy to Home Assistant

1. Copy the `trmnl` folder from `custom_components/trmnl/`
2. Paste it into your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

### Step 3: Configure

Follow the same configuration steps as above.

## Configuration Options

### Required Configuration

- **API Key**: Your TRMNL API key from the dashboard
- **Device ID**: The unique identifier for your TRMNL device

### Optional Configuration

- **Name**: Custom name for the integration (defaults to "TRMNL")
- **Update Interval**: Polling frequency in seconds (default: 30)
- **Webhook Port**: Port for webhook reception (default: 8123)

## Verification

After installation, verify the integration is working:

1. **Check Entities**: Go to **Settings** → **Devices & Services** → **Entities**
2. **Look for TRMNL entities**:

   - `sensor.trmnl_device_status`
   - `binary_sensor.trmnl_device_online`
   - `sensor.trmnl_screen_[screen_id]`
   - `light.trmnl_screen_[screen_id]_light`
   - `switch.trmnl_device_restart`

3. **Check Logs**: Enable debug logging to see API communication:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.trmnl: debug
   ```

## Troubleshooting

### Common Issues

1. **Integration not found**:

   - Ensure HACS is properly installed
   - Check repository URL is correct
   - Restart Home Assistant after adding repository

2. **Configuration fails**:

   - Verify API key is correct
   - Check device ID exists
   - Ensure network connectivity to TRMNL API

3. **Entities not created**:

   - Check Home Assistant logs for errors
   - Verify API communication is successful
   - Restart the integration

4. **Services not working**:
   - Check service registration in logs
   - Verify entity targeting
   - Test with Developer Tools → Services

### Debug Steps

1. **Enable Debug Logging**:

   ```yaml
   logger:
     default: info
     logs:
       custom_components.trmnl: debug
   ```

2. **Check Configuration**:

   - Go to **Settings** → **Devices & Services**
   - Find TRMNL integration
   - Click **Configure**
   - Verify all settings

3. **Test API Connection**:

   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://api.usetrmnl.com/v1/devices/YOUR_DEVICE_ID
   ```

4. **Restart Integration**:
   - Go to **Settings** → **Devices & Services**
   - Find TRMNL integration
   - Click **Reload**

## Updating

### HACS Updates

1. HACS will automatically check for updates
2. Go to **HACS** → **Integrations**
3. Look for update notifications
4. Click **Update** when available
5. Restart Home Assistant

### Manual Updates

1. Download the latest release
2. Replace the `trmnl` folder in `custom_components/`
3. Restart Home Assistant

## Uninstallation

### Remove Integration

1. Go to **Settings** → **Devices & Services**
2. Find TRMNL integration
3. Click **Unload**
4. Click **Delete**

### Remove from HACS

1. Go to **HACS** → **Integrations**
2. Find TRMNL
3. Click **Remove**
4. Restart Home Assistant

### Clean Up Files

1. Remove `custom_components/trmnl/` directory
2. Remove any TRMNL entities from dashboards
3. Remove TRMNL automations and scripts

## Support

### Getting Help

1. **Check Logs**: Enable debug logging for detailed information
2. **GitHub Issues**: Report bugs and request features
3. **Community Forum**: Ask questions in the Home Assistant community
4. **TRMNL Documentation**: Refer to [TRMNL docs](https://docs.usetrmnl.com/go)

### Useful Links

- [Home Assistant Documentation](https://www.home-assistant.io/docs/)
- [HACS Documentation](https://hacs.xyz/docs/)
- [TRMNL Website](https://usetrmnl.com/)
- [TRMNL API Documentation](https://docs.usetrmnl.com/go)

## Advanced Configuration

### Multiple Devices

To configure multiple TRMNL devices:

1. Add the integration multiple times
2. Use different names for each instance
3. Configure different device IDs
4. Set appropriate update intervals

### Custom Services

The integration provides several custom services:

- `trmnl.trmnl_update_screen`: Update screen content
- `trmnl.trmnl_install_plugin`: Install plugins
- `trmnl.trmnl_uninstall_plugin`: Remove plugins
- `trmnl.trmnl_restart_device`: Restart device
- `trmnl.trmnl_set_brightness`: Control brightness
- `trmnl.trmnl_setup_webhook`: Configure webhooks

### Automation Examples

```yaml
# Update screen on motion
automation:
  - alias: "TRMNL Motion Alert"
    trigger:
      platform: state
      entity_id: binary_sensor.motion_sensor
      to: "on"
    action:
      service: trmnl.trmnl_update_screen
      data:
        screen_id: "main_screen"
        content: "Motion Detected!"

# Set brightness at night
automation:
  - alias: "TRMNL Night Mode"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      service: trmnl.trmnl_set_brightness
      data:
        brightness: 20
```

## Conclusion

The TRMNL integration provides comprehensive control over your TRMNL devices through Home Assistant. Follow this guide for successful installation and configuration. For additional help, refer to the support resources listed above.
