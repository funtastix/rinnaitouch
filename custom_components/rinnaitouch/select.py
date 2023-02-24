"""Select to choose preset"""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST
)

from pyrinnaitouch import RinnaiSystem, RinnaiOperatingMode

from .const import (
    PRESET_AUTO,
    PRESET_MANUAL
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities): # pylint: disable=unused-argument
    """Set up the preset select entities."""
    ip_address = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME)
    if name == "":
        name = "Rinnai Touch"
    async_add_entities([
        RinnaiSelectPresetEntity(ip_address, name + " Preset Select")
    ])
    return True

class RinnaiSelectPresetEntity(SelectEntity):
    """A preset select entity."""

    def __init__(self, ip_address, name):
        self._host = ip_address
        self._system: RinnaiSystem = RinnaiSystem.get_instance(ip_address)
        device_id = str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name
        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        #this very infrequently fails on startup so wrapping in try except
        try:
            self.schedule_update_ha_state()
        except: #pylint: disable=bare-except
            pass

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
        if self._system.get_stored_status().unit_status.operating_mode == RinnaiOperatingMode.AUTO:
            return PRESET_AUTO
        return PRESET_MANUAL

    @property
    def options(self):
        """If the switch is currently on or off."""
        return [PRESET_MANUAL, PRESET_AUTO]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option == PRESET_AUTO:
            await self._system.set_unit_auto()
        else:
            await self._system.set_unit_manual()
