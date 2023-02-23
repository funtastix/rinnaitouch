"""Advance buttons to move to next schedule"""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_NAME, CONF_HOST

from pyrinnaitouch import RinnaiSystem, RinnaiSystemMode, RinnaiOperatingMode, RinnaiSystemStatus

from .const import CONF_ZONE_A, CONF_ZONE_B, CONF_ZONE_C, CONF_ZONE_D, CONF_ZONE_COMMON

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass, entry, async_add_entities
):  # pylint: disable=unused-argument
    """Set up the advance button entities."""
    ip_address = entry.data.get(CONF_HOST)
    name = entry.data.get(CONF_NAME)
    if name == "":
        name = "Rinnai Touch"
    async_add_entities([RinnaiAdvanceButton(ip_address, name + " Advance Button")])
    if entry.data.get(CONF_ZONE_A):
        async_add_entities(
            [RinnaiZoneAdvanceButton(ip_address, "A", name + " Zone A Advance Button")]
        )
    if entry.data.get(CONF_ZONE_B):
        async_add_entities(
            [RinnaiZoneAdvanceButton(ip_address, "B", name + " Zone B Advance Button")]
        )
    if entry.data.get(CONF_ZONE_C):
        async_add_entities(
            [RinnaiZoneAdvanceButton(ip_address, "C", name + " Zone C Advance Button")]
        )
    if entry.data.get(CONF_ZONE_D):
        async_add_entities(
            [RinnaiZoneAdvanceButton(ip_address, "D", name + " Zone D Advance Button")]
        )
    if entry.data.get(CONF_ZONE_COMMON):
        async_add_entities(
            [
                RinnaiZoneAdvanceButton(
                    ip_address, "U", name + " Common Zone Advance Button"
                )
            ]
        )
    return True


class RinnaiButtonEntity(ButtonEntity):
    """Base class button entity to set up naming and system."""

    def __init__(self, ip_address, name):
        self._host = ip_address
        self._system = RinnaiSystem.get_instance(ip_address)
        device_id = (
            str.lower(self.__class__.__name__) + "_" + str.replace(ip_address, ".", "_")
        )

        self._attr_unique_id = device_id
        self._attr_name = name
        self._system.subscribe_updates(self.system_updated)

    def system_updated(self):
        """After system is updated write the new state to HA."""
        # this very infrequently fails on startup so wrapping in try except
        try:
            self.schedule_update_ha_state()
        except:  # pylint: disable=bare-except
            pass

    @property
    def name(self):
        """Name of the entity."""
        return self._attr_name


class RinnaiAdvanceButton(RinnaiButtonEntity):
    """Main advance button entity."""

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        if self.available:
            if self._system.get_stored_status().unit_status.advanced:
                return "mdi:close-circle-outline"
        return "mdi:location-exit"

    @property
    def available(self) -> bool:
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if (
            state.mode in (RinnaiSystemMode.HEATING, RinnaiSystemMode.COOLING)
            and state.unit_status.operating_mode == RinnaiOperatingMode.AUTO
        ):
            return state.system_on
        return False

    async def async_press(self) -> None:
        """Handle the button press."""
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if state.mode in (RinnaiSystemMode.HEATING, RinnaiSystemMode.COOLING):
            if state.unit_status.advanced:
                await self._system.unit_advance_cancel()
            else:
                await self._system.unit_advance()

class RinnaiZoneAdvanceButton(RinnaiButtonEntity):
    """Advance button entity for a zone."""

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

    @property
    def icon(self):
        """Return the icon to use in the frontend for this device."""
        return "mdi:location-exit"

    @property
    def available(self):
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if state.mode in (RinnaiSystemMode.HEATING, RinnaiSystemMode.COOLING):
            return (
                self._attr_zone in state.unit_status.zones.keys()
                and state.unit_status.zones[self._attr_zone].auto_mode
            )
        return False

    async def async_press(self) -> None:
        """Handle the button press."""
        state: RinnaiSystemStatus = self._system.get_stored_status()
        if state.mode in (RinnaiSystemMode.HEATING, RinnaiSystemMode.COOLING) \
            and self._attr_zone in state.unit_status.zones.keys():
            if state.unit_status.zones[self._attr_zone].advanced:
                await self._system.unit_zone_advance_cancel(self._attr_zone)
            else:
                await self._system.set_unit_zone_advance(self._attr_zone)
