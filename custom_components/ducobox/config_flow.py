
"""
Config flow voor DucoBox Energy Comfort integratie.

- UI-configuratie van host/IP en (optioneel) verify_ssl.
- Opties-flow voor aanpasbaar scan_interval (opgeslagen in entry.options).

Data in ConfigEntry:
- data: { host: str, verify_ssl: bool }
- options: { scan_interval: int }
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
    """ConfigFlow voor DucoBox.

    Behandelt de eerste stap waarin de gebruiker host/IP en verify_ssl instelt.
    Maakt een ConfigEntry aan met data en default options.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """UI-stap: host + verify_ssl."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host: str | None = user_input.get(CONF_HOST)
            verify_ssl: bool = bool(user_input.get(CONF_VERIFY_SSL, False))

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
        """YAML-import (optioneel): routeert naar user-step."""
        return await self.async_step_user(user_input)


def async_get_options_flow(config_entry: ConfigEntry):
    """Geeft de OptionsFlow-handler terug."""
    return DucoboxOptionsFlowHandler(config_entry)


class DucoboxOptionsFlowHandler(config_entries.OptionsFlow):
    """Opties-flow voor DucoBox.

    Laat gebruiker 'scan_interval' aanpassen. 'verify_ssl' blijft onderdeel
    van entry.data (wordt hier niet gewijzigd om consistent te blijven).
    """

    def __init__(self, config_entry: ConfigEntry) -> None:
        # In OptionsFlow zelf de entry bewaren; geen super().__init__ aanroepen.
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Opties hoofd-stap."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Valideer scan_interval
            try:
                scan_interval = int(user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
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
        # current_ssl is alleen informatief; niet wijzigbaar via options
        current_ssl = self.config_entry.data.get(CONF_VERIFY_SSL, False)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current_scan): int,
                # Als je verify_ssl via options wilt kunnen aanpassen, voeg het
                # hier toe en schrijf het dan expliciet naar options.
                # We tonen het hier niet in het formulier om verwarring te voorkomen.
            }
        )

        # Je kunt description_placeholders gebruiken om de huidige SSL-stand te tonen
        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"verify_ssl": str(current_ssl)},
        )
