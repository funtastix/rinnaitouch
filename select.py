from homeassistant.components.select import SelectEntity
from homeassistant.const import (
    CONF_HOST
)

from .const import (
    PRESET_HEAT,
    PRESET_COOL,
    PRESET_EVAP
)
from pyrinnaitouch import RinnaiSystem

import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data.get(CONF_HOST)
    async_add_entities([
        RinnaiSelectPresetEntity(ip_address, "Rinnai Touch Preset Select")
    ])
    return True

class RinnaiSelectPresetEntity(SelectEntity):

    def __init__(self, ip_address, name):
        self._host = ip_address
        self._system = RinnaiSystem.getInstance(ip_address)
        device_id = str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name
        self._system.SubscribeUpdates(self.system_updated)

    def system_updated(self):
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
        if self._system._status.heaterMode :
            return PRESET_HEAT
        elif self._system._status.coolingMode :
            return PRESET_COOL
        else:
            return PRESET_EVAP

    @property
    def options(self):
        """If the switch is currently on or off."""
        modes = []
        if self._system._status.hasHeater:
            modes.append(PRESET_HEAT)
        if self._system._status.hasCooling:
            modes.append(PRESET_COOL)
        if self._system._status.hasEvap:
            modes.append(PRESET_EVAP)
        return modes

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option == PRESET_COOL:
            await self._system.set_cooling_mode()
        if option == PRESET_HEAT:
            await self._system.set_heater_mode()
        if option == PRESET_EVAP:
            await self._system.set_evap_mode()
