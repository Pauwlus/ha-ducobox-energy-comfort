
import logging
from homeassistant.components.sensor import SensorEntity
from .const import (
    DOMAIN,
    NODE_TYPE_BOX,
    NODE_TYPE_UCHR,
    NODE_TYPE_UCRH,
    NODE_TYPE_UCCO2,
    NODE_TYPE_VLV,
)
from .helpers import build_base_unique, sanitize, infer_location

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []

    nodes = getattr(coordinator, 'nodes', []) or []
    for node in nodes:
        node_id = node.get('node')
        info = (coordinator.data or {}).get(node_id, {})
        devtype = str(info.get("devtype") or node.get("devtype") or "NODE").upper()
        # normalize alias
        if devtype == NODE_TYPE_UCRH:
            devtype = NODE_TYPE_UCHR
        subtype = info.get("subtype") or node.get("subtype")
        serial = info.get("serial") or node.get("serial")
        location = infer_location(info) if info else (node.get("location") or f"Node {node_id}")
        base_unique = build_base_unique(devtype, subtype, node_id, serial)

        if devtype == NODE_TYPE_BOX:
            for cat in ("EnergyInfo", "EnergyFan"):
                cat_dict = info.get(cat) or {}
                keys = list(cat_dict.keys()) if isinstance(cat_dict, dict) else []
                for k in keys:
                    name = f"{location} {k}"
                    entities.append(DucoBoxSensor(entry, coordinator, node_id, devtype, location, base_unique, k, name))
            for k in ("temp", "co2", "rh", "trgt", "actl", "snsr", "state", "mode"):
                name = f"{location} {k}"
                entities.append(DucoBoxSensor(entry, coordinator, node_id, devtype, location, base_unique, k, name))
        elif devtype in (NODE_TYPE_UCHR, NODE_TYPE_UCRH):
            for k in ("temp", "rh", "snsr", "state"):
                name = f"{location} {k}"
                entities.append(DucoBoxSensor(entry, coordinator, node_id, devtype, location, base_unique, k, name))
        elif devtype == NODE_TYPE_UCCO2:
            for k in ("temp", "co2", "snsr"):
                name = f"{location} {k}"
                entities.append(DucoBoxSensor(entry, coordinator, node_id, devtype, location, base_unique, k, name))
        elif devtype == NODE_TYPE_VLV:
            for k in ("trgt", "actl", "snsr"):
                name = f"{location} {k}"
                entities.append(DucoBoxSensor(entry, coordinator, node_id, devtype, location, base_unique, k, name))

    async_add_entities(entities, update_before_add=True)

class DucoBoxSensor(SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, entry, coordinator, node_id, devtype, location, base_unique, item, name):
        self._entry = entry; self._coordinator = coordinator
        self._node_id = node_id; self._devtype = devtype; self._location = location
        self._base_unique = base_unique; self._item = item
        self._attr_name = name
        self._attr_unique_id = f"{base_unique}_{sanitize(item)}"
        self._attr_suggested_object_id = sanitize(item)
        self._attr_device_info = {"identifiers": {(DOMAIN, f"device-{base_unique}")}, "manufacturer": "DUCO", "model": devtype, "name": self._device_name(devtype, location, node_id)}

    @property
    def native_unit_of_measurement(self):
        key = str(self._item).lower()
        if key in ("temp", "temperature"): return "°C"
        if key in ("rh", "humidity"): return "%"
        if key in ("co2",): return "ppm"
        return None

    @property
    def unique_id(self): return self._attr_unique_id

    @property
    def should_poll(self): return False

    async def async_added_to_hass(self):
        self.async_on_remove(self._coordinator.async_add_listener(self.async_write_ha_state))

    def _device_name(self, devtype, location, node_id):
        if devtype.upper() in ("UCHR", "UCCO2", "VLV"): return f"DucoBox node - {location}"
        if devtype.upper() == "BOX": return f"DucoBox - {node_id}"
        return f"DucoBox node - {location}"

    @property
    def name(self):
        return self._attr_name

    @property
    def native_value(self):
        info = self._coordinator.data.get(self._node_id, {})
        key = self._item
        if key in info:
            return self._convert(info.get(key))
        for cat in ("EnergyInfo", "EnergyFan"):
            cat_dict = info.get(cat)
            if isinstance(cat_dict, dict) and key in cat_dict:
                return self._convert(cat_dict[key])
        return None

    def _convert(self, v):
        try:
            if isinstance(v, str):
                if v.isdigit(): return int(v)
                return float(v)
            return v
        except Exception: return v
