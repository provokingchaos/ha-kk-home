"""Support for KK Home locks."""
import logging
import aiohttp
from homeassistant.components.lock import LockEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

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
        url = "https://api.kksecurityhome.com/v3/gateway/set-lock-close"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json={}, timeout=10) as response:
                    if response.status == 200:
                        await self.coordinator.async_request_refresh()
                    else:
                        _LOGGER.error("Failed to lock device, status: %s", response.status)
            except Exception as ex:
                _LOGGER.error("Failed to lock device: %s", ex)

    async def async_unlock(self, **kwargs):
        """Send unlock command."""
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
        url = "https://api.kksecurityhome.com/v3/gateway/set-lock-open"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json={}, timeout=10) as response:
                    if response.status == 200:
                        await self.coordinator.async_request_refresh()
                    else:
                        _LOGGER.error("Failed to unlock device, status: %s", response.status)
            except Exception as ex:
                _LOGGER.error("Failed to unlock device: %s", ex)
