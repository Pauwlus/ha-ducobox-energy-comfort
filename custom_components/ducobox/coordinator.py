
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import DucoClient

class DucoCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: DucoClient, scan_interval: int) -> None:
        from datetime import timedelta
        import logging
        super().__init__(hass, logger=logging.getLogger(__name__), name="DucoBox Coordinator", update_interval=timedelta(seconds=scan_interval))
        self._client = client
        self.nodes = []
    async def async_config_entry_first_refresh(self) -> None:
        self.nodes = await self._client.discover_nodes()
        self.logger.debug('DucoBox: discovered nodes: %s', self.nodes)
        if not self.nodes:
            self.logger.warning('DucoBox: no nodes discovered; fallback nodes applied')
            self.nodes = [{"node": 0, "devtype": "BOX", "subtype": None, "serial": None, "location": "DucoBox"}] + [{"node": i, "devtype": "UCHR", "subtype": None, "serial": None, "location": f"Node {i}"} for i in range(1, 13)]
        await super().async_config_entry_first_refresh()
    async def _async_update_data(self):
        data = {}
        try:
            for n in self.nodes:
                node_id = n["node"]
                self.logger.debug('DucoBox: fetching node info for node %s', node_id)
                info = await self._client.fetch_node_info(node_id)
                self.logger.debug('DucoBox: node %s info keys: %s', node_id, list(info.keys()))
                info.setdefault("node", node_id)
                info.setdefault("devtype", n.get("devtype"))
                info.setdefault("subtype", n.get("subtype"))
                info.setdefault("serial", info.get("serial") or n.get("serial"))
                info.setdefault("location", info.get("location") or n.get("location"))
                data[node_id] = info
            return data
        except Exception as err:
            raise UpdateFailed(str(err))
