
"""Sensor platform for DucoBox."""
from __future__ import annotations
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    NODE_TYPE_BOX,
    NODE_TYPE_UCHR,
    NODE_TYPE_UCCO2,
    NODE_TYPE_VLV,
    ATTRS_BOX_CATEGORIES,
    ATTRS_UCHR,
    ATTRS_UCCO2,
    ATTRS_VLV,
)
from .helpers import build_base_unique, build_entity_id, sanitize, infer_location


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities: List[Entity] = []

    for node_id, info in coordinator.data.items():
        devtype = str(info.get("devtype") or "NODE").upper()
        subtype = info.get("subtype")
        serial = info.get("serial")
        location = infer_location(info)
        base_unique = build_base_unique(devtype, subtype, node_id, serial)

        # BOX categories: create sensors for each key in the categories
        if devtype == NODE_TYPE_BOX:
            for cat in ATTRS_BOX_CATEGORIES:
                cat_dict = info.get(cat) or info.get(cat.upper()) or {}
                if isinstance(cat_dict, dict):
                    for k, v in cat_dict.items():
                        name = f"{location} {k}"
                        ent_id = build_entity_id("sensor", base_unique, k)
                        entities.append(DucoBoxSensor(entry, coordinator, node_id, devtype, location, base_unique, k, name, ent_id))
        # UCHR/UCCO2/VLV specific attributes
        attrs_map = {
            NODE_TYPE_UCHR: ATTRS_UCHR,
            NODE_TYPE_UCCO2: ATTRS_UCCO2,
            NODE_TYPE_VLV: ATTRS_VLV,
        }
        if devtype in attrs_map:
            for k in attrs_map[devtype]:
                name = f"{location} {k}"
                ent_id = build_entity_id("sensor", base_unique, k)
                entities.append(DucoBoxSensor(entry, coordinator, node_id, devtype, location, base_unique, k, name, ent_id))

    # Register entities and enforce entity_id in registry
    ent_reg = er.async_get(hass)
    for ent in entities:
        # Pre-register entity to enforce entity_id
        ent_reg.async_get_or_create(
            domain="sensor",
            platform=DOMAIN,
            unique_id=ent.unique_id,
            config_entry_id=entry.entry_id,
            suggested_object_id=ent.entity_id.split(".")[1],
            entity_id=ent.entity_id,
        )
    async_add_entities(entities)


class DucoBoxSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, entry, coordinator, node_id: int, devtype: str, location: str, base_unique: str, item: str, name: str, entity_id: str) -> None:
        self._entry = entry
        self._coordinator = coordinator
        self._node_id = node_id
        self._devtype = devtype
        self._location = location
        self._base_unique = base_unique
        self._item = item
        self._attr_name = name
        self._forced_entity_id = entity_id
        self._attr_unique_id = f"{base_unique}_{sanitize(item)}"
        # Link to device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"device-{devtype}-{node_id}")},
            "manufacturer": "DUCO",
            "model": devtype,
            "name": self._device_name(devtype, location, node_id),
        }

    @property
    def entity_id(self) -> str:
        return self._forced_entity_id

    @property
    def native_unit_of_measurement(self):
        key = self._item.lower()
        if key in ("temp", "temperature"):
            return "°C"
        if key in ("rh", "humidity"):
            return "%"
        if key in ("co2",):
            return "ppm"
        return None

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def should_poll(self) -> bool:
        return False

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self.async_write_ha_state))

    def _device_name(self, devtype: str, location: str, node_id: int) -> str:
        if devtype.upper() in ("UCHR", "UCCO2", "VLV"):
            return f"DucoBox node - {location}"
        if devtype.upper() == "BOX":
            return f"DucoBox - {node_id}"
        return f"DucoBox node - {location}"

    @property
    def native_value(self):
        # Read value from coordinator data
        info = self._coordinator.data.get(self._node_id, {})
        key = self._item
        # Direct key
        val = info.get(key)
        if val is not None:
            return self._convert(val)
        # Look into categories (for BOX)
        for cat in ("energyinfo", "energyfan", "Energyinfo", "Energyfan"):
            cat_dict = info.get(cat)
            if isinstance(cat_dict, dict):
                if key in cat_dict:
                    return self._convert(cat_dict[key])
        return None

    def _convert(self, v: Any) -> Any:
        # Convert strings to numbers where appropriate
        try:
            if isinstance(v, str):
                if v.isdigit():
                    return int(v)
                return float(v)
            return v
        except Exception:
            return v

