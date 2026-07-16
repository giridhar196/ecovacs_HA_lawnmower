"""Ecovacs Open Platform integration for Home Assistant lawn mowers."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EcovacsOpenApi
from .const import CONF_API_KEY, CONF_API_URL, DOMAIN
from .coordinator import EcovacsOpenCoordinator

PLATFORMS: list[Platform] = [Platform.LAWN_MOWER, Platform.SENSOR]

type EcovacsOpenConfigEntry = ConfigEntry[EcovacsOpenCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: EcovacsOpenConfigEntry) -> bool:
    """Set up Ecovacs Open from a config entry."""
    session = async_get_clientsession(hass)
    api = EcovacsOpenApi(
        session,
        entry.data[CONF_API_KEY],
        entry.data[CONF_API_URL],
    )
    coordinator = EcovacsOpenCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EcovacsOpenConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
