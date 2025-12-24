
from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers for clean entity_ids and names
# ---------------------------------------------------------------------------

def slugify_location(loc: str) -> str:
    """Create a deterministic slug from the Duco location string."""
    slug = re.sub(r"[^a-z0-9]+", "_", (loc or "").lower())
    slug = slug.strip("_")
    # Prefix to keep sensors grouped by integration in entity_id
    return f"ducobox_{slug}" if slug else "ducobox_node"

# Only expose per-node sensors for these device types
ALLOWED_NODE_DEVTYPES = {"VLV"}  # Add types here if needed

# ---------------------------------------------------------------------------
# Box-level sensor mapping (from /boxinfoget)
# Each tuple: (section, key, device_class, unit, friendly_name, suggested_object_id_suffix)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    base_device_id = coordinator.base_device_id or "ducobox-unknown"

    entities: list[SensorEntity] = []

    # ---- Box-level sensors (from /boxinfoget) ----
    for section, key, device_class, unit, nice_name, object_suffix in SENSOR_MAP:
        name = f"{entry.title} {nice_name}"
        unique_id = f"{base_device_id}-box-{key.lower()}"
        ent = DucoBoxSimpleSensor(
            coordinator=coordinator,
            name=name,
            unique_id=unique_id,
            section=section,
            key=key,
            unit=unit,
            device_class=device_class,
        )
        ent._attr_suggested_object_id = f"ducobox_{object_suffix}"
        ent._attr_has_entity_name = True
        entities.append(ent)

    # ---- Per-node sensors (Airflow actual/target + RH/CO2) ----
    for node in coordinator.nodes:
        devtype = (node.get("devtype") or "unknown").upper()
        if devtype not in ALLOWED_NODE_DEVTYPES:
            continue

        subtype = int(node.get("subtype", 0))
        node_id = int(node.get("node", 0))
        serialnb = node.get("serialnb", "n-a")
        location = node.get("location", f"Node {node_id}")
        loc_slug = slugify_location(location)

        # Airflow Actual (%)
        metric_key = "actl"
        uid = coordinator.api.build_entity_unique_id(
            base_device_id, devtype, subtype, node_id, serialnb, metric_key
        )
        ent = DucoNodeValueSensor(
            coordinator=coordinator,
            name=f"{location} Airflow Actual (%)",
            unique_id=uid,
            node_id=node_id,
            key=metric_key,
            unit="%",
        )
        ent._attr_suggested_object_id = f"{loc_slug}_airflow_actual"
        ent._attr_has_entity_name = True
        entities.append(ent)

        # Airflow Target (%)
        metric_key = "trgt"
        uid = coordinator.api.build_entity_unique_id(
            base_device_id, devtype, subtype, node_id, serialnb, metric_key
        )
        ent = DucoNodeValueSensor(
            coordinator=coordinator,
            name=f"{location} Airflow Target (%)",
            unique_id=uid,
            node_id=node_id,
            key=metric_key,
            unit="%",
        )
        ent._attr_suggested_object_id = f"{loc_slug}_airflow_target"
        ent._attr_has_entity_name = True
        entities.append(ent)

        # Humidity (rh)
        if node.get("rh") is not None:
            uid = coordinator.api.build_entity_unique_id(
                base_device_id, devtype, subtype, node_id, serialnb, "humidity"
            )
            ent = DucoNodeEnvSensor(
                coordinator=coordinator,
                name=f"{location} Humidity",
                unique_id=uid,
                node_id=node_id,
                kind="humidity",
                unit="%",
            )
            ent._attr_suggested_object_id = f"{loc_slug}_humidity"
            ent._attr_has_entity_name = True
            entities.append(ent)

        # CO2 (co2)
        if node.get("co2") is not None:
            uid = coordinator.api.build_entity_unique_id(
                base_device_id, devtype, subtype, node_id, serialnb, "co2"
            )
            ent = DucoNodeEnvSensor(
                coordinator=coordinator,
                name=f"{location} CO2",
                unique_id=uid,
                node_id=node_id,
                kind="co2",
                unit="ppm",
            )
            ent._attr_suggested_object_id = f"{loc_slug}_co2"
            ent._attr_has_entity_name = True
            entities.append(ent)

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

class DucoBoxSimpleSensor(CoordinatorEntity, SensorEntity):
    """Box-level sensors from /boxinfoget."""

    def __init__(
        self,
        coordinator,
        name: str,
        unique_id: str,
        section: str,
        key: str,
        unit: str,
        device_class: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._section = section
        self._key = key
        self._attr_native_unit_of_measurement = unit
        # Keep strings for wide HA compatibility
        self._attr_device_class = device_class if device_class in ("temperature", "humidity", "time", "speed") else None
        # optional: self._attr_state_class = "measurement"

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
        # Some firmwares report temperatures in tenths of °C
        if self._attr_device_class == "temperature" and isinstance(val, (int, float)):
            return round(val / 10.0, 1) if val and val > 100 else val
        return val


class DucoNodeValueSensor(CoordinatorEntity, SensorEntity):
    """Per-node airflow sensors (Actual/Target)."""

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
            if node.get("node") == self._node_id:
                return node.get(self._key)
        return None


class DucoNodeEnvSensor(CoordinatorEntity, SensorEntity):
    """Per-node environment sensors (Humidity rh / CO2 co2)."""

    def __init__(self, coordinator, name: str, unique_id: str, node_id: int, kind: str, unit: str) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._node_id = node_id
        self._kind = kind  # "humidity" or "co2"
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
            if node.get("node") == self._node_id:
                if self._kind == "humidity":
                    return node.get("rh")
                if self._kind == "co2":
                    return node.get("co2")
        return None
