
"""Setup for the DucoBox integration."""
from __future__ import annotations
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, area_registry as ar

from .const import DOMAIN, PLATFORMS, CONF_HOST, CONF_FRIENDLY_NAME, CONF_SCAN_INTERVAL, OPTION_AREAS
from .api import DucoClient
from .coordinator import DucoCoordinator
from .helpers import build_base_unique


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL) or 30
    client = DucoClient(hass, host)
    coordinator = DucoCoordinator(hass, client, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    # Create devices in registry and assign areas per options
    device_reg = dr.async_get(hass)
    area_reg = ar.async_get(hass)
    area_map: dict[str, str] = entry.options.get(OPTION_AREAS, {}) if entry.options else {}

    for node in coordinator.nodes:
        node_id = node["node"]
        devtype = node.get("devtype") or "NODE"
        location = node.get("location") or f"Node {node_id}"
        info = coordinator.data.get(node_id, {})
        base_unique = build_base_unique(str(info.get('devtype') or devtype), info.get('subtype'), node_id, info.get('serial'))
        # Device name rules
        if devtype.upper() in ("UCHR", "UCCO2", "VLV"):
            device_name = f"DucoBox node - {location}"
        elif devtype.upper() == "BOX":
            device_name = f"DucoBox - {node_id}"
        else:
            device_name = f"DucoBox node - {location}"
        identifiers = {(DOMAIN, f"device-{base_unique}")}
        device = device_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers=identifiers,
            name=device_name,
            manufacturer="DUCO",
            model=devtype,
        )
        # Assign area if provided in options
        area_id = area_map.get(f"{devtype}-{node_id}")
        if area_id and area_reg.async_get_area(area_id):
            device_reg.async_update_device(device.id, area_id=area_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded

