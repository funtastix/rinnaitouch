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
    """Set up the sensor entities."""
    ip_address = entry.data.get(CONF_HOST)
    async_add_entities([
        RinnaiMainTemperatureSensor(ip_address,
                                    "Rinnai Touch Main Temperature Sensor",
                                    "temperature"),
        RinnaiMainTemperatureSensor(ip_address,
                                    "Rinnai Touch Main Target Temperature Sensor",
                                    "set_temp")
    ])
    if entry.data.get(CONF_ZONE_A):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address,
                                        "A",
                                        "Rinnai Touch Zone A Target Temperature Sensor",
                                        "set_temp"),
            RinnaiZoneTemperatureSensor(ip_address,
                                        "A",
                                        "Rinnai Touch Zone A Temperature Sensor",
                                        "temp")
        ])
    if entry.data.get(CONF_ZONE_B):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address,
                                        "B",
                                        "Rinnai Touch Zone B Target Temperature Sensor",
                                        "set_temp"),
            RinnaiZoneTemperatureSensor(ip_address,
                                        "B",
                                        "Rinnai Touch Zone B Temperature Sensor",
                                        "temp")
        ])
    if entry.data.get(CONF_ZONE_C):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address,
                                        "C",
                                        "Rinnai Touch Zone C Target Temperature Sensor",
                                        "set_temp"),
            RinnaiZoneTemperatureSensor(ip_address,
                                        "C",
                                        "Rinnai Touch Zone C Temperature Sensor",
                                        "temp")
        ])
    if entry.data.get(CONF_ZONE_D):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address,
                                        "D",
                                        "Rinnai Touch Zone C Target Temperature Sensor",
                                        "set_temp"),
            RinnaiZoneTemperatureSensor(ip_address,
                                        "D",
                                        "Rinnai Touch Zone C Temperature Sensor",
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
        self.async_write_ha_state()

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

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        if self._system.get_stored_status().cooling_mode:
            self._attr_native_value = int(round(float(getattr(
                                            self._system.get_stored_status().cooling_status,
                                            self._temp_attr
                                        ))/self.multiplier))
        elif self._system.get_stored_status().heater_mode:
            self._attr_native_value = int(round(float(getattr(
                                            self._system.get_stored_status().heater_status,
                                            self._temp_attr
                                        ))/self.multiplier))
        elif self._system.get_stored_status().evap_mode and self._temp_attr == "temperature":
            self._attr_native_value = int(round(float(getattr(
                                            self._system.get_stored_status().evap_status,
                                            self._temp_attr
                                        ))/self.multiplier))
        else:
            self._attr_native_value = 0

    @property
    def available(self):
        if self._system.get_stored_status().heater_mode:
            return not getattr(
                        self._system.get_stored_status().cooling_status,
                        self._temp_attr
                    ) == 999
        if self._system.get_stored_status().cooling_mode:
            return not getattr(
                        self._system.get_stored_status().heater_status,
                        self._temp_attr
                    ) == 999
        if self._system.get_stored_status().evap_mode and self._temp_attr == "temperature":
            return not getattr(
                        self._system.get_stored_status().evap_status,
                        self._temp_attr
                    ) == 999
        return False

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

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        if (
            self._system.get_stored_status().cooling_mode
            and self._attr_zone in self._system.get_stored_status().cooling_status.zones
        ):
            self._attr_native_value = int(round(float(getattr(
                                        self._system.get_stored_status().cooling_status,
                                        "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
                                    ))/self.multiplier))
        elif (
            self._system.get_stored_status().heater_mode
            and self._attr_zone in self._system.get_stored_status().heater_status.zones
        ):
            self._attr_native_value = int(round(float(getattr(
                                        self._system.get_stored_status().heater_status,
                                        "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
                                    ))/self.multiplier))
        elif (
            self._system.get_stored_status().evap_mode
            and self._attr_zone in self._system.get_stored_status().evap_status.zones
            and self._temp_attr == "temp"
        ):
            self._attr_native_value = int(round(float(getattr(
                                        self._system.get_stored_status().evap_status,
                                        "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
                                    ))/self.multiplier))
        else:
            self._attr_native_value = 0

    @property
    def available(self):
        if (
            self._system.get_stored_status().heater_mode
            and self._attr_zone in self._system.get_stored_status().heater_status.zones
        ):
            return not getattr(
                    self._system.get_stored_status().heater_status,
                    "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
                ) == 999
        if (
            self._system.get_stored_status().cooling_mode
            and self._attr_zone in self._system.get_stored_status().cooling_status.zones
        ):
            return not getattr(
                    self._system.get_stored_status().cooling_status,
                    "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
                ) == 999
        if (
            self._system.get_stored_status().evap_mode
            and self._attr_zone in self._system.get_stored_status().evap_status.zones
            and self._temp_attr == "temp"
        ):
            return not getattr(
                    self._system.get_stored_status().evap_status,
                    "zone_" + self._attr_zone.lower() + "_" + self._temp_attr
                ) == 999
        return False
