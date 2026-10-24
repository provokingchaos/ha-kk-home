"""Support for KK Home sensors (Battery and Signal)."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up KK Home sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # Add lock battery sensors
    for lock_id in coordinator.data.get("locks", {}):
        entities.append(KKHomeBatterySensor(coordinator, lock_id))

    async_add_entities(entities)

class KKHomeBatterySensor(CoordinatorEntity, SensorEntity):
    """Representation of a KK Home Lock Battery Sensor."""

    def __init__(self, coordinator, lock_id):
        """Initialize the sensor."""
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
        }

    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self.lock_id}_battery"

    @property
    def name(self):
        """Return the name of the sensor."""
        lock_name = self.coordinator.data["locks"].get(self.lock_id, {}).get("name", "KK Lock")
        return f"{lock_name} Battery"

    @property
    def native_value(self):
        """Return the battery percentage."""
        lock_data = self.coordinator.data["locks"].get(self.lock_id, {})
        return lock_data.get("battery")

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return PERCENTAGE

    @property
    def device_class(self):
        """Return the sensor device class."""
        return SensorDeviceClass.BATTERY

    @property
    def state_class(self):
        """Return the state class."""
        return SensorStateClass.MEASUREMENT
