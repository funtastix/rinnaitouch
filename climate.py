"""Support for the Rinnai Touch Controller.

To support the controller and make it work with the HA climate entity,these are the mappings:

HVAC modes:
HVAC_MODE_HEAT_COOL -> Manual Mode (all operating modes)
HVAC_MODE_AUTO -> Auto Mode (all operating modes)
HVAC_MODE_OFF -> Unit Off (any operating mode)
HVAC_MODE_FAN_ONLY - Only circulation fan is on while in heating or cooling mode

PRESET modes:
PRESET_COOL -> Cooling mode
PRESET_HEAT -> Heater mode
PRESET_EVAP -> Evap mode

"""
from __future__ import annotations
from datetime import timedelta

import logging

from pyrinnaitouch import RinnaiSystem

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_PRESET_MODE
)
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    ATTR_TEMPERATURE
)
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from .const import (
    PRESET_HEAT,
    PRESET_COOL,
    PRESET_EVAP,
    CONF_TEMP_SENSOR,
#    CONF_TEMP_SENSOR_A,
#    CONF_TEMP_SENSOR_B,
#    CONF_TEMP_SENSOR_C,
#    CONF_TEMP_SENSOR_D,
    CONF_ZONE_A,
    CONF_ZONE_B,
    CONF_ZONE_C,
    CONF_ZONE_D
)

SUPPORT_FLAGS_MAIN = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE
SUPPORT_FLAGS_ZONE = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up climate entities."""
    ip_address = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME)
    temperature_entity = entry.data.get(CONF_TEMP_SENSOR)
    temperature_entity_a = None #entry.data.get(CONF_TEMP_SENSOR_A)
    temperature_entity_b = None #entry.data.get(CONF_TEMP_SENSOR_B)
    temperature_entity_c = None #entry.data.get(CONF_TEMP_SENSOR_C)
    temperature_entity_d = None #entry.data.get(CONF_TEMP_SENSOR_D)
    async_add_entities([RinnaiTouch(hass, ip_address, name, temperature_entity)])
    if entry.data.get(CONF_ZONE_A):
        async_add_entities([RinnaiTouchZone(hass, ip_address, name, "A", temperature_entity_a)])
    if entry.data.get(CONF_ZONE_B):
        async_add_entities([RinnaiTouchZone(hass, ip_address, name, "B", temperature_entity_b)])
    if entry.data.get(CONF_ZONE_C):
        async_add_entities([RinnaiTouchZone(hass, ip_address, name, "C", temperature_entity_c)])
    if entry.data.get(CONF_ZONE_D):
        async_add_entities([RinnaiTouchZone(hass, ip_address, name, "D", temperature_entity_d)])
    return True

class RinnaiTouch(ClimateEntity):
    """Main climate entity for the unit."""

    # pylint: disable=too-many-instance-attributes,too-many-public-methods
    def __init__(self, hass, ip_address, name = "Rinnai Touch", temperature_entity = None):
        self._host = ip_address
        _LOGGER.info("Set up RinnaiTouch entity %s", ip_address)
        self._system = RinnaiSystem.get_instance(ip_address)
        device_id = "rinnaitouch_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name

        self._hass = hass
        self._temerature_entity_name = temperature_entity
        self._sensor_temperature = 0
        self.update_external_temperature()

        self._support_flags = SUPPORT_FLAGS_MAIN

        self._TEMPERATURE_STEP = 1
        self._TEMPERATURE_LIMITS = {"min": 8, "max": 30}
        self._COMFORT_LIMITS = {"min": 19, "max": 34}
        self._FAN_LIMITS = {"min": 0, "max": 16}
        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        self.async_write_ha_state()

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._attr_name

    @property
    def unique_id(self):
        """Return the unique id for this heater."""
        return self._attr_unique_id

    @property
    def device_info(self):
        """Return device information about this heater."""
        return {
            "connections": {(CONNECTION_NETWORK_MAC, self._host)},
            "identifiers": {("Rinnai Touch", self.unique_id)},
            "model": "Rinnai Touch Wifi",
            "name": self.name,
            "manufacturer": "Rinnai/Brivis",
        }

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        hvac_mode = self.hvac_mode

        if hvac_mode == HVAC_MODE_OFF:
            return "mdi:hvac-off"

        if hvac_mode == HVAC_MODE_FAN_ONLY:
            return "mdi:fan"

        preset_mode = self.preset_mode

        if preset_mode == PRESET_COOL:
            return "mdi:snowflake"
        if preset_mode == PRESET_EVAP:
            return "mdi:snowflake-melt"
        if preset_mode == PRESET_HEAT:
            return "mdi:fire"

        return "mdi:hvac"

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._system.get_stored_status().temp_unit == RinnaiSystem.TEMP_FAHRENHEIT:
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        # pylint: disable=too-many-return-statements
        if self.hvac_mode == HVAC_MODE_OFF:
            return 0

        if self.preset_mode == PRESET_COOL:
            if self.hvac_mode == HVAC_MODE_FAN_ONLY:
                return self._system.get_stored_status().cooling_status.fan_speed
            return self._system.get_stored_status().cooling_status.set_temp
        if self.preset_mode == PRESET_EVAP:
            if self.hvac_mode == HVAC_MODE_AUTO:
                return int(self._system.get_stored_status().evap_status.comfort)
            if self.hvac_mode == HVAC_MODE_HEAT_COOL:
                return int(self._system.get_stored_status().evap_status.fan_speed)
        if self.preset_mode == PRESET_HEAT:
            if self.hvac_mode == HVAC_MODE_FAN_ONLY:
                return self._system.get_stored_status().heater_status.fan_speed
            return self._system.get_stored_status().heater_status.set_temp

        return 999

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._TEMPERATURE_STEP

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self.preset_mode in (PRESET_COOL, PRESET_HEAT):
            if self.hvac_mode == HVAC_MODE_FAN_ONLY:
                return self._FAN_LIMITS["min"]
            return self._TEMPERATURE_LIMITS["min"]
        if self.preset_mode == PRESET_EVAP and self.hvac_mode == HVAC_MODE_AUTO:
            return self._COMFORT_LIMITS["min"]
        return self._FAN_LIMITS["min"]

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self.preset_mode in (PRESET_COOL, PRESET_HEAT):
            if self.hvac_mode == HVAC_MODE_FAN_ONLY:
                return self._FAN_LIMITS["max"]
            return self._TEMPERATURE_LIMITS["max"]
        if self.preset_mode == PRESET_EVAP and self.hvac_mode == HVAC_MODE_AUTO:
            return self._COMFORT_LIMITS["max"]
        return self._FAN_LIMITS["max"]

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        # pylint: disable=too-many-branches
        #_LOGGER.debug("Setting new HVAC mode from %s to %s", self.hvac_mode, hvac_mode)
        if not hvac_mode == self.hvac_mode:
            if hvac_mode == HVAC_MODE_HEAT_COOL:
                #turn whatever the preset is on and put it into manual mode
                if self.preset_mode == PRESET_COOL:
                    await self._system.turn_cooling_on()
                    await self._system.set_cooling_manual()
                if self.preset_mode == PRESET_HEAT:
                    await self._system.turn_heater_on()
                    await self._system.set_heater_manual()
                if self.preset_mode == PRESET_EVAP:
                    await self._system.turn_evap_on()
                    await self._system.set_evap_manual()
            elif hvac_mode == HVAC_MODE_AUTO:
                #turn whatever the preset is on and put it into auto mode
                if self.preset_mode == PRESET_COOL:
                    await self._system.turn_cooling_on()
                    await self._system.set_cooling_auto()
                if self.preset_mode == PRESET_HEAT:
                    await self._system.turn_heater_on()
                    await self._system.set_heater_auto()
                if self.preset_mode == PRESET_EVAP:
                    await self._system.turn_evap_on()
                    await self._system.set_evap_auto()
            elif hvac_mode == HVAC_MODE_OFF:
                #turn whatever the preset is off
                if self.preset_mode == PRESET_COOL:
                    await self._system.turn_cooling_off()
                if self.preset_mode == PRESET_HEAT:
                    await self._system.turn_heater_off()
                if self.preset_mode == PRESET_EVAP:
                    await self._system.turn_evap_off()
            elif hvac_mode == HVAC_MODE_FAN_ONLY:
                #turn whatever the preset is off
                if self.preset_mode == PRESET_COOL:
                    await self._system.turn_cooling_off()
                    await self._system.turn_cooling_fan_only()
                if self.preset_mode == PRESET_HEAT:
                    await self._system.turn_heater_off()
                    await self._system.turn_heater_fan_only()

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        if not preset_mode == self.preset_mode:
            if preset_mode == PRESET_COOL:
                await self._system.set_cooling_mode()
            if preset_mode == PRESET_HEAT:
                await self._system.set_heater_mode()
            if preset_mode == PRESET_EVAP:
                await self._system.set_evap_mode()

    def set_humidity(self, humidity):
        """Set new target humidity."""
        return False

    def set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        return False

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            await self.async_set_target_temperature(kwargs.get(ATTR_TEMPERATURE))

    async def async_set_target_temperature(self, target_temperature):
        """Set the target temperature, fan speed or comfort level."""
        target_temperature = int(round(target_temperature))

        if not self.min_temp <= target_temperature <= self.max_temp:
            raise ValueError(
                f"Target temperature ({target_temperature}) must be between "
                f'{self.min_temp} and {self.max_temp}.'
            )
        if self.preset_mode == PRESET_COOL:
            if self.hvac_mode == HVAC_MODE_FAN_ONLY:
                await self._system.set_cooling_fan_speed(target_temperature)
            else:
                await self._system.set_cooling_temp(target_temperature)
        if self.preset_mode == PRESET_HEAT:
            if self.hvac_mode == HVAC_MODE_FAN_ONLY:
                await self._system.set_heater_fan_speed(target_temperature)
            else:
                await self._system.set_heater_temp(target_temperature)
        if self.preset_mode == PRESET_EVAP and self.hvac_mode == HVAC_MODE_AUTO :
            await self._system.set_evap_comfort(target_temperature)
        if self.preset_mode == PRESET_EVAP and self.hvac_mode == HVAC_MODE_HEAT_COOL :
            await self._system.set_evap_fan_speed(target_temperature)

    @property
    def current_temperature(self):
        """Return the current temperature."""
        #NC7 returns temp in XXX -> ZXS -> MT
        #Implement later, as I have the NC6 that doesn't return a temperature
        #implemented use of an external sensor (optional) which returns 0 if none selected
        if self._system.get_stored_status().cooling_mode:
            temp = self._system.get_stored_status().cooling_status.temperature
        elif self._system.get_stored_status().heater_mode:
            temp = self._system.get_stored_status().heater_status.temperature
            _LOGGER.debug("Internal temperature sensor reports: %s", temp)
        elif self._system.get_stored_status().evap_mode:
            temp = self._system.get_stored_status().evap_status.temperature
            _LOGGER.debug("Internal temperature sensor reports: %s", temp)

        if int(temp) < 999:
            _LOGGER.debug("Internal temperature sensor should be reported: %s", int(temp) < 999)
            return int(round(float(temp)/10))
        return self._sensor_temperature

    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        # pylint: disable=too-many-return-statements,too-many-branches
        if not self._system.get_stored_status().system_on:
            return HVAC_MODE_OFF
        if self.preset_mode == PRESET_COOL:
            if self._system.get_stored_status().cooling_status.cooling_on:
                if self._system.get_stored_status().cooling_status.manual_mode:
                    return HVAC_MODE_HEAT_COOL
                if self._system.get_stored_status().cooling_status.auto_mode:
                    return HVAC_MODE_AUTO
            else:
                #system on, cooling mode, but cooling off indicates fan only
                return HVAC_MODE_FAN_ONLY
        if self.preset_mode == PRESET_HEAT:
            if self._system.get_stored_status().heater_status.heater_on:
                if self._system.get_stored_status().heater_status.manual_mode:
                    return HVAC_MODE_HEAT_COOL
                if self._system.get_stored_status().heater_status.auto_mode:
                    return HVAC_MODE_AUTO
            else:
                #system on, heater mode, but heater off indicates fan only
                return HVAC_MODE_FAN_ONLY
        if self.preset_mode == PRESET_EVAP:
            if self._system.get_stored_status().evap_status.manual_mode:
                return HVAC_MODE_HEAT_COOL
            if self._system.get_stored_status().evap_status.auto_mode:
                return HVAC_MODE_AUTO
        return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        if self.preset_mode == PRESET_EVAP:
            return [HVAC_MODE_HEAT_COOL, HVAC_MODE_AUTO, HVAC_MODE_OFF ]
        return [HVAC_MODE_HEAT_COOL, HVAC_MODE_AUTO, HVAC_MODE_FAN_ONLY, HVAC_MODE_OFF ]

    @property
    def preset_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        if self._system.get_stored_status().heater_mode :
            return PRESET_HEAT
        if self._system.get_stored_status().cooling_mode :
            return PRESET_COOL
        return PRESET_EVAP

    @property
    def preset_modes(self):
        """Return the list of available HVAC modes."""
        modes = []
        if self._system.get_stored_status().has_heater:
            modes.append(PRESET_HEAT)
        if self._system.get_stored_status().has_cooling:
            modes.append(PRESET_COOL)
        if self._system.get_stored_status().has_evap:
            modes.append(PRESET_EVAP)
        return modes

    def turn_aux_heat_on(self):
        """Turn auxiliary heater on."""
        return False

    def turn_aux_heat_off(self):
        """Turn auxiliary heater off."""
        return False

    async def async_update(self):
        """Update system with latest status."""
        await self._system.get_status()
        self.update_external_temperature()

    def update_external_temperature(self):
        """Update external temperature reading."""
        _LOGGER.debug("External temperature sensor entity name: %s", self._temerature_entity_name)
        if self._temerature_entity_name is not None:
            temperature_entity = self._hass.states.get(self._temerature_entity_name)
            #_LOGGER.debug("External temperature sensor entity: %s", temperature_entity)
            if temperature_entity is not None and temperature_entity.state != "unavailable":
                _LOGGER.debug("External temperature sensor reports: %s", temperature_entity.state)
                try:
                    self._sensor_temperature = int(round(float(temperature_entity.state)))
                except ValueError:
                    self._sensor_temperature = 0

    @property
    def available(self):
        if (
            self._system.get_stored_status().heater_mode
            or self._system.get_stored_status().cooling_mode
            or self._system.get_stored_status().evap_mode
        ):
            return True
        return False


class RinnaiTouchZone(ClimateEntity):
    """Climate entity for a zone."""
    # pylint: disable=too-many-instance-attributes,too-many-public-methods

    #some common
    def __init__(self, hass, ip_address, name, zone, temperature_entity = None):
        # pylint: disable=too-many-arguments

        _LOGGER.debug("Set up RinnaiTouch zone %s entity %s", zone, ip_address)
        self._system = RinnaiSystem.get_instance(ip_address)
        device_id = "rinnaitouch_zone" + zone + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name + " Zone " + zone
        self._attr_zone = zone

        self._temerature_entity_name = temperature_entity
        self._sensor_temperature = 0
        self.update_external_temperature()

        self._hass = hass

        self._support_flags = SUPPORT_FLAGS_ZONE

        self._TEMPERATURE_STEP = 1
        self._TEMPERATURE_LIMITS = {"min": 8, "max": 30}
        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        self.async_write_ha_state()

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._attr_name

    @property
    def unique_id(self):
        """Return the unique id for this heater."""
        return self._attr_unique_id

    #not common
    #@property
    #def device_info(self):
    #    """Return device information about this heater."""
    #    return {
    #        "connections": {(CONNECTION_NETWORK_MAC, self._host)},
    #        "identifiers": {("Rinnai Touch Zone", self.unique_id)},
    #        "model": "Rinnai Touch Wifi Zone",
    #        "name": self.name,
    #        "manufacturer": "Rinnai/Brivis",
    #    }


    #TODO: add Multi-Set Point Fan Only mode for zones
    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        hvac_mode = self.hvac_mode

        if hvac_mode == HVAC_MODE_OFF:
            return "mdi:hvac-off"

        preset_mode = self.preset_mode

        if preset_mode == PRESET_COOL:
            return "mdi:snowflake"
        if preset_mode == PRESET_EVAP:
            return "mdi:snowflake-melt"
        if preset_mode == PRESET_HEAT:
            return "mdi:fire"

        return "mdi:hvac"

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._system.get_stored_status().temp_unit == RinnaiSystem.TEMP_FAHRENHEIT:
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS

    #not common
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        # pylint: disable=too-many-return-statements
        if self.hvac_mode == HVAC_MODE_OFF:
            return 0

        if self._system.get_stored_status().is_multi_set_point:
            if self.preset_mode == PRESET_COOL:
                return getattr(
                        self._system.get_stored_status().cooling_status,
                        "zone_" + self._attr_zone.lower() + "_set_temp"
                    )
            if self.preset_mode == PRESET_EVAP:
                if self.hvac_mode == HVAC_MODE_AUTO:
                    return int(self._system.get_stored_status().evap_status.comfort)
                if self.hvac_mode == HVAC_MODE_HEAT_COOL:
                    return int(self._system.get_stored_status().evap_status.fan_speed)
            if self.preset_mode == PRESET_HEAT:
                return getattr(
                        self._system.get_stored_status().heater_status,
                        "zone_" + self._attr_zone.lower() + "_set_temp"
                    )

        if self.preset_mode == PRESET_COOL:
            return self._system.get_stored_status().cooling_status.set_temp
        if self.preset_mode == PRESET_EVAP:
            if self.hvac_mode == HVAC_MODE_AUTO:
                return int(self._system.get_stored_status().evap_status.comfort)
            if self.hvac_mode == HVAC_MODE_HEAT_COOL:
                return int(self._system.get_stored_status().evap_status.fan_speed)
        if self.preset_mode == PRESET_HEAT:
            return self._system.get_stored_status().heater_status.set_temp

        return 999

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._TEMPERATURE_STEP

    #not common
    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self._system.get_stored_status().is_multi_set_point:
            if self.preset_mode in (PRESET_COOL, PRESET_HEAT):
                return self._TEMPERATURE_LIMITS["min"]
        return self.target_temperature

    #not common
    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self._system.get_stored_status().is_multi_set_point:
            if self.preset_mode in (PRESET_COOL, PRESET_HEAT):
                return self._TEMPERATURE_LIMITS["max"]
        return self.target_temperature

    #not common
    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        # pylint: disable=too-many-branches
        if not hvac_mode == self.hvac_mode:
            if hvac_mode == HVAC_MODE_HEAT_COOL:
                #turn whatever the preset is on and put it into manual mode
                if self.preset_mode == PRESET_COOL:
                    await self._system.turn_cooling_zone_on(self._attr_zone)
                    await self._system.set_cooling_zone_manual(self._attr_zone)
                if self.preset_mode == PRESET_HEAT:
                    await self._system.turn_heater_zone_on(self._attr_zone)
                    await self._system.set_heater_zone_manual(self._attr_zone)
                if self.preset_mode == PRESET_EVAP:
                    await self._system.turn_evap_zone_on(self._attr_zone)
                    await self._system.set_evap_zone_manual(self._attr_zone)
            elif hvac_mode == HVAC_MODE_AUTO:
                #turn whatever the preset is on and put it into auto mode
                if self.preset_mode == PRESET_COOL:
                    await self._system.turn_cooling_zone_on(self._attr_zone)
                    await self._system.set_cooling_zone_auto(self._attr_zone)
                if self.preset_mode == PRESET_HEAT:
                    await self._system.turn_heater_zone_on(self._attr_zone)
                    await self._system.set_heater_zone_auto(self._attr_zone)
                if self.preset_mode == PRESET_EVAP:
                    await self._system.turn_evap_zone_on(self._attr_zone)
                    await self._system.set_evap_zone_auto(self._attr_zone)
            elif hvac_mode == HVAC_MODE_OFF:
                #turn whatever the zone off
                if self.preset_mode == PRESET_COOL:
                    await self._system.turn_cooling_zone_off(self._attr_zone)
                if self.preset_mode == PRESET_HEAT:
                    await self._system.turn_heater_zone_off(self._attr_zone)
                if self.preset_mode == PRESET_EVAP:
                    await self._system.turn_evap_zone_off(self._attr_zone)

    #not common, cannot change the preset per zone
    async def async_set_preset_mode(self, preset_mode):
        """Cannot change the preset per zone"""
        return False

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            await self.async_set_target_temperature(kwargs.get(ATTR_TEMPERATURE))

    #not common
    async def async_set_target_temperature(self, target_temperature):
        """Set the new target temperate in a zone."""
        if self._system.get_stored_status().is_multi_set_point:
            target_temperature = int(round(target_temperature))

            if not self.min_temp <= target_temperature <= self.max_temp:
                raise ValueError(
                    f"Target temperature ({target_temperature}) must be between "
                    f'{self.min_temp} and {self.max_temp}.'
                )
            if self.preset_mode == PRESET_COOL:
                await self._system.set_cooling_zone_temp(target_temperature)
            if self.preset_mode == PRESET_HEAT:
                await self._system.set_heater_zone_temp(target_temperature)
        else:
            return False

    #not common
    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._system.get_stored_status().cooling_mode:
            temp = getattr(
                        self._system.get_stored_status().cooling_status,
                        "zone_" + self._attr_zone.lower() + "_temp"
                    )
        elif self._system.get_stored_status().heater_mode:
            temp = getattr(
                        self._system.get_stored_status().heater_status,
                        "zone_" + self._attr_zone.lower() + "_temp"
                    )
        elif self._system.get_stored_status().evap_mode:
            temp = getattr(
                        self._system.get_stored_status().evap_status,
                        "zone_" + self._attr_zone.lower() + "_temp"
                    )

        if int(temp) < 999:
            return int(round(float(temp)/10))
        return self._sensor_temperature

    #not common
    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        # pylint: disable=too-many-return-statements
        if self.preset_mode == PRESET_COOL:
            if not getattr(
                        self._system.get_stored_status().cooling_status,
                        "zone_" + self._attr_zone.lower()
                    ):
                return HVAC_MODE_OFF
            if not getattr(
                        self._system.get_stored_status().cooling_status,
                        "zone_" + self._attr_zone.lower() + "_auto"
                    ):
                return HVAC_MODE_HEAT_COOL
            if getattr(
                        self._system.get_stored_status().cooling_status,
                        "zone_" + self._attr_zone.lower() + "_auto"
                    ):
                return HVAC_MODE_AUTO
        if self.preset_mode == PRESET_HEAT:
            if not getattr(
                        self._system.get_stored_status().heater_status,
                        "zone_" + self._attr_zone.lower()
                    ):
                return HVAC_MODE_OFF
            if not getattr(
                        self._system.get_stored_status().heater_status,
                        "zone_" + self._attr_zone.lower() + "_auto"
                    ):
                return HVAC_MODE_HEAT_COOL
            if getattr(
                        self._system.get_stored_status().heater_status,
                        "zone_" + self._attr_zone.lower() + "_auto"
                    ):
                return HVAC_MODE_AUTO
        if self.preset_mode == PRESET_EVAP:
            if not getattr(
                        self._system.get_stored_status().evap_status,
                        "zone_" + self._attr_zone.lower()
                    ):
                return HVAC_MODE_OFF
            if not getattr(
                        self._system.get_stored_status().evap_status,
                        "zone_" + self._attr_zone.lower() + "_auto"
                    ):
                return HVAC_MODE_HEAT_COOL
            if getattr(
                        self._system.get_stored_status().evap_status,
                        "zone_" + self._attr_zone.lower() + "_auto"
                    ):
                return HVAC_MODE_AUTO
        return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return [HVAC_MODE_HEAT_COOL, HVAC_MODE_AUTO, HVAC_MODE_OFF ]

    @property
    def preset_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        if self._system.get_stored_status().heater_mode :
            return PRESET_HEAT
        if self._system.get_stored_status().cooling_mode :
            return PRESET_COOL
        return PRESET_EVAP

    #not common. Only return the mode that is set on the main
    @property
    def preset_modes(self):
        """Return the list of available HVAC modes."""
        if self._system.get_stored_status().heater_mode :
            return [PRESET_HEAT]
        if self._system.get_stored_status().cooling_mode :
            return [PRESET_COOL]
        return [PRESET_EVAP]

    def turn_aux_heat_on(self):
        """Turn auxiliary heater on."""
        return False

    def turn_aux_heat_off(self):
        """Turn auxiliary heater off."""
        return False

    #not common
    async def async_update(self):
        """Do nothing."""
        pass # pylint: disable=unnecessary-pass

    #not common
    @property
    def available(self):
        if self._system.get_stored_status().heater_mode:
            return self._attr_zone in self._system.get_stored_status().heater_status.zones
        if self._system.get_stored_status().cooling_mode:
            return self._attr_zone in self._system.get_stored_status().cooling_status.zones
        return False

    def update_external_temperature(self):
        """Update latest external temperature reading."""
        _LOGGER.debug("External temperature sensor entity name (zone %s): %s",
                      self._attr_zone,
                      self._temerature_entity_name
                  )
        if self._temerature_entity_name is not None and self._hass:
            temperature_entity = self._hass.states.get(self._temerature_entity_name)
            #_LOGGER.debug("External temperature sensor entity: %s", temperature_entity)
            if temperature_entity is not None and temperature_entity.state != "unavailable":
                _LOGGER.debug("External temperature sensor reports: %s", temperature_entity.state)
                try:
                    self._sensor_temperature = int(round(float(temperature_entity.state)))
                except ValueError:
                    self._sensor_temperature = 0
