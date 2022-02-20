from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    CONF_HOST
)

from custom_components.rinnaitouch.pyrinnaitouch import RinnaiSystem

import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data.get(CONF_HOST)
    async_add_entities([
        RinnaiOnOffSwitch(ip_address, "Rinnai Touch On Off Switch"),
        RinnaiCoolingModeSwitch(ip_address, "Rinnai Touch Cooling Mode Switch"),
        RinnaiHeaterModeSwitch(ip_address, "Rinnai Touch Heater Mode Switch"),
        RinnaiEvapModeSwitch(ip_address, "Rinnai Touch Evap Mode Switch"),
        RinnaiZoneSwitch(ip_address, "A", "Rinnai Touch Zone A Switch"),
        RinnaiZoneSwitch(ip_address, "B", "Rinnai Touch Zone B Switch"),
        RinnaiZoneSwitch(ip_address, "C", "Rinnai Touch Zone C Switch"),
        RinnaiZoneSwitch(ip_address, "D", "Rinnai Touch Zone D Switch")
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

