
from __future__ import annotations
import logging
from datetime import timedelta
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry

from .const import DEFAULT_SCAN_INTERVAL
from .api import DucoBoxApi

_LOGGER = logging.getLogger(__name__)

class DucoCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: DucoBoxApi, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="ducobox",
            update_interval=timedelta(seconds=scan_interval or DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry
        self.api = api
        self.nodes: List[Dict[str, Any]] = []
        self.base_device_id: str | None = None

    async def _async_setup(self) -> None:
        box = await self.api.get_box_info()
        self.base_device_id = DucoBoxApi.build_base_device_id(box)
        nodes = await self.api.discover_nodes_from_index()
        self.nodes = nodes or await self.api.discover_nodes(max_nodes=64)
        _LOGGER.info("Discovered %s nodes", len(self.nodes))

    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            box = await self.api.get_box_info()
            fresh: List[Dict[str, Any]] = []
            for info in self.nodes:
                nid = info.get('node')
                cur = await self.api.get_node_info(nid)
                if cur:
                    fresh.append(cur)
            self.nodes = fresh or self.nodes
            return {"box": box, "nodes": self.nodes}
        except Exception as err:
            raise UpdateFailed(f"Update failed: {err}")
