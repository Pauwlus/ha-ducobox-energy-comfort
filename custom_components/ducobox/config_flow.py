
from typing import Any, Dict
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import area_registry as ar
from .const import DOMAIN, CONF_HOST, CONF_FRIENDLY_NAME, CONF_SCAN_INTERVAL, DEFAULT_NAME, DEFAULT_SCAN_INTERVAL, OPTION_AREAS, NODE_RANGE_START, NODE_RANGE_END
from .api import DucoClient

class DucoBoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input: Dict[str, Any] | None = None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            name = user_input.get(CONF_FRIENDLY_NAME) or DEFAULT_NAME
            scan_interval = int(user_input.get(CONF_SCAN_INTERVAL) or DEFAULT_SCAN_INTERVAL)
            client = DucoClient(self.hass, host)
            try:
                nodes = await client.discover_nodes_by_range(NODE_RANGE_START, NODE_RANGE_END)
                self._host = host; self._name = name; self._scan_interval = scan_interval; self._nodes = nodes
                return await self.async_step_area_mapping()
            except Exception:
                errors["base"] = "cannot_connect"
        data_schema = vol.Schema({vol.Required(CONF_HOST): str, vol.Optional(CONF_FRIENDLY_NAME, default=DEFAULT_NAME): str, vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int})
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
    async def async_step_area_mapping(self, user_input: Dict[str, Any] | None = None):
        area_reg = ar.async_get(self.hass); areas = {a.id: a.name for a in area_reg.async_list_areas()}
        if user_input is not None:
            areas_map = {}
            for n in self._nodes:
                key = f"{n.get('devtype')}-{n.get('node')}"; sel = user_input.get(key)
                if sel: areas_map[key] = sel
            data = {CONF_HOST: self._host, CONF_FRIENDLY_NAME: self._name, CONF_SCAN_INTERVAL: self._scan_interval}
            options = {OPTION_AREAS: areas_map}
            return self.async_create_entry(title=self._name, data=data, options=options)
        schema_dict = {}
        for n in self._nodes:
            key = f"{n.get('devtype')}-{n.get('node')}"
            schema_dict[vol.Optional(key)] = vol.In(areas)
        return self.async_show_form(step_id="area_mapping", data_schema=vol.Schema(schema_dict))
