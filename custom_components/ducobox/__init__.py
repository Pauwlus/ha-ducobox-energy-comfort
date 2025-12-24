
from __future__ import annotations
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN, CONF_HOST, CONF_SCAN_INTERVAL
from .api import DucoBoxApi
from .coordinator import DucoCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "select"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = aiohttp_client.async_get_clientsession(hass)
    api = DucoBoxApi(entry.data[CONF_HOST], session)
    coordinator = DucoCoordinator(hass, entry, api, entry.data.get(CONF_SCAN_INTERVAL))
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
