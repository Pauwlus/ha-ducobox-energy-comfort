
from __future__ import annotations

import async_timeout
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import (
    UnitOfTemperature,           # <-- vervangt TEMP_CELSIUS
    PERCENTAGE,
    CONCENTRATION_PARTS_PER_MILLION,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo  # NIEUW

from .const import (
    DUCOBOX_NODE1,
    DUCOBOX_BOXINFO,
    DUCO_ZONE1,
    DUCO_ZONE2,
    DUCO_NODE2,
    DUCO_NODE3,
    DUCO_NODE4,
    SCAN_INTERVAL as SCAN_SECONDS,
)

SCAN_INTERVAL = timedelta(seconds=SCAN_SECONDS)

SENSOR_DESCRIPTIONS = [
    # --- Hoofdunit: node 1 (trgt/actl/snsr) ---
    {"name": "DucoBox trgt", "unique_id": "ducobox_trgt", "unit": PERCENTAGE, "url": DUCOBOX_NODE1, "path": ["trgt"]},
    {"name": "DucoBox actl", "unique_id": "ducobox_actl", "unit": PERCENTAGE, "url": DUCOBOX_NODE1, "path": ["actl"]},
    {"name": "DucoBox snsr", "unique_id": "ducobox_snsr", "unit": PERCENTAGE, "url": DUCOBOX_NODE1, "path": ["snsr"]},

    # --- Hoofdunit: boxinfoget (temperaturen) ---
    {"name": "DucoBox temp aanzuiging vers", "unique_id": "ducobox_temp_oda", "unit": UnitOfTemperature.CELSIUS,
     "url": DUCOBOX_BOXINFO, "path": ["EnergyInfo", "TempODA"], "scale": 0.1,
     "device_class": SensorDeviceClass.TEMPERATURE},
    {"name": "DucoBox temp aanvoer woning", "unique_id": "ducobox_temp_sup", "unit": UnitOfTemperature.CELSIUS,
     "url": DUCOBOX_BOXINFO, "path": ["EnergyInfo", "TempSUP"], "scale": 0.1,
     "device_class": SensorDeviceClass.TEMPERATURE},
    {"name": "DucoBox temp afzuiging woning", "unique_id": "ducobox_temp_eta", "unit": UnitOfTemperature.CELSIUS,
     "url": DUCOBOX_BOXINFO, "path": ["EnergyInfo", "TempETA"], "scale": 0.1,
     "device_class": SensorDeviceClass.TEMPERATURE},
    {"name": "DucoBox temp afvoer", "unique_id": "ducobox_temp_eha", "unit": UnitOfTemperature.CELSIUS,
     "url": DUCOBOX_BOXINFO, "path": ["EnergyInfo", "TempEHA"], "scale": 0.1,
     "device_class": SensorDeviceClass.TEMPERATURE},

    # --- Zone 1 ---
    {"name": "Duco zone 1 beneden trgt", "unique_id": "duco_zone1_trgt", "unit": PERCENTAGE,
     "url": DUCO_ZONE1, "path": ["trgt"]},
    {"name": "Duco zone 1 beneden actl", "unique_id": "duco_zone1_actl", "unit": PERCENTAGE,
     "url": DUCO_ZONE1, "path": ["actl"]},
    {"name": "Duco zone 1 beneden snsr", "unique_id": "duco_zone1_snsr", "unit": PERCENTAGE,
     "url": DUCO_ZONE1, "path": ["snsr"]},

    # --- Zone 2 ---
    {"name": "Duco zone 2 boven trgt", "unique_id": "duco_zone2_trgt", "unit": PERCENTAGE,
     "url": DUCO_ZONE2, "path": ["trgt"]},
    {"name": "Duco zone 2 boven actl", "unique_id": "duco_zone2_actl", "unit": PERCENTAGE,
     "url": DUCO_ZONE2, "path": ["actl"]},
    {"name": "Duco zone 2 boven snsr", "unique_id": "duco_zone2_snsr", "unit": PERCENTAGE,
     "url": DUCO_ZONE2, "path": ["snsr"]},

    # --- Node 2 ---
    {"name": "Duco node 2 Badkamer Temp", "unique_id": "duco_node2_temp", "unit": UnitOfTemperature.CELSIUS,
     "url": DUCO_NODE2, "path": ["temp"], "device_class": SensorDeviceClass.TEMPERATURE},
    {"name": "Duco node 2 Badkamer rh", "unique_id": "duco_node2_rh", "unit": PERCENTAGE,
     "url": DUCO_NODE2, "path": ["rh"], "device_class": SensorDeviceClass.HUMIDITY},
    {"name": "Duco node 2 Badkamer snsr", "unique_id": "duco_node2_snsr", "unit": PERCENTAGE,
     "url": DUCO_NODE2, "path": ["snsr"]},

    # --- Node 3 ---
    {"name": "Duco node 3 Slaapkamer Temp", "unique_id": "duco_node3_temp", "unit": UnitOfTemperature.CELSIUS,
     "url": DUCO_NODE3, "path": ["temp"], "device_class": SensorDeviceClass.TEMPERATURE},
    {"name": "Duco node 3 Slaapkamer co2", "unique_id": "duco_node3_co2",
     "unit": CONCENTRATION_PARTS_PER_MILLION, "url": DUCO_NODE3, "path": ["co2"],
     "device_class": SensorDeviceClass.CO2},
    {"name": "Duco node 3 Slaapkamer snsr", "unique_id": "duco_node3_snsr", "unit": PERCENTAGE,
     "url": DUCO_NODE3, "path": ["snsr"]},

    # --- Node 4 ---
    {"name": "Duco node 4 Woonkamer Temp", "unique_id": "duco_node4_temp", "unit": UnitOfTemperature.CELSIUS,
     "url": DUCO_NODE4, "path": ["temp"], "device_class": SensorDeviceClass.TEMPERATURE},
    {"name": "Duco node 4 Woonkamer co2", "unique_id": "duco_node4_co2",
     "unit": CONCENTRATION_PARTS_PER_MILLION, "url": DUCO_NODE4, "path": ["co2"],
     "device_class": SensorDeviceClass.CO2},
    {"name": "Duco node 4 Woonkamer snsr", "unique_id": "duco_node4_snsr", "unit": PERCENTAGE,
     "url": DUCO_NODE4, "path": ["snsr"]},
]




async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up sensors from a config entry (UI)."""
    session = async_get_clientsession(hass)
    host = entry.data.get("host")
    verify_ssl = entry.data.get("verify_ssl", False)
    if not host:
        return

    # 👉 1) Versie best-effort ophalen (één keer tijdens setup)
    sw_version = await _fetch_sw_version(session, host, verify_ssl)

    # 👉 2) DeviceInfo definiëren (één device voor alle entiteiten)
    device_info = DeviceInfo(
        identifiers={("ducobox", host)},         # stabiele identifier voor dit apparaat
        name="DucoBox",
        manufacturer="DUCO",
        model="DucoBox Energy Comfort",
        sw_version=sw_version,                   # 👈 automatische firmware/software-versie
        configuration_url=f"http://{host}",      # klikbare link in HA UI
    )

    # 👉 3) Entities aanmaken en koppelen aan device_info
    entities = [
        DucoBoxSensor(
            session=session,
            name=desc["name"],
            unique_id=desc["unique_id"],
            unit=desc.get("unit"),
            url=desc["url"].format(host=host),
            path=desc["path"],
            scale=desc.get("scale", 1.0),
            device_class=desc.get("device_class"),
            verify_ssl=verify_ssl,
            device_info=device_info,             # 👈 koppel aan Device
        )
        for desc in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities, True)

# (optioneel) legacy YAML-setup
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    session = async_get_clientsession(hass)
    host = config.get("host")
    verify_ssl = config.get("verify_ssl", False)
    if not host:
        return
    entities = [
        DucoBoxSensor(
            session=session,
            name=desc["name"],
            unique_id=desc["unique_id"],
            unit=desc.get("unit"),
            url=desc["url"].format(host=host),
            path=desc["path"],
            scale=desc.get("scale", 1.0),
            device_class=desc.get("device_class"),
            verify_ssl=verify_ssl,
        )
        for desc in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities, True)


def _extract_value(data: dict, path: list[str]):
    cur = data
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
        if cur is None:
            return None
    return cur

# Added for supporting device ===================
sync def _fetch_sw_version(session, host: str, verify_ssl: bool) -> str | None:
    """Probeer de firmware/software-versie van de DucoBox op te halen.

    We proberen een paar gangbare endpoints/velden en stoppen zodra we iets bruikbaars vinden.
    Alle calls zijn best-effort; bij fouten geven we None terug (geen crash).
    """
    import async_timeout

    # Kandidaten endpoints (relative path) en mogelijke sleutel-paden in de JSON
    endpoints = [
        "/info",
        "/boxinfoget",
        "/nodeinfoget?node=1",
    ]
    # Mogelijke sleutel(paden) die in de praktijk gezien worden
    version_keys = [
        ["swversion"],
        ["sw_version"],
        ["SWVersion"],
        ["firmware"],
        ["fw_version"],
        ["version"],
        # En soms diep genest (best-effort)
        ["HeatRecovery", "General", "swversion"],
        ["General", "swversion"],
    ]

    base_http = f"http://{host}"
    # Als jouw box HTTPS met self-signed gebruikt, kun je hier ook https:// proberen
    bases = [base_http]

    for base in bases:
        for ep in endpoints:
            url = f"{base}{ep}"
            try:
                async with async_timeout.timeout(5):
                    resp = await session.get(url, ssl=verify_ssl or None)
                    if resp.status != 200:
                        continue
                    data = await resp.json(content_type=None)
            except Exception:
                continue

            # Probeer verschillende key-paden
            for path in version_keys:
                cur = data
                ok = True
                for key in path:
                    if not isinstance(cur, dict) or key not in cur:
                        ok = False
                        break
                    cur = cur[key]
                if ok and isinstance(cur, (str, int, float)) and str(cur).strip():
                    return str(cur).strip()

    return None
# ===============================================




class DucoBoxSensor(SensorEntity):
    _attr_should_poll = True

    def __init__(
        self,
        session,
        name,
        unique_id,
        unit,
        url,
        path,
        scale=1.0,
        device_class=None,
        verify_ssl=False,
        device_info: DeviceInfo | None = None,  # 👈 NIEUW
    ):
        self._session = session
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_native_unit_of_measurement = unit
        self._url = url
        self._path = path
        self._scale = scale
        self._attr_native_value = None
        self._verify_ssl = verify_ssl
        if device_class:
            self._attr_device_class = device_class
        if device_info is not None:
            self._attr_device_info = device_info  # 👈 Koppeling met Apparaat


