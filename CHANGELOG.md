# Changelog

All notable changes to this project will be documented in this file.

## [3.6.0] - 2025-01-07

### 🎉 Major New Feature: Dashboard Capture Service

Transform your Home Assistant dashboards into beautiful TRMNL displays with comprehensive automation support.

#### ✨ New Features

- **Dashboard Capture Service** (`trmnl.send_dashboard_to_device`)
  - Full Playwright browser automation for dashboard screenshots
  - Support for all Home Assistant themes
  - Configurable capture dimensions (optimized for 7.5" TRMNL default 800x480)
  - Advanced image processing with PIL/Pillow

#### 🔧 Customization Options

- **Orientation Support**: landscape, portrait, landscape_inverted, portrait_inverted
- **Positioning Controls**: center X/Y offsets for precise positioning
- **Margin Controls**: individual margin settings for all sides
- **Fine Rotation**: ±15° adjustment for unlevel TRMNL mounting
- **Theme Integration**: Apply any Home Assistant theme to dashboard capture

#### 🤖 Automation Support

- **2 Automation Blueprints**:
  - Scheduled dashboard capture with weekday filtering
  - Weather-based dashboard switching with time triggers
- **8 Example Automations** covering common use cases:
  - Daily morning/evening updates
  - Hourly work updates
  - Weather alert dashboards
  - Motion-triggered updates
  - Multi-device parallel updates
  - Dashboard rotation throughout the day
- **Comprehensive Documentation**: troubleshooting, performance tips, design recommendations

#### 🛠 Technical Implementation

- Browser automation using Playwright with Chromium
- Image processing pipeline with PIL/Pillow
- Automatic screen creation and device assignment via Terminus API
- Resource cleanup and error handling
- Debug logging support

#### 📦 Dependencies Added

- `playwright` - Browser automation for dashboard capture
- `pillow` - Image processing for orientation and positioning

#### 🎯 Use Cases

- **Morning Dashboard**: Weather, calendar, and daily briefing
- **Work Dashboard**: Productivity metrics and status indicators  
- **Evening Dashboard**: Relaxation themes and evening routines
- **Weather Alerts**: Severe weather information and warnings
- **Motion Activation**: Update display when someone enters the room
- **Multi-Device Orchestration**: Different dashboards for different rooms

## [2.0.0] - 2024-08-27

### Major Features Added
- **Real Browser Screenshots**: Complete Puppeteer-based screenshot service for capturing actual Home Assistant dashboards
- **Enhanced Dashboard Service**: Convert any HA dashboard to TRMNL-compatible screens with full customization
- **Screenshot Service Deployment**: Production-ready Node.js service with Docker support
- **Advanced Display Controls**: Margins, alignment, zoom, wait times, and CSS selector support
- **Multiple Dashboard Collections**: Create playlists from multiple dashboards automatically
- **Fallback Image Generation**: Automatic fallback when screenshots fail
- **Professional Documentation**: Complete setup guides, examples, and troubleshooting

### New Services
- `trmnl.create_dashboard_screen` - Convert single HA dashboard to TRMNL screen
- `trmnl.update_dashboard_screen` - Update existing screens with new content
- `trmnl.create_dashboard_collection` - Multiple dashboards with automatic playlist creation

### Technical Improvements
- Complete screenshot service with Puppeteer + Chrome + Sharp
- Docker deployment with health monitoring
- Enhanced error handling and logging
- GitHub Actions for automated validation and releases
- HACS-ready repository structure
- Professional README with usage examples

### Tested & Validated
- Screenshot service working on production server
- Real dashboard conversion tested and functional
- Docker deployment validated
- HACS validation passing

## [1.0.0] - 2024-08-27

### Added
- Initial release of TRMNL Home Assistant Integration
- Real browser screenshot capability using Puppeteer
- Support for Home Assistant dashboard conversion to TRMNL screens
- Multiple dashboard collection support with playlist creation
- Configurable display settings (margins, alignment, zoom, wait time)
- CSS selector support for targeting specific dashboard elements
- Complete Home Assistant integration with config flow
- HACS compatibility
- Comprehensive documentation and setup guides
- Docker support for screenshot service
- GitHub Actions for automated releases and validation

### Features
- `trmnl.create_dashboard_screen` service for single dashboard screenshots
- `trmnl.update_dashboard_screen` service for updating existing screens
- `trmnl.create_dashboard_collection` service for multiple dashboards
- Full TRMNL API integration for device control
- Fallback image generation when screenshots fail
- Debug logging support

### Technical
- Supports Home Assistant 2023.1+
- Uses aiohttp for async HTTP requests
- Pillow for image processing fallbacks
- Real-time screenshot service with health monitoring
- Proper error handling and logging
- HACS validation and Hassfest compliance