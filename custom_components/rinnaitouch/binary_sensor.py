"""Binary sensors for prewetting and preheating"""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST
)

from pyrinnaitouch import RinnaiSystem

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities): # pylint: disable=unused-argument
    """Set up the binary sensor entities."""
    ip_address = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME)
    if name == "":
        name = "Rinnai Touch"
    async_add_entities([
        RinnaiPrewetBinarySensorEntity(ip_address, name + " Evap Prewetting Sensor"),
        RinnaiPreheatBinarySensorEntity(ip_address, name + " Preheating Sensor")
    ])
    return True

class RinnaiBinarySensorEntity(BinarySensorEntity):
    """Base class for all binary sensor entities setting up names and system instance."""

    def __init__(self, ip_address, name):
        self._host = ip_address
        self._system = RinnaiSystem.get_instance(ip_address)
        device_id = str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = name

    @property
    def name(self):
        """Name of the entity."""
        return self._attr_name

    @property
    def is_on(self):
        return False

class RinnaiPrewetBinarySensorEntity(RinnaiBinarySensorEntity):
    """Binary sensor for prewetting on/off during evap operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        self.async_write_ha_state()

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:snowflake-melt"

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        if self._system.get_stored_status().evap_mode:
            return (
                self._system.get_stored_status().evap_status.prewetting
                or self._system.get_stored_status().evap_status.cooler_busy
            )
        return False

    @property
    def available(self):
        return self._system.get_stored_status().evap_mode

class RinnaiPreheatBinarySensorEntity(RinnaiBinarySensorEntity):
    """Binary sensor for preheating on/off during heater operation."""

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        self.async_write_ha_state()

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:fire-alert"

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        if self._system.get_stored_status().heater_mode:
            return self._system.get_stored_status().heater_status.preheating
        return False

    @property
    def available(self):
        return self._system.get_stored_status().heater_mode
