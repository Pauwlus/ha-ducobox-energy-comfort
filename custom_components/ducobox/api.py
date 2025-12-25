
"""HTTP client for DucoBox."""
from __future__ import annotations
import asyncio
from typing import Any, Dict, List
from yarl import URL

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession


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

    async def fetch_index(self) -> str:
        """Fetch the index HTML listing nodes."""
        url = self._url("index.html")
        async with self._session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            return await resp.text()

    async def fetch_node_info(self, node: int) -> Dict[str, Any]:
        """Fetch detailed info for a node."""
        url = self._url(f"nodeinfoget?node={node}")
        async with self._session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            # Try JSON first, fallback to text parse
            try:
                return await resp.json(content_type=None)
            except Exception:
                text = await resp.text()
                return self._parse_kv(text)

    def _parse_kv(self, text: str) -> Dict[str, Any]:
        """Parse a simple key=value text response into dict."""
        data: Dict[str, Any] = {}
        for line in text.splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                data[k.strip()] = v.strip()
        return data

    async def discover_nodes(self) -> List[Dict[str, Any]]:
        """Scrape nodes from the index page.

        Returns list of dicts: {node, devtype, subtype, serial, location}
        """
        html = await self.fetch_index()
        nodes: List[Dict[str, Any]] = []
        # Very lightweight parsing: look for lines like `node=12`, Type, Serial, Location
        import re
        rows = re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", html)
        for row in rows:
            cols = re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", row)
            text_cols = [re.sub(r"<[^>]+>", "", c).strip() for c in cols]
            if not text_cols:
                continue
            # Heuristics: find 'node' number in any column
            node_num = None
            for c in text_cols:
                m = re.search(r"node\s*:?\s*(\d+)", c, re.I)
                if m:
                    node_num = int(m.group(1))
                    break
            # Also accept pure integer column
            if node_num is None:
                for c in text_cols:
                    if c.isdigit():
                        node_num = int(c)
                        break
            if node_num is None:
                continue
            # Type/devtype
            devtype = None
            for c in text_cols:
                if re.search(r"(BOX|UCHR|UCCO2|VLV)", c, re.I):
                    devtype = re.search(r"(BOX|UCHR|UCCO2|VLV)", c, re.I).group(1).upper()
                    break
            # Subtype & serial
            subtype = None
            serial = None
            for c in text_cols:
                m = re.search(r"subtype\s*:?\s*([\w-]+)", c, re.I)
                if m:
                    subtype = m.group(1)
                m2 = re.search(r"serial\s*:?\s*([\w-]+)", c, re.I)
                if m2:
                    serial = m2.group(1)
            # Location
            location = None
            for c in text_cols:
                if re.search(r"(location|room|zone)\s*:?", c, re.I):
                    # assume after colon
                    parts = re.split(r":", c)
                    if len(parts) > 1:
                        location = parts[1].strip()
                # Else last column might be location name
            if location is None and len(text_cols) >= 3:
                location = text_cols[-1]
            nodes.append({"node": node_num, "devtype": devtype or "NODE", "subtype": subtype, "serial": serial, "location": location or f"Node {node_num}"})
        # If no table rows, fallback: scan text lines
        if not nodes:
            for line in html.splitlines():
                m = re.search(r"node\s*(\d+).*type\s*(BOX|UCHR|UCCO2|VLV)", line, re.I)
                if m:
                    nodes.append({"node": int(m.group(1)), "devtype": m.group(2).upper(), "subtype": None, "serial": None, "location": f"Node {m.group(1)}"})
        return nodes

