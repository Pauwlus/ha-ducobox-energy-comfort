
DOMAIN = "ducobox"
PLATFORMS = ["sensor"]
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_NAME = "DucoBox Energy Comfort"
CONF_HOST = "host"
CONF_FRIENDLY_NAME = "friendly_name"
CONF_SCAN_INTERVAL = "scan_interval"
OPTION_AREAS = "areas"
NODE_TYPE_BOX = "BOX"
NODE_TYPE_UCHR = "UCHR"
NODE_TYPE_UCCO2 = "UCCO2"
NODE_TYPE_VLV = "VLV"
BOX_REQUIRED_CATEGORIES = ("EnergyInfo", "EnergyFan")
BOX_DEFAULT_ENERGYINFO_KEYS = (
    "TempODA","TempSUP","TempETA","TempEHA","BypassStatus","BypassRequestedTemp",
    "FrostProtState","FrostProtPressReduct","FrostProtHeaterLevel","FilterRemainingTime"
)
BOX_DEFAULT_ENERGYFAN_KEYS = (
    "SupplyFanSpeed","SupplyFanPressTarget","SupplyFanPressActual","SupplyFanPwmLevel","SupplyFanPwmPercentage",
    "ExhaustFanSpeed","ExhaustFanPressTarget","ExhaustFanPressActual","ExhaustFanPwmLevel","ExhaustFanPwmPercentage"
)
NODE_RANGE_START = 1
NODE_RANGE_END = 100
