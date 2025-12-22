
"""
Sensor platform voor DucoBox Energy Comfort.

Doel:
- Maakt sensor-entiteiten aan voor DucoBox (targets, actuele waardes, temperatuur, CO2, RH, zones).
- Koppelt alle entiteiten aan één Device ("DucoBox") in de Device Registry, zodat
  je in HA een apparaat ziet met bijbehorende sensoren.
"""

from __future__ import annotations

import async_timeout
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import (
    UnitOfTemperature,
    PERCENTAGE,
    CONCENTRATION_PARTS_PER_MILLION,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry

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

# Polling-interval voor entiteiten (seconden -> timedelta)
SCAN_INTERVAL = timedelta(seconds=SCAN_SECONDS)


# Beschrijvingen voor alle sensoren: naam, id, unit, bron-URL en pad in JSON.
# Deze informatie wordt gebruikt om entiteiten te genereren in setup.
SENSOR_DESCRIPTIONS: list[dict[str, Any]] = [
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


def _build_device_info(host: str) -> DeviceInfo:
    """
    Helper: maakt het DeviceInfo object voor de Device Registry.

    Doel:
    - Groepeert alle entiteiten onder één apparaat ("DucoBox").

    Parameters:
    - host: de geconfigureerde host/IP van de DucoBox (str)

    Return:
    - DeviceInfo: object met identifiers, naam en basismetadata
    """
    return DeviceInfo(
        identifiers={("ducobox", host)},       # dezelfde identifiers voor alle entiteiten van deze box
        name="DucoBox",
        manufacturer="DUCO",
        model="DucoBox Energy Comfort",
        configuration_url=f"http://{host}",    # klikbare link in HA UI
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """
    Setup voor UI-configuratie (config entry).

    Doel:
    - Maakt sensor-entiteiten aan voor de geconfigureerde DucoBox.
    - Koppelt entiteiten aan het Device ("DucoBox") via DeviceInfo.

    Parameters:
    - hass: HomeAssistant instance
    - entry: ConfigEntry met data: host (str), verify_ssl (bool)
    - async_add_entities: callback om entiteiten aan HA toe te voegen

    Return:
    - None
    """
    session = async_get_clientsession(hass)
    host = entry.data.get("host")
    # verify_ssl: uit options (indien aanwezig), anders data fallback
    verify_ssl = entry.options.get("verify_ssl", entry.data.get("verify_ssl", False))
    if not host:
        return

    device_info = _build_device_info(host)

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
            device_info=device_info,  # koppeling met Device
        )
        for desc in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities, True)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """
    Legacy YAML-setup (optioneel).

    Doel:
    - Ondersteunt 'sensor: - platform: ducobox' configuratie zonder UI.

    Parameters:
    - hass: HomeAssistant instance
    - config: dict met 'host' (str) en optioneel 'verify_ssl' (bool)
    - async_add_entities: callback
    - discovery_info: niet gebruikt

    Return:
    - None
    """
    session = async_get_clientsession(hass)
    host = config.get("host")
    verify_ssl = config.get("verify_ssl", False)
    if not host:
        return

    device_info = _build_device_info(host)

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
            device_info=device_info,
        )
        for desc in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities, True)


def _extract_value(data: dict, path: list[str]) -> Any | None:
    """
    Helper: haalt een waarde uit genest JSON via een key-pad.

    Parameters:
    - data: dict (volledige JSON payload)
    - path: lijst van keys, bijv. ["EnergyInfo", "TempSUP"]

    Return:
    - de gevonden waarde (Any) of None als pad niet bestaat
    """
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
        if cur is None:
            return None
    return cur


class DucoBoxSensor(SensorEntity):
    """
    Entiteitsklasse voor één DucoBox sensor.

    Doel:
    - Haalt periodiek data op via HTTP (aiohttp) en stelt native_value.

    Belangrijk:
    - _attr_should_poll = True -> gebruikt SCAN_INTERVAL voor polling
    - DeviceInfo (_attr_device_info) koppelt entiteit aan het apparaat.
    """

    _attr_should_poll = True

    def __init__(
        self,
        session,
        name: str,
        unique_id: str,
        unit: str | None,
        url: str,
        path: list[str],
        scale: float = 1.0,
        device_class: SensorDeviceClass | None = None,
        verify_ssl: bool = False,
        device_info: DeviceInfo | None = None,
    ) -> None:
        """
        Constructor.

        Parameters:
        - session: aiohttp ClientSession (gedeeld door HA)
        - name: entiteitsnaam (str)
        - unique_id: unieke id (str)
        - unit: unit of measurement (str | None)
        - url: endpoint voor dit datapunt (str)
        - path: JSON key-pad (list[str])
        - scale: vermenigvuldigingsfactor (float, default 1.0)
        - device_class: optioneel, UI weergaveklasse
        - verify_ssl: certificaatcontrole bij HTTPS (bool)
        - device_info: koppeling met Device registry (optioneel)

        Return:
        - None
        """
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
            # Koppeling met het apparaat "DucoBox"
            self._attr_device_info = device_info

    async def async_update(self) -> None:
        """
        Polling update.

        Doel:
        - Haalt actuele JSON op vanaf self._url.
        - Extraheert waarde via _extract_value en zet native_value.
        - Past optioneel schaalfactor toe.

        Parameters:
        - None

        Return:
        - None
        """
        try:
            async with async_timeout.timeout(10):
                resp = await self._session.get(self._url, ssl=self._verify_ssl or None)
                if resp.status != 200:
                    return
                data = await resp.json(content_type=None)
        except Exception:
            return

        raw = _extract_value(data, self._path)
        if raw is None:
            return

        try:
            value = float(raw) * self._scale
        except Exception:
            value = raw

        self._attr_native_value = value
