"""Support for the Rinnai Touch Controller.

To support the controller and make it work with the HA climate entity,these are the mappings:

HVAC modes:
HVAC_MODE_HEAT -> Heating mode (gas heater)
HVAC_MODE_COOL -> Cooling Mode (evap or refrigerated)
HVAC_MODE_OFF -> Unit Off (any operating mode)
HVAC_MODE_FAN_ONLY - Only circulation fan is on while in heating or cooling mode

PRESET modes:
PRESET_MANUAL -> Manual mode
PRESET_AUTO -> Auto mode

Cooling selector (preselected, only available if multiple cooling methods installed)
COOLING_EVAP -> Evap mode
COOLING_COOL -> Refrigerated mode
"""
from __future__ import annotations
from datetime import timedelta

import logging

from pyrinnaitouch import (
    RinnaiSystem,
    RinnaiSystemMode,
    TEMP_FAHRENHEIT,
    RinnaiCapabilities,
    RinnaiOperatingMode
)

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate import (
    HVACMode,
    ClimateEntityFeature,
    #    SUPPORT_TARGET_TEMPERATURE,
    #    SUPPORT_PRESET_MODE,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    UnitOfTemperature,
    ATTR_TEMPERATURE,
)
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from .const import (
    PRESET_AUTO,
    PRESET_MANUAL,
    COOLING_EVAP,
    COOLING_COOL,
    COOLING_NONE,
    CONF_TEMP_SENSOR,
    CONF_TEMP_SENSOR_A,
    CONF_TEMP_SENSOR_B,
    CONF_TEMP_SENSOR_C,
    CONF_TEMP_SENSOR_D,
    CONF_TEMP_SENSOR_COMMON,
    CONF_ZONE_A,
    CONF_ZONE_B,
    CONF_ZONE_C,
    CONF_ZONE_D,
    CONF_ZONE_COMMON,
)

SUPPORT_FLAGS_MAIN = (
    ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
)
SUPPORT_FLAGS_ZONE = (
    ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up climate entities."""
    ip_address = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME)
    temperature_entity = entry.data.get(CONF_TEMP_SENSOR)
    temperature_entity_a = entry.data.get(CONF_TEMP_SENSOR_A)
    temperature_entity_b = entry.data.get(CONF_TEMP_SENSOR_B)
    temperature_entity_c = entry.data.get(CONF_TEMP_SENSOR_C)
    temperature_entity_d = entry.data.get(CONF_TEMP_SENSOR_D)
    temperature_entity_common = entry.data.get(CONF_TEMP_SENSOR_COMMON)
    async_add_entities([RinnaiTouch(hass, ip_address, name, temperature_entity)])
    if entry.data.get(CONF_ZONE_A):
        async_add_entities(
            [RinnaiTouchZone(hass, ip_address, name, "A", temperature_entity_a)]
        )
    if entry.data.get(CONF_ZONE_B):
        async_add_entities(
            [RinnaiTouchZone(hass, ip_address, name, "B", temperature_entity_b)]
        )
    if entry.data.get(CONF_ZONE_C):
        async_add_entities(
            [RinnaiTouchZone(hass, ip_address, name, "C", temperature_entity_c)]
        )
    if entry.data.get(CONF_ZONE_D):
        async_add_entities(
            [RinnaiTouchZone(hass, ip_address, name, "D", temperature_entity_d)]
        )
    if entry.data.get(CONF_ZONE_COMMON):
        async_add_entities(
            [RinnaiTouchZone(hass, ip_address, name, "U", temperature_entity_common)]
        )
    return True


class RinnaiTouch(ClimateEntity):
    """Main climate entity for the unit."""

    # pylint: disable=too-many-instance-attributes,too-many-public-methods
    def __init__(self, hass, ip_address, name="Rinnai Touch", temperature_entity=None):
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
        self.update_external_temperature()
        # this very infrequently fails on startup so wrapping in try except
        try:
            self.schedule_update_ha_state()
        except:  # pylint: disable=bare-except
            pass

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

        if hvac_mode == HVACMode.OFF:
            return "mdi:hvac-off"

        if hvac_mode == HVACMode.FAN_ONLY:
            return "mdi:fan"

        if hvac_mode == HVACMode.COOL:
            if self.cooling_mode == COOLING_EVAP:
                return "mdi:snowflake-melt"
            return "mdi:snowflake"

        if hvac_mode == HVACMode.HEAT:
            return "mdi:fire"

        return "mdi:hvac"

    @property
    def cooling_mode(self):
        """Return the cooling mode we're in mode."""
        if self._system.get_stored_status().mode == RinnaiSystemMode.COOLING:
            return COOLING_COOL
        if self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
            return COOLING_EVAP
        return COOLING_NONE

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._system.get_stored_status().temp_unit == TEMP_FAHRENHEIT:
            return UnitOfTemperature.FAHRENHEIT
        return UnitOfTemperature.CELSIUS

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        # pylint: disable=too-many-return-statements
        if self.hvac_mode == HVACMode.OFF:
            return 0

        if self.cooling_mode == COOLING_COOL:
            if self.hvac_mode == HVACMode.FAN_ONLY:
                return self._system.get_stored_status().unit_status.fan_speed
            return self._system.get_stored_status().unit_status.set_temp
        if self.cooling_mode == COOLING_EVAP:
            if self.preset_mode == PRESET_AUTO:
                return int(self._system.get_stored_status().unit_status.comfort)
            if self.preset_mode == PRESET_MANUAL:
                return int(self._system.get_stored_status().unit_status.fan_speed)
        if self.cooling_mode == COOLING_NONE:
            if self.hvac_mode == HVACMode.FAN_ONLY:
                return self._system.get_stored_status().unit_status.fan_speed
            return self._system.get_stored_status().unit_status.set_temp

        return 999

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._TEMPERATURE_STEP

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self.cooling_mode == COOLING_EVAP and self.preset_mode == PRESET_AUTO:
            return self._COMFORT_LIMITS["min"]
        if self.cooling_mode != COOLING_EVAP and self.hvac_mode != HVACMode.FAN_ONLY:
            return self._TEMPERATURE_LIMITS["min"]
        return self._FAN_LIMITS["min"]

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self.cooling_mode == COOLING_EVAP and self.preset_mode == PRESET_AUTO:
            return self._COMFORT_LIMITS["max"]
        if self.cooling_mode != COOLING_EVAP and self.hvac_mode != HVACMode.FAN_ONLY:
            return self._TEMPERATURE_LIMITS["max"]
        return self._FAN_LIMITS["max"]

    @property
    def preferred_cooling_mode(self):
        """Return the preferred cooling mode, prioritising refrigerated over evap."""
        if RinnaiCapabilities.COOLER in self._system.get_stored_status().capabilities:
            return COOLING_COOL
        if RinnaiCapabilities.EVAP in self._system.get_stored_status().capabilities:
            return COOLING_EVAP
        return COOLING_NONE

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        # pylint: disable=too-many-branches
        # _LOGGER.debug("Setting new HVAC mode from %s to %s", self.hvac_mode, hvac_mode)
        if not hvac_mode == self.hvac_mode:
            if hvac_mode == HVACMode.HEAT:
                # turn whatever the preset is on and put it into manual mode
                await self._system.turn_unit_on()
                await self._system.set_heater_mode()
            elif hvac_mode == HVACMode.COOL:
                # turn whatever the preset is on and put it into auto mode
                if self.preferred_cooling_mode == COOLING_COOL:
                    await self._system.turn_unit_on()
                    await self._system.set_cooling_mode()
                if self.preferred_cooling_mode == COOLING_EVAP:
                    await self._system.turn_evap_on()
                    await self._system.set_evap_mode()
            elif hvac_mode == HVACMode.OFF:
                # turn whatever the preset is off
                if self.cooling_mode == COOLING_EVAP:
                    await self._system.turn_evap_off()
                else:
                    await self._system.turn_unit_off()
            elif hvac_mode == HVACMode.FAN_ONLY:
                # turn whatever the preset is off
                await self._system.turn_unit_off()
                if self.cooling_mode == COOLING_COOL:
                    await self._system.turn_unit_fan_only()
                if self.cooling_mode == COOLING_NONE:
                    await self._system.turn_unit_fan_only()

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        if not preset_mode == self.preset_mode:
            if preset_mode == PRESET_AUTO:
                await self._system.set_unit_auto()
            if preset_mode == PRESET_MANUAL:
                await self._system.set_unit_manual()

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
                f"{self.min_temp} and {self.max_temp}."
            )
        if self.cooling_mode == COOLING_COOL:
            if self.hvac_mode == HVACMode.FAN_ONLY:
                await self._system.set_unit_fanspeed(target_temperature)
            else:
                await self._system.set_unit_temp(target_temperature)
        if self.cooling_mode == COOLING_NONE:
            if self.hvac_mode == HVACMode.FAN_ONLY:
                await self._system.set_unit_fanspeed(target_temperature)
            else:
                await self._system.set_unit_temp(target_temperature)
        if self.cooling_mode == COOLING_EVAP and self.preset_mode == PRESET_AUTO:
            await self._system.set_evap_comfort(target_temperature)
        if self.cooling_mode == COOLING_EVAP and self.preset_mode == PRESET_MANUAL:
            await self._system.set_evap_fanspeed(target_temperature)

    @property
    def current_temperature(self):
        """Return the current temperature."""
        # NC7 returns temp in XXX -> ZXS -> MT
        # implemented use of an external sensor (optional) which returns 0 if none selected
        temp = self._system.get_stored_status().unit_status.temperature
        _LOGGER.debug("Internal temperature sensor reports: %s", temp)

        if int(temp) < 999:
            _LOGGER.debug(
                "Internal temperature sensor should be reported: %s", int(temp) < 999
            )
            return float(temp) / 10
        return self._sensor_temperature

    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        # pylint: disable=too-many-return-statements,too-many-branches
        if not self._system.get_stored_status().system_on:
            return HVACMode.OFF
        if self._system.get_stored_status().mode == RinnaiSystemMode.COOLING:
            if self._system.get_stored_status().unit_status.is_on:
                return HVACMode.COOL
            # system on, cooling mode, but cooling off indicates fan only
            return HVACMode.FAN_ONLY
        if self._system.get_stored_status().mode == RinnaiSystemMode.HEATING:
            if self._system.get_stored_status().unit_status.is_on:
                return HVACMode.HEAT
            # system on, heater mode, but heater off indicates fan only
            return HVACMode.FAN_ONLY
        if self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
            return HVACMode.COOL
        return HVACMode.OFF

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        if self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
            return [HVACMode.COOL, HVACMode.HEAT, HVACMode.OFF]
        return [HVACMode.COOL, HVACMode.HEAT, HVACMode.FAN_ONLY, HVACMode.OFF]

    @property
    def preset_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        if self._system.get_stored_status().unit_status.operating_mode == RinnaiOperatingMode.AUTO:
            return PRESET_AUTO
        return PRESET_MANUAL

    @property
    def preset_modes(self):
        """Return the list of available HVAC modes."""
        return [PRESET_AUTO, PRESET_MANUAL]

    def turn_aux_heat_on(self):
        """Turn auxiliary heater on."""
        return False

    def turn_aux_heat_off(self):
        """Turn auxiliary heater off."""
        return False

    def update_external_temperature(self):
        """Update external temperature reading."""
        _LOGGER.debug(
            "External temperature sensor entity name: %s", self._temerature_entity_name
        )
        if self._temerature_entity_name is not None:
            temperature_entity = self._hass.states.get(self._temerature_entity_name)
            # _LOGGER.debug("External temperature sensor entity: %s", temperature_entity)
            if (
                temperature_entity is not None
                and temperature_entity.state != "unavailable"
            ):
                _LOGGER.debug(
                    "External temperature sensor reports: %s", temperature_entity.state
                )
                try:
                    self._sensor_temperature = float(temperature_entity.state)
                except ValueError:
                    self._sensor_temperature = 0

    @property
    def available(self):
        if self._system.get_stored_status().mode != RinnaiSystemMode.NONE:
            return True
        return False


class RinnaiTouchZone(ClimateEntity):
    """Climate entity for a zone."""

    # pylint: disable=too-many-instance-attributes,too-many-public-methods

    # some common
    def __init__(self, hass, ip_address, name, zone, temperature_entity=None):
        # pylint: disable=too-many-arguments

        _LOGGER.debug("Set up RinnaiTouch zone %s entity %s", zone, ip_address)
        self._system = RinnaiSystem.get_instance(ip_address)
        device_id = "rinnaitouch_zone" + zone + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name + " Zone " + zone
        if zone == "U":
            self._attr_name = name + "Common Zone"
        self._attr_zone = zone

        self._hass = hass

        self._temerature_entity_name = temperature_entity
        self._sensor_temperature = 0
        self.update_external_temperature()

        self._support_flags = SUPPORT_FLAGS_ZONE

        self._TEMPERATURE_STEP = 1
        self._TEMPERATURE_LIMITS = {"min": 8, "max": 30}
        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        # this very infrequently fails on startup so wrapping in try except
        try:
            self.schedule_update_ha_state()
        except:  # pylint: disable=bare-except
            pass

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

    # not common
    # @property
    # def device_info(self):
    #    """Return device information about this heater."""
    #    return {
    #        "connections": {(CONNECTION_NETWORK_MAC, self._host)},
    #        "identifiers": {("Rinnai Touch Zone", self.unique_id)},
    #        "model": "Rinnai Touch Wifi Zone",
    #        "name": self.name,
    #        "manufacturer": "Rinnai/Brivis",
    #    }

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        hvac_mode = self.hvac_mode

        if hvac_mode == HVACMode.OFF:
            return "mdi:hvac-off"

        if hvac_mode == HVACMode.FAN_ONLY:
            return "mdi:fan"

        if hvac_mode == HVACMode.COOL:
            if self.cooling_mode == COOLING_EVAP:
                return "mdi:snowflake-melt"
            return "mdi:snowflake"

        if hvac_mode == HVACMode.HEAT:
            return "mdi:fire"

        return "mdi:hvac"

    @property
    def cooling_mode(self):
        """Return the cooling mode we're in mode."""
        if self._system.get_stored_status().mode == RinnaiSystemMode.COOLING:
            return COOLING_COOL
        if self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
            return COOLING_EVAP
        return COOLING_NONE

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._system.get_stored_status().temp_unit == TEMP_FAHRENHEIT:
            return UnitOfTemperature.FAHRENHEIT
        return UnitOfTemperature.CELSIUS

    # not common
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        # pylint: disable=too-many-return-statements
        if self.hvac_mode == HVACMode.OFF:
            return 0

        if self._system.get_stored_status().is_multi_set_point:
            if self.cooling_mode == COOLING_COOL:
                return float(
                    self._system.get_stored_status()
                    .unit_status.zones[self._attr_zone]
                    .set_temp
                )
            if self.cooling_mode == COOLING_EVAP:
                if self.preset_mode == PRESET_AUTO:
                    return int(self._system.get_stored_status().unit_status.comfort)
                if self.preset_mode == PRESET_MANUAL:
                    return int(self._system.get_stored_status().unit_status.fan_speed)
            if self.cooling_mode == COOLING_NONE:
                return float(
                    self._system.get_stored_status()
                    .unit_status.zones[self._attr_zone]
                    .set_temp
                )

        if self.cooling_mode == COOLING_COOL:
            return float(self._system.get_stored_status().unit_status.set_temp)
        if self.cooling_mode == COOLING_EVAP:
            if self.preset_mode == PRESET_AUTO:
                return int(self._system.get_stored_status().unit_status.comfort)
            if self.preset_mode == PRESET_MANUAL:
                return int(self._system.get_stored_status().unit_status.fan_speed)
        if self.cooling_mode == COOLING_NONE:
            return float(self._system.get_stored_status().unit_status.set_temp)

        return 999

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._TEMPERATURE_STEP

    # not common
    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self._system.get_stored_status().is_multi_set_point:
            if self.cooling_mode in (COOLING_COOL, COOLING_NONE):
                return self._TEMPERATURE_LIMITS["min"]
        return self.target_temperature

    # not common
    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self._system.get_stored_status().is_multi_set_point:
            if self.cooling_mode in (COOLING_COOL, COOLING_NONE):
                return self._TEMPERATURE_LIMITS["max"]
        return self.target_temperature

    @property
    def preferred_cooling_mode(self):
        """Return the preferred cooling mode, prioritising refrigerated over evap."""
        if RinnaiCapabilities.COOLER in self._system.get_stored_status().capabilities:
            return COOLING_COOL
        if RinnaiCapabilities.EVAP in self._system.get_stored_status().capabilities:
            return COOLING_EVAP
        return COOLING_NONE

    # not common
    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        # pylint: disable=too-many-branches
        # _LOGGER.debug("Setting new HVAC mode from %s to %s", self.hvac_mode, hvac_mode)
        if not hvac_mode == self.hvac_mode:
            if hvac_mode == HVACMode.HEAT and self.cooling_mode == COOLING_NONE:
                # turn whatever the preset is on and put it into manual mode
                await self._system.turn_unit_zone_on(self._attr_zone)
            elif hvac_mode == HVACMode.COOL:
                # turn whatever the preset is on and put it into auto mode
                if self.preferred_cooling_mode == COOLING_COOL:
                    await self._system.turn_unit_zone_on(self._attr_zone)
                if self.preferred_cooling_mode == COOLING_EVAP:
                    await self._system.turn_evap_zone_on(self._attr_zone)
            elif hvac_mode == HVACMode.OFF:
                # turn whatever the preset is off
                if self.cooling_mode == COOLING_COOL:
                    await self._system.turn_unit_zone_off(self._attr_zone)
                if self.cooling_mode == COOLING_EVAP:
                    await self._system.turn_evap_zone_off(self._attr_zone)
                if self.cooling_mode == COOLING_NONE:
                    await self._system.turn_unit_zone_off(self._attr_zone)

    # not common
    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        if not preset_mode == self.preset_mode:
            if preset_mode == PRESET_AUTO:
                if self.cooling_mode == COOLING_COOL:
                    await self._system.set_unit_zone_auto(self._attr_zone)
                if self.cooling_mode == COOLING_EVAP:
                    await self._system.set_evap_zone_auto(self._attr_zone)
                if self.cooling_mode == COOLING_NONE:
                    await self._system.set_unit_zone_auto(self._attr_zone)
            if preset_mode == PRESET_MANUAL:
                if self.cooling_mode == COOLING_COOL:
                    await self._system.set_unit_zone_manual(self._attr_zone)
                if self.cooling_mode == COOLING_EVAP:
                    await self._system.set_evap_zone_manual(self._attr_zone)
                if self.cooling_mode == COOLING_NONE:
                    await self._system.set_unit_zone_manual(self._attr_zone)

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            await self.async_set_target_temperature(kwargs.get(ATTR_TEMPERATURE))

    # not common
    async def async_set_target_temperature(self, target_temperature):
        """Set the new target temperate in a zone."""
        if self._system.get_stored_status().is_multi_set_point:
            target_temperature = int(round(target_temperature))

            if not self.min_temp <= target_temperature <= self.max_temp:
                raise ValueError(
                    f"Target temperature ({target_temperature}) must be between "
                    f"{self.min_temp} and {self.max_temp}."
                )
            if self.cooling_mode == COOLING_COOL:
                await self._system.set_unit_zone_temp(
                    self._attr_zone, target_temperature
                )
            if self.cooling_mode == COOLING_NONE:
                await self._system.set_unit_zone_temp(
                    self._attr_zone, target_temperature
                )
        else:
            return False

    # not common
    @property
    def current_temperature(self):
        """Return the current temperature."""
        temp = temp = (
            self._system.get_stored_status()
            .unit_status.zones[self._attr_zone]
            .temperature
        )

        if int(temp) < 999:
            return float(temp) / 10
        return self._sensor_temperature

    # not common
    @property
    def hvac_mode(self):
        """Return current HVAC mode, ie Heat or Off."""
        # pylint: disable=too-many-return-statements
        if self.cooling_mode == COOLING_COOL:
            if (
                self._attr_zone
                not in self._system.get_stored_status().unit_status.zones.keys()
            ):
                return HVACMode.OFF
            return HVACMode.COOL
        if self.cooling_mode == COOLING_NONE:
            if (
                self._attr_zone
                not in self._system.get_stored_status().unit_status.zones.keys()
            ):
                return HVACMode.OFF
            return HVACMode.HEAT
        if self.cooling_mode == COOLING_EVAP:
            if (
                self._attr_zone
                not in self._system.get_stored_status().unit_status.zones.keys()
            ):
                return HVACMode.OFF
            return HVACMode.COOL
        return HVACMode.OFF

    # not common. Only return the mode that is set on the main
    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        if self._system.get_stored_status().mode == RinnaiSystemMode.HEATING:
            return [HVACMode.HEAT, HVACMode.OFF]
        if self._system.get_stored_status().mode == RinnaiSystemMode.COOLING:
            return [HVACMode.COOL, HVACMode.OFF]
        if self._system.get_stored_status().mode == RinnaiSystemMode.EVAP:
            return [HVACMode.COOL, HVACMode.OFF]
        return [HVACMode.OFF]

    @property
    def preset_mode(self):
        """Return current Preset mode, ie Auto or Manual."""
        # pylint: disable=too-many-return-statements
        if (
            self._system.get_stored_status()
            .unit_status.zones[self._attr_zone]
            .auto_mode
        ):
            return PRESET_AUTO
        return PRESET_MANUAL

    # not common. Only return the mode that is set on the main
    @property
    def preset_modes(self):
        """Return the list of available Preset modes."""
        return [PRESET_AUTO, PRESET_MANUAL]

    def turn_aux_heat_on(self):
        """Turn auxiliary heater on."""
        return False

    def turn_aux_heat_off(self):
        """Turn auxiliary heater off."""
        return False

    # not common
    async def async_update(self):
        """Do nothing."""
        pass  # pylint: disable=unnecessary-pass

    # not common
    @property
    def available(self):
        if self._system.get_stored_status().mode \
                in (RinnaiSystemMode.COOLING, RinnaiSystemMode.HEATING):
            return (
                self._attr_zone
                in self._system.get_stored_status().unit_status.zones.keys()
            )
        return False

    def update_external_temperature(self):
        """Update latest external temperature reading."""
        _LOGGER.debug(
            "External temperature sensor entity name (zone %s): %s",
            self._attr_zone,
            self._temerature_entity_name,
        )
        if self._temerature_entity_name is not None and self._hass:
            temperature_entity = self._hass.states.get(self._temerature_entity_name)
            # _LOGGER.debug("External temperature sensor entity: %s", temperature_entity)
            if (
                temperature_entity is not None
                and temperature_entity.state != "unavailable"
            ):
                _LOGGER.debug(
                    "External temperature sensor reports: %s", temperature_entity.state
                )
                try:
                    self._sensor_temperature = int(
                        round(float(temperature_entity.state))
                    )
                except ValueError:
                    self._sensor_temperature = 0
