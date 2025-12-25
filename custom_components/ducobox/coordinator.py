
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
        self._box_node = None

    async def async_config_entry_first_refresh(self) -> None:
        LOGGER.warning('DucoBox: coordinator first refresh START — probing range %s..%s', NODE_RANGE_START, NODE_RANGE_END)
        # Probe nodes by range; includes BOX at node 1 in your sample
        discovered = await self._client.discover_nodes_by_range(NODE_RANGE_START, NODE_RANGE_END)
        self.nodes.extend(discovered)
        # Identify BOX node (prefer devtype BOX among discovered)
        for n in self.nodes:
            if str(n.get('devtype')).upper() == 'BOX':
                self._box_node = n.get('node')
                break
        # Fetch boxinfoget and map to BOX node (node 1 in your sample)
        try:
            box_info = await self._client.fetch_box_info()
            target_node = self._box_node if self._box_node is not None else 1
            box_info.setdefault('node', target_node)
            box_info.setdefault('devtype', 'BOX')
            self.data[target_node] = box_info
            # Ensure a BOX node exists in nodes list
            if self._box_node is None:
                self.nodes.insert(0, {
                    'node': target_node,
                    'devtype': 'BOX',
                    'subtype': box_info.get('subtype'),
                    'serial': box_info.get('serial'),
                    'location': box_info.get('General', {}).get('InstallerState') or box_info.get('location') or 'DucoBox'
                })
            LOGGER.warning('DucoBox: BOX mapped to node %s via /boxinfoget', target_node)
        except Exception as ex:
            LOGGER.warning("DucoBox: /boxinfoget not available (%s).", ex)
        LOGGER.warning('DucoBox: coordinator discovered %d node(s): %s', len(self.nodes), self.nodes)
        await super().async_config_entry_first_refresh()

    async def _async_update_data(self):
        try:
            for n in self.nodes:
                node_id = n["node"]
                if str(n.get('devtype')).upper() == 'BOX':
                    try:
                        info = await self._client.fetch_box_info()
                        info.setdefault('node', node_id)
                        info.setdefault('devtype', 'BOX')
                        self.data[node_id] = info
                    except Exception:
                        pass
                else:
                    info = await self._client.fetch_node_info(node_id)
                    if "serial" not in info and "serialnb" in info:
                        info["serial"] = info.get("serialnb")
                    info.setdefault("node", node_id)
                    info.setdefault("devtype", n.get("devtype"))
                    info.setdefault("subtype", n.get("subtype"))
                    info.setdefault("serial", info.get("serial") or n.get("serial"))
                    info.setdefault("location", info.get("location") or n.get("location"))
                    self.data[node_id] = info
            LOGGER.warning('DucoBox: coordinator update tick; nodes=%s, data_keys=%s', [n.get('node') for n in self.nodes], list(self.data.keys()))
            return self.data
        except Exception as err:
            LOGGER.error('DucoBox: update failed: %s', err)
            raise UpdateFailed(str(err))
