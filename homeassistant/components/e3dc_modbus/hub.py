"""Modbushub for E3DC integration."""

from __future__ import annotations

from datetime import timedelta
import logging
import threading
from typing import Any, Optional

from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN

# Logging
_LOGGER = logging.getLogger(__name__)


class E3DCModbusHub:
    """Thread safe wrapper class for pymodbus."""

    _sensors: list[Any] = []
    data: dict[str, Any] = {}
    # Modbus register offset
    _modbus_register_offset: int = 0

    def __init__(
        self,
        hass: HomeAssistant,
        name,
        host,
        port,
        modbus_address,
        scan_interval,
    ) -> None:
        """Initialize the Modbus hub."""

        self._hass = hass
        self._client = ModbusTcpClient(
            host=host, port=port, timeout=max(3, (scan_interval - 1))
        )
        self._lock = threading.Lock()
        self._name = name
        self._address = modbus_address
        self._scan_interval = timedelta(seconds=scan_interval)
        # self.max_export_control_site_limit = max_export_control_site_limit
        self._unsub_interval_method = None
        self._sensors = []
        self.data = {}

        self._manufacturer = "HagerEnergy GmbH"
        self._model = "S10 E AIO Pro 912"
        self._sw_version = "0.1.0"

        # self._sensors.append()

    @callback
    def async_add_e3dc_sensor(self, update_callback):
        """Listen for data updates."""
        # This is the first sensor, set up interval.
        if not self._sensors:
            self.connect()
            self._unsub_interval_method = async_track_time_interval(
                self._hass, self.async_refresh_modbus_data, self._scan_interval
            )

        self._sensors.append(update_callback)

    @callback
    def async_remove_e3dc_sensor(self, update_callback):
        """Remove data update."""
        if update_callback in self._sensors:
            self._sensors.remove(update_callback)
            _LOGGER.debug(
                "Callback %s was removed from hub %s", update_callback, self._name
            )
        else:  # This should not happen.
            _LOGGER.warning(
                "Callback %s was not registered for removal on hub %s",
                update_callback,
                self._name,
            )

        if not self._sensors:
            # Stop the interval timer upon removal of last sensor.
            self._unsub_interval_method()
            self._unsub_interval_method = None
            self.close()

    async def async_refresh_modbus_data(self, _now: Optional[int] = None) -> None:
        """Time to update Modbus Data."""
        if not self._sensors:
            return

        try:
            update_result = self.read_modbus_data()

        except ErrrorReadingModbusData:
            _LOGGER.exception("Error reading modbus data")
            update_result = False

        if update_result:
            for update_callback in self._sensors:
                update_callback()
            # for sensor in self._sensors:
            # _LOGGER.debug("Sensor: %s", sensor)
            # sensor.async_update()

    @property
    def name(self):
        """Return the name of this hub."""
        return self._name

    def close(self):
        """Disconnect client."""
        with self._lock:
            self._client.close()

    def connect(self):
        """Connect client."""
        result = False
        with self._lock:
            result = self._client.connect()

        if result:
            _LOGGER.info(
                "Successfully connected to %s:%s",
                self._client.comm_params.host,
                self._client.comm_params.port,
            )
        else:
            # Raise exception if not able to connect to E3DC Modbus
            _LOGGER.warning(
                "Not able to connect to %s:%s",
                self._client.comm_params.host,
                self._client.comm_params.port,
            )
            raise ConnectionError("Failed to connect to E3DC Modbus")
        return result

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device."""
        # _LOGGER.debug("Geräte UID: %s %s", DOMAIN, self.unique_id)
        # _LOGGER.debug("Data: %s", self.data.get("manufacturer"))
        return {
            "identifiers": {(DOMAIN, self._name)},
            "manufacturer": self._manufacturer,
            "model": self.data.get("model"),
            "name": self._name,
            "sw_version": self.data.get("firmware"),
            "configuration_url": "https://s10.e3dc.com/",
        }

    # from homeassistant.helpers import device_registry as dr
    #        manufacturer="E3/DC",
    #        model=self.e3dc.model,
    #        name=self.e3dc.model,
    #        connections={(dr.CONNECTION_NETWORK_MAC, self.e3dc.macAddress)},
    #        identifiers={(DOMAIN, self.uid)},
    #        sw_version=self._sw_version,
    #        configuration_url="https://s10.e3dc.com/",

    # def read_register(self, register):
    #     """Read a register from the E3DC Modbus."""
    #     with self._lock:
    #         result = self._client.read_holding_registers(register, 1)
    #     return result

    def read_holding_registers(self, unit, address, count):
        """Read holding registers."""
        with self._lock:
            return self._client.read_holding_registers(
                address=address, count=count, slave=unit
            )

    def write_registers(self, unit, address, payload):
        """Write registers."""
        with self._lock:
            return self._client.write_registers(
                address=address, values=payload, slave=unit
            )

    def read_modbus_data(self):
        """Read the modbus data from various sources."""
        return (
            self.read_modbus_data_identificationblock()
            # and self.read_modbus_data_inverter()
            # and self.read_modbus_data_currentdc()
            # and self.read_modbus_data_new()
            #        and self.read_modbus_power_limit()
            #        and self.read_modbus_data_meter1()
            #        and self.read_modbus_data_meter2()
            #        and self.read_modbus_data_meter3()
            #        and self.read_modbus_data_storage()
            #        and self.read_modbus_data_battery1()
            #        and self.read_modbus_data_battery2()
        )

    def read_modbus_data_identificationblock(self):
        """Read the identification block from the E3DC Modbus."""
        # response = self.read_holding_registers(
        #     unit=self._address, address=40001, count=1
        # )
        # _LOGGER.debug(
        #     "ModbusResponse: %s",
        #     BinaryPayloadDecoder.fromRegisters(response.registers, byteorder=">"),
        # )

        def decode_string(decoder):
            s = decoder.decode_string(32)  # get 32 char string
            s = s.partition(b"\0")[0]  # omit NULL terminators
            s = s.decode("utf-8")  # decode UTF-8
            return str(s)

        modbusfirmware_data = self.read_holding_registers(
            unit=self._address, address=40001, count=1
        )

        if modbusfirmware_data.isError():
            return False

        decoder = BinaryPayloadDecoder.fromRegisters(
            modbusfirmware_data.registers, byteorder=">"
        )
        self.data["modbusfirmware"] = decoder.decode_16bit_uint()
        # _LOGGER.debug("Modbus Firmware: %s", self.data["modbusfirmware"])

        registercount_data = self.read_holding_registers(
            unit=self._address, address=40002, count=1
        )
        if registercount_data.isError():
            return False

        decoder = BinaryPayloadDecoder.fromRegisters(
            registercount_data.registers, byteorder=">"
        )
        self.data["registercount"] = decoder.decode_16bit_uint()

        manufacturer_data = self.read_holding_registers(
            unit=self._address, address=40003, count=16
        )
        if manufacturer_data.isError():
            return False

        decoder = BinaryPayloadDecoder.fromRegisters(
            manufacturer_data.registers, byteorder=">"
        )
        self.data["manufacturer"] = decode_string(decoder)

        model_data = self.read_holding_registers(
            unit=self._address, address=40019, count=16
        )
        if model_data.isError():
            return False

        decoder = BinaryPayloadDecoder.fromRegisters(
            model_data.registers, byteorder=">"
        )
        self.data["model"] = decode_string(decoder)

        serialnumber_data = self.read_holding_registers(
            unit=self._address, address=40035, count=16
        )
        if serialnumber_data.isError():
            return False

        decoder = BinaryPayloadDecoder.fromRegisters(
            serialnumber_data.registers, byteorder=">"
        )
        self.data["serialnumber"] = decode_string(decoder)

        firmware_data = self.read_holding_registers(
            unit=self._address, address=40051, count=16
        )
        if firmware_data.isError():
            return False

        decoder = BinaryPayloadDecoder.fromRegisters(
            firmware_data.registers, byteorder=">"
        )
        self.data["firmware"] = decode_string(decoder)
        _LOGGER.debug("Data: %s", self.data)

        return True


class ErrrorReadingModbusData(HomeAssistantError):
    """Error reading Modbus data."""
