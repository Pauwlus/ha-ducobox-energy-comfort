
from __future__ import annotations
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_MAP = [
    ("EnergyInfo", "FilterRemainingTime", "time", "hours"),
    ("EnergyFan", "SupplyFanSpeed", "speed", "rpm"),
    ("EnergyFan", "ExhaustFanSpeed", "speed", "rpm"),
    ("EnergyFan", "SupplyFanPressActual", None, "Pa"),
    ("EnergyFan", "SupplyFanPressTarget", None, "Pa"),
    ("EnergyFan", "ExhaustFanPressActual", None, "Pa"),
    ("EnergyFan", "ExhaustFanPressTarget", None, "Pa"),
    ("EnergyInfo", "TempODA", "temperature", "°C"),
    ("EnergyInfo", "TempSUP", "temperature", "°C"),
    ("EnergyInfo", "TempETA", "temperature", "°C"),
    ("EnergyInfo", "TempEHA", "temperature", "°C"),
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    base_device_id = coordinator.base_device_id or "ducobox-unknown"

    entities = []
    for section, key, device_class, unit in SENSOR_MAP:
        name = f"{entry.title} {key}"
        unique_id = f"{base_device_id}-box-{key.lower()}"
        entities.append(DucoBoxSimpleSensor(coordinator, name, unique_id, section, key, unit, device_class))

    # Per-node sensors: actl/trgt plus humidity & CO2 if available
    for node in coordinator.nodes:
        devtype = node.get('devtype', 'unknown')
        subtype = int(node.get('subtype', 0))
        node_id = int(node.get('node', 0))
        serialnb = node.get('serialnb', 'n-a')
        location = node.get('location', f"Node {node_id}")
        for metric_key, unit in (("actl", "%"), ("trgt", "%")):
            name = f"{location} {metric_key.upper()}"
            unique_id = coordinator.api.build_entity_unique_id(base_device_id, devtype, subtype, node_id, serialnb, metric_key)
            entities.append(DucoNodeValueSensor(coordinator, name, unique_id, node_id, metric_key, unit))
        humidity_val = node.get('rh')
        co2_val = node.get('co2')
        if humidity_val is not None:
            uid = coordinator.api.build_entity_unique_id(base_device_id, devtype, subtype, node_id, serialnb, "humidity")
            entities.append(DucoNodeEnvSensor(coordinator, f"{location} Humidity", uid, node_id, "humidity", "%"))
        if co2_val is not None:
            uid = coordinator.api.build_entity_unique_id(base_device_id, devtype, subtype, node_id, serialnb, "co2")
            entities.append(DucoNodeEnvSensor(coordinator, f"{location} CO2", uid, node_id, "co2", "ppm"))

    async_add_entities(entities)

class DucoBoxSimpleSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, name: str, unique_id: str, section: str, key: str, unit: str, device_class: str | None = None) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._section = section
        self._key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class if device_class in ("temperature", "humidity") else None

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

class DucoNodeValueSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, name: str, unique_id: str, node_id: int, key: str, unit: str) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._node_id = node_id
        self._key = key
        self._attr_native_unit_of_measurement = unit

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
            if node.get('node') == self._node_id:
                return node.get(self._key)
        return None

class DucoNodeEnvSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, name: str, unique_id: str, node_id: int, kind: str, unit: str) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._node_id = node_id
        self._kind = kind
        self._attr_native_unit_of_measurement = unit
        if kind == "humidity":
            self._attr_device_class = "humidity"
        elif kind == "co2":
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
            if node.get('node') == self._node_id:
                if self._kind == 'humidity':
                    return node.get('rh')
                if self._kind == 'co2':
                    return node.get('co2')
        return None
