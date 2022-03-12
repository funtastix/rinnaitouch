"""Switches for Auto/Manual, On/Off, Mode, Water Pump and Fan"""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    CONF_HOST
)

from pyrinnaitouch import RinnaiSystem

from .const import (
    CONF_ZONE_A,
    CONF_ZONE_B,
    CONF_ZONE_C,
    CONF_ZONE_D
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities): # pylint: disable=unused-argument
    """Set up the switch entities."""
    ip_address = entry.data.get(CONF_HOST)
    async_add_entities([
        RinnaiOnOffSwitch(ip_address, "Rinnai Touch On Off Switch"),
        RinnaiCoolingModeSwitch(ip_address, "Rinnai Touch Cooling Mode Switch"),
        RinnaiHeaterModeSwitch(ip_address, "Rinnai Touch Heater Mode Switch"),
        RinnaiEvapModeSwitch(ip_address, "Rinnai Touch Evap Mode Switch"),
        RinnaiWaterpumpSwitch(ip_address, "Rinnai Touch Water Pump Switch"),
        RinnaiEvapFanSwitch(ip_address, "Rinnai Touch Evap Fan Switch"),
        RinnaiCircFanSwitch(ip_address, "Rinnai Touch Circulation Fan Switch"),
        RinnaiAutoSwitch(ip_address, "Rinnai Touch Auto Switch")
    ])
    if entry.data.get(CONF_ZONE_A):
        async_add_entities([
            RinnaiZoneSwitch(ip_address, "A", "Rinnai Touch Zone A Switch"),
            RinnaiZoneAutoSwitch(ip_address, "A", "Rinnai Touch Zone A Auto Switch")
        ])
    if entry.data.get(CONF_ZONE_B):
        async_add_entities([
            RinnaiZoneSwitch(ip_address, "B", "Rinnai Touch Zone B Switch"),
            RinnaiZoneAutoSwitch(ip_address, "B", "Rinnai Touch Zone B Auto Switch")
        ])
    if entry.data.get(CONF_ZONE_C):
        async_add_entities([
            RinnaiZoneSwitch(ip_address, "C", "Rinnai Touch Zone C Switch"),
            RinnaiZoneAutoSwitch(ip_address, "C", "Rinnai Touch Zone C Auto Switch")
        ])
    if entry.data.get(CONF_ZONE_D):
        async_add_entities([
            RinnaiZoneSwitch(ip_address, "D", "Rinnai Touch Zone D Switch"),
            RinnaiZoneAutoSwitch(ip_address, "D", "Rinnai Touch Zone D Auto Switch")
        ])
    return True

class RinnaiExtraEntity(Entity):
    """Base entity with a name and system update capability."""

    def __init__(self, ip_address, name):
        self._host = ip_address
        self._system = RinnaiSystem.getInstance(ip_address)
        device_id = str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name
        self._system.SubscribeUpdates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        self.async_write_ha_state()

    @property
    def name(self):
        """Name of the entity."""
        return self._attr_name

class RinnaiOnOffSwitch(RinnaiExtraEntity, SwitchEntity):
    """Main on/off switch for the system."""

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
        return self._system.GetOfflineStatus().systemOn

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        #turn whatever the preset is on and put it into manual mode
        if self._system.GetOfflineStatus().coolingMode:
            await self._system.turn_cooling_on()
        elif self._system.GetOfflineStatus().heaterMode:
            await self._system.turn_heater_on()
        elif self._system.GetOfflineStatus().evapMode:
            await self._system.turn_evap_on()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        #turn whatever the preset is off
        if self._system.GetOfflineStatus().coolingMode:
            await self._system.turn_cooling_off()
        elif self._system.GetOfflineStatus().heaterMode:
            await self._system.turn_heater_off()
        elif self._system.GetOfflineStatus().evapMode:
            await self._system.turn_evap_off()

class RinnaiCoolingModeSwitch(RinnaiExtraEntity, SwitchEntity):
    """A switch to turn the system into cooling mode."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._is_on = False

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:snowflake"
        return "mdi:snowflake-off"

    @property
    def is_on(self):
        return self._system.GetOfflineStatus().coolingMode

    @property
    def available(self):
        return self._system.GetOfflineStatus().hasCooling

    async def async_turn_on(self, **kwargs):
        if not self._system.GetOfflineStatus().coolingMode:
            await self._system.set_cooling_mode()

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        pass # pylint: disable=unnecessary-pass

class RinnaiHeaterModeSwitch(RinnaiExtraEntity, SwitchEntity):
    """A switch to turn the system into heater mode."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._is_on = False

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:fire"
        return "mdi:fire-off"

    @property
    def is_on(self):
        return self._system.GetOfflineStatus().heaterMode

    @property
    def available(self):
        return self._system.GetOfflineStatus().hasHeater

    async def async_turn_on(self, **kwargs):
        if not self._system.GetOfflineStatus().heaterMode:
            await self._system.set_heater_mode()

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        pass # pylint: disable=unnecessary-pass

class RinnaiEvapModeSwitch(RinnaiExtraEntity, SwitchEntity):
    """A switch to turn the system into evap mode."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._is_on = False

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:water-outline"
        return "mdi:water-off-outline"

    @property
    def is_on(self):
        return self._system.GetOfflineStatus().evapMode

    @property
    def available(self):
        return self._system.GetOfflineStatus().hasEvap

    async def async_turn_on(self, **kwargs):
        if not self._system.GetOfflineStatus().evapMode:
            await self._system.set_evap_mode()

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        pass # pylint: disable=unnecessary-pass

class RinnaiZoneSwitch(RinnaiExtraEntity, SwitchEntity):
    """A switch to turn a zone on or off."""

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, name)
        self._is_on = False
        self._attr_zone = zone
        device_id = str.lower(self.__class__.__name__) + "_" \
            + zone + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:home-thermometer"
        return "mdi:home-thermometer-outline"

    @property
    def available(self):
        if self._system.GetOfflineStatus().heaterMode:
            return self._attr_zone in self._system.GetOfflineStatus().heaterStatus.zones
        if self._system.GetOfflineStatus().coolingMode:
            return self._attr_zone in self._system.GetOfflineStatus().coolingStatus.zones
        if self._system.GetOfflineStatus().evapMode:
            return self._attr_zone in self._system.GetOfflineStatus().evapStatus.zones
        return False

    @property
    def is_on(self):
        if self._system.GetOfflineStatus().heaterMode:
            return getattr(self._system.GetOfflineStatus().heaterStatus, "zone" + self._attr_zone)
        if self._system.GetOfflineStatus().coolingMode:
            return getattr(self._system.GetOfflineStatus().coolingStatus, "zone" + self._attr_zone)
        if self._system.GetOfflineStatus().evapMode:
            return getattr(self._system.GetOfflineStatus().evapStatus, "zone" + self._attr_zone)
        return False

    async def async_turn_on(self, **kwargs):
        if self._system.GetOfflineStatus().heaterMode:
            await self._system.turn_heater_zone_on(self._attr_zone)
        elif self._system.GetOfflineStatus().coolingMode:
            await self._system.turn_cooling_zone_on(self._attr_zone)
        elif self._system.GetOfflineStatus().evapMode:
            await self._system.turn_evap_zone_on(self._attr_zone)

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        if self._system.GetOfflineStatus().heaterMode:
            await self._system.turn_heater_zone_off(self._attr_zone)
        elif self._system.GetOfflineStatus().coolingMode:
            await self._system.turn_cooling_zone_off(self._attr_zone)
        elif self._system.GetOfflineStatus().evapMode:
            await self._system.turn_evap_zone_off(self._attr_zone)

class RinnaiWaterpumpSwitch(RinnaiExtraEntity, SwitchEntity):
    """A switch to turn the waterpump on or off in evap mode."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._is_on = False

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:water-check-outline"
        return "mdi:water-remove-outline"

    @property
    def available(self):
        if (
            self._system.GetOfflineStatus().evapMode
            and self._system.GetOfflineStatus().evapStatus.evapOn
            and self._system.GetOfflineStatus().evapStatus.manualMode
        ):
            return True
        return False

    @property
    def is_on(self):
        if self.available:
            return self._system.GetOfflineStatus().evapStatus.waterPumpOn
        return False

    async def async_turn_on(self, **kwargs):
        if self.available:
            await self._system.turn_evap_pump_on()

    async def async_turn_off(self, **kwargs):
        if self.available:
            await self._system.turn_evap_pump_off()

class RinnaiEvapFanSwitch(RinnaiExtraEntity, SwitchEntity):
    """A switch to turn the fan on or off in evap mode."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._is_on = False

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:fan"
        return "mdi:fan-off"

    @property
    def available(self):
        if (
            self._system.GetOfflineStatus().evapMode
            and self._system.GetOfflineStatus().evapStatus.evapOn
            and self._system.GetOfflineStatus().evapStatus.manualMode
        ):
            return True
        return False

    @property
    def is_on(self):
        if self.available:
            return self._system.GetOfflineStatus().evapStatus.FanOn
        return False

    async def async_turn_on(self, **kwargs):
        if self.available:
            await self._system.turn_evap_fan_on()

    async def async_turn_off(self, **kwargs):
        if self.available:
            await self._system.turn_evap_fan_off()

class RinnaiAutoSwitch(RinnaiExtraEntity, SwitchEntity):
    """A switch to change between auto and manual operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._is_on = False

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:calendar-sync"
        return "mdi:sync"

    @property
    def available(self):
        if self._system.GetOfflineStatus().systemOn:
            return True
        return False

    @property
    def is_on(self):
        if self.available:
            if self._system.GetOfflineStatus().coolingMode:
                return self._system.GetOfflineStatus().coolingStatus.autoMode
            if self._system.GetOfflineStatus().heaterMode:
                return self._system.GetOfflineStatus().heaterStatus.autoMode
            if self._system.GetOfflineStatus().evapMode:
                return self._system.GetOfflineStatus().evapStatus.autoMode
        return False

    async def async_turn_on(self, **kwargs):
        if self.available:
            if self._system.GetOfflineStatus().coolingMode:
                await self._system.set_cooling_auto()
            if self._system.GetOfflineStatus().heaterMode:
                await self._system.set_heater_auto()
            if self._system.GetOfflineStatus().evapMode:
                await self._system.set_evap_auto()

    async def async_turn_off(self, **kwargs):
        if self.available:
            if self._system.GetOfflineStatus().coolingMode:
                await self._system.set_cooling_manual()
            if self._system.GetOfflineStatus().heaterMode:
                await self._system.set_heater_manual()
            if self._system.GetOfflineStatus().evapMode:
                await self._system.set_evap_manual()

class RinnaiCircFanSwitch(RinnaiExtraEntity, SwitchEntity):
    """A switch to turn the circ fan on or off in heater or cooling mode when the system is off."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._is_on = False

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:fan"
        return "mdi:fan-off"

    @property
    def available(self):
        if not (
            self._system.GetOfflineStatus().coolingMode
            or self._system.GetOfflineStatus().heaterMode
        ):
            return False
        if not self._system.GetOfflineStatus().systemOn:
            return True
        if (
            not self._system.GetOfflineStatus().heaterStatus.heaterOn
            and not self._system.GetOfflineStatus().coolingStatus.coolingOn
        ):
            return True
        return False

    @property
    def is_on(self):
        if self.available:
            if self._system.GetOfflineStatus().coolingMode:
                return self._system.GetOfflineStatus().coolingStatus.circulationFanOn
            if self._system.GetOfflineStatus().heaterMode:
                return self._system.GetOfflineStatus().heaterStatus.circulationFanOn
        return False

    async def async_turn_on(self, **kwargs):
        if self.available:
            if self._system.GetOfflineStatus().coolingMode:
                await self._system.turn_cooling_fan_only()
            if self._system.GetOfflineStatus().heaterMode:
                await self._system.turn_heater_fan_only()

    async def async_turn_off(self, **kwargs):
        if self.available:
            if self._system.GetOfflineStatus().coolingMode:
                await self._system.turn_cooling_off()
            if self._system.GetOfflineStatus().heaterMode:
                await self._system.turn_heater_off()

class RinnaiZoneAutoSwitch(RinnaiExtraEntity, SwitchEntity):
    """A switch to change to auto or manual operation in a zone."""

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, name)
        self._is_on = False
        self._attr_zone = zone
        device_id = str.lower(self.__class__.__name__) + "_" \
            + zone + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:calendar-sync"
        return "mdi:sync"

    @property
    def available(self):
        if self._system.GetOfflineStatus().systemOn:
            if self._system.GetOfflineStatus().coolingMode:
                return self._system.GetOfflineStatus().coolingStatus.autoMode
            if self._system.GetOfflineStatus().heaterMode:
                return self._system.GetOfflineStatus().heaterStatus.autoMode
            if self._system.GetOfflineStatus().evapMode:
                return self._system.GetOfflineStatus().evapStatus.autoMode
            return True
        return False

    @property
    def is_on(self):
        if self.available:
            if self._system.GetOfflineStatus().heaterMode:
                return getattr(
                            self._system.GetOfflineStatus().heaterStatus,
                            "zone" + self._attr_zone + "Auto"
                        )
            if self._system.GetOfflineStatus().coolingMode:
                return getattr(
                            self._system.GetOfflineStatus().coolingStatus,
                            "zone" + self._attr_zone + "Auto"
                        )
            if self._system.GetOfflineStatus().evapMode:
                return getattr(
                            self._system.GetOfflineStatus().evapStatus,
                            "zone" + self._attr_zone + "Auto"
                        )
        return False

    async def async_turn_on(self, **kwargs):
        if self.available:
            if self._system.GetOfflineStatus().heaterMode:
                await self._system.set_heater_zone_auto(self._attr_zone)
            elif self._system.GetOfflineStatus().coolingMode:
                await self._system.set_cooling_zone_auto(self._attr_zone)
            elif self._system.GetOfflineStatus().evapMode:
                await self._system.set_evap_zone_auto(self._attr_zone)

    async def async_turn_off(self, **kwargs):
        if self.available:
            if self._system.GetOfflineStatus().heaterMode:
                await self._system.set_heater_zone_manual(self._attr_zone)
            elif self._system.GetOfflineStatus().coolingMode:
                await self._system.set_cooling_zone_manual(self._attr_zone)
            elif self._system.GetOfflineStatus().evapMode:
                await self._system.set_evap_zone_manual(self._attr_zone)
