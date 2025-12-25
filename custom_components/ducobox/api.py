
from typing import Any, Dict, List
import logging
from yarl import URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import KNOWN_NODE_TYPES

_LOGGER = logging.getLogger(__name__)

class DucoClient:
    def __init__(self, hass: HomeAssistant, host: str) -> None:
        self._hass = hass
        self._host = host.rstrip('/')
        self._session = async_get_clientsession(hass)
    def _url(self, path: str) -> URL:
        base = self._host
        if not base.startswith("http://") and not base.startswith("https://"):
            base = f"http://{base}"
        return URL(base) / path.lstrip('/')
    async def fetch_node_info(self, node: int) -> Dict[str, Any]:
        url = self._url("nodeinfoget")
        async with self._session.get(url, params={"node": node}, timeout=10) as resp:
            _LOGGER.warning("DucoBox API: GET %s?node=%s -> %s", str(url), node, resp.status)
            resp.raise_for_status()
            try:
                data = await resp.json(content_type=None)
            except Exception:
                text = await resp.text(); data = self._parse_kv(text)
        devtype = str(data.get("devtype") or "UNKN").upper()
        data["devtype"] = devtype
        return data
    async def fetch_box_info(self) -> Dict[str, Any]:
        url = self._url("boxinfoget")
        async with self._session.get(url, timeout=10) as resp:
            _LOGGER.warning("DucoBox API: GET %s -> %s", str(url), resp.status)
            resp.raise_for_status()
            try:
                data = await resp.json(content_type=None)
            except Exception:
                text = await resp.text(); data = self._parse_kv(text)
        data.setdefault("devtype","BOX")
        return data
    def _parse_kv(self, text: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for line in text.splitlines():
            if '=' in line:
                k,v = line.split('=',1); data[k.strip()] = v.strip()
        return data
    async def discover_nodes_by_range(self, start: int = 1, end: int = 100) -> List[Dict[str, Any]]:
        nodes: List[Dict[str, Any]] = []
        for node in range(start, end+1):
            try:
                info = await self.fetch_node_info(node)
            except Exception as ex:
                _LOGGER.warning("DucoBox: node %s fetch failed: %s", node, ex)
                continue
            devtype = str(info.get("devtype", "UNKN")).upper()
            location = (info.get("location") or info.get("room") or "").strip()
            if devtype not in KNOWN_NODE_TYPES:
                _LOGGER.debug("DucoBox: node %s not present (UNKN devtype)", node)
                continue
            if len(location) < 2:
                _LOGGER.debug("DucoBox: node %s rejected (invalid/empty location)", node)
                continue
            nodes.append({
                "node": node,
                "devtype": devtype,
                "subtype": info.get("subtype"),
                "serial": info.get("serial"),
                "location": location,
            })
        return nodes
