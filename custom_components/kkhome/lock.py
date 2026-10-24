"""Support for KK Home locks."""
from homeassistant.components.lock import LockEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up KK Home locks from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for lock_id in coordinator.data.get("locks", {}):
        entities.append(KKHomeLock(coordinator, lock_id))

    async_add_entities(entities)

class KKHomeLock(CoordinatorEntity, LockEntity):
    """Representation of a KK Home Lock."""

    def __init__(self, coordinator, lock_id):
        """Initialize the lock."""
        super().__init__(coordinator)
        self.lock_id = lock_id

    @property
    def device_info(self):
        """Return device information."""
        lock_data = self.coordinator.data["locks"].get(self.lock_id, {})
        return {
            "identifiers": {(DOMAIN, self.lock_id)},
            "name": lock_data.get("name", "KK Lock"),
            "manufacturer": "KK Home",
            "model": "VE019",
            "sw_version": lock_data.get("firmware"),
        }

    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self.lock_id}_lock"

    @property
    def name(self):
        """Return the name of the lock."""
        return self.coordinator.data["locks"].get(self.lock_id, {}).get("name")

    @property
    def is_locked(self):
        """Return true if lock is locked."""
        lock_data = self.coordinator.data["locks"].get(self.lock_id, {})
        # openStatus: 1 = Locked, 2 = Unlocked based on captures
        return lock_data.get("open_status") == 1

    async def async_lock(self, **kwargs):
        """Send lock command."""
        # Implement API call for locking here
        pass

    async def async_unlock(self, **kwargs):
        """Send unlock command."""
        # Implement API call for unlocking here
        pass
