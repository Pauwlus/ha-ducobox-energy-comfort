
from __future__ import annotations
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DUCO_OPERATION_MODES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = []
    for node in coordinator.nodes:
        devtype = node.get('devtype', 'unknown')
        subtype = int(node.get('subtype', 0))
        node_id = int(node.get('node', 0))
        serialnb = node.get('serialnb', 'n-a')
        location = node.get('location', f"Node {node_id}")
        unique_id = coordinator.api.build_entity_unique_id(coordinator.base_device_id or "ducobox-unknown", devtype, subtype, node_id, serialnb, "operation_mode")
        entities.append(DucoOperationModeSelect(coordinator, location, unique_id, node_id))

    async_add_entities(entities)

class DucoOperationModeSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, location: str, unique_id: str, node_id: int) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{location} Operation Mode"
        self._attr_unique_id = unique_id
        self._node_id = node_id
        self._attr_options = DUCO_OPERATION_MODES

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
    def current_option(self) -> str | None:
        for node in self.coordinator.nodes:
            if node.get('node') == self._node_id:
                return node.get('mode')
        return None

    async def async_select_option(self, option: str) -> None:
        if option not in DUCO_OPERATION_MODES:
            raise ValueError("Unsupported mode")
        ok = await self.coordinator.api.set_node_mode(self._node_id, option)
        if not ok:
            _LOGGER.warning("Failed to set mode for node %s", self._node_id)
        await self.coordinator.async_request_refresh()
