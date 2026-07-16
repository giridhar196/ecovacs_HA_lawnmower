"""Ecovacs lawn mower integration (cloud account + optional Open Platform)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import EcovacsOpenApi
from .const import CONF_API_KEY, CONF_API_URL, CONF_MODE, DOMAIN, MODE_CLOUD, MODE_OPEN
from .controller import EcovacsCloudController
from .coordinator import EcovacsOpenCoordinator
from .services import async_setup_services

CLOUD_PLATFORMS: list[Platform] = [
    Platform.LAWN_MOWER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]
OPEN_PLATFORMS: list[Platform] = [Platform.LAWN_MOWER, Platform.SENSOR]

type EcovacsOpenConfigEntry = ConfigEntry


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration component."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: EcovacsOpenConfigEntry) -> bool:
    """Set up from a config entry."""
    mode = entry.data.get(CONF_MODE, MODE_OPEN)
    hass.data.setdefault(DOMAIN, {})

    if mode == MODE_CLOUD:
        controller = EcovacsCloudController(hass, entry.data)
        await controller.initialize()
        entry.runtime_data = controller
        hass.data[DOMAIN][entry.entry_id] = controller
        entry.async_on_unload(controller.teardown)
        await hass.config_entries.async_forward_entry_setups(entry, CLOUD_PLATFORMS)
        return True

    session = async_get_clientsession(hass)
    api = EcovacsOpenApi(
        session,
        entry.data[CONF_API_KEY],
        entry.data[CONF_API_URL],
    )
    coordinator = EcovacsOpenCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, OPEN_PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EcovacsOpenConfigEntry) -> bool:
    """Unload a config entry."""
    mode = entry.data.get(CONF_MODE, MODE_OPEN)
    platforms = CLOUD_PLATFORMS if mode == MODE_CLOUD else OPEN_PLATFORMS
    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old Open Platform-only entries."""
    if entry.version < 2:
        data = {**entry.data, CONF_MODE: MODE_OPEN}
        hass.config_entries.async_update_entry(entry, data=data, version=2)
    return True
