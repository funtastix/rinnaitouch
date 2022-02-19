from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers import Entity
from homeassistant.const import (
    CONF_HOST
)

from custom_components.rinnaitouch.pyrinnaitouch import RinnaiSystem

import logging

_LOGGER = logging.getLogger(__name__)

#TODO: Manual/Auto, Advance Period, CircFan
async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data.get(CONF_HOST)
    async_add_entities([
        RinnaiOnOffSwitch(ip_address, "Rinnai Touch On Off Switch"),
        RinnaiCoolingModeSwitch(ip_address, "Rinnai Touch Cooling Mode Switch"),
        RinnaiHeaterModeSwitch(ip_address, "Rinnai Touch Heater Mode Switch"),
        RinnaiEvapModeSwitch(ip_address, "Rinnai Touch Evap Mode Switch"),
        RinnaiZoneSwitch(ip_address, "A", "Rinnai Touch Zone A Switch"),
        RinnaiZoneSwitch(ip_address, "B", "Rinnai Touch Zone B Switch"),
        RinnaiZoneSwitch(ip_address, "C", "Rinnai Touch Zone C Switch"),
        RinnaiZoneSwitch(ip_address, "D", "Rinnai Touch Zone D Switch")
    ])
    return True

class RinnaiExtraEntity(Entity):

    def __init__(self, ip_address, name):
        self._host = ip_address
        self._system = RinnaiSystem.getInstance(ip_address)
        device_id = str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name

    @property
    def name(self):
        """Name of the entity."""
        return self._attr_name

class RinnaiOnOffSwitch(RinnaiExtraEntity, SwitchEntity):
    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._is_on = False

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:power"

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._system._status.systemOn

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        #turn whatever the preset is on and put it into manual mode
        if self._system._status.coolingMode:
            await self._system.turn_cooling_on()
        elif self._system._status.heaterMode:
            await self._system.turn_heater_on()
        elif self._system._status.evapMode:
            await self._system.turn_evap_on()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        #turn whatever the preset is off
        if self._system._status.coolingMode:
            await self._system.turn_cooling_off()
        elif self._system._status.heaterMode:
            await self._system.turn_heater_off()
        elif self._system._status.evapMode:
            await self._system.turn_evap_off()

class RinnaiCoolingModeSwitch(RinnaiExtraEntity, SwitchEntity):

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._is_on = False

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on():
            return "mdi:snowflake"
        else:
            return "mdi:snowflake-off"

    @property
    def is_on(self):
        return self._system._status.coolingMode

    async def async_turn_on(self, **kwargs):
        if not self._system._status.coolingMode:
            await self._system.set_cooling_mode()

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        pass

class RinnaiHeaterModeSwitch(RinnaiExtraEntity, SwitchEntity):

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._is_on = False

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on():
            return "mdi:fire"
        else:
            return "mdi:fire-off"

    @property
    def is_on(self):
        return self._system._status.heaterMode

    async def async_turn_on(self, **kwargs):
        if not self._system._status.heaterMode:
            await self._system.set_heating_mode()

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        pass

class RinnaiEvapModeSwitch(RinnaiExtraEntity, SwitchEntity):

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._is_on = False

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on():
            return "mdi:water-outline"
        else:
            return "mdi:water-off-outline"

    @property
    def is_on(self):
        return self._system._status.evapMode

    async def async_turn_on(self, **kwargs):
        if not self._system._status.evapMode:
            await self._system.set_evap_mode()

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        pass

class RinnaiZoneSwitch(RinnaiExtraEntity, SwitchEntity):

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, name)
        self._is_on = False
        self._attr_zone = zone
        device_id = str.lower(self.__class__.__name__) + "_" + zone + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on():
            return "mdi:home-thermometer"
        else:
            return "mdi:home-thermometer-outline"

    @property
    def available(self):
        if self._system._status.heaterMode:
            return self._attr_zone in self._system._status.heaterStatus.zones
        elif self._system._status.coolingMode:
            return self._attr_zone in self._system._status.coolingStatus.zones
        return false

    @property
    def is_on(self):
        if self._system._status.heaterMode:
            return getattr(self._system._status.heaterStatus, "zone" + self._attr_zone)
        elif self._system._status.coolingMode:
            return getattr(self._system._status.coolingStatus, "zone" + self._attr_zone)
        return false

    async def async_turn_on(self, **kwargs):
        if self._system._status.heaterMode:
            await self._system.turn_heater_zone_on(self._attr_zone)
        elif self._system._status.coolingMode:
            await self._system.turn_cooling_zone_on(self._attr_zone)

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        if self._system._status.heaterMode:
            await self._system.turn_heater_zone_off(self._attr_zone)
        elif self._system._status.coolingMode:
            await self._system.turn_cooling_zone_off(self._attr_zone)
