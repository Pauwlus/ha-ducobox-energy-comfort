
import re
ASCII_SAFE = re.compile(r"[^a-z0-9_-]")

def sanitize(s: str) -> str:
    if s is None: s = ""
    s = s.strip().lower().replace(" ", "-")
    return ASCII_SAFE.sub("", s)

def build_base_unique(devtype, subtype, node_id, serial):
    parts = [sanitize(devtype)]
    if subtype: parts.append(sanitize(str(subtype)))
    if node_id is not None: parts.append(sanitize(str(node_id)))
    if serial: parts.append(sanitize(str(serial)))
    return "_".join([p for p in parts if p])

def build_entity_id(domain, base_unique, item):
    prefix = sanitize("ducobox")
    key = "_".join([prefix, base_unique, sanitize(item)])
    return f"{domain}.{key}"

def infer_location(info):
    for key in ("location","loc","room","zone_desc","name"):
        val = info.get(key)
        if isinstance(val,str) and val.strip():
            return val.strip()
    devtype = info.get("devtype") or info.get("type") or "node"
    nid = info.get("node") or info.get("node_id") or info.get("zone")
    return f"{devtype} {nid}".strip()
