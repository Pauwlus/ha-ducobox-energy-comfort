
"""Data update coordinator for DucoBox."""
from __future__ import annotations
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DucoClient


class DucoCoordinator(DataUpdateCoordinator[Dict[int, Dict[str, Any]]]):
    def __init__(self, hass: HomeAssistant, client: DucoClient, scan_interval: int) -> None:
        from datetime import timedelta
        super().__init__(
            hass,
            logger=__import__('logging').getLogger(__name__),
            name="DucoBox Coordinator",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._client = client
        self.nodes: List[Dict[str, Any]] = []

    async def async_config_entry_first_refresh(self) -> None:
        # Discover nodes first
        self.nodes = await self._client.discover_nodes()
        await super().async_config_entry_first_refresh()

    async def _async_update_data(self) -> Dict[int, Dict[str, Any]]:
        data: Dict[int, Dict[str, Any]] = {}
        try:
            # Refresh per-node info
            for n in self.nodes:
                node_id = n["node"]
                info = await self._client.fetch_node_info(node_id)
                # Annotate with devtype/location if missing
                info.setdefault("node", node_id)
                info.setdefault("devtype", n.get("devtype"))
                info.setdefault("subtype", n.get("subtype"))
                info.setdefault("serial", info.get("serial") or n.get("serial"))
                info.setdefault("location", info.get("location") or n.get("location"))
                data[node_id] = info
            return data
        except Exception as err:
            raise UpdateFailed(str(err))

