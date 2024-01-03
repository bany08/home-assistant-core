"""The E3DC Hauskraftwerk integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_MODBUS_ADDRESS,
    DEFAULT_MODBUS_ADDRESS,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .hub import E3DCModbusHub

# from .sensor import DemoSensor

# Logging
_LOGGER = logging.getLogger(__name__)


E3DC_MODBUS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.string,
        vol.Optional(
            CONF_MODBUS_ADDRESS, default=DEFAULT_MODBUS_ADDRESS
        ): cv.positive_int,
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): cv.positive_int,
    }
)


CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({cv.slug: E3DC_MODBUS_SCHEMA})}, extra=vol.ALLOW_EXTRA
)

# PLATFORMS = ["number", "select", "sensor"]
PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the E3DC modbus component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up E3DC Hauskraftwerk from a config entry."""
    # Stelle sicher, dass das DOMAIN Dictionary existiert
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]
    port = entry.data[CONF_PORT]
    modbus_address = entry.data.get(CONF_MODBUS_ADDRESS, 1)
    scan_interval = entry.data[CONF_SCAN_INTERVAL]
    # assert isinstance(entry.unique_id, str)
    # uid = entry.unique_id

    # _LOGGER.info("Setup Hauskraftwerk %s.%s", DOMAIN, name)
    # _LOGGER.info("Host: %s", host)
    # _LOGGER.info("Port: %s", port)
    # _LOGGER.info("UID: %s", uid)

    # TO_DO 1. Create API instance
    # TO_DO 2. Validate the API connection (and authentication)
    # TO_DO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    # """Register the hub."""

    hub = E3DCModbusHub(
        hass,
        name,
        host,
        port,
        modbus_address,
        scan_interval,
    )
    # hass.data[DOMAIN][name] = {"hub": hub}
    # Register the hub under the entry's entry_id
    hass.data[DOMAIN][entry.entry_id] = {"hub": hub}
    # _LOGGER.info("Domain Entry_ID: %s.%s", DOMAIN, entry.entry_id)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#    """Unload a config entry."""
#    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
#        hass.data[DOMAIN].pop(entry.entry_id)

#    return unload_ok


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
    else:
        _LOGGER.warning("Entry ID %s not found in hass.data[DOMAIN]", entry.entry_id)
    # Perform further cleanup steps here if necessary.
    return True
