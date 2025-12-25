
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
