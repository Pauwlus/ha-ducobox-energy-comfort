
"""Helper utilities for DucoBox integration."""
from __future__ import annotations
import re
from typing import Any, Dict

ASCII_SAFE = re.compile(r"[^a-z0-9_-]")


def sanitize(s: str) -> str:
    """Lowercase ASCII-only, spaces -> '-', remove invalid chars."""
    if s is None:
        s = ""
    s = s.strip().lower().replace(" ", "-")
    return ASCII_SAFE.sub("", s)


def build_base_unique(devtype: str, subtype: str | None, node_id: str | int | None, serial: str | None) -> str:
    """Compose unique base id from hardware fields.

    Format: devtype_subtype_nodeid_serial (lowercase ascii). Missing parts omitted.
    """
    parts = [sanitize(devtype)]
    if subtype:
        parts.append(sanitize(str(subtype)))
    if node_id is not None:
        parts.append(sanitize(str(node_id)))
    if serial:
        parts.append(sanitize(str(serial)))
    # Ensure uniqueness and stability
    base = "_".join([p for p in parts if p])
    return base


def build_entity_id(domain: str, base_unique: str, item: str) -> str:
    """Construct entity_id following spec: lowercase ascii, separators '-/_'.

    Example: sensor.ducobox_uchr_12_123456_temp
    """
    prefix = sanitize("ducobox")
    key = "_".join([prefix, base_unique, sanitize(item)])
    return f"{domain}.{key}"


def infer_location(info: Dict[str, Any]) -> str:
    """Extract a human-friendly location description from node info dict."""
    for key in ("location", "loc", "room", "zone_desc", "name"):
        val = info.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    # Fallback: type + node id
    devtype = info.get("devtype") or info.get("type") or "node"
    nid = info.get("node") or info.get("node_id") or info.get("zone")
    return f"{devtype} {nid}".strip()

