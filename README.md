# KK Home Integration for Home Assistant

A custom Home Assistant integration for **KK Home** smart locks (such as the VE019 door lock) and Wi-Fi gateways/bridges (SGAHA-SG3), leveraging token-based API polling and state tracking.

---

## Features

- **Lock Entity:** Full support for locking (`/v3/gateway/set-lock-close`) and unlocking (`/v3/gateway/set-lock-open`) your doors directly from Home Assistant.
- **Gateway Power Switch:** Toggle your Wi-Fi bridge / outlet power state on and off (`/v3/gateway/set-gateway-power`).
- **Battery Tracking Sensor:** Exposes real-time battery percentage (`power`) for your lock sub-devices as native Home Assistant battery sensors.
- **DataUpdateCoordinator Architecture:** Efficiently polls the KK Home API every 30 seconds to keep states synchronized across devices without hammering the cloud service.
- **Config Flow UI:** Fully integrated with the Home Assistant UI for seamless setup using your captured API token.

---

## Supported Devices

- **Gateways:** KK Wi-Fi Bridge (`SGAHA-SG3` / `G1`)
- **Locks:** Smart Door Lock (`VE019` / `SA501`)

---

## Installation

### Method 1: HACS (Recommended)

1. Ensure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance.
2. Open HACS and navigate to **Integrations**.
3. Click the three dots in the top-right corner and select **Custom repositories**.
4. Add your GitLab repository URL:
   - **Repository:** `https://gitlab.com/your-username/ha-kk-home` (or your GitHub URL if mirrored)
   - **Category:** `Integration`
5. Click **Add**.
6. Find the new **KK Home** integration in HACS, click **Download**, and restart Home Assistant.

### Method 2: Manual Installation

1. Download or clone this repository.
2. Copy the `custom_components/kkhome` directory into your Home Assistant `config/custom_components/` folder.
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, go to **Settings** > **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **KK Home**.
4. Paste your captured KK Home **JWT Token** when prompted and submit.

---

## Entity Mappings

| Platform | Entity Type | API Mapping | Description |
| :--- | :--- | :--- | :--- |
| **Lock** | `lock.*` | `subDevices[0].openStatus` | `1` = Locked, `2` = Unlocked |
| **Switch** | `switch.*_power` | `gwPowerStatus` | Controls gateway / outlet power state |
| **Sensor** | `sensor.*_battery` | `subDevices[0].power` | Reports lock battery percentage |

---

## Troubleshooting

- **Token Expiration:** KK Home JWT tokens have an expiration timestamp. If your devices stop updating and show authentication errors, you will need to re-capture a fresh token from your app traffic and re-configure the integration entry.
- **Debug Logging:** To enable verbose logging for troubleshooting network requests, add the following to your `configuration.yaml`:
  ```yaml
  logger:
    logs:
      custom_components.kkhome: debug
