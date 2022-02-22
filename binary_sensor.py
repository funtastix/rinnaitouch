from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import (
    CONF_HOST
)

from custom_components.rinnaitouch.pyrinnaitouch import RinnaiSystem

import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data.get(CONF_HOST)
    async_add_entities([
        RinnaiPrewetBinarySensorEntity(ip_address, "Rinnai Touch Evap Prewetting Sensor"),
        RinnaiPreheatBinarySensorEntity(ip_address, "Rinnai Touch Evap Preheating Sensor")
    ])
    return True

class RinnaiBinarySensorEntity(BinarySensorEntity):

    def __init__(self, ip_address, name):
        self._host = ip_address
        self._system = RinnaiSystem.getInstance(ip_address)
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

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._system.SubscribeUpdates(self.system_updated)

    def system_updated(self):
        self.async_write_ha_state()

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:snowflake-melt"

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        if self._system._status.evapMode:
            return self._system._status.evapStatus.prewetting or self._system._status.evapStatus.coolerBusy
        else:
            return False

class RinnaiPreheatBinarySensorEntity(RinnaiBinarySensorEntity):

    def __init__(self, ip_address, name):
        super().__init__(ip_address, name)
        self._system.SubscribeUpdates(self.system_updated)

    def system_updated(self):
        self.async_write_ha_state()

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:fire-alert"

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        if self._system._status.heaterMode:
            return self._system._status.heaterStatus.preheating
        else:
            return False
