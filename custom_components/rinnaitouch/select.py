"""Select to choose preset"""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.const import (
    CONF_HOST
)

from pyrinnaitouch import RinnaiSystem

from .const import (
    PRESET_AUTO,
    PRESET_MANUAL
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities): # pylint: disable=unused-argument
    """Set up the preset select entities."""
    ip_address = entry.data.get(CONF_HOST)
    async_add_entities([
        RinnaiSelectPresetEntity(ip_address, "Rinnai Touch Preset Select")
    ])
    return True

class RinnaiSelectPresetEntity(SelectEntity):
    """A preset select entity."""

    def __init__(self, ip_address, name):
        self._host = ip_address
        self._system = RinnaiSystem.get_instance(ip_address)
        device_id = str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name
        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        self.async_write_ha_state()

    @property
    def name(self):
        """Name of the entity."""
        return self._attr_name

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:format-list-group"

    @property
    def current_option(self):
        """If the switch is currently on or off."""
        # pylint: disable=too-many-return-statements
        if self._system.get_stored_status().heater_mode :
            if self._system.get_stored_status().heater_status.auto_mode:
                return PRESET_AUTO
            return PRESET_MANUAL
        if self._system.get_stored_status().cooling_mode :
            if self._system.get_stored_status().cooling_status.auto_mode:
                return PRESET_AUTO
            return PRESET_MANUAL
        if self._system.get_stored_status().evap_mode :
            if self._system.get_stored_status().evap_status.auto_mode:
                return PRESET_AUTO
            return PRESET_MANUAL
        return PRESET_MANUAL

    @property
    def options(self):
        """If the switch is currently on or off."""
        return [PRESET_MANUAL, PRESET_AUTO]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self._system.get_stored_status().heater_mode :
            if option == PRESET_AUTO:
                await self._system.set_heater_auto()
            else:
                await self._system.set_heater_manual()
        if self._system.get_stored_status().cooling_mode :
            if option == PRESET_AUTO:
                await self._system.set_cooling_auto()
            else:
                await self._system.set_cooling_manual()
        if self._system.get_stored_status().evap_mode :
            if option == PRESET_AUTO:
                await self._system.set_evap_auto()
            else:
                await self._system.set_evap_manual()
