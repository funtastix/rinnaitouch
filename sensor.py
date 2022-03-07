"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_HOST,
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
    async_add_entities([
        RinnaiMainTemperatureSensor(ip_address, "Rinnai Touch Main Temperature Sensor", "temperature"),
        RinnaiMainTemperatureSensor(ip_address, "Rinnai Touch Main Target Temperature Sensor", "setTemp")
    ])
    if entry.data.get(CONF_ZONE_A):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address, "A", "Rinnai Touch Zone A Target Temperature Sensor", "setTemp"),
            RinnaiZoneTemperatureSensor(ip_address, "A", "Rinnai Touch Zone A Temperature Sensor", "temp")
        ])
    if entry.data.get(CONF_ZONE_B):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address, "B", "Rinnai Touch Zone B Target Temperature Sensor", "setTemp"),
            RinnaiZoneTemperatureSensor(ip_address, "B", "Rinnai Touch Zone B Temperature Sensor", "temp")
        ])
    if entry.data.get(CONF_ZONE_C):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address, "C", "Rinnai Touch Zone C Target Temperature Sensor", "setTemp"),
            RinnaiZoneTemperatureSensor(ip_address, "C", "Rinnai Touch Zone C Temperature Sensor", "temp")
        ])
    if entry.data.get(CONF_ZONE_D):
        async_add_entities([
            RinnaiZoneTemperatureSensor(ip_address, "D", "Rinnai Touch Zone C Target Temperature Sensor", "setTemp"),
            RinnaiZoneTemperatureSensor(ip_address, "D", "Rinnai Touch Zone C Temperature Sensor", "temp")
        ])
    return True

class RinnaiTemperatureSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, ip_address, name):
        self._host = ip_address
        self._system = RinnaiSystem.getInstance(ip_address)
        device_id = str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name

        self._attr_native_unit_of_measurement = TEMP_CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
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
        return "mdi:thermometer"

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_native_value = 0

class RinnaiMainTemperatureSensor(RinnaiTemperatureSensor):

    def __init__(self, ip_address, name, temp_attr):
        super().__init__(ip_address, name)
        self._temp_attr = temp_attr
        device_id = str.lower(self.__class__.__name__) + "_" + temp_attr + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self.multiplier = 10
        if self._temp_attr == "setTemp":
            self.multiplier = 1

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        if self._system._status.coolingMode:
            self._attr_native_value = int(round(float(getattr(self._system._status.coolingStatus,self._temp_attr))/self.multiplier))
        elif self._system._status.heaterMode:
            self._attr_native_value = int(round(float(getattr(self._system._status.heaterStatus,self._temp_attr))/self.multiplier))
        elif self._system._status.evapMode and self._temp_attr == "temperature":
            self._attr_native_value = int(round(float(getattr(self._system._status.evapStatus,self._temp_attr))/self.multiplier))
        else:
            self._attr_native_value = 0

    @property
    def available(self):
        if self._system._status.heaterMode:
            return not getattr(self._system._status.coolingStatus,self._temp_attr) == 999
        elif self._system._status.coolingMode:
            return not getattr(self._system._status.heaterStatus,self._temp_attr) == 999
        elif self._system._status.evapMode and self._temp_attr == "temperature":
            return not getattr(self._system._status.evapStatus,self._temp_attr) == 999
        return False

class RinnaiZoneTemperatureSensor(RinnaiTemperatureSensor):

    def __init__(self, ip_address, zone, name, temp_attr = "temp"):
        super().__init__(ip_address, name)
        self._attr_zone = zone
        self._temp_attr = temp_attr
        device_id = str.lower(self.__class__.__name__) + "_" + temp_attr + "_" + zone + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self.multiplier = 10
        if self._temp_attr == "setTemp":
            self.multiplier = 1

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        if self._system._status.coolingMode and self._attr_zone in self._system._status.coolingStatus.zones:
            self._attr_native_value = int(round(float(getattr(self._system._status.coolingStatus,"zone" + self._attr_zone + self._temp_attr))/self.multiplier))
        elif self._system._status.heaterMode and self._attr_zone in self._system._status.heaterStatus.zones:
            self._attr_native_value = int(round(float(getattr(self._system._status.heaterStatus,"zone" + self._attr_zone + self._temp_attr))/self.multiplier))
        elif self._system._status.evapMode and self._attr_zone in self._system._status.evapStatus.zones and self._temp_attr == "temp":
            self._attr_native_value = int(round(float(getattr(self._system._status.evapStatus,"zone" + self._attr_zone + self._temp_attr))/self.multiplier))
        else:
            self._attr_native_value = 0

    @property
    def available(self):
        if self._system._status.heaterMode and self._attr_zone in self._system._status.heaterStatus.zones:
            return not getattr(self._system._status.heaterStatus,"zone" + self._attr_zone + self._temp_attr) == 999
        elif self._system._status.coolingMode and self._attr_zone in self._system._status.coolingStatus.zones:
            return not getattr(self._system._status.coolingStatus,"zone" + self._attr_zone + self._temp_attr) == 999
        elif self._system._status.evapMode and self._attr_zone in self._system._status.evapStatus.zones and self._temp_attr == "temp":
            return not getattr(self._system._status.evapStatus,"zone" + self._attr_zone + self._temp_attr) == 999
        return False
