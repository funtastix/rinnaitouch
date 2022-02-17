# pylint: skip-file
"""Config flow for rinnai-brivis-wifi."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.data_entry_flow import AbortFlow

from .const import DEFAULT_NAME, DOMAIN
from custom_components.rinnaitouch.pyrinnaitouch import RinnaiSystem

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str
    }
)


class RinnaiTouchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rinnai Touch."""

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            system = RinnaiSystem.getInstance(user_input[CONF_HOST])
            device_id = "rinnaitouch_" + str.replace(user_input[CONF_HOST], ".", "_")
            try:
               status = await system.GetStatus() 
            except AbortFlow:
                return self.async_abort(reason="single_instance_allowed")
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )