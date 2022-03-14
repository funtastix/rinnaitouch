"""Set up main entity."""
# pylint: disable=duplicate-code
import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.const import Platform

from pyrinnaitouch import RinnaiSystem

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.CLIMATE,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.SELECT
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the rinnaitouch integration from a config entry."""

    ip_address = entry.data.get(CONF_HOST)
    _LOGGER.debug("Get controller with IP: %s", ip_address)

    try:
        system = RinnaiSystem.get_instance(ip_address)
        #scenes = await system.getSupportedScenes()
        scenes = []
        await system.get_status()
    except (
        Exception,
        ConnectionError,
        ConnectionRefusedError,
    ) as err:
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = RinnaiData(system=system, scenes=scenes)
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

@dataclass
class RinnaiData:
    """Data for the Rinnai Touch integration."""

    system: RinnaiSystem
    scenes: list

class RinnaiEntity(Entity):
    """Base entity."""

    def __init__(self):
        pass
