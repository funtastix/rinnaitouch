"""Platform for sensor integration."""
from __future__ import annotations
#import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.const import UnitOfTemperature
from homeassistant.const import CONF_NAME, CONF_HOST

from pyrinnaitouch import (
    RinnaiSystem,
    RinnaiSchedulePeriod,
    RinnaiSystemMode,
    RinnaiOperatingMode,
    RinnaiSystemStatus
)

from .const import (
    CONF_ZONE_A,
    CONF_ZONE_B,
    CONF_ZONE_C,
    CONF_ZONE_D,
    CONF_ZONE_COMMON,
    DEFAULT_NAME
)

#_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass, entry, async_add_entities
):  # pylint: disable=unused-argument
    """Set up the sensor entities."""
    ip_address = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME)
    if name == "":
        name = DEFAULT_NAME
    async_add_entities(
        [
            RinnaiMainTemperatureSensor(ip_address, name, "temperature"),
            RinnaiMainTemperatureSensor(ip_address, name, "set_temp"),
            RinnaiSchedulePeriodSensor(ip_address, name),
            RinnaiAdvancePeriodSensor(ip_address, name),
        ]
    )
    if entry.data.get(CONF_ZONE_A):
        async_add_entities(
            [
                RinnaiZoneTemperatureSensor(ip_address,"A",name,"set_temp"),
                RinnaiZoneTemperatureSensor(ip_address, "A", name, "temperature"),
            ]
        )
    if entry.data.get(CONF_ZONE_B):
        async_add_entities(
            [
                RinnaiZoneTemperatureSensor(ip_address,"B",name,"set_temp"),
                RinnaiZoneTemperatureSensor(ip_address, "B", name, "temperature"),
            ]
        )
    if entry.data.get(CONF_ZONE_C):
        async_add_entities(
            [
                RinnaiZoneTemperatureSensor(ip_address,"C",name,"set_temp"),
                RinnaiZoneTemperatureSensor(ip_address, "C", name, "temperature"),
            ]
        )
    if entry.data.get(CONF_ZONE_D):
        async_add_entities(
            [
                RinnaiZoneTemperatureSensor(ip_address,"D",name,"set_temp"),
                RinnaiZoneTemperatureSensor(ip_address, "D", name, "temperature"),
            ]
        )
    if entry.data.get(CONF_ZONE_COMMON):
        async_add_entities(
            [
                RinnaiZoneTemperatureSensor(ip_address,"U",name,"set_temp"),
                RinnaiZoneTemperatureSensor(ip_address, "U", name, "temperature"),
            ]
        )
    return True


class RinnaiTemperatureSensor(SensorEntity):
    """Representation of a Sensor."""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, ip_address, name):
        self._system: RinnaiSystem = RinnaiSystem.get_instance(ip_address)
        device_id = (
            str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")
        )

        self._host = ip_address
        self._attr_unique_id = device_id
        self._attr_name = name
        self._attr_device_name = name

        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        # this very infrequently fails on startup so wrapping in try except
        try:
            self.schedule_update_ha_state()
        except:  # pylint: disable=bare-except
            pass

    @property
    def device_info(self):
        """Return device information about this heater."""
        return {
            #"connections": {(CONNECTION_NETWORK_MAC, self._host)},
            "identifiers": {("rinnai_touch", self._host)},
            "model": "Rinnai Touch Wifi",
            "name": self._attr_device_name,
            "manufacturer": "Rinnai/Brivis",
        }

    @property
    def name(self):
        """Name of the entity."""
        return self._attr_name._attr_name.replace("Zone U", "Common Zone")

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
        if temp_attr == "set_temp":
            self._attr_name = name + " Main Target Temperature Sensor"
        else:
            self._attr_name = name + " Main Temperature Sensor"
        self._temp_attr = temp_attr
        device_id = (
            str.lower(self.__class__.__name__)
            + "_"
            + temp_attr
            + "_"
            + str.replace(ip_address, ".", "_")
        )

        self._attr_unique_id = device_id
        self.multiplier = 10
        if self._temp_attr == "set_temp":
            self.multiplier = 1

    @property
    def native_value(self) -> float:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if state.mode in (RinnaiSystemMode.COOLING, RinnaiSystemMode.HEATING):
            return (
                float(
                    getattr(
                        state.unit_status, self._temp_attr
                    )
                )
                / self.multiplier
            )
        if (
            state.mode == RinnaiSystemMode.EVAP
            and self._temp_attr == "temperature"
        ):
            return (
                float(
                    getattr(
                        state.unit_status, self._temp_attr
                    )
                )
                / self.multiplier
            )
        return 0

    @property
    def available(self):
        return self.native_value < 99 and self.native_value > 0

class RinnaiZoneTemperatureSensor(RinnaiTemperatureSensor):
    """Temperature sensor on a zone."""

    def __init__(self, ip_address, zone, name, temp_attr="temperature"):
        super().__init__(ip_address, name)
        if temp_attr == "set_temp":
            self._attr_name = name + " Zone " + zone + " Target Temperature Sensor"
        else:
            self._attr_name = name + " Zone " + zone + " Temperature Sensor"
        self._attr_zone = zone
        self._temp_attr = temp_attr
        device_id = (
            str.lower(self.__class__.__name__)
            + "_"
            + temp_attr
            + "_"
            + zone
            + str.replace(ip_address, ".", "_")
        )

        self._attr_unique_id = device_id
        self.multiplier = 10
        if self._temp_attr == "set_temp":
            self.multiplier = 1

    @property
    def native_value(self) -> float:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if (
            state.mode in (RinnaiSystemMode.COOLING, RinnaiSystemMode.HEATING)
            and self._attr_zone in state.unit_status.zones.keys()
        ):
            return (
                float(
                    getattr(
                        state.unit_status.zones[self._attr_zone],
                        self._temp_attr,
                    )
                )
                / self.multiplier
            )
        if (
            state.mode == RinnaiSystemMode.EVAP
            and self._attr_zone in state.unit_status.zones.keys()
            and self._temp_attr == "temperature"
        ):
            return (
                float(
                    getattr(
                        state.unit_status.zones[self._attr_zone],
                        self._temp_attr,
                    )
                )
                / self.multiplier
            )
        return 0

    @property
    def available(self):
        return self.native_value < 99 and self.native_value > 0


class RinnaiPeriodSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, ip_address, name):
        self._system = RinnaiSystem.get_instance(ip_address)
        device_id = (
            str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")
        )

        self._host = ip_address
        self._attr_unique_id = device_id
        self._attr_name = name
        self._attr_device_name = name
        self._attr_period = None

        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        # this very infrequently fails on startup so wrapping in try except
        try:
            self.schedule_update_ha_state()
        except:  # pylint: disable=bare-except
            pass

    @property
    def device_info(self):
        """Return device information about this heater."""
        return {
            #"connections": {(CONNECTION_NETWORK_MAC, self._host)},
            "identifiers": {("rinnai_touch", self._host)},
            "model": "Rinnai Touch Wifi",
            "name": self._attr_device_name,
            "manufacturer": "Rinnai/Brivis",
        }

    @property
    def name(self):
        """Name of the entity."""
        return self._attr_name._attr_name.replace("Zone U", "Common Zone")

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
            state.mode in (RinnaiSystemMode.COOLING, RinnaiSystemMode.HEATING)
            and state.unit_status.is_on
            and state.unit_status.operating_mode == RinnaiOperatingMode.AUTO
        ):
            return self.schedule_period_to_str(state.unit_status)
        return "N/A"

    def schedule_period_to_str(self, status) -> str | None:
        """Convert SchedulePeriod to a UI presentable sensor string value."""
        state = getattr(status, self._attr_period)
        if state == RinnaiSchedulePeriod.WAKE:
            return "Wake"
        if state == RinnaiSchedulePeriod.LEAVE:
            return "Leave"
        if state == RinnaiSchedulePeriod.RETURN:
            return "Return"
        if state == RinnaiSchedulePeriod.PRE_SLEEP:
            return "Pre-Sleep"
        if state == RinnaiSchedulePeriod.SLEEP:
            return "Sleep"
        return None


class RinnaiSchedulePeriodSensor(RinnaiPeriodSensor):
    """Main on/off switch for the system."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_name = name + " Schedule Time Period Sensor"
        self._attr_period = "schedule_period"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:calendar-month"


class RinnaiAdvancePeriodSensor(RinnaiPeriodSensor):
    """Main on/off switch for the system."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_name = name + " Advance Time Period Sensor"
        self._attr_period = "advance_period"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:calendar-arrow-right"

    @property
    def native_value(self):
        if self._system.get_stored_status().unit_status.advanced:
            return super().native_value
        return "N/A"
