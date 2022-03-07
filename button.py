from homeassistant.components.button import ButtonEntity
from homeassistant.const import (
    CONF_HOST
)

from .const import (
    CONF_ZONE_A,
    CONF_ZONE_B,
    CONF_ZONE_C,
    CONF_ZONE_D
)

from custom_components.rinnaitouch.pyrinnaitouch import RinnaiSystem

import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data.get(CONF_HOST)
    async_add_entities([RinnaiAdvanceButton(ip_address, "Rinnai Touch Advance Button")])
    if entry.data.get(CONF_ZONE_A):
        async_add_entities([RinnaiZoneAdvanceButton(ip_address, "A", "Rinnai Touch Zone A Advance Button")])
    if entry.data.get(CONF_ZONE_B):
        async_add_entities([RinnaiZoneAdvanceButton(ip_address, "B", "Rinnai Touch Zone B Advance Button")])
    if entry.data.get(CONF_ZONE_C):
        async_add_entities([RinnaiZoneAdvanceButton(ip_address, "C", "Rinnai Touch Zone C Advance Button")])
    if entry.data.get(CONF_ZONE_D):
        async_add_entities([RinnaiZoneAdvanceButton(ip_address, "D", "Rinnai Touch Zone D Advance Button")])
    return True

class RinnaiButtonEntity(ButtonEntity):

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

class RinnaiAdvanceButton(RinnaiButtonEntity):

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:location-exit"

    async def async_press(self) -> None:
        """Handle the button press."""
        if self._system._status.coolingMode:
            await self._system.cooling_advance()
        elif self._system._status.heaterMode:
            await self._system.heater_advance()

class RinnaiZoneAdvanceButton(RinnaiButtonEntity):

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, name)
        self._attr_zone = zone
        device_id = str.lower(self.__class__.__name__) + "_" + zone + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:location-exit"

    @property
    def available(self):
        if self._system._status.heaterMode:
            return self._attr_zone in self._system._status.heaterStatus.zones
        elif self._system._status.coolingMode:
            return self._attr_zone in self._system._status.coolingStatus.zones
        return False

    async def async_press(self) -> None:
        """Handle the button press."""
        if self._system._status.coolingMode:
            await self._system.cooling_zone_advance(self._attr_zone)
        elif self._system._status.heaterMode:
            await self._system.heater_zone_advance(self._attr_zone)
