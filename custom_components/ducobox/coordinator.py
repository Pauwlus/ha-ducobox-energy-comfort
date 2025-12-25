
from datetime import timedelta
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import DucoClient
from .const import NODE_RANGE_START, NODE_RANGE_END

LOGGER = logging.getLogger(__name__)

class DucoCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: DucoClient, scan_interval: int) -> None:
        super().__init__(hass, logger=LOGGER, name="DucoBox Coordinator", update_interval=timedelta(seconds=scan_interval))
        self._client = client
        self.nodes = []
        self.data = {}

    async def async_config_entry_first_refresh(self) -> None:
        # Discover nodes by probing range only
        LOGGER.warning('DucoBox: coordinator first refresh START — probing range %s..%s', NODE_RANGE_START, NODE_RANGE_END)
        # Always fetch BOX info
        try:
            box_info = await self._client.fetch_box_info()
            self.data[0] = {**box_info, "node": 0, "devtype": "BOX", "location": box_info.get("location") or "DucoBox"}
            self.nodes.append({
                "node": 0,
                "devtype": "BOX",
                "subtype": box_info.get("subtype"),
                "serial": box_info.get("serial"),
                "location": box_info.get("location") or "DucoBox",
            })
        except Exception as ex:
            LOGGER.debug("DucoBox: /boxinfoget not available (%s). Continuing without BOX injection.", ex)
        # Probe nodes 1..100 (configurable via const)
        discovered = await self._client.discover_nodes_by_range(NODE_RANGE_START, NODE_RANGE_END)
        self.nodes.extend(discovered)
        LOGGER.warning('DucoBox: coordinator discovered %d node(s): %s', len(self.nodes), self.nodes)
        await super().async_config_entry_first_refresh()

    async def _async_update_data(self):
        try:
            # Refresh per-node info
            for n in self.nodes:
                node_id = n["node"]
                if node_id == 0:
                    # Refresh BOX
                    try:
                        info = await self._client.fetch_box_info()
                    except Exception:
                        info = self.data.get(0, {})
                    info.setdefault("node", 0)
                    info.setdefault("devtype", "BOX")
                    info.setdefault("location", info.get("location") or n.get("location") or "DucoBox")
                    self.data[0] = info
                else:
                    info = await self._client.fetch_node_info(node_id)
                    devtype = str(info.get("devtype", n.get("devtype") or "UNKN")).upper()
                    info.setdefault("node", node_id)
                    info.setdefault("devtype", devtype)
                    info.setdefault("subtype", n.get("subtype"))
                    info.setdefault("serial", info.get("serial") or n.get("serial"))
                    info.setdefault("location", info.get("location") or n.get("location"))
                    self.data[node_id] = info
            return self.data
        except Exception as err:
            raise UpdateFailed(str(err))
