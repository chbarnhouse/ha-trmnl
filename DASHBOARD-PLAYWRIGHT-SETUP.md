# Dashboard Capture Setup - Playwright Installation

The TRMNL integration's dashboard capture feature requires Playwright for browser automation. Due to platform compatibility issues in some Home Assistant environments, Playwright is now an optional dependency.

## Current Status

- **Dashboard capture service**: Conditionally available based on Playwright installation
- **Core TRMNL features**: Always available (device control, playlists, etc.)
- **Graceful fallback**: Integration loads successfully even without Playwright

## Installation Methods

### Method 1: Home Assistant OS (Recommended)

If you're running Home Assistant OS, the dashboard capture feature should work automatically in most cases. If you see Playwright installation errors:

1. **Restart Home Assistant** after installing the TRMNL integration
2. **Check the logs** for specific error messages
3. **Wait for retry** - Home Assistant will attempt to install dependencies multiple times

### Method 2: Docker Container

For Docker installations, you may need to use a custom container with Playwright pre-installed:

```dockerfile
FROM homeassistant/home-assistant:stable

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2

# Install Playwright
RUN pip install playwright
RUN playwright install chromium
```

### Method 3: Home Assistant Core (Manual Installation)

If running Home Assistant Core on your own Python environment:

```bash
# Activate your Home Assistant virtual environment
source /srv/homeassistant/bin/activate

# Install Playwright
pip install playwright

# Install browser binaries
playwright install chromium

# Restart Home Assistant
sudo systemctl restart home-assistant@homeassistant
```

### Method 4: Alternative Browser Services

If Playwright installation continues to fail, consider these alternatives:

1. **External Screenshot Service**: Set up a separate service for dashboard capture
2. **Image Upload**: Manually create dashboard images and upload via TRMNL API
3. **Wait for Updates**: Future versions may include alternative browser automation

## Troubleshooting

### Common Error Messages

**"Requirements for trmnl not found: ['playwright']"**
- **Solution**: Playwright installation failed. Try methods above.

**"No solution found when resolving dependencies"**  
- **Solution**: Platform compatibility issue. Use Docker method or external service.

**"Dashboard capture is not available"**
- **Expected**: Service will show this message when Playwright is not installed
- **Solution**: This is normal - the rest of the integration still works

### Verification Steps

1. **Check Integration Status**:
   - Go to Settings > Devices & Services > TRMNL
   - Integration should load successfully even without Playwright

2. **Check Service Availability**:
   - Go to Developer Tools > Services
   - Look for `trmnl.send_dashboard_to_device`
   - If missing: Playwright is not available
   - If present: Dashboard capture is ready

3. **Check Logs**:
   ```
   # Should see one of these messages:
   INFO: Dashboard capture service enabled (Playwright available)
   WARNING: Dashboard capture service disabled - Playwright not available
   ```

## Feature Status by Platform

| Platform | Core Features | Dashboard Capture | Notes |
|----------|---------------|-------------------|-------|
| **Home Assistant OS** | ✅ Always | ⚠️ Usually works | May need restart |
| **Home Assistant Container** | ✅ Always | ❌ Often fails | Platform compatibility |
| **Home Assistant Core** | ✅ Always | ✅ Manual install | Full control |
| **Home Assistant Supervised** | ✅ Always | ⚠️ Varies | Depends on host |

## Alternative Solutions

If dashboard capture is not available on your system, you can still display dashboards on TRMNL using:

1. **Manual Screenshots**: Take screenshots and upload via TRMNL web interface
2. **External Tools**: Use other screenshot services with TRMNL API
3. **Static Images**: Create dashboard-style images and send them
4. **Future Updates**: We're working on platform-independent solutions

## Support

If you continue to experience issues:

1. **Check Home Assistant logs** for specific error messages
2. **Report compatibility issues** on the GitHub repository
3. **Consider alternative approaches** listed above
4. **Use core features** while dashboard capture is unavailable

The integration is designed to work fully even without the dashboard capture feature!