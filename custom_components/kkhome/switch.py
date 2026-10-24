"""Support for KK Home gateway power switch (outlet/gateway status)."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up KK Home gateway switch from a config entry."""
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
        return f"{self.coordinator.data['gateways'].get(self.gw_id, {}).get('name')} Power"

    @property
    def is_on(self):
        """Return true if switch is on."""
        gw_data = self.coordinator.data["gateways"].get(self.gw_id, {})
        return gw_data.get("power_status") == 1

    async def async_turn_on(self, **kwargs):
        """Turn the gateway power on."""
        # Implement POST /v3/gateway/set-gateway-power with powerStatus: 1
        pass

    async def async_turn_off(self, **kwargs):
        """Turn the gateway power off."""
        # Implement POST /v3/gateway/set-gateway-power with powerStatus: 0
        pass
