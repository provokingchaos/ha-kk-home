# KK Home Integration for Home Assistant

A custom Home Assistant integration for **KK Home** smart locks (such as the VE019 door lock) and Wi-Fi gateways/bridges (SGAHA-SG3), supporting credential-based authentication, token management, and real-time device state tracking.

## Features

- **Credential Authentication:** Log in directly using your KK Home account email and password via the Home Assistant UI config flow.
- **Lock Entity:** Full support for locking and unlocking your doors directly from Home Assistant.
- **Gateway Power Switch:** Toggle your Wi-Fi bridge / outlet power state on and off.
- **Battery Tracking Sensor:** Exposes real-time battery percentage for your lock sub-devices as native Home Assistant battery sensors.
- **DataUpdateCoordinator Architecture:** Efficiently polls the KK Home API every 30 seconds to keep states synchronized across devices.

## Supported Devices

- **Gateways:** KK Wi-Fi Bridge (`SGAHA-SG3` / `G1`)
- **Locks:** Smart Door Lock (`VE019` / `SA501`)

## Repository Architecture & File Layout

custom_components/
└── kkhome/
    ├── __init__.py
    ├── config_flow.py
    ├── const.py
    ├── coordinator.py
    ├── lock.py
    ├── manifest.json
    ├── sensor.py
    ├── switch.py
    └── translations/
        └── en.json

| File Path | Description |
| :--- | :--- |
| `custom_components/kkhome/__init__.py` | Initializes the integration entry, sets up the data update coordinator using stored authentication tokens, and loads platform setups. |
| `custom_components/kkhome/config_flow.py` | Handles UI configuration forms, authenticating user email and password credentials against the KK Home API to dynamically store session tokens. |
| `custom_components/kkhome/const.py` | Defines domain constants and global variables used across the integration files. |
| `custom_components/kkhome/coordinator.py` | Manages background polling of the KK Home API (`/v3/user/device/list`), safely parsing raw bytes to prevent mimetype decoding issues. |
| `custom_components/kkhome/lock.py` | Implements Home Assistant lock entities for smart door locks, executing open/close commands and updating states. |
| `custom_components/kkhome/manifest.json` | Declares integration metadata, domain keys, versioning, and enables UI configuration flows (`"config_flow": true`). |
| `custom_components/kkhome/sensor.py` | Exposes device battery percentage and telemetry as native Home Assistant sensors. |
| `custom_components/kkhome/switch.py` | Implements power control switches for Wi-Fi bridges and gateway outlets. |
| `custom_components/kkhome/translations/en.json` | Stores localized text strings and error descriptions for the UI config flow wizard. |

## Installation

### Method 1: HACS (Recommended)

1. Open HACS in your Home Assistant instance and navigate to **Integrations**.
2. Click the three dots in the top-right corner and select **Custom repositories**.
3. Add your repository URL:
   - **Repository:** `https://gitlab.com/your-username/ha-kk-home`
   - **Category:** `Integration`
4. Click **Add**, download the integration through HACS, and restart Home Assistant.

### Method 2: Manual Installation

1. Clone or download this repository.
2. Copy the `custom_components/kkhome` directory into your Home Assistant `config/custom_components/` folder.
3. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Settings** > **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **KK Home**.
4. Enter your KK Home account **Email** and **Password** when prompted and submit.

## Entity Mappings

| Platform | Entity Type | API Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Lock** | `lock.*` | `subDevices[0].openStatus` | `1` = Locked, `2` = Unlocked |
| **Switch** | `switch.*_power` | `gwPowerStatus` | Controls gateway / outlet power state |
| **Sensor** | `sensor.*_battery` | `subDevices[0].power` | Reports lock battery percentage |

## Troubleshooting

- **Debug Logging:** To enable verbose logging for troubleshooting network requests or login responses, add the following to your `configuration.yaml`:

logger:
  default: warning
  logs:
    custom_components.kkhome: debug
