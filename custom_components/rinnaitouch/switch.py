"""Switches for Auto/Manual, On/Off, Mode, Water Pump and Fan"""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import Entity
from homeassistant.const import CONF_NAME, CONF_HOST

from pyrinnaitouch import RinnaiSystem, RinnaiSystemMode, RinnaiCapabilities, RinnaiOperatingMode

from .const import CONF_ZONE_A, CONF_ZONE_B, CONF_ZONE_C, CONF_ZONE_D, CONF_ZONE_COMMON

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass, entry, async_add_entities
):  # pylint: disable=unused-argument
    """Set up the switch entities."""
    ip_address = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME)
    if name == "":
        name = "Rinnai Touch"
    async_add_entities(
        [
            RinnaiOnOffSwitch(ip_address, name + " On Off Switch"),
            RinnaiCoolingModeSwitch(ip_address, name + " Cooling Mode Switch"),
            RinnaiHeaterModeSwitch(ip_address, name + " Heater Mode Switch"),
            RinnaiEvapModeSwitch(ip_address, name + " Evap Mode Switch"),
            RinnaiWaterpumpSwitch(ip_address, name + " Water Pump Switch"),
            RinnaiEvapFanSwitch(ip_address, name + " Evap Fan Switch"),
            RinnaiCircFanSwitch(ip_address, name + " Circulation Fan Switch"),
            RinnaiAutoSwitch(ip_address, name + " Auto Switch"),
        ]
    )
    if entry.data.get(CONF_ZONE_A):
        async_add_entities(
            [
                RinnaiZoneSwitch(ip_address, "A", name + " Zone A Switch"),
                RinnaiZoneAutoSwitch(ip_address, "A", name + " Zone A Auto Switch"),
            ]
        )
    if entry.data.get(CONF_ZONE_B):
        async_add_entities(
            [
                RinnaiZoneSwitch(ip_address, "B", name + " Zone B Switch"),
                RinnaiZoneAutoSwitch(ip_address, "B", name + " Zone B Auto Switch"),
            ]
        )
    if entry.data.get(CONF_ZONE_C):
        async_add_entities(
            [
                RinnaiZoneSwitch(ip_address, "C", name + " Zone C Switch"),
                RinnaiZoneAutoSwitch(ip_address, "C", name + " Zone C Auto Switch"),
            ]
        )
    if entry.data.get(CONF_ZONE_D):
        async_add_entities(
            [
                RinnaiZoneSwitch(ip_address, "D", name + " Zone D Switch"),
                RinnaiZoneAutoSwitch(ip_address, "D", name + " Zone D Auto Switch"),
            ]
        )
    if entry.data.get(CONF_ZONE_COMMON):
        async_add_entities(
            [
                RinnaiZoneSwitch(ip_address, "U", name + " Common Zone Switch"),
                RinnaiZoneAutoSwitch(
                    ip_address, "U", name + " Common Zone Auto Switch"
                ),
            ]
        )
    return True


class RinnaiExtraEntity(Entity):
    """Base entity with a name and system update capability."""

    def __init__(self, ip_address, name):
        self._host = ip_address
        self._system = RinnaiSystem.get_instance(ip_address)
        device_id = (
            str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")
        )

        self._attr_unique_id = device_id
        self._attr_name = name
        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        # this very infrequently fails on startup so wrapping in try except
        try:
            self.schedule_update_ha_state()
        except:  # pylint: disable=bare-except
            pass

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
        return self._system.get_stored_status().system_on

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        # turn whatever the preset is on and put it into manual mode
        if self._system.get_stored_status().mode == RinnaiSystemMode.COOLING:
            await self._system.turn_cooling_on()
        elif self._system.get_stored_status().mode == RinnaiSystemMode.HEATING:
            await self._system.turn_heater_on()
        elif self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
            await self._system.turn_evap_on()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        # turn whatever the preset is off
        if self._system.get_stored_status().mode == RinnaiSystemMode.COOLING:
            await self._system.turn_cooling_off()
        elif self._system.get_stored_status().mode == RinnaiSystemMode.HEATING:
            await self._system.turn_heater_off()
        elif self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
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
        return self._system.get_stored_status().mode == RinnaiSystemMode.COOLING

    @property
    def available(self):
        return RinnaiCapabilities.COOLER in self._system.get_stored_status().capabilities

    async def async_turn_on(self, **kwargs):
        if not self._system.get_stored_status().mode == RinnaiSystemMode.COOLING:
            await self._system.set_cooling_mode()

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        pass  # pylint: disable=unnecessary-pass


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
        return self._system.get_stored_status().mode == RinnaiSystemMode.HEATING

    @property
    def available(self):
        return RinnaiCapabilities.HEATER in self._system.get_stored_status().capabilities

    async def async_turn_on(self, **kwargs):
        if not self._system.get_stored_status().mode == RinnaiSystemMode.HEATING:
            await self._system.set_heater_mode()

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        pass  # pylint: disable=unnecessary-pass


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
        return self._system.get_stored_status().mode == RinnaiSystemMode.EVAP

    @property
    def available(self):
        return RinnaiCapabilities.EVAP in self._system.get_stored_status().capabilities

    async def async_turn_on(self, **kwargs):
        if not self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
            await self._system.set_evap_mode()

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        pass  # pylint: disable=unnecessary-pass


class RinnaiZoneSwitch(RinnaiExtraEntity, SwitchEntity):
    """A switch to turn a zone on or off."""

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, name)
        self._is_on = False
        self._attr_zone = zone
        device_id = (
            str.lower(self.__class__.__name__)
            + "_"
            + zone
            + str.replace(ip_address, ".", "_")
        )

        self._attr_unique_id = device_id

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:home-thermometer"
        return "mdi:home-thermometer-outline"

    @property
    def available(self):
        return self._attr_zone in self._system.get_stored_status().unit_status.zones.keys()

    @property
    def is_on(self):
        if self._attr_zone not in self._system.get_stored_status().unit_status.zones.keys():
            return False
        return self._system.get_stored_status().unit_status.zones[self._attr_zone].user_enabled \
            or int(self._system.get_stored_status().unit_status.zones[self._attr_zone].set_temp) > 7

    async def async_turn_on(self, **kwargs):
        if self._system.get_stored_status().mode == RinnaiSystemMode.COOLING:
            await self._system.turn_unit_zone_on(self._attr_zone)
        elif self._system.get_stored_status().mode == RinnaiSystemMode.HEATING:
            await self._system.turn_unit_zone_on(self._attr_zone)
        elif self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
            await self._system.turn_evap_zone_on(self._attr_zone)

    async def async_turn_off(self, **kwargs):
        """Turning it off does nothing"""
        if self._system.get_stored_status().mode == RinnaiSystemMode.COOLING:
            await self._system.turn_unit_zone_on(self._attr_zone)
        elif self._system.get_stored_status().mode == RinnaiSystemMode.HEATING:
            await self._system.turn_unit_zone_on(self._attr_zone)
        elif self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
            await self._system.turn_evap_zone_on(self._attr_zone)


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
        state = self._system.get_stored_status()
        if state.mode == RinnaiSystemMode.EVAP \
            and state.unit_status.is_on \
            and state.unit_status.operating_mode == RinnaiOperatingMode.MANUAL:
            return True
        return False

    @property
    def is_on(self):
        if self.available:
            return self._system.get_stored_status().unit_status.water_pump_on
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
        state = self._system.get_stored_status()
        if state.mode == RinnaiSystemMode.EVAP \
            and state.unit_status.is_on \
            and state.unit_status.operating_mode == RinnaiOperatingMode.MANUAL:
            return True
        return False

    @property
    def is_on(self):
        if self.available:
            return self._system.get_stored_status().unit_status.fan_on
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
        if self._system.get_stored_status().system_on:
            return True
        return False

    @property
    def is_on(self):
        if self.available:
            return self._system.get_stored_status().unit_status.operating_mode == \
                RinnaiOperatingMode.AUTO
        return False

    async def async_turn_on(self, **kwargs):
        if self.available:
            if self._system.get_stored_status().mode \
                in (RinnaiSystemMode.COOLING, RinnaiSystemMode.HEATING):
                await self._system.set_unit_auto()
            if self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
                await self._system.set_evap_auto()

    async def async_turn_off(self, **kwargs):
        if self.available:
            if self._system.get_stored_status().mode \
                in (RinnaiSystemMode.COOLING, RinnaiSystemMode.HEATING):
                await self._system.set_unit_manual()
            if self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
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
            self._system.get_stored_status().mode \
                in (RinnaiSystemMode.COOLING, RinnaiSystemMode.HEATING)
        ):
            return False
        if not self._system.get_stored_status().system_on:
            return True
        if (
            not self._system.get_stored_status().unit_status.is_on
        ):
            return True
        return False

    @property
    def is_on(self):
        if self.available:
            return self._system.get_stored_status().unit_status.circulation_fan_on
        return False

    async def async_turn_on(self, **kwargs):
        if self.available:
            await self._system.turn_unit_fan_only()

    async def async_turn_off(self, **kwargs):
        if self.available:
            await self._system.turn_unit_off()


class RinnaiZoneAutoSwitch(RinnaiExtraEntity, SwitchEntity):
    """A switch to change to auto or manual operation in a zone."""

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, name)
        self._is_on = False
        self._attr_zone = zone
        device_id = (
            str.lower(self.__class__.__name__)
            + "_"
            + zone
            + str.replace(ip_address, ".", "_")
        )

        self._attr_unique_id = device_id

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.is_on:
            return "mdi:calendar-sync"
        return "mdi:sync"

    @property
    def available(self):
        if self._system.get_stored_status().system_on\
            and self._attr_zone in self._system.get_stored_status().unit_status.zones.keys():
            return self._system.get_stored_status().unit_status.operating_mode == \
                RinnaiOperatingMode.AUTO
        return False

    @property
    def is_on(self):
        if self.available:
            return (
                self._system.get_stored_status()
                .unit_status.zones[self._attr_zone]
                .auto_mode
            )
        return False

    async def async_turn_on(self, **kwargs):
        if self.available:
            if self._system.get_stored_status().mode \
                in (RinnaiSystemMode.COOLING, RinnaiSystemMode.HEATING):
                await self._system.set_unit_zone_auto(self._attr_zone)
            else:
                await self._system.set_evap_zone_auto(self._attr_zone)

    async def async_turn_off(self, **kwargs):
        if self.available:
            if self._system.get_stored_status().mode \
                in (RinnaiSystemMode.COOLING, RinnaiSystemMode.HEATING):
                await self._system.set_unit_zone_manual(self._attr_zone)
            else:
                await self._system.set_evap_zone_manual(self._attr_zone)
