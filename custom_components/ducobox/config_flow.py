
"""
Config flow voor DucoBox Energy Comfort integratie.
Dit maakt UI-configuratie mogelijk (host + verify_ssl) en een opties-flow (scan_interval).
"""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, SCAN_INTERVAL as DEFAULT_SCAN_INTERVAL

# Sleutels gebruikt in config entry data / options
CONF_HOST = "host"
CONF_VERIFY_SSL = "verify_ssl"
CONF_SCAN_INTERVAL = "scan_interval"


class DucoboxConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow voor DucoBox."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step where the user enters host and ssl settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input.get(CONF_HOST)
            verify_ssl = user_input.get(CONF_VERIFY_SSL, False)

            if not host:
                errors[CONF_HOST] = "required"
            else:
                # Stel een unieke ID in op basis van host, zodat dubbele entries worden voorkomen
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"DucoBox @ {host}",
                    data={CONF_HOST: host, CONF_VERIFY_SSL: verify_ssl},
                    options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
                )

        data_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_VERIFY_SSL, default=False): bool,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Support for YAML import if someone uses platform YAML."""
        # Re-route naar user-step
        return await self.async_step_user(user_input)

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry):
        return DucoboxOptionsFlowHandler(config_entry)



class DucoboxOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        # Roep de superconstructor aan; HA zet self.config_entry voor je klaar.
        super().__init__(config_entry)
    
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
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
                # verify_ssl kan ook als optie worden bewaard (naast data). We updaten beide voor eenvoud.
                verify_ssl = bool(user_input.get(CONF_VERIFY_SSL, self.config_entry.data.get(CONF_VERIFY_SSL, False)))

                # Update options
                options = dict(self.config_entry.options)
                options[CONF_SCAN_INTERVAL] = scan_interval

                # Let op: het direct aanpassen van config_entry.data vanuit OptionsFlow
                # is in sommige HA-versies niet mogelijk; verify_ssl blijft daarom primair
                # in data zoals ingesteld bij de eerste setup.
                return self.async_create_entry(title="DucoBox opties", data=options)

        # Defaults ophalen
        current_scan = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        current_ssl = self.config_entry.data.get(CONF_VERIFY_SSL, False)

        data_schema = vol.Schema({
            vol.Required(CONF_SCAN_INTERVAL, default=current_scan): int,
            vol.Optional(CONF_VERIFY_SSL, default=current_ssl): bool,
        })

        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)
