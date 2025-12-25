
from datetime import timedelta
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import DucoClient

LOGGER = logging.getLogger(__name__)

class DucoCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: DucoClient, scan_interval: int) -> None:
        super().__init__(hass, logger=LOGGER, name="DucoBox Coordinator", update_interval=timedelta(seconds=scan_interval))
        self._client = client
        self.nodes = []

    async def async_config_entry_first_refresh(self) -> None:
        # Discover nodes from index
        self.nodes = await self._client.discover_nodes()
        LOGGER.debug('DucoBox: discovered nodes: %s', self.nodes)

        # Always fetch /boxinfoget and inject BOX node if missing
        try:
            box_info = await self._client.fetch_box_info()
            has_box = any(str(n.get("devtype", "")).upper() == "BOX" for n in self.nodes)
            if not has_box:
                LOGGER.debug("DucoBox: injecting BOX node from /boxinfoget")
                self.nodes.insert(0, {
                    "node": 0,
                    "devtype": "BOX",
                    "subtype": box_info.get("subtype"),
                    "serial": box_info.get("serial"),
                    "location": box_info.get("location") or "DucoBox",
                })
            # prime cache so BOX sensors appear even if later fetch fails
            if not hasattr(self, "data") or self.data is None:
                self.data = {}
            self.data[0] = {**box_info, "node": 0, "devtype": "BOX", "location": box_info.get("location") or "DucoBox"}
        except Exception as ex:
            LOGGER.debug("DucoBox: /boxinfoget not available (%s). Continuing.", ex)

        if not self.nodes:
            LOGGER.warning(
                "DucoBox: no nodes discovered from index.html; applying fallback set "
                "(BOX + nodes 1..6). If your box exposes '/boxinfoget', that will be used for BOX."
            )
            self.nodes = [{"node": 0, "devtype": "BOX", "subtype": None, "serial": None, "location": "DucoBox"}] +                          [{"node": i, "devtype": "UCHR", "subtype": None, "serial": None, "location": f"Node {i}"} for i in range(1, 7)]

        await super().async_config_entry_first_refresh()

    async def _async_update_data(self):
        data = getattr(self, "data", {}) or {}
        try:
            for n in self.nodes:
                node_id = n["node"]
                devtype = str(n.get("devtype", "")).upper()
                if devtype == "BOX":
                    try:
                        info = await self._client.fetch_box_info()
                    except Exception:
                        info = data.get(node_id, {})
                    info.setdefault("node", node_id)
                    info.setdefault("devtype", "BOX")
                    info.setdefault("location", info.get("location") or n.get("location") or "DucoBox")
                    data[node_id] = info
                else:
                    LOGGER.debug('DucoBox: fetching node info for node %s', node_id)
                    info = await self._client.fetch_node_info(node_id)
                    LOGGER.debug('DucoBox: node %s info keys: %s', node_id, list(info.keys()))
                    info.setdefault("node", node_id)
                    info.setdefault("devtype", n.get("devtype"))
                    info.setdefault("subtype", n.get("subtype"))
                    info.setdefault("serial", info.get("serial") or n.get("serial"))
                    info.setdefault("location", info.get("location") or n.get("location"))
                    data[node_id] = info
            return data
        except Exception as err:
            raise UpdateFailed(str(err))
