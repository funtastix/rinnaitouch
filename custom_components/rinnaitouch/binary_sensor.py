"""Binary sensors for prewetting and preheating"""
# import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import CONF_NAME, CONF_HOST

from pyrinnaitouch import RinnaiSystem, RinnaiSystemMode, RinnaiSystemStatus
from .const import (
    CONF_ZONE_A,
    CONF_ZONE_B,
    CONF_ZONE_C,
    CONF_ZONE_D,
    CONF_ZONE_COMMON,
    DEFAULT_NAME,
)

# _LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass, entry, async_add_entities
):  # pylint: disable=unused-argument
    """Set up the binary sensor entities."""
    ip_address = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME)
    if name == "":
        name = DEFAULT_NAME
    async_add_entities(
        [
            RinnaiPreheatBinarySensorEntity(ip_address, name),
            RinnaiGasValveBinarySensorEntity(ip_address, name),
            RinnaiCallingHeatBinarySensorEntity(ip_address, name),
            RinnaiCompressorBinarySensorEntity(ip_address, name),
            RinnaiCallingCoolBinarySensorEntity(ip_address, name),
            RinnaiPrewetBinarySensorEntity(ip_address, name),
            RinnaiPumpOperatingBinarySensorEntity(ip_address, name),
            RinnaiCoolerBusyBinarySensorEntity(ip_address, name),
            RinnaiFanOperatingBinarySensorEntity(ip_address, name),
        ]
    )
    if entry.data.get(CONF_ZONE_A):
        async_add_entities(
            [
                RinnaiZonePreheatBinarySensorEntity(ip_address, "A", name),
                RinnaiZoneGasValveBinarySensorEntity(ip_address, "A", name),
                RinnaiZoneCallingHeatBinarySensorEntity(ip_address, "A", name),
                RinnaiZoneCompressorBinarySensorEntity(ip_address, "A", name),
                RinnaiZoneCallingCoolBinarySensorEntity(ip_address, "A", name),
                RinnaiZoneFanOperatingBinarySensorEntity(ip_address, "A", name),
            ]
        )
    if entry.data.get(CONF_ZONE_B):
        async_add_entities(
            [
                RinnaiZonePreheatBinarySensorEntity(ip_address, "B", name),
                RinnaiZoneGasValveBinarySensorEntity(ip_address, "B", name),
                RinnaiZoneCallingHeatBinarySensorEntity(ip_address, "B", name),
                RinnaiZoneCompressorBinarySensorEntity(ip_address, "B", name),
                RinnaiZoneCallingCoolBinarySensorEntity(ip_address, "B", name),
                RinnaiZoneFanOperatingBinarySensorEntity(ip_address, "B", name),
            ]
        )
    if entry.data.get(CONF_ZONE_C):
        async_add_entities(
            [
                RinnaiZonePreheatBinarySensorEntity(ip_address, "C", name),
                RinnaiZoneGasValveBinarySensorEntity(ip_address, "C", name),
                RinnaiZoneCallingHeatBinarySensorEntity(ip_address, "C", name),
                RinnaiZoneCompressorBinarySensorEntity(ip_address, "C", name),
                RinnaiZoneCallingCoolBinarySensorEntity(ip_address, "C", name),
                RinnaiZoneFanOperatingBinarySensorEntity(ip_address, "C", name),
            ]
        )
    if entry.data.get(CONF_ZONE_D):
        async_add_entities(
            [
                RinnaiZonePreheatBinarySensorEntity(ip_address, "D", name),
                RinnaiZoneGasValveBinarySensorEntity(ip_address, "D", name),
                RinnaiZoneCallingHeatBinarySensorEntity(ip_address, "D", name),
                RinnaiZoneCompressorBinarySensorEntity(ip_address, "D", name),
                RinnaiZoneCallingCoolBinarySensorEntity(ip_address, "D", name),
                RinnaiZoneFanOperatingBinarySensorEntity(ip_address, "D", name),
            ]
        )
    if entry.data.get(CONF_ZONE_COMMON):
        async_add_entities(
            [
                RinnaiZonePreheatBinarySensorEntity(ip_address, "U", name),
                RinnaiZoneGasValveBinarySensorEntity(ip_address, "U", name),
                RinnaiZoneCallingHeatBinarySensorEntity(ip_address, "U", name),
                RinnaiZoneCompressorBinarySensorEntity(ip_address, "U", name),
                RinnaiZoneCallingCoolBinarySensorEntity(ip_address, "U", name),
                RinnaiZoneFanOperatingBinarySensorEntity(ip_address, "U", name),
            ]
        )
    return True


class RinnaiBinarySensorEntity(BinarySensorEntity):
    """Base class for all binary sensor entities setting up names and system instance."""

    def __init__(self, ip_address, name) -> None:
        self._host = ip_address
        self._system: RinnaiSystem = RinnaiSystem.get_instance(ip_address)
        device_id = (
            str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")
        )

        self._attr_unique_id = device_id
        self._attr_name = name + " Binary Sensor"
        self._attr_device_name = name
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
            # "connections": {(CONNECTION_NETWORK_MAC, self._host)},
            "identifiers": {("rinnai_touch", self._host)},
            "model": "Rinnai Touch Wifi",
            "name": self._attr_device_name,
            "manufacturer": "Rinnai/Brivis",
        }

    @property
    def name(self) -> str:
        """Name of the entity."""
        return self._attr_name.replace("Zone U", "Common Zone")

    @property
    def is_on(self) -> bool:
        return False


class RinnaiUnitStateBinarySensorEntity(RinnaiBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_unit_mode = None
        self._attr_check_multi = True
        self._attr_status_attr = None

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if not self.available:
            return "mdi:eye"
        if self.is_on:
            return "mdi:eye-check"
        return "mdi:eye-remove"

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if self.available:
            return getattr(state.unit_status, self._attr_status_attr, False)
        return False

    @property
    def available(self):
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if self._attr_check_multi:
            if state.is_multi_set_point:
                return False
        return state.mode == self._attr_unit_mode


class RinnaiPreheatBinarySensorEntity(RinnaiUnitStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_name = name + " Preheating Sensor"
        self._attr_unit_mode = RinnaiSystemMode.HEATING
        self._attr_status_attr = "preheating"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:fire-alert"


class RinnaiGasValveBinarySensorEntity(RinnaiUnitStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_name = name + " Gas Valve Active Sensor"
        self._attr_unit_mode = RinnaiSystemMode.HEATING
        self._attr_status_attr = "gas_valve_active"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:gas-burner"


class RinnaiCallingHeatBinarySensorEntity(RinnaiUnitStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_name = name + " Calling Heat Sensor"
        self._attr_unit_mode = RinnaiSystemMode.HEATING
        self._attr_status_attr = "calling_for_heat"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:thermometer-alert"


class RinnaiCompressorBinarySensorEntity(RinnaiUnitStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_name = name + " Compressor Active Sensor"
        self._attr_unit_mode = RinnaiSystemMode.COOLING
        self._attr_status_attr = "compressor_active"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:cog-clockwise"


class RinnaiCallingCoolBinarySensorEntity(RinnaiUnitStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_name = name + " Calling Cool Sensor"
        self._attr_unit_mode = RinnaiSystemMode.COOLING
        self._attr_status_attr = "calling_for_cool"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:thermometer-alert"


class RinnaiPrewetBinarySensorEntity(RinnaiUnitStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_name = name + " Evap Prewetting Sensor"
        self._attr_unit_mode = RinnaiSystemMode.EVAP
        self._attr_check_multi = False
        self._attr_status_attr = "prewetting"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:snowflake-melt"


class RinnaiPumpOperatingBinarySensorEntity(RinnaiUnitStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_name = name + " Pump Operating Sensor"
        self._attr_unit_mode = RinnaiSystemMode.EVAP
        self._attr_check_multi = False
        self._attr_status_attr = "pump_operating"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:water-alert"


class RinnaiCoolerBusyBinarySensorEntity(RinnaiUnitStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_name = name + " Cooler Busy Sensor"
        self._attr_unit_mode = RinnaiSystemMode.EVAP
        self._attr_check_multi = False
        self._attr_status_attr = "cooler_busy"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:cog-clockwise"


class RinnaiFanOperatingBinarySensorEntity(RinnaiUnitStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._attr_name = name + " Fan Active Sensor"
        self._attr_status_attr = "fan_operating"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:fan-alert"

    @property
    def available(self):
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if state.mode == RinnaiSystemMode.EVAP:
            return True
        if state.is_multi_set_point:
            return False
        return True


class RinnaiZoneStateBinarySensorEntity(RinnaiBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, name)
        self._attr_zone = zone
        device_id = (
            str.lower(self.__class__.__name__)
            + "_"
            + zone
            + str.replace(ip_address, ".", "_")
        )
        self._attr_unique_id = device_id
        self._attr_unit_mode = None
        self._attr_status_attr = None

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if not self.available:
            return "mdi:eye"
        if self.is_on:
            return "mdi:eye-check"
        return "mdi:eye-remove"

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if self.available:
            return getattr(
                state.unit_status.zones[self._attr_zone], self._attr_status_attr, False
            )
        return False

    @property
    def available(self):
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if state.is_multi_set_point:
            return (
                state.mode == self._attr_unit_mode
                and self._attr_zone in state.unit_status.zones
            )
        return False


class RinnaiZonePreheatBinarySensorEntity(RinnaiZoneStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, zone, name)
        self._attr_name = name + " Zone " + zone + " Preheating Sensor"
        self._attr_unit_mode = RinnaiSystemMode.HEATING
        self._attr_status_attr = "preheating"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:fire-alert"


class RinnaiZoneGasValveBinarySensorEntity(RinnaiZoneStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, zone, name)
        self._attr_name = name + " Zone " + zone + " Gas Valve Active Sensor"
        self._attr_unit_mode = RinnaiSystemMode.HEATING
        self._attr_status_attr = "gas_valve_active"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:gas-burner"


class RinnaiZoneCallingHeatBinarySensorEntity(RinnaiZoneStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, zone, name)
        self._attr_name = name + " Zone " + zone + " Calling Heat Sensor"
        self._attr_unit_mode = RinnaiSystemMode.HEATING
        self._attr_status_attr = "calling_for_work"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:thermometer-alert"


class RinnaiZoneCompressorBinarySensorEntity(RinnaiZoneStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, zone, name)
        self._attr_name = name + " Zone " + zone + " Compressor Active Sensor"
        self._attr_unit_mode = RinnaiSystemMode.COOLING
        self._attr_status_attr = "compressor_active"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:cog-clockwise"


class RinnaiZoneCallingCoolBinarySensorEntity(RinnaiZoneStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, zone, name)
        self._attr_name = name + " Zone " + zone + " Calling Cool Sensor"
        self._attr_unit_mode = RinnaiSystemMode.COOLING
        self._attr_status_attr = "calling_for_work"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:thermometer-alert"


class RinnaiZoneFanOperatingBinarySensorEntity(RinnaiZoneStateBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, zone, name):
        super().__init__(ip_address, zone, name)
        self._attr_name = name + " Zone " + zone + " Fan Active Sensor"
        self._attr_status_attr = "fan_operating"

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:fan-alert"

    @property
    def available(self):
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if state.mode == RinnaiSystemMode.EVAP:
            return False
        if state.is_multi_set_point:
            return True
        return False
