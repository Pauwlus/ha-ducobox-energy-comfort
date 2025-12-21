
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service import verify_domain_control

from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DucoBox from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["host"] = entry.data.get("host")
    hass.data[DOMAIN]["verify_ssl"] = entry.data.get("verify_ssl", False)

    # Forward setup naar platform(s) — *awaisen* tijdens setup (juist).
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Async, niet-blokkerende service
    async def handle_set_mode(call):
        await verify_domain_control(hass, DOMAIN, call)
        mode = str(call.data.get("mode", "")).upper()
        zone = str(call.data.get("zone", "main"))
        node_map = {"main": 1, "zone1": 67, "zone2": 68}

        host = hass.data[DOMAIN].get("host")
        verify_ssl = hass.data[DOMAIN].get("verify_ssl", False)
        node = node_map.get(zone)
        if not host or node is None or not mode:
            return

        url = f"http://{host}/nodesetoperstate?node={node}&value={mode}"
        session = async_get_clientsession(hass)
        try:
            resp = await session.get(url, ssl=verify_ssl or None)
            if resp.status >= 400:
                return
        except Exception:
            return

    hass.services.async_register(DOMAIN, "set_mode", handle_set_mode)
    return True
