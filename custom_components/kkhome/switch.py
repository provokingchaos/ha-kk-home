"""Support for KK Home gateway power switches."""

from __future__ import annotations

import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up KK Home switches from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        KKHomeGatewaySwitch(coordinator, gw_id)
        for gw_id in coordinator.data.get("gateways", {})
    ]
    async_add_entities(entities)


class KKHomeGatewaySwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a KK Home Gateway Power Switch."""

    def __init__(self, coordinator, gw_id: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.gw_id = gw_id

    @property
    def _gw_data(self) -> dict:
        return self.coordinator.data.get("gateways", {}).get(self.gw_id, {})

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.gw_id)},
            "name": self._gw_data.get("name", "KK Wi-Fi Bridge"),
            "manufacturer": "KK Home",
            "model": "SGAHA-SG3",
        }

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.gw_id}_power"

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        gw_name = self._gw_data.get("name", "KK Wi-Fi Bridge")
        return f"{gw_name} Power"

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._gw_data.get("power_status") == 1

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self.coordinator.api.async_set_gateway_power(self.gw_id, power_on=True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self.coordinator.api.async_set_gateway_power(self.gw_id, power_on=False)
        await self.coordinator.async_request_refresh()
