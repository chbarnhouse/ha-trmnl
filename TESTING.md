# Testing Guide for TRMNL Integration

This guide explains how to test the TRMNL integration during development and before release.

## Prerequisites

1. **Home Assistant Development Environment**: Set up a local Home Assistant development environment
2. **TRMNL API Access**: Get API credentials from [TRMNL](https://docs.usetrmnl.com/go)
3. **Test Device**: Access to a TRMNL device for testing

## Local Development Testing

### 1. Setup Development Environment

```bash
# Clone your repository
git clone https://github.com/chbarnhouse/ha-trmnl.git
cd ha-trmnl

# Copy to Home Assistant custom_components directory
cp -r custom_components/trmnl ~/.homeassistant/custom_components/

# Restart Home Assistant
```

### 2. Test Configuration Flow

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "TRMNL"
3. Enter your test credentials:
   - API Key: Your TRMNL API key
   - Device ID: Your test device ID
   - Name: "Test TRMNL Device"
   - Update Interval: 30
   - Webhook Port: 8123
4. Verify the configuration completes successfully

### 3. Test Entity Creation

After successful configuration, verify that entities are created:

- **Sensors**: Device status, screen information, plugin status
- **Binary Sensors**: Device online status, screen activity, plugin running
- **Switches**: Device restart, plugin control
- **Lights**: Screen brightness control
- **Cameras**: Screen display

### 4. Test API Communication

Check the Home Assistant logs for successful API communication:

```bash
# Enable debug logging
logger:
  default: info
  logs:
    custom_components.trmnl: debug

# Check logs
tail -f ~/.homeassistant/home-assistant.log | grep TRMNL
```

## Integration Testing

### 1. Test Device Discovery

- Verify device information is correctly retrieved
- Check that device state is properly determined
- Ensure firmware version and model information is displayed

### 2. Test Screen Management

- Update screen content using the service
- Verify screen state changes
- Test brightness control
- Check screen activity sensors

### 3. Test Plugin Management

- Install a test plugin
- Verify plugin status updates
- Uninstall the plugin
- Check plugin control switches

### 4. Test Device Control

- Test device restart functionality
- Verify webhook setup
- Check update intervals
- Test error handling

## Service Testing

### 1. Test Screen Update Service

```yaml
# Test in Developer Tools → Services
service: trmnl.trmnl_update_screen
data:
  screen_id: "main_screen"
  content: "Test Content"
  template: false
target:
  entity_id: sensor.trmnl_device_status
```

### 2. Test Plugin Installation

```yaml
service: trmnl.trmnl_install_plugin
data:
  plugin_id: "test_plugin"
  config: '{"test": "value"}'
target:
  entity_id: sensor.trmnl_device_status
```

### 3. Test Device Restart

```yaml
service: trmnl.trmnl_restart_device
target:
  entity_id: sensor.trmnl_device_status
```

### 4. Test Brightness Control

```yaml
service: trmnl.trmnl_set_brightness
data:
  brightness: 75
target:
  entity_id: sensor.trmnl_device_status
```

## Webhook Testing

### 1. Test Webhook Reception

1. Set up webhook in TRMNL dashboard
2. Send test webhook to your Home Assistant instance
3. Verify webhook data is processed
4. Check that entities update accordingly

### 2. Test Real-time Updates

- Verify that webhook events trigger immediate updates
- Check that polling continues to work
- Ensure no duplicate updates occur

## Error Handling Testing

### 1. Test Invalid API Key

- Use invalid API key in configuration
- Verify appropriate error message
- Check that configuration fails gracefully

### 2. Test Invalid Device ID

- Use non-existent device ID
- Verify error handling
- Check user feedback

### 3. Test Network Issues

- Disconnect network during operation
- Verify timeout handling
- Check reconnection logic

### 4. Test API Errors

- Mock API error responses
- Verify error logging
- Check user notification

## Performance Testing

### 1. Test Update Intervals

- Test different update intervals (10s, 30s, 60s)
- Verify performance impact
- Check memory usage

### 2. Test Multiple Devices

- Configure multiple TRMNL devices
- Verify performance with multiple coordinators
- Check resource usage

### 3. Test Webhook Load

- Send multiple webhooks rapidly
- Verify processing performance
- Check queue handling

## UI Testing

### 1. Test Entity Cards

- Verify entity information display
- Check attribute visibility
- Test entity controls

### 2. Test Device Info

- Verify device information page
- Check entity relationships
- Test device control options

### 3. Test Configuration

- Test configuration flow
- Verify validation
- Check error messages

## Integration Tests

### 1. Test with Other Integrations

- Test with automation platform
- Verify script integration
- Check template sensor compatibility

### 2. Test with HACS

- Install through HACS
- Verify installation process
- Check update mechanism

## Release Testing

### 1. Pre-release Checklist

- [ ] All tests pass locally
- [ ] Code follows Home Assistant standards
- [ ] Documentation is complete
- [ ] Requirements are specified
- [ ] Manifest is correct
- [ ] Translations are complete

### 2. Release Testing

- [ ] Test on different Home Assistant versions
- [ ] Test on different platforms (Linux, Windows, macOS)
- [ ] Test with different Python versions
- [ ] Verify HACS compatibility

### 3. Post-release Monitoring

- [ ] Monitor GitHub issues
- [ ] Check user feedback
- [ ] Monitor error logs
- [ ] Track usage statistics

## Troubleshooting

### Common Issues

1. **Integration won't load**: Check API credentials and device ID
2. **Entities not created**: Verify API communication
3. **Services not working**: Check service registration
4. **Webhooks not received**: Verify webhook configuration

### Debug Commands

```bash
# Check integration status
ha core restart

# View logs
tail -f ~/.homeassistant/home-assistant.log

# Check configuration
ha config check

# Test API connection
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.usetrmnl.com/v1/devices/YOUR_DEVICE_ID
```

## Testing Tools

### 1. Home Assistant Test Suite

```bash
# Run Home Assistant tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_trmnl.py -v
```

### 2. API Testing

```bash
# Test TRMNL API endpoints
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.usetrmnl.com/v1/devices

curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.usetrmnl.com/v1/devices/YOUR_DEVICE_ID/status
```

### 3. Mock Testing

Create mock responses for testing without real API access:

```python
# Mock API responses for testing
MOCK_DEVICE_INFO = {
    "id": "test_device",
    "name": "Test Device",
    "model": "TRMNL Test",
    "firmware_version": "1.0.0"
}
```

## Conclusion

Thorough testing ensures the integration works reliably for users. Test all functionality, error conditions, and edge cases before release. Monitor user feedback and continuously improve the integration based on real-world usage.
