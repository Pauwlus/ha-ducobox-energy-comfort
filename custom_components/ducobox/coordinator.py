
from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry

from .const import DEFAULT_SCAN_INTERVAL, NODES_FILENAME
from .api import DucoBoxApi

_LOGGER = logging.getLogger(__name__)

@dataclass
class PredefinedNode:
    node: int
    devtype: str = "unknown"
    subtype: int = 0
    location: str = ""
    serialnb: str = "n-a"

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
        self.predefined_nodes: List[PredefinedNode] = []
        self.base_device_id: str | None = None

    def _load_nodes_config(self) -> List[PredefinedNode]:
        """Load node definitions from /config/ducobox/nodes.json or fallback to package nodes.json."""
        paths: List[Path] = []
        try:
            # Preferred: /config/ducobox/nodes.json
            cfg_path = Path(self.hass.config.path("ducobox")) / NODES_FILENAME
            paths.append(cfg_path)
        except Exception:
            pass
        # Fallback: custom_components/ducobox/nodes.json (next to this file)
        try:
            pkg_path = Path(__file__).parent / NODES_FILENAME
            paths.append(pkg_path)
        except Exception:
            pass

        for p in paths:
            try:
                if p.exists():
                    with p.open("r", encoding="utf-8") as fh:
                        data = json.load(fh)
                        nodes: List[PredefinedNode] = []
                        for n in data or []:
                            nodes.append(
                                PredefinedNode(
                                    node=int(n.get("node")),
                                    devtype=str(n.get("devtype", "unknown")),
                                    subtype=int(n.get("subtype", 0)),
                                    location=str(n.get("location", f"Node {n.get('node')}")),
                                    serialnb=str(n.get("serialnb", "n-a")),
                                )
                            )
                        if nodes:
                            _LOGGER.info("Loaded %s predefined nodes from %s", len(nodes), p)
                            return nodes
            except Exception as err:
                _LOGGER.warning("Failed loading nodes file %s: %s", p, err)
        _LOGGER.info("No predefined nodes found; proceeding with none.")
        return []

    async def _async_setup(self) -> None:
        box = await self.api.get_box_info()
        self.base_device_id = DucoBoxApi.build_base_device_id(box)
        self.predefined_nodes = self._load_nodes_config()
        # Initialize 'nodes' with static definitions
        self.nodes = [vars(n) for n in self.predefined_nodes]

    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            box = await self.api.get_box_info()
            # Fetch live data for predefined nodes
            fresh: List[Dict[str, Any]] = []
            for n in self.predefined_nodes:
                try:
                    cur = await self.api.get_node_info(n.node)
                except Exception as err:
                    _LOGGER.debug("Node %s update error: %s", n.node, err)
                    cur = None
                merged = vars(n).copy()
                if isinstance(cur, dict):
                    merged.update(cur)
                fresh.append(merged)
            self.nodes = fresh
            return {"box": box, "nodes": self.nodes}
        except Exception as err:
            raise UpdateFailed(f"Update failed: {err}")
