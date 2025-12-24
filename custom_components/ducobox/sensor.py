
from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_CREATE_NODE_CONTROLS

_LOGGER = logging.getLogger(__name__)

# Helpers

def slugify_location(loc: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (loc or "").lower())
    slug = slug.strip("_")
    return f"ducobox_{slug}" if slug else "ducobox_node"

# Node device types to include
ALLOWED_NODE_DEVTYPES = {"UCRH", "UCCO2", "VLV"}

# Box-level sensors from /boxinfoget
SENSOR_MAP = [
    ("EnergyInfo", "FilterRemainingTime", "time", "hours", "Filter Remaining Time", "filter_remaining_time"),
    ("EnergyFan", "SupplyFanSpeed", "speed", "rpm", "Supply Fan Speed", "supply_fan_speed"),
    ("EnergyFan", "ExhaustFanSpeed", "speed", "rpm", "Exhaust Fan Speed", "exhaust_fan_speed"),
    ("EnergyFan", "SupplyFanPressActual", None, "Pa", "Supply Fan Pressure (Actual)", "supply_fan_pressure_actual"),
    ("EnergyFan", "SupplyFanPressTarget", None, "Pa", "Supply Fan Pressure (Target)", "supply_fan_pressure_target"),
    ("EnergyFan", "ExhaustFanPressActual", None, "Pa", "Exhaust Fan Pressure (Actual)", "exhaust_fan_pressure_actual"),
    ("EnergyFan", "ExhaustFanPressTarget", None, "Pa", "Exhaust Fan Pressure (Target)", "exhaust_fan_pressure_target"),
    ("EnergyInfo", "TempODA", "temperature", "°C", "Outdoor Air Temperature", "temp_oda"),
    ("EnergyInfo", "TempSUP", "temperature", "°C", "Supply Air Temperature", "temp_sup"),
    ("EnergyInfo", "TempETA", "temperature", "°C", "Extract Air Temperature", "temp_eta"),
    ("EnergyInfo", "TempEHA", "temperature", "°C", "Exhaust Air Temperature", "temp_eha"),
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    base_device_id = coordinator.base_device_id or "ducobox-unknown"

    entities: list[SensorEntity] = []

    # Box-level
    for section, key, device_class, unit, nice_name, object_suffix in SENSOR_MAP:
        name = f"{entry.title} {nice_name}"
        unique_id = f"{base_device_id}-box-{key.lower()}"
        ent = DucoBoxSimpleSensor(coordinator, name, unique_id, section, key, unit, device_class)
        ent._attr_suggested_object_id = f"ducobox_{object_suffix}"
        ent._attr_has_entity_name = True
        entities.append(ent)

    # Option: create node sensors for UCRH/UCCO2/VLV
    if entry.options.get(CONF_CREATE_NODE_CONTROLS, False):
        for node in coordinator.nodes:
            devtype = (node.get("devtype") or "unknown").upper()
            if devtype not in ALLOWED_NODE_DEVTYPES:
                continue

            subtype = int(node.get("subtype", 0))
            node_id = int(node.get("node", 0))
            serialnb = node.get("serialnb", "n-a")
            location = node.get("location", f"Node {node_id}")
            loc_slug = slugify_location(location)

            # Common node metrics: mode/state/trgt/actl/snsr
            metrics = [
                ("mode", None, f"{location} Mode", f"{loc_slug}_mode"),
                ("state", None, f"{location} State", f"{loc_slug}_state"),
                ("trgt", "%", f"{location} Airflow Target (%)", f"{loc_slug}_airflow_target"),
                ("actl", "%", f"{location} Airflow Actual (%)", f"{loc_slug}_airflow_actual"),
                ("snsr", None, f"{location} Sensor", f"{loc_slug}_sensor"),
            ]
            for key, unit, friendly, obj_id in metrics:
                uid = coordinator.api.build_entity_unique_id(base_device_id, devtype, subtype, node_id, serialnb, key)
                ent = DucoNodeGenericSensor(coordinator, friendly, uid, node_id, key, unit)
                ent._attr_suggested_object_id = obj_id
                ent._attr_has_entity_name = True
                entities.append(ent)

            # Optional: expose humidity and CO2 if present
            if node.get("rh") is not None:
                uid = coordinator.api.build_entity_unique_id(base_device_id, devtype, subtype, node_id, serialnb, "humidity")
                ent = DucoNodeGenericSensor(coordinator, f"{location} Humidity", uid, node_id, "rh", "%")
                ent._attr_suggested_object_id = f"{loc_slug}_humidity"
                ent._attr_has_entity_name = True
                entities.append(ent)
            if node.get("co2") is not None:
                uid = coordinator.api.build_entity_unique_id(base_device_id, devtype, subtype, node_id, serialnb, "co2")
                ent = DucoNodeGenericSensor(coordinator, f"{location} CO2", uid, node_id, "co2", "ppm")
                ent._attr_suggested_object_id = f"{loc_slug}_co2"
                ent._attr_has_entity_name = True
                entities.append(ent)
    else:
        _LOGGER.info("DucoBox: Node entities disabled via options; only box sensors are active.")

    async_add_entities(entities)

class DucoBoxSimpleSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, name: str, unique_id: str, section: str, key: str, unit: str, device_class: str | None = None) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._section = section
        self._key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class if device_class in ("temperature", "humidity", "time", "speed") else None

    @property
    def device_info(self):
        base = self.coordinator.base_device_id or "ducobox-unknown"
        return {
            "identifiers": {(DOMAIN, base)},
            "manufacturer": "Duco",
            "model": "DucoBox",
            "name": self.coordinator.entry.title,
        }

    @property
    def native_value(self) -> Any:
        box = self.coordinator.data.get("box", {})
        section = box.get(self._section, {})
        val = section.get(self._key)
        if self._attr_device_class == "temperature" and isinstance(val, (int, float)):
            return round(val / 10.0, 1) if val and val > 100 else val
        return val

class DucoNodeGenericSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, name: str, unique_id: str, node_id: int, key: str, unit: str | None) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._node_id = node_id
        self._key = key
        self._attr_native_unit_of_measurement = unit
        # Map simple device classes for known keys
        if key in ("rh", "humidity"):
            self._attr_device_class = "humidity"
        elif key == "co2":
            self._attr_device_class = "carbon_dioxide"
        else:
            self._attr_device_class = None

    @property
    def device_info(self):
        base = self.coordinator.base_device_id or "ducobox-unknown"
        return {
            "identifiers": {(DOMAIN, base)},
            "manufacturer": "Duco",
            "model": "DucoBox",
            "name": self.coordinator.entry.title,
        }

    @property
    def native_value(self):
        for node in self.coordinator.nodes:
            if node.get("node") == self._node_id:
                return node.get(self._key)
        return None
