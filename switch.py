from homeassistant.components.switch import SwitchEntity
from custom_components.rinnaitouch.pyrinnaitouch import RinnaiSystem

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    ip_address = entry.data.get(CONF_HOST)
    async_add_entities([RinnaiOnOffSwitch(hass, ip_address)])
    return True

class RinnaiOnOffSwitch(SwitchEntity):
    def __init__(self, hass, ip_address):
        self._is_on = False
        self._host = ip_address
        self._system = RinnaiSystem.getInstance(ip_address)
        device_id = "rinnaionoffswitch_" + str.replace(ip_address, ".", "_")

        self._attr_unique_id = device_id
        self._attr_name = f"Rinnai Touch On Off Switch"

        self._hass = hass

    @property
    def name(self):
        """Name of the entity."""
        return self._attr_name

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._system._status.systemOn

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        #turn whatever the preset is on and put it into manual mode
        if self._system._status.coolingMode:
            await self._system.turn_cooling_on()
        elif self._system._status.heaterMode:
            await self._system.turn_heater_on()
        elif self._system._status.evapMode:
            await self._system.turn_evap_on()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        #turn whatever the preset is off
        if self._system._status.coolingMode:
            await self._system.turn_cooling_off()
        elif self._system._status.heaterMode:
            await self._system.turn_heater_off()
        elif self._system._status.evapMode:
            await self._system.turn_evap_off()
