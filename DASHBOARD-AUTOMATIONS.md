# TRMNL Dashboard Automations

This document provides comprehensive guidance for automating dashboard captures and updates to your TRMNL devices.

## Service: `trmnl.send_dashboard_to_device`

The dashboard capture service allows you to automatically capture Home Assistant dashboards and display them on your TRMNL device.

### Service Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `device_id` | string | *required* | TRMNL device identifier |
| `dashboard_path` | string | *required* | Dashboard path (e.g., `/lovelace/main`) |
| `theme` | string | *optional* | Home Assistant theme to apply |
| `width` | integer | `800` | Capture width in pixels |
| `height` | integer | `480` | Capture height in pixels |
| `orientation` | string | `landscape` | Display orientation |
| `center_x_offset` | integer | `0` | Horizontal offset from center (-200 to 200) |
| `center_y_offset` | integer | `0` | Vertical offset from center (-200 to 200) |
| `margin_top` | integer | `0` | Top margin in pixels |
| `margin_bottom` | integer | `0` | Bottom margin in pixels |
| `margin_left` | integer | `0` | Left margin in pixels |
| `margin_right` | integer | `0` | Right margin in pixels |
| `rotation_angle` | float | `0.0` | Fine rotation adjustment (-15.0° to 15.0°) |

### Orientation Options

- `landscape` - Default horizontal orientation
- `portrait` - Rotated 90° clockwise
- `landscape_inverted` - Rotated 180°
- `portrait_inverted` - Rotated 90° counter-clockwise

## Automation Blueprints

### 1. Scheduled Dashboard Capture

**File:** `blueprints/automation/trmnl/scheduled_dashboard_capture.yaml`

Perfect for daily dashboard updates at specific times.

**Features:**
- Configurable schedule time
- Optional weekday-only filtering
- Full customization of all capture parameters
- Easy device and dashboard selection

### 2. Weather-Based Dashboard Update

**File:** `blueprints/automation/trmnl/weather_dashboard_update.yaml`

Automatically switches between different dashboards based on time of day and weather conditions.

**Features:**
- Morning and evening dashboard switching
- Weather alert dashboard for severe conditions
- Time-based and weather state triggers
- Customizable themes for each scenario

## Common Automation Patterns

### Time-Based Updates

```yaml
# Daily morning update
- alias: "TRMNL Morning Dashboard"
  trigger:
    - platform: time
      at: "07:00:00"
  condition:
    - condition: time
      weekday: [mon, tue, wed, thu, fri]
  action:
    - service: trmnl.send_dashboard_to_device
      data:
        device_id: "your_device_id"
        dashboard_path: "/lovelace/morning"
        theme: "sunrise"
```

### Event-Driven Updates

```yaml
# Update when someone comes home
- alias: "TRMNL Welcome Home"
  trigger:
    - platform: state
      entity_id: person.john
      to: "home"
  action:
    - service: trmnl.send_dashboard_to_device
      data:
        device_id: "trmnl_hallway"
        dashboard_path: "/lovelace/welcome"
        theme: "greeting"
```

### Multi-Device Updates

```yaml
# Update all devices simultaneously
- alias: "TRMNL All Devices Update"
  trigger:
    - platform: time
      at: "08:00:00"
  action:
    - parallel:
        - service: trmnl.send_dashboard_to_device
          data:
            device_id: "trmnl_kitchen"
            dashboard_path: "/lovelace/kitchen"
        - service: trmnl.send_dashboard_to_device
          data:
            device_id: "trmnl_office"
            dashboard_path: "/lovelace/work"
```

## Advanced Configurations

### Portrait Orientation Setup

For TRMNL devices mounted in portrait orientation:

```yaml
action:
  - service: trmnl.send_dashboard_to_device
    data:
      device_id: "your_device_id"
      dashboard_path: "/lovelace/portrait"
      orientation: "portrait"
      width: 480
      height: 800
```

### Fine-Tuned Positioning

For TRMNL devices that are slightly unlevel or need positioning adjustments:

```yaml
action:
  - service: trmnl.send_dashboard_to_device
    data:
      device_id: "your_device_id"
      dashboard_path: "/lovelace/main"
      rotation_angle: 2.5  # Compensate for unlevel mounting
      center_x_offset: 10  # Shift slightly right
      margin_top: 15       # Add top margin
```

### Dynamic Dashboard Selection

Use templates for intelligent dashboard selection:

```yaml
action:
  - service: trmnl.send_dashboard_to_device
    data:
      device_id: "your_device_id"
      dashboard_path: >
        {% if is_state('sun.sun', 'above_horizon') %}
          /lovelace/day
        {% else %}
          /lovelace/night
        {% endif %}
      theme: >
        {% if is_state('sun.sun', 'above_horizon') %}
          light
        {% else %}
          dark
        {% endif %}
```

## Dashboard Design Tips

### Optimal Layouts for TRMNL

1. **Standard 7.5" TRMNL (800x480)**
   - Use 4-column layouts for cards
   - Keep text size 14px or larger
   - Avoid tiny icons or detailed charts

2. **Portrait Mode (480x800)**
   - Single column layouts work best
   - Stack cards vertically
   - Use larger card heights

### Theme Considerations

- **High Contrast Themes** work best on e-ink displays
- **Minimal Themes** reduce visual clutter
- **Custom TRMNL Themes** can be created specifically for your device

### Card Recommendations

**Good for TRMNL:**
- Weather cards with large text
- Simple sensor displays
- Calendar events
- Status indicators

**Avoid on TRMNL:**
- Complex charts with many data points
- Video/camera feeds
- Rapidly updating data
- Fine-detailed maps

## Troubleshooting

### Common Issues

1. **Dashboard not loading**
   - Verify dashboard path is correct
   - Check Home Assistant accessibility
   - Ensure theme exists

2. **Image appears rotated incorrectly**
   - Adjust `orientation` parameter
   - Use `rotation_angle` for fine tuning

3. **Content cut off**
   - Increase `width` and `height`
   - Adjust margins and offsets
   - Check dashboard responsive design

4. **Automation not triggering**
   - Verify device_id is correct
   - Check automation conditions
   - Review Home Assistant logs

### Debug Mode

Enable debug logging for detailed troubleshooting:

```yaml
logger:
  logs:
    custom_components.trmnl: debug
```

## Performance Considerations

- **Browser Resources**: Dashboard capture uses Playwright browser automation
- **Processing Time**: Allow 5-10 seconds for capture and processing
- **Frequency**: Avoid updates more frequent than every 5 minutes
- **Resource Cleanup**: Browser instances are automatically cleaned up after each capture

## Security Notes

- Dashboard capture accesses your Home Assistant instance internally
- No external network requests are made during capture
- Images are processed locally before sending to TRMNL
- Consider dashboard privacy when using sensitive data

---

For more examples and advanced configurations, see the `examples/dashboard_automations.yaml` file.