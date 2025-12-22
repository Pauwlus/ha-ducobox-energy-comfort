
"""
Config flow voor DucoBox Energy Comfort integratie.

Doel:
- UI-configuratie van host/IP en (optioneel) verify_ssl.
- Opties-flow voor aanpasbaar scan_interval.

Belangrijk:
- Voor UI-setup wordt een ConfigEntry aangemaakt met data:
  { host: str, verify_ssl: bool }
- Opties-flow schrijft scan_interval in entry.options.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigEntry
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, SCAN_INTERVAL as DEFAULT_SCAN_INTERVAL

# Sleutels gebruikt in config entry data / options
CONF_HOST = "host"
CONF_VERIFY_SSL = "verify_ssl"
CONF_SCAN_INTERVAL = "scan_interval"


class DucoboxConfigFlow(ConfigFlow, domain=DOMAIN):
    """
    ConfigFlow voor DucoBox.

    Doel:
    - Behandelt de eerste stap waarin de gebruiker host/IP en verify_ssl instelt.
    Return:
    - Maakt een ConfigEntry aan met data en options.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        UI-stap: host + verify_ssl.

        Parameters:
        - user_input: dict met 'host' (str) en optioneel 'verify_ssl' (bool)

        Return:
        - FlowResult: toont formulier of creëert entry
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input.get(CONF_HOST)
            verify_ssl = user_input.get(CONF_VERIFY_SSL, False)

            if not host:
                errors[CONF_HOST] = "required"
            else:
                # Unieke ID op basis van host, voorkomt dubbele entries
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"DucoBox @{host}",
                    data={CONF_HOST: host, CONF_VERIFY_SSL: verify_ssl},
                    options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_VERIFY_SSL, default=False): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """
        YAML-import (optioneel).

        Parameters:
        - user_input: dict met host/verify_ssl uit YAML

        Return:
        - FlowResult (routeert naar user-step)
        """
        return await self.async_step_user(user_input)

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry):
        """
        Geeft de OptionsFlow-handler terug.

        Parameters:
        - config_entry: bestaande entry voor deze integratie

        Return:
        - DucoboxOptionsFlowHandler instance
        """
        return DucoboxOptionsFlowHandler(config_entry)


class DucoboxOptionsFlowHandler(config_entries.OptionsFlow):
    """
    Opties-flow voor DucoBox.

    Doel:
    - Laat gebruiker 'scan_interval' aanpassen.
    - verify_ssl blijft onderdeel van entry.data; hier tonen we desgewenst de
      huidige waarde voor informatieve doeleinden (niet wijzigen).

    Gebruik:
    - HA beheert self.config_entry; roep super().__init__(config_entry) aan.
    """

    def __init__(self, config_entry: ConfigEntry) -> None:
        """
        Constructor.

        Parameters:
        - config_entry: bestaande config entry

        Return:
        - None
        """
        # Belangrijk: super aanroepen; HA zet zelf self.config_entry.
        super().__init__(config_entry)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """
        Opties hoofd-stap.

        Parameters:
        - user_input: dict met 'scan_interval' (int), optioneel 'verify_ssl' (bool, niet opgeslagen)

        Return:
        - FlowResult: maakt options entry of toont formulier
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Valideer scan_interval
            try:
                scan_interval = int(
                    user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                )
                if scan_interval <= 0:
                    raise ValueError
            except Exception:
                errors[CONF_SCAN_INTERVAL] = "invalid_scan_interval"
            else:
                # Schrijf alleen options; data (verify_ssl, host) blijft in entry.data.
                options = dict(self.config_entry.options)
                options[CONF_SCAN_INTERVAL] = scan_interval
                return self.async_create_entry(title="DucoBox opties", data=options)

        # Defaults ophalen
        current_scan = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        current_ssl = self.config_entry.data.get(CONF_VERIFY_SSL, False)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current_scan): int,
                vol.Optional(CONF_VERIFY_SSL, default=current_ssl): bool,  # informatief
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
