from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform

from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up DucoBox integration."""

    # Load sensors
    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )

    # Register native service
    async def handle_set_mode(call):
        mode = call.data.get("mode")
        zone = call.data.get("zone")

        base = "http://ducobox.localdomain/nodesetoperstate?"

        node_map = {
            "main": 1,
            "zone1": 67,
            "zone2": 68
        }

        url = f"{base}node={node_map[zone]}&value={mode.upper()}"

        import requests
        requests.get(url)

    hass.services.async_register(
        DOMAIN,
        "set_mode",
        handle_set_mode
    )

    return True
