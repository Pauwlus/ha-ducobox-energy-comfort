
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN, NODE_TYPE_BOX, NODE_TYPE_UCHR, NODE_TYPE_UCCO2, NODE_TYPE_VLV, ATTRS_BOX_CATEGORIES, ATTRS_UCHR, ATTRS_UCCO2, ATTRS_VLV
from .helpers import build_base_unique, build_entity_id, sanitize, infer_location

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []
    # Ensure we have at least one refresh
    if not getattr(coordinator, 'data', None):
        try:
            await coordinator.async_refresh()
        except Exception:
            pass
    for node in getattr(coordinator, 'nodes', []) or []:
        node_id = node.get('node')
        info = (coordinator.data or {}).get(node_id, {})
        _LOGGER.debug('DucoBox: building entities for node %s devtype=%s', node_id, str(info.get('devtype', 'NODE')))
        devtype = str(info.get("devtype") or "NODE").upper()
        subtype = info.get("subtype")
        serial = info.get("serial")
        location = infer_location(info)
        base_unique = build_base_unique(devtype, subtype, node_id, serial)
        if devtype == NODE_TYPE_BOX:
            created = False
            for cat in ATTRS_BOX_CATEGORIES:
                cat_dict = info.get(cat) or info.get(cat.upper()) or {}
                if isinstance(cat_dict, dict) and cat_dict:
                    for k in cat_dict.keys():
                        name = f"{location} {k}"; ent_id = build_entity_id("sensor", base_unique, k)
                        entities.append(DucoBoxSensor(entry, coordinator, node_id, devtype, location, base_unique, k, name, ent_id))
                        created = True
            if not created:
                for k in list(info.keys()):
                    lk = str(k).lower()
                    if lk.startswith('energyinfo_') or lk.startswith('energyfan_'):
                        item = k.split('_', 1)[1] if '_' in k else k
                        name = f"{location} {item}"; ent_id = build_entity_id("sensor", base_unique, item)
                        entities.append(DucoBoxSensor(entry, coordinator, node_id, devtype, location, base_unique, item, name, ent_id))
        attrs_map = {NODE_TYPE_UCHR: ATTRS_UCHR, NODE_TYPE_UCCO2: ATTRS_UCCO2, NODE_TYPE_VLV: ATTRS_VLV}
        if devtype in attrs_map:
            for k in attrs_map[devtype]:
                name = f"{location} {k}"; ent_id = build_entity_id("sensor", base_unique, k)
                entities.append(DucoBoxSensor(entry, coordinator, node_id, devtype, location, base_unique, k, name, ent_id))
    ent_reg = er.async_get(hass)
    for ent in entities:
        ent_reg.async_get_or_create(domain="sensor", platform=DOMAIN, unique_id=ent.unique_id, config_entry_id=entry.entry_id, suggested_object_id=ent.entity_id.split(".")[1], entity_id=ent.entity_id)
    async_add_entities(entities)

class DucoBoxSensor(SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, entry, coordinator, node_id, devtype, location, base_unique, item, name, entity_id):
        self._entry = entry; self._coordinator = coordinator
        self._node_id = node_id; self._devtype = devtype; self._location = location
        self._base_unique = base_unique; self._item = item
        self._attr_name = name; self._forced_entity_id = entity_id
        self._attr_unique_id = f"{base_unique}_{sanitize(item)}"
        self._attr_device_info = {"identifiers": {(DOMAIN, f"device-{base_unique}")}, "manufacturer": "DUCO", "model": devtype, "name": self._device_name(devtype, location, node_id)}
    @property
    def entity_id(self): return self._forced_entity_id
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
    async def async_added_to_hass(self): self.async_on_remove(self._coordinator.async_add_listener(self.async_write_ha_state))
    def _device_name(self, devtype, location, node_id):
        if devtype.upper() in ("UCHR", "UCCO2", "VLV"): return f"DucoBox node - {location}"
        if devtype.upper() == "BOX": return f"DucoBox - {node_id}"
        return f"DucoBox node - {location}"
    @property
    def native_value(self):
        info = self._coordinator.data.get(self._node_id, {})
        key = self._item; val = info.get(key)
        if val is not None: return self._convert(val)
        for cat in ("energyinfo", "energyfan", "Energyinfo", "Energyfan"):
            cat_dict = info.get(cat)
            if isinstance(cat_dict, dict) and key in cat_dict: return self._convert(cat_dict[key])
        flat_key_prefixes = ['energyinfo_', 'energyfan_']
        for pref in flat_key_prefixes:
            if info.get(pref + key) is not None: return self._convert(info.get(pref + key))
        return None
    def _convert(self, v):
        try:
            if isinstance(v, str):
                if v.isdigit(): return int(v)
                return float(v)
            return v
        except Exception: return v
