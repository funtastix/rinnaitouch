# pylint: skip-file
"""Support for the Rinnai Touch Controller.

To support the controller and make it work with the HA climate entity,these are the mappings:

HVAC modes:
HVAC_MODE_HEAT_COOL -> Manual Mode (all operating modes)
HVAC_MODE_AUTO -> Auto Mode (all operating modes)
HVAC_MODE_OFF -> Unit Off (any operating mode)

PRESET modes:
PRESET_COOL -> Cooling mode
PRESET_HEAT -> Heater mode
PRESET_EVAP -> Evap mode

"""
from __future__ import annotations

from collections.abc import Callable, Coroutine
import logging

from custom_components.rinnaitouch.pyrinnaitouch import RinnaiSystem

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_ON,
    FAN_OFF,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_OFF,
    HVAC_MODES,
    ATTR_HVAC_MODE,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_PRESET_MODE
)
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    PRECISION_WHOLE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    ATTR_TEMPERATURE,
    STATE_UNAVAILABLE
)

from .const import *

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE + SUPPORT_FAN_MODE + SUPPORT_PRESET_MODE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME)
    temperature_entity = entry.data.get(CONF_TEMP_SENSOR)
    async_add_entities([RinnaiTouch(hass, ip_address, name, temperature_entity)])
    async_add_entities([RinnaiTouchZone(hass, ip_address, name, "A")])
    async_add_entities([RinnaiTouchZone(hass, ip_address, name, "B")])
    async_add_entities([RinnaiTouchZone(hass, ip_address, name, "C")])
    async_add_entities([RinnaiTouchZone(hass, ip_address, name, "D")])
    return True

class RinnaiTouch(ClimateEntity):

    def __init__(self, hass, ip_address, name = "Rinnai Touch", temperature_entity = None):
        self._host = ip_address
        _LOGGER.info("Set up RinnaiTouch entity %s", ip_address)
        self._system = RinnaiSystem.getInstance(ip_address)
        device_id = "rinnaitouch_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name

        self._hass = hass
        self._temerature_entity_name = temperature_entity
        self._sensor_temperature = 0
        self.update_external_temperature()

        self._support_flags = SUPPORT_FLAGS
        
        self._TEMPERATURE_STEP = 1
        self._TEMPERATURE_LIMITS = {"min": 8, "max": 30}
        self._COMFORT_LIMITS = {"min": 19, "max": 34}
        self._FAN_LIMITS = {"min": 0, "max": 16}

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

        preset_mode = self.preset_mode

        if preset_mode == PRESET_COOL:
            return "mdi:snowflake"
        if preset_mode == PRESET_EVAP:
            return "mdi:snowflake-melt"
        if preset_mode == PRESET_HEAT:
            return "mdi:fire"

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._system._status.tempUnit == RinnaiSystem.TEMP_FAHRENHEIT:
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.hvac_mode == HVAC_MODE_OFF:
            return 0
        else:
            if self.preset_mode == PRESET_COOL:
                return self._system._status.coolingStatus.setTemp
            if self.preset_mode == PRESET_EVAP:
                if self.hvac_mode == HVAC_MODE_AUTO:
                    return int(self._system._status.evapStatus.comfort)
                elif self.hvac_mode == HVAC_MODE_HEAT_COOL:
                    return int(self._system._status.evapStatus.fanSpeed)
            if self.preset_mode == PRESET_HEAT:
                return self._system._status.heaterStatus.setTemp
        return 999

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._TEMPERATURE_STEP

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self.preset_mode == PRESET_COOL or self.preset_mode == PRESET_HEAT:
            return self._TEMPERATURE_LIMITS["min"]
        elif self.preset_mode == PRESET_EVAP and self.hvac_mode == HVAC_MODE_AUTO:
            return self._COMFORT_LIMITS["min"]
        else:
            return self._FAN_LIMITS["min"]

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self.preset_mode == PRESET_COOL or self.preset_mode == PRESET_HEAT:
            return self._TEMPERATURE_LIMITS["max"]
        elif self.preset_mode == PRESET_EVAP and self.hvac_mode == HVAC_MODE_AUTO:
            return self._COMFORT_LIMITS["max"]
        else:
            return self._FAN_LIMITS["max"]

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
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

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        if not preset_mode == self.preset_mode:
            if preset_mode == PRESET_COOL:
                await self._system.set_cooling_mode()
            if preset_mode == PRESET_HEAT:
                await self._system.set_heater_mode()
            if preset_mode == PRESET_EVAP:
                await self._system.set_evap_mode()

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        if not fan_mode == self.fan_mode:
            if preset_mode == PRESET_COOL:
                if fan_mode == FAN_OFF:
                    await self._system.turn_cooling_off()
                if fan_mode == FAN_ON:
                    await self._system.turn_cooling_fan_only()
            if preset_mode == PRESET_HEAT:
                if fan_mode == FAN_OFF:
                    await self._system.turn_heater_off()
                if fan_mode == FAN_ON:
                    await self._system.turn_heater_fan_only()
            if preset_mode == PRESET_EVAP:
                if fan_mode == FAN_OFF:
                    await self._system.turn_evap_fan_off()
                    await self._system.turn_evap_pump_on()
                if fan_mode == FAN_ON:
                    await self._system.turn_evap_fan_on()
                    await self._system.turn_evap_pump_on()
                if fan_mode == FAN_ONLY:
                    await self._system.turn_evap_fan_on()
                    await self._system.turn_evap_pump_off()

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
        target_temperature = int(round(target_temperature))

        if not self.min_temp <= target_temperature <= self.max_temp:
            raise ValueError(
                f"Target temperature ({target_temperature}) must be between "
                f'{self.min_temp} and {self.max_temp}.'
            )
        if self.preset_mode == PRESET_COOL:
            await self._system.set_cooling_temp(target_temperature)
        if self.preset_mode == PRESET_HEAT:
            await self._system.set_heater_temp(target_temperature)
        if self.preset_mode == PRESET_EVAP and self.hvac_mode == HVAC_MODE_AUTO :
            await self._system.set_evap_comfort(target_temperature)
        if self.preset_mode == PRESET_EVAP and self.hvac_mode == HVAC_MODE_HEAT_COOL :
            await self._system.set_evap_fanspeed(target_temperature)

    @property
    def current_temperature(self):
        """Return the current temperature."""
        #NC7 returns temp in XXX -> ZXS -> MT
        #Implement later, as I have the NC6 that doesn't return a temperature
        #implemented use of an external sensor (optional) which returns 0 if none selected
        if self._system._status.coolingMode:
            temp = self._system._status.coolingStatus.temperature
        elif self._system._status.heaterMode:
            temp = self._system._status.heaterStatus.temperature
        elif self._system._status.evapMode:
            temp = self._system._status.evapStatus.temperature

        if not temp == 999:
            return int(round(float(temp)/10))
        return self._sensor_temperature

    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        #sysStatusJson = "{\"Status\": { \"System\": { " \
        #    + "\"CoolingMode\":"  + str(self._system._status.coolingMode) + "," \
        #    + "\"EvapMode\":"  + str(self._system._status.evapMode) + "," \
        #    + "\"HeaterMode\":"  + str(self._system._status.heaterMode) + "," \
        #    + "\"CoolingStatus\":"  + str(self._system._status.coolingStatus) + "," \
        #    + "\"EvapStatus\":"  + str(self._system._status.evapStatus) + "," \
        #    + "\"HeaterStatus\":"  + str(self._system._status.heaterStatus) + "," \
        #    + "\"SystemOn\": " + str(self._system._status.systemOn) + " },"
        #_LOGGER.debug("HVAC MODE for System: %s",self._system._status.systemOn)
        #_LOGGER.debug("System Status: %s", sysStatusJson)
        if not self._system._status.systemOn:
            return HVAC_MODE_OFF
        if self.preset_mode == PRESET_COOL:
            if self._system._status.coolingStatus.manualMode:
                return HVAC_MODE_HEAT_COOL
            elif self._system._status.coolingStatus.autoMode:
                return HVAC_MODE_AUTO
        if self.preset_mode == PRESET_HEAT:
            if self._system._status.heaterStatus.manualMode:
                return HVAC_MODE_HEAT_COOL
            elif self._system._status.heaterStatus.autoMode:
                return HVAC_MODE_AUTO
        if self.preset_mode == PRESET_EVAP:
            if self._system._status.evapStatus.manualMode:
                return HVAC_MODE_HEAT_COOL
            elif self._system._status.evapStatus.autoMode:
                return HVAC_MODE_AUTO
        return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return [HVAC_MODE_HEAT_COOL, HVAC_MODE_AUTO, HVAC_MODE_OFF ]

    @property
    def fan_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        if self.preset_mode == PRESET_EVAP:
            if self._system._status.evapStatus.fanOn and not self._system._status.evapStatus.waterPumpOn:
                return FAN_ONLY
            elif self._system._status.evapStatus.fanOn:
                return FAN_ON
            else:
                return FAN_OFF
        elif self.preset_mode == PRESET_COOL:
            if self._system._status.coolingStatus.circulationFanOn:
                return FAN_ON
            else:
                return FAN_OFF
        elif self.preset_mode == PRESET_HEAT:
            if self._system._status.heaterStatus.circulationFanOn:
                return FAN_ON
            else:
                return FAN_OFF
        return FAN_OFF

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        if self.preset_mode == PRESET_EVAP:
            return [FAN_ON, FAN_OFF, FAN_ONLY ]
        return [FAN_ON, FAN_OFF ]

    @property
    def preset_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        if self._system._status.heaterMode :
            return PRESET_HEAT
        elif self._system._status.coolingMode :
            return PRESET_COOL
        else:
            return PRESET_EVAP

    @property
    def preset_modes(self):
        """Return the list of available HVAC modes."""
        modes = []
        if self._system._status.hasHeater:
            modes.append(PRESET_HEAT)
        if self._system._status.hasCooling:
            modes.append(PRESET_COOL)
        if self._system._status.hasEvap:
            modes.append(PRESET_EVAP)
        return modes

    def turn_aux_heat_on(self):
        """Turn auxiliary heater on."""
        return False

    def turn_aux_heat_off(self):
        """Turn auxiliary heater off."""
        return False

    async def async_update(self):
        await self._system.GetStatus()
        self.update_external_temperature()

    def update_external_temperature(self):
        _LOGGER.debug("External temperature sensor entity name: %s", self._temerature_entity_name)
        if self._temerature_entity_name is not None:
            temperature_entity = self._hass.states.get(self._temerature_entity_name)
            #_LOGGER.debug("External temperature sensor entity: %s", temperature_entity)
            if temperature_entity is not None:
                _LOGGER.debug("External temperature sensor reports: %s", temperature_entity.state)
                self._sensor_temperature = int(round(float(temperature_entity.state)))

    @property
    def available(self):
        if self._system._status.heaterMode or self._system._status.coolingMode or self._system._status.evapMode:
            return True
        return False


class RinnaiTouchZone(ClimateEntity):

    #some common
    def __init__(self, hass, ip_address, name, zone):
        self._host = ip_address
        _LOGGER.debug("Set up RinnaiTouch zone %s entity %s", zone, ip_address)
        self._system = RinnaiSystem.getInstance(ip_address)
        device_id = "rinnaitouch_zone" + zone + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name + " Zone " + zone
        self._attr_zone = zone

        self._hass = hass

        self._support_flags = SUPPORT_FLAGS
        
        self._TEMPERATURE_STEP = 1
        self._TEMPERATURE_LIMITS = {"min": 8, "max": 30}

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
    @property
    def device_info(self):
        """Return device information about this heater."""
        return {
            "connections": {(CONNECTION_NETWORK_MAC, self._host)},
            "identifiers": {("Rinnai Touch Zone", self.unique_id)},
            "model": "Rinnai Touch Wifi Zone",
            "name": self.name,
            "manufacturer": "Rinnai/Brivis",
        }

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

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._system._status.tempUnit == RinnaiSystem.TEMP_FAHRENHEIT:
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS

    #not common
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.hvac_mode == HVAC_MODE_OFF:
            return 0
        else:
            if self._system._status.isMultiSetPoint:
                if self.preset_mode == PRESET_COOL:
                    return getattr(self._system._status.coolingStatus, "zone" + self._attr_zone + "setTemp")
                if self.preset_mode == PRESET_EVAP:
                    if self.hvac_mode == HVAC_MODE_AUTO:
                        return int(self._system._status.evapStatus.comfort)
                    elif self.hvac_mode == HVAC_MODE_HEAT_COOL:
                        return int(self._system._status.evapStatus.fanSpeed)
                if self.preset_mode == PRESET_HEAT:
                    return getattr(self._system._status.heaterStatus, "zone" + self._attr_zone + "setTemp")
            else:
                if self.preset_mode == PRESET_COOL:
                    return self._system._status.coolingStatus.setTemp
                if self.preset_mode == PRESET_EVAP:
                    if self.hvac_mode == HVAC_MODE_AUTO:
                        return int(self._system._status.evapStatus.comfort)
                    elif self.hvac_mode == HVAC_MODE_HEAT_COOL:
                        return int(self._system._status.evapStatus.fanSpeed)
                if self.preset_mode == PRESET_HEAT:
                    return self._system._status.heaterStatus.setTemp
        return 999

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._TEMPERATURE_STEP

    #not common
    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self._system._status.isMultiSetPoint:
            if self.preset_mode == PRESET_COOL or self.preset_mode == PRESET_HEAT:
                return self._TEMPERATURE_LIMITS["min"]
        return self.target_temperature

    #not common
    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self._system._status.isMultiSetPoint:
            if self.preset_mode == PRESET_COOL or self.preset_mode == PRESET_HEAT:
                return self._TEMPERATURE_LIMITS["max"]
        return self.target_temperature
    
    #not common
    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
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

    #not common, cannot change the fan mode per zone
    async def async_set_fan_mode(self, fan_mode):
        """Cannot change the fan mode per zone"""
        return False

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

    #not common
    async def async_set_target_temperature(self, target_temperature):
        if self._system._status.isMultiSetPoint:
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
        if self._system._status.coolingMode:
            temp = getattr(self._system._status.coolingStatus, "zone" + self._attr_zone + "temp")
        elif self._system._status.heaterMode:
            temp = getattr(self._system._status.heaterStatus, "zone" + self._attr_zone + "temp")
        elif self._system._status.evapMode:
            temp = getattr(self._system._status.evapStatus, "zone" + self._attr_zone + "temp")

        if not temp == 999:
            return int(round(float(temp)/10))
        return 0

    #not common
    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        if self.preset_mode == PRESET_COOL:
            if not getattr(self._system._status.coolingStatus, "zone" + self._attr_zone):
                return HVAC_MODE_OFF
            elif not getattr(self._system._status.coolingStatus, "zone" + self._attr_zone + "Auto"):
                return HVAC_MODE_HEAT_COOL
            elif getattr(self._system._status.coolingStatus, "zone" + self._attr_zone + "Auto"):
                return HVAC_MODE_AUTO
        if self.preset_mode == PRESET_HEAT:
            if not getattr(self._system._status.heaterStatus, "zone" + self._attr_zone):
                return HVAC_MODE_OFF
            elif not getattr(self._system._status.heaterStatus, "zone" + self._attr_zone + "Auto"):
                return HVAC_MODE_HEAT_COOL
            elif getattr(self._system._status.heaterStatus, "zone" + self._attr_zone + "Auto"):
                return HVAC_MODE_AUTO
        if self.preset_mode == PRESET_EVAP:
            if not getattr(self._system._status.evapStatus, "zone" + self._attr_zone):
                return HVAC_MODE_OFF
            elif not getattr(self._system._status.evapStatus, "zone" + self._attr_zone + "Auto"):
                return HVAC_MODE_HEAT_COOL
            elif getattr(self._system._status.evapStatus, "zone" + self._attr_zone + "Auto"):
                return HVAC_MODE_AUTO
        return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return [HVAC_MODE_HEAT_COOL, HVAC_MODE_AUTO, HVAC_MODE_OFF ]

    @property
    def fan_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        if self.preset_mode == PRESET_EVAP:
            if self._system._status.evapStatus.fanOn and not self._system._status.evapStatus.waterPumpOn:
                return FAN_ONLY
            elif self._system._status.evapStatus.fanOn:
                return FAN_ON
            else:
                return FAN_OFF
        elif self.preset_mode == PRESET_COOL:
            if self._system._status.coolingStatus.circulationFanOn:
                return FAN_ON
            else:
                return FAN_OFF
        elif self.preset_mode == PRESET_HEAT:
            if self._system._status.heaterStatus.circulationFanOn:
                return FAN_ON
            else:
                return FAN_OFF
        return FAN_OFF

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        if self.preset_mode == PRESET_EVAP:
            return [FAN_ON, FAN_OFF, FAN_ONLY ]
        return [FAN_ON, FAN_OFF ]

    @property
    def preset_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        if self._system._status.heaterMode :
            return PRESET_HEAT
        elif self._system._status.coolingMode :
            return PRESET_COOL
        else:
            return PRESET_EVAP

    #not common. Only return the mode that is set on the main
    @property
    def preset_modes(self):
        """Return the list of available HVAC modes."""
        if self._system._status.heaterMode :
            return [PRESET_HEAT]
        elif self._system._status.coolingMode :
            return [PRESET_COOL]
        else:
            return [PRESET_EVAP]

    def turn_aux_heat_on(self):
        """Turn auxiliary heater on."""
        return False

    def turn_aux_heat_off(self):
        """Turn auxiliary heater off."""
        return False

    #not common
    async def async_update(self):
        await super().async_update()

    #not common
    @property
    def available(self):
        if self._system._status.heaterMode:
            return self._attr_zone in self._system._status.heaterStatus.zones
        elif self._system._status.coolingMode:
            return self._attr_zone in self._system._status.coolingStatus.zones
        return False
