
"""Constants for the DucoBox integration."""
from __future__ import annotations

DOMAIN = "ducobox"
PLATFORMS = ["sensor"]
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_NAME = "DucoBox Energy Comfort"
CONF_HOST = "host"
CONF_FRIENDLY_NAME = "friendly_name"
CONF_SCAN_INTERVAL = "scan_interval"
OPTION_AREAS = "areas"  # mapping of device_id -> area_id

# Known node types
NODE_TYPE_BOX = "BOX"
NODE_TYPE_UCHR = "UCHR"
NODE_TYPE_UCCO2 = "UCCO2"
NODE_TYPE_VLV = "VLV"

# Attribute sets by type
ATTRS_BOX_CATEGORIES = ("energyinfo", "energyfan")
ATTRS_UCHR = ("temp", "rh", "snsr", "state")
ATTRS_UCCO2 = ("temp", "co2", "snsr")
ATTRS_VLV = ("trgt", "actl", "snsr")

