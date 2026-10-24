"""Support for KK Home gateway power switches."""
import logging
import json
import aiohttp
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up KK Home switches from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for gw_id in coordinator.data.get("gateways", {}):
        entities.append(KKHomeGatewaySwitch(coordinator, gw_id))

    async_add_entities(entities)

class KKHomeGatewaySwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a KK Home Gateway Power Switch."""

    def __init__(self, coordinator, gw_id):
        """Initialize the switch."""
        super().__init__(coordinator)
        self.gw_id = gw_id

    @property
    def device_info(self):
        """Return device information."""
        gw_data = self.coordinator.data["gateways"].get(self.gw_id, {})
        return {
            "identifiers": {(DOMAIN, self.gw_id)},
            "name": gw_data.get("name", "KK Wi-Fi Bridge"),
            "manufacturer": "KK Home",
            "model": "SGAHA-SG3",
        }

    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self.gw_id}_power"

    @property
    def name(self):
        """Return the name of the switch."""
        gw_name = self.coordinator.data["gateways"].get(self.gw_id, {}).get("name", "KK Wi-Fi Bridge")
        return f"{gw_name} Power"

    @property
    def is_on(self):
        """Return true if switch is on."""
        gw_data = self.coordinator.data["gateways"].get(self.gw_id, {})
        return gw_data.get("power_status") == 1

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._set_power(1)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._set_power(0)

    async def _set_power(self, status: int):
        """Send power command to gateway."""
        headers = {
            "Host": "api.kksecurityhome.com",
            "k-tenant": "kawden",
            "k-version": "3.5.0",
            "token": self.coordinator.token,
            "User-Agent": "KKHome/3.5.0 (iPhone; iOS 27.0.1; Scale/3.00)",
            "phoneName": "iPhone19,3",
            "k-language": "en_US",
            "k-signv": "1.0.0",
            "Content-Type": "application/json",
        }
        url = "https://api.kksecurityhome.com/v3/gateway/set-gateway-power"
        payload = {"esn": self.gw_id, "powerStatus": status}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=payload, timeout=10) as response:
                    body_bytes = await response.read()
                    res = json.loads(body_bytes.decode("utf-8"))
                    
                    if response.status == 200 and res.get("code") == 200:
                        await self.coordinator.async_request_refresh()
                    else:
                        _LOGGER.error("Failed to change gateway power state, response: %s", res)
            except Exception as ex:
                _LOGGER.error("Failed to change gateway power state: %s", ex)
