# CLAUDE.md - HA Integration

This file provides guidance to Claude Code when working on the ha-integration component.

---

## Project Overview

**Component**: TRMNL Home Assistant Integration (Python)
**Status**: Phase 2-3 (API Client & Config Flow) - Ready to start
**Repository**: trmnl-ha-integration
**License**: MIT

This is a HACS-compatible Home Assistant integration for TRMNL e-ink devices. It enables:
- Device discovery from TRMNL cloud and BYOS servers
- Entity management for device status (battery, signal, etc.)
- Screenshot update triggering via services
- WebSocket API for addon communication

## Architecture Context

**CRITICAL**: Read the master CLAUDE.md first for orchestration context.

### Key Design Decisions (Phase 0 Complete)
See ../docs/adr/ for full rationale:

1. **Image Hosting**: HA Ingress proxy (not direct port)
   - Secure by default (HTTPS managed by HA)
   - No user network configuration needed
   - Works for both cloud and BYOS TRMNL

2. **Authentication**: Rotating HMAC-signed tokens (24h TTL)
   - Automatic rotation (6h before expiry)
   - Self-validating (no state needed)
   - Addon validates via HMAC signature

3. **BYOS Support**: Full feature parity
   - Same API, same behavior for cloud and self-hosted
   - Different auth options (API key, basic auth, IP allowlist)
   - Unified codebase, no separate implementations

### Data Flow (Corrected via Phase 0)

**Original Assumption (WRONG)**:
```
Addon → [POST base64 to plugin] → Plugin receives image
```

**Corrected Architecture (VERIFIED)**:
```
1. Integration discovers TRMNL devices (cloud + BYOS)
2. Integration exposes WebSocket API for addon
3. Addon captures screenshot and hosts at URL
4. Integration updates TRMNL variables with image URL + token
5. TRMNL Server calls plugin on schedule
6. Plugin returns HTML with <img src="[addon-url]">
7. TRMNL Server fetches image and converts to e-ink
8. Device displays image
```

## Technical Stack

- **Language**: Python 3.11+
- **Framework**: Home Assistant Integration API
- **Key Libraries**: aiohttp, pydantic
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Linting**: black, pylint, mypy
- **Type Checking**: mypy with strict mode

## Development Phases

### Phase 2 (Week 3): API Client Implementation
- Implement CloudAPIClient
- Implement BYOSAPIClient with fallbacks
- Write comprehensive tests
- Validate device discovery

**Reference**: [HA Integration Dev Plan - Phase 2](../docs/ha-integration-dev-plan.md#phase-2-trmnl-api-client-days-3-7)

### Phase 3 (Week 4): Configuration Flow & WebSocket API
- Implement config_flow.py
- Implement data coordinator
- Implement WebSocket handlers for addon
- Implement services for screenshot triggering

**Reference**: [HA Integration Dev Plan - Phase 3-5](../docs/ha-integration-dev-plan.md#phase-3-configuration-flow-days-8-10)

## API Contract (This Component)

### WebSocket API (Integration ← → Addon)

**Handlers to implement**:
1. `trmnl/get_devices` - Return list of TRMNL devices
2. `trmnl/update_screenshot` - Trigger screenshot refresh
3. `trmnl/get_config` - Return addon configuration

See [API Contracts - Section 1](../docs/api-contracts.md#1-integration--addon-communication-websocket-api) for full spec.

### TRMNL API Communication (Integration → TRMNL Server)

**Must implement**:
- CloudAPIClient: Call usetrmnl.com API
- BYOSAPIClient: Call self-hosted server API (with fallbacks)
- Variables API: Update merge_vars with image URLs + tokens

See [API Contracts - Section 2.2](../docs/api-contracts.md#22-update-trmnl-variables-integration--trmnl-server-api) for full spec.

## Common Commands

```bash
# Setup
pip install -r requirements-dev.txt

# Testing
pytest tests/                           # Run all tests
pytest tests/test_api_cloud.py -v      # Run specific test file
pytest tests/ --cov=custom_components/trmnl --cov-report=html

# Linting & Formatting
black custom_components/trmnl/
pylint custom_components/trmnl/
mypy custom_components/trmnl/ --strict

# Running HA dev instance
# (See Home Assistant dev environment setup)

# View coverage report
open htmlcov/index.html
```

## Code Structure

```
custom_components/trmnl/
├── __init__.py                 # Integration entry point, setup
├── manifest.json               # HACS metadata
├── const.py                    # Constants and error codes
├── config_flow.py              # User configuration UI
├── coordinator.py              # Data update coordinator
├── websocket_api.py            # WebSocket API for addon
├── services.py                 # Service definitions
│
├── api/                        # TRMNL API client
│   ├── __init__.py
│   ├── base.py                # Base API client (abstract)
│   ├── cloud.py               # Cloud TRMNL implementation
│   └── byos.py                # BYOS implementation
│
├── models/                     # Data models
│   ├── __init__.py
│   ├── device.py              # TRMNLDevice model
│   └── types.py               # Type definitions
│
├── entities/                   # Entity definitions
│   ├── __init__.py
│   ├── device.py              # Device entities
│   ├── sensor.py              # Sensor entities
│   └── switch.py              # Switch entities
│
└── tests/
    ├── conftest.py            # Pytest fixtures
    ├── test_config_flow.py
    ├── test_api_cloud.py
    ├── test_api_byos.py
    ├── test_coordinator.py
    └── test_websocket_api.py
```

## Development Priorities

1. **Security First**: No hardcoded credentials, proper encryption
2. **HACS Compatibility**: Follow all HA integration requirements
3. **Cloud & BYOS Support**: Equal support for both server types
4. **Comprehensive Testing**: >90% coverage of critical paths
5. **Clear Documentation**: Docstrings for all public APIs

## Code Style & Standards

- **Type Hints**: Required for all function signatures
- **Docstrings**: Google-style for all classes and methods
- **Line Length**: 100 characters (black default)
- **Error Handling**: Specific exceptions, no bare except
- **Logging**: Use _LOGGER, never log credentials
- **Tests**: Both unit and integration tests required

## Key Dependencies

### Runtime
- `aiohttp>=3.9.0` - Async HTTP client
- `pydantic>=2.5.0` - Data validation

### Development
- `pytest>=7.4.0` - Testing
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.1.0` - Coverage reports
- `black>=23.10.0` - Code formatting
- `pylint>=3.0.0` - Linting
- `mypy>=1.6.0` - Type checking

## TRMNL Platform Reference

### Cloud API
- **Base URL**: https://usetrmnl.com/api
- **Auth**: Bearer token (API key)
- **Endpoints**:
  - `GET /devices` - List devices
  - `GET /devices/{id}` - Get device details
  - `POST /custom_plugins/{uuid}/variables` - Update variables

### BYOS API
- **Base URL**: http://[server-url]/api (varies)
- **Auth**: API key, basic auth, or none (depends on server)
- **Endpoints**: Same as cloud API (with fallbacks for compatibility)

See [TRMNL Research - Cloud vs BYOS](../docs/trmnl-research.md#7-cloud-vs-byos-implementation) for differences.

## Testing Requirements

### Unit Tests
- Test API client with mock responses
- Test config flow validation
- Test coordinator update logic
- Test WebSocket message handling
- Test entity creation and updates

### Integration Tests
- Test config flow end-to-end
- Test device discovery with real API
- Test WebSocket connection and messages
- Test coordinator error recovery

### Test Coverage
- Minimum: 85%
- Target: >90%
- Critical paths: 100%

## Security Considerations

### Credential Storage
- API keys stored in HA config entries (encrypted by HA)
- Never logged or exposed in logs
- Never used in error messages

### Input Validation
- Validate all user input in config flow
- Validate API responses (type and structure)
- Validate WebSocket messages from addon

### Error Handling
- Catch specific exceptions (not generic Exception)
- Log errors with context (not sensitive data)
- Handle timeouts and connection errors gracefully

## Important Context for Future Developers

- This is the **foundation** for the entire system (all other components depend on it)
- BYOS support requires careful API client design (see ADR 003)
- Token rotation in addon depends on updates via this component
- WebSocket API must be rock-solid (addon reliability depends on it)

## Quick Links

- **Master CLAUDE.md**: ../CLAUDE.md
- **Complete Dev Plan**: ../docs/ha-integration-dev-plan.md
- **API Contracts**: ../docs/api-contracts.md
- **Architecture Decisions**: ../docs/adr/
- **TRMNL Research**: ../docs/trmnl-research.md
- **HA Developer Docs**: https://developers.home-assistant.io/
