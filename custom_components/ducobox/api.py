
from __future__ import annotations
import asyncio
import aiohttp
import logging
from typing import Any, Dict, Optional, List

from .const import BOX_INFO_ENDPOINT, NODE_INFO_ENDPOINT, SET_NODE_MODE_ENDPOINT

_LOGGER = logging.getLogger(__name__)

class DucoBoxApi:
    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        self._host = host.rstrip('/')
        self._session = session

    @property
    def base_url(self) -> str:
        if self._host.startswith('http://') or self._host.startswith('https://'):
            return self._host
        return f"http://{self._host}"

    async def get_box_info(self) -> Dict[str, Any]:
        url = f"{self.base_url}{BOX_INFO_ENDPOINT}"
        async with self._session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def get_node_info(self, node_id: int) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{NODE_INFO_ENDPOINT.format(node=node_id)}"
        async with self._session.get(url, timeout=10) as resp:
            if resp.status == 404:
                return None
            resp.raise_for_status()
            data = await resp.json(content_type=None)
            if not isinstance(data, dict) or 'node' not in data:
                return None
            return data

    async def set_node_mode(self, node_id: int, mode: str) -> bool:
        url = f"{self.base_url}{SET_NODE_MODE_ENDPOINT.format(node=node_id, mode=mode)}"
        async with self._session.post(url, timeout=10) as resp:
            return resp.status == 200

    @staticmethod
    def build_base_device_id(box_info: Dict[str, Any]) -> str:
        general = box_info.get('General', {}) if isinstance(box_info, dict) else {}
        rf = str(general.get('RFHomeID', '')).lower().replace(':', '').replace('0x', '')
        serial = str(general.get('Serial', ''))
        serial_clean = serial.lower().strip().replace(':', '').replace(' ', '_') if serial else 'unknown'
        return f"ducobox-{rf}-{serial_clean}"

    @staticmethod
    def build_entity_unique_id(base_device_id: str, devtype: str, subtype: int, node_id: int, serialnb: str, metric: str) -> str:
        serial_clean = (serialnb or 'n-a').lower().replace(':', '').replace(' ', '-')
        devtype_clean = (devtype or 'unknown').lower()
        return f"{base_device_id}_{devtype_clean}_{subtype}_{node_id}_{serial_clean}_{metric}"
