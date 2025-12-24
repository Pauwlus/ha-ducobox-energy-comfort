
from __future__ import annotations

DOMAIN = "ducobox"
DEFAULT_SCAN_INTERVAL = 30
CONF_HOST = "host"
CONF_FRIENDLY_NAME = "friendly_name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CREATE_NODE_CONTROLS = "create_node_controls"  # toggle for node entities (controls & sensors)

DUCO_OPERATION_MODES = ["AUTO", "MAN1", "MAN2", "MAN3"]

BOX_INFO_ENDPOINT = "/boxinfoget"
NODE_INFO_ENDPOINT = "/nodeinfoget?node={node}"
SET_NODE_MODE_ENDPOINT = "/nodesetoperstate?node={node}&value={mode}"
