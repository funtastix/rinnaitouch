"""Platform for sensor integration."""
from __future__ import annotations
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.const import TEMP_CELSIUS
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST
)

from pyrinnaitouch import RinnaiSystem, SchedulePeriod

from .const import (
    CONF_ZONE_A,
    CONF_ZONE_B,
    CONF_ZONE_C,
    CONF_ZONE_D
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities): # pylint: disable=unused-argument
    """Set up the sensor entities."""
    ip_address = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME)
    if name == "":
        name = "Rinnai Touch"
    async_add_entities([
        RinnaiMainTemperatureSensor(ip_address,
                                    name + " Main Temperature Sensor",
                                    "temperature"),
        RinnaiMainTemperatureSensor(ip_address,
                                    name + " Main Target Temperature Sensor",
                                    "set_temp"),
        RinnaiSchedulePeriodSensor(ip_address,
                                   name + " Schedule Time Period Sensor"),
        RinnaiAdvancePeriodSensor(ip_address,
                                  name + " Advance Time Period Sensor")
    ])
    if entry.data.get(CONF_ZONE_A):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address,
                                        "A",
                                        name + " Zone A Target Temperature Sensor",
                                        "set_temp"),
            RinnaiZoneTemperatureSensor(ip_address,
                                        "A",
                                        name + " Zone A Temperature Sensor",
                                        "temp")
        ])
    if entry.data.get(CONF_ZONE_B):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address,
                                        "B",
                                        name + " Zone B Target Temperature Sensor",
                                        "set_temp"),
            RinnaiZoneTemperatureSensor(ip_address,
                                        "B",
                                        name + " Zone B Temperature Sensor",
                                        "temp")
        ])
    if entry.data.get(CONF_ZONE_C):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address,
                                        "C",
                                        name + " Zone C Target Temperature Sensor",
                                        "set_temp"),
            RinnaiZoneTemperatureSensor(ip_address,
                                        "C",
                                        name + " Zone C Temperature Sensor",
                                        "temp")
        ])
    if entry.data.get(CONF_ZONE_D):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address,
                                        "D",
                                        name + " Zone C Target Temperature Sensor",
                                        "set_temp"),
            RinnaiZoneTemperatureSensor(ip_address,
                                        "D",
                                        name + " Zone C Temperature Sensor",
                                        "temp")
        ])
    return True

class RinnaiTemperatureSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, ip_address, name):
        self._system = RinnaiSystem.get_instance(ip_address)
        device_id = str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name

        self._attr_native_unit_of_measurement = TEMP_CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        #this very infrequently fails on startup so wrapping in try except
        try:
            self.schedule_update_ha_state()
        except:
            pass 

    @property
    def name(self):
        """Name of the entity."""
        return self._attr_name

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:thermometer"

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_native_value = 0

class RinnaiMainTemperatureSensor(RinnaiTemperatureSensor):
    """Temparature sensor on the main unit"""

    def __init__(self, ip_address, name, temp_attr):
        super().__init__(ip_address, name)
        self._temp_attr = temp_attr
        device_id = str.lower(self.__class__.__name__) + "_" + temp_attr + "_" \
                    + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self.multiplier = 10
        if self._temp_attr == "set_temp":
            self.multiplier = 1

    @property
    def native_value(self) -> float:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        if self._system.get_stored_status().cooling_mode:
            return float(getattr(
                            self._system.get_stored_status().cooling_status,
                            self._temp_attr
                        ))/self.multiplier
        if self._system.get_stored_status().heater_mode:
            return float(getattr(
                            self._system.get_stored_status().heater_status,
                            self._temp_attr
                        ))/self.multiplier
        if self._system.get_stored_status().evap_mode and self._temp_attr == "temperature":
            return float(getattr(
                            self._system.get_stored_status().evap_status,
                            self._temp_attr
                        ))/self.multiplier
        return 0

    @property
    def available(self):
        return self.native_value < 99 and self.native_value > 0
#        if self._system.get_stored_status().cooling_mode:
#            return not getattr(
#                        self._system.get_stored_status().cooling_status,
#                        self._temp_attr
#                    ) == 999
#        if self._system.get_stored_status().heater_mode:
#            return not getattr(
#                        self._system.get_stored_status().heater_status,
#                        self._temp_attr
#                    ) == 999
#        if self._system.get_stored_status().evap_mode and self._temp_attr == "temperature":
#            return not getattr(
#                        self._system.get_stored_status().evap_status,
#                        self._temp_attr
#                    ) == 999
#        return False

class RinnaiZoneTemperatureSensor(RinnaiTemperatureSensor):
    """Temperature sensor on a zone."""

    def __init__(self, ip_address, zone, name, temp_attr = "temp"):
        super().__init__(ip_address, name)
        self._attr_zone = zone
        self._temp_attr = temp_attr
        device_id = str.lower(self.__class__.__name__) + "_" + temp_attr + "_" \
                    + zone + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self.multiplier = 10
        if self._temp_attr == "set_temp":
            self.multiplier = 1

    @property
    def native_value(self) -> float:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        if (
            self._system.get_stored_status().cooling_mode
            and self._attr_zone in self._system.get_stored_status().cooling_status.zones
        ):
            return float(getattr(
                            self._system.get_stored_status().cooling_status,
                            "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
                        ))/self.multiplier
        if (
            self._system.get_stored_status().heater_mode
            and self._attr_zone in self._system.get_stored_status().heater_status.zones
        ):
            return float(getattr(
                            self._system.get_stored_status().heater_status,
                            "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
                        ))/self.multiplier
        if (
            self._system.get_stored_status().evap_mode
            and self._attr_zone in self._system.get_stored_status().evap_status.zones
            and self._temp_attr == "temp"
        ):
            return float(getattr(
                            self._system.get_stored_status().evap_status,
                            "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
                        ))/self.multiplier
        return 0

    @property
    def available(self):
        return self.native_value < 99 and self.native_value > 0
#        if (
#            self._system.get_stored_status().heater_mode
#            and self._attr_zone in self._system.get_stored_status().heater_status.zones
#        ):
#            return not getattr(
#                    self._system.get_stored_status().heater_status,
#                    "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
#                ) == 999
#        if (
#            self._system.get_stored_status().cooling_mode
#            and self._attr_zone in self._system.get_stored_status().cooling_status.zones
#        ):
#            return not getattr(
#                    self._system.get_stored_status().cooling_status,
#                    "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
#                ) == 999
#        if (
#            self._system.get_stored_status().evap_mode
#            and self._attr_zone in self._system.get_stored_status().evap_status.zones
#            and self._temp_attr == "temp"
#        ):
#            return not getattr(
#                    self._system.get_stored_status().evap_status,
#                    "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
#                ) == 999
#        return False

class RinnaiPeriodSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, ip_address, name):
        self._system = RinnaiSystem.get_instance(ip_address)
        device_id = str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name
        self._attr_period = None

        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        #this very infrequently fails on startup so wrapping in try except
        try:
            self.schedule_update_ha_state()
        except:
            pass 

    @property
    def name(self):
        """Name of the entity."""
        return self._attr_name

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:calendar-question"

    @property
    def native_value(self) -> str | None:
        """Fetch new state data for the sensor."""
        state = self._system.get_stored_status()
        if not state.system_on:
            return "N/A"
        if (
            state.cooling_mode
            and state.cooling_status.cooling_on
            and state.cooling_status.auto_mode
        ):
            return self.schedule_period_to_str(state.cooling_status)
        if (
            state.heater_mode
            and state.heater_status.heater_on
            and state.heater_status.auto_mode
        ):
            return self.schedule_period_to_str(state.heater_status)
        return "N/A"

    def schedule_period_to_str(self, status) -> str | None:
        """Convert SchedulePeriod to a UI presentable sensor string value."""
        state = getattr(status, self._attr_period)
        if state == SchedulePeriod.WAKE:
            return "Wake"
        if state == SchedulePeriod.LEAVE:
            return "Leave"
        if state == SchedulePeriod.RETURN:
            return "Return"
        if state == SchedulePeriod.PRE_SLEEP:
            return "Pre-Sleep"
        if state == SchedulePeriod.SLEEP:
            return "Sleep"
        return None

class RinnaiSchedulePeriodSensor(RinnaiPeriodSensor):
    """Main on/off switch for the system."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_period = "schedule_period"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:calendar-month"

class RinnaiAdvancePeriodSensor(RinnaiPeriodSensor):
    """Main on/off switch for the system."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_period = "advance_period"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:calendar-arrow-right"

    @property
    def native_value(self):
        if (
            self._system.get_stored_status().heater_status.advanced
            or self._system.get_stored_status().cooling_status.advanced
        ):
            return super().native_value
        return "N/A"
