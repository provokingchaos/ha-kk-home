"""Data update coordinator for KK Home."""
import logging
import json
from datetime import timedelta
import aiohttp

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
API_ENDPOINT = "https://api.kksecurityhome.com/v3/user/device/list"

class KKHomeDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for KK Home devices."""

    def __init__(self, hass, token: str):
        """Initialize coordinator."""
        self.token = token
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        """Fetch data from KK Home API."""
        headers = {
            "Host": "api.kksecurityhome.com",
            "k-tenant": "kawden",
            "k-version": "3.5.0",
            "token": self.token,
            "User-Agent": "KKHome/3.5.0 (iPhone; iOS 27.0.1; Scale/3.00)",
            "phoneName": "iPhone19,3",
            "k-language": "en_US",
            "k-signv": "1.0.0",
            "Content-Length": "0",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(API_ENDPOINT, headers=headers, timeout=10) as response:
                    if response.status == 401:
                        raise ConfigEntryAuthFailed("Authentication token expired or invalid.")
                    
                    if response.status != 200:
                        raise UpdateFailed(f"Error communicating with API: Status {response.status}")
                    
                    # Read raw bytes to bypass aiohttp strict content-type JSON checking
                    body_bytes = await response.read()
                    response_text = body_bytes.decode("utf-8")
                    
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError as jde:
                        raise UpdateFailed(f"Failed to parse API response as JSON: {jde}")
                    
                    if data.get("code") != 200:
                        raise UpdateFailed(f"API returned error: {data.get('msg')}")
                    
                    return self._parse_devices(data.get("data", []))

            except aiohttp.ClientError as error:
                raise UpdateFailed(f"Error fetching data: {error}")

    def _parse_devices(self, raw_devices: list) -> dict:
        """Parse raw device list into structured dictionary."""
        parsed_data = {
            "gateways": {},
            "locks": {}
        }

        for device in raw_devices:
            esn = device.get("wifiSN") or device.get("esn")
            if device.get("deviceType") == "GATEWAY":
                parsed_data["gateways"][esn] = {
                    "id": esn,
                    "name": device.get("lockNickname", "KK Wi-Fi Bridge"),
                    "power_status": device.get("gwPowerStatus"),
                    "led_status": device.get("gwLedStatus"),
                    "power": device.get("power"),
                    "ip": device.get("ip"),
                    "wifi_signal": device.get("wifiSignal"),
                    "online": device.get("online") == "1",
                }

                for sub in device.get("subDevices", []):
                    sub_esn = sub.get("wifiSN") or sub.get("mac")
                    parsed_data["locks"][sub_esn] = {
                        "id": sub_esn,
                        "master_sn": esn,
                        "name": sub.get("lockNickname", "KK Lock"),
                        "open_status": sub.get("openStatus"),
                        "battery": sub.get("power"),
                        "firmware": sub.get("lockFirmwareVersion"),
                        "online": sub.get("online") == "1",
                        "rssi": sub.get("rssi"),
                    }

        return parsed_data
