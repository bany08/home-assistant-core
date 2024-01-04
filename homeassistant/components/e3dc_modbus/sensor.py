"""Sensors."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, IDENTIFICATIONBLOCK_SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)

# async def async_setup_entry(
#    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
# ) -> None:
#    """Initialisieren."""
#    # hub_name = entry.data[CONF_NAME]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    hub_name = hass.data[DOMAIN][entry.entry_id]["hub"].name
    # _LOGGER.debug("Platformname: %s", hass.data[DOMAIN])
    # hub = hass.data[DOMAIN][hub_name]["hub"]
    hub = hass.data[DOMAIN][entry.entry_id]["hub"]  # Object of class E3DCModbusHub

    entities = []
    # sensor = E3DCSensor(hub_name, hub, "Hersteller", "manufacturer", "W", "mdi:factory")
    for sensor_info in IDENTIFICATIONBLOCK_SENSOR_TYPES.values():
        _LOGGER.debug("Sensorinfo: %s", sensor_info)
        sensor = E3DCSensor(
            hub_name,
            hub,
            sensor_info[0],
            sensor_info[1],
            sensor_info[2],
            sensor_info[3],
        )
        entities.append(sensor)

    async_add_entities(entities, update_before_add=True)


class E3DCSensor(SensorEntity):
    """Representation of an E3DC Modbus sensor.

    Sensor: [Name, Key, TranslationKey, Register, Datatype, Count, Unit, Icon]
    """

    _attr_has_entity_name = True

    # def __init__(self, platform_name, hub, device_info, name, key, unit, icon, register, datatype, count, Scaninterval):
    # def __init__(self, platform_name, hub, device_info, name, key, unit, icon, test=""):
    def __init__(self, platform_name, hub, name, key, unit, icon) -> None:
        """Initialize the sensor."""
        self._platform_name = platform_name
        self._hub = hub
        self._key = key
        self._name = name
        self._register = None
        self._datatype = None
        self._count = None
        self._scaninterval = 5  # Scaninterval
        self._unit_of_measurement = unit
        self._icon = icon
        self._state = None
        self._attr_name = key
        self._attr_unique_id = f"{DOMAIN}_{self._key}"
        self.translation_key = key
        # self._device_info = device_info
        # self._attr_state_class = STATE_CLASS_MEASUREMENT
        # if self._unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR:
        #    self._attr_state_class = STATE_CLASS_TOTAL_INCREASING
        #    self._attr_device_class = SensorDeviceClass.ENERGY
        #    if (
        #        STATE_CLASS_TOTAL_INCREASING == STATE_CLASS_MEASUREMENT
        #    ):  # compatibility to 2021.8
        #        self._attr_last_reset = dt_util.utc_from_timestamp(0)
        # if self._unit_of_measurement == UnitOfPower.WATT:
        #    self._attr_device_class = SensorDeviceClass.POWER

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self._hub.async_add_e3dc_sensor(self._modbus_data_updated)

    async def async_will_remove_from_hass(self) -> None:
        """Remove Sensors."""
        self._hub.async_remove_e3dc_sensor(self._modbus_data_updated)

    @callback
    def _modbus_data_updated(self):
        self._update_state()
        self.async_write_ha_state()
        # _LOGGER.debug("Entity %s updated", self.entity_id)

    @callback
    def _update_state(self):
        if self._key in self._hub.data:
            self._state = self._hub.data[self._key]

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        # Diese ID sollte einzigartig sein und bleibt unverändert.
        return f"{DOMAIN}_{self._key}"

    @property
    def name(self) -> str | None:
        """Return the name."""
        return f"{self._name}"

    # @property
    # def unit_of_measurement(self) -> str | None:
    #     """Return the unit of measurement."""
    #     return self._unit_of_measurement

    @property
    def icon(self) -> str | None:
        """Return the sensor icon."""
        return self._icon

    @property
    def register(self) -> int | None:
        """Return the sensor register."""
        return self._register

    @property
    def datatype(self) -> str | None:
        """Return the sensor datatype."""
        return self._datatype

    @property
    def count(self) -> int | None:
        """Return the sensor count."""
        return self._count

    @property
    def scaninterval(self) -> int | None:
        """Return the sensor count."""
        return self._scaninterval

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
        # if self._key in self._hub.data:
        # return self._hub.data[self._key]
        # else:
        # return None

    # @property
    # def extra_state_attributes(self) -> Optional[Mapping[str, Any]]:
    #    """Return extra state attributes based on the sensor key."""
    #    if self._key in ["status", "statusvendor"] and self.state in DEVICE_STATUSSES:
    #        return {ATTR_STATUS_DESCRIPTION: DEVICE_STATUSSES[self.state]}
    #    elif "battery1" in self._key and "battery1_attrs" in self._hub.data:
    #        return self._hub.data["battery1_attrs"]
    #    elif "battery2" in self._key and "battery2_attrs" in self._hub.data:
    #        return self._hub.data["battery2_attrs"]
    #    return None

    @property
    def should_poll(self) -> bool:
        """Data is delivered by the hub."""
        return False

    # async def async_update(self) -> None:
    #     """Aktualisiere den Zustand des Sensors."""
    #     # _LOGGER.debug("Key: %s", self._key)
    #     _LOGGER.debug("Hub.data: %s", self._hub.data)
    #     # Führe hier die Logik durch, um den Zustand des Sensors zu aktualisieren
    #     self._update_state()
    #     # self._state = self._hub.get_sensor_data()
    #     if self._key in self._hub.data:
    #         _LOGGER.debug("Value: %s", self._hub.data[self._key])
    #         self._state = self._hub.data[self._key]

    @property
    def device_info(self) -> DeviceInfo:
        """Return default device info."""
        return self._hub.device_info
