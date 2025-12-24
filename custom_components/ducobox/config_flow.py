
from __future__ import annotations
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_FRIENDLY_NAME,
    CONF_SCAN_INTERVAL,
    CONF_CREATE_NODE_CONTROLS,
)
from .api import DucoBoxApi

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_FRIENDLY_NAME): str,
    vol.Required(CONF_SCAN_INTERVAL, default=30): int,
})

class DucoBoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 2

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        errors: Dict[str, str] = {}
        if user_input is not None:
            session = aiohttp_client.async_get_clientsession(self.hass)
            api = DucoBoxApi(user_input[CONF_HOST], session)
            try:
                await api.get_box_info()
            except Exception as err:
                _LOGGER.warning("Connection failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                unique_id = f"{DOMAIN}-{user_input[CONF_HOST].lower()}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input[CONF_FRIENDLY_NAME], data=user_input)
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)

    async def async_step_import(self, user_input: Dict[str, Any]) -> FlowResult:
        return await self.async_step_user(user_input)

    async def async_get_options_flow(self, config_entry):
        return DucoBoxOptionsFlowHandler(config_entry)

class DucoBoxOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        if user_input is not None:
            # Split between data (connection settings) and options (behavior toggles)
            new_data = dict(self.entry.data)
            new_data[CONF_HOST] = user_input[CONF_HOST]
            new_data[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]

            new_options = dict(self.entry.options)
            new_options[CONF_CREATE_NODE_CONTROLS] = user_input[CONF_CREATE_NODE_CONTROLS]

            self.hass.config_entries.async_update_entry(
                self.entry,
                data=new_data,
                options=new_options,
                title=user_input[CONF_FRIENDLY_NAME],
            )
            await self.hass.config_entries.async_reload(self.entry.entry_id)
            return self.async_create_entry(title="Options", data={})

        schema = vol.Schema({
            vol.Required(CONF_HOST, default=self.entry.data.get(CONF_HOST)): str,
            vol.Required(CONF_FRIENDLY_NAME, default=self.entry.title): str,
            vol.Required(CONF_SCAN_INTERVAL, default=self.entry.data.get(CONF_SCAN_INTERVAL, 30)): int,
            vol.Required(CONF_CREATE_NODE_CONTROLS, default=self.entry.options.get(CONF_CREATE_NODE_CONTROLS, False)): bool,
        })
        return self.async_show_form(step_id="init", data_schema=schema)
