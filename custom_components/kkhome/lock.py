"""Support for KK Home locks."""

from __future__ import annotations

import logging
from homeassistant.components.lock import LockEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up KK Home locks from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        KKHomeLock(coordinator, lock_id)
        for lock_id in coordinator.data.get("locks", {})
    ]
    async_add_entities(entities)


class KKHomeLock(CoordinatorEntity, LockEntity):
    """Representation of a KK Home Lock."""

    def __init__(self, coordinator, lock_id: str) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        self.lock_id = lock_id

    @property
    def _lock_data(self) -> dict:
        return self.coordinator.data.get("locks", {}).get(self.lock_id, {})

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.lock_id)},
            "name": self._lock_data.get("name", "KK Lock"),
            "manufacturer": "KK Home",
            "model": "VE019",
            "sw_version": self._lock_data.get("firmware"),
        }

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self.lock_id}_lock"

    @property
    def name(self) -> str:
        """Return the name of the lock."""
        return self._lock_data.get("name", "KK Lock")

    @property
    def is_locked(self) -> bool | None:
        """Return true if lock is locked."""
        status = self._lock_data.get("open_status")
        if status is None:
            return None
        # openStatus: 1 = Locked, 2 (or 0) = Unlocked
        return int(status) == 1

    async def async_lock(self, **kwargs) -> None:
        """Send lock command and immediately request a state refresh."""
        await self.coordinator.api.async_set_lock(self._lock_data, lock=True)
        # Force an immediate poll to update UI state without waiting 30 seconds
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs) -> None:
        """Send unlock command and immediately request a state refresh."""
        await self.coordinator.api.async_set_lock(self._lock_data, lock=False)
        # Force an immediate poll to update UI state without waiting 30 seconds
        await self.coordinator.async_request_refresh()
