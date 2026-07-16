"""Minimal Home Assistant stubs for pure unit tests."""

from __future__ import annotations

import sys
import types
from datetime import timedelta


def _ensure_module(name: str) -> types.ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    sys.modules[name] = module
    parent_name, _, child = name.rpartition(".")
    if parent_name:
        parent = _ensure_module(parent_name)
        setattr(parent, child, module)
    return module


class _ConfigEntry:
    pass


class _HomeAssistant:
    pass


class _DataUpdateCoordinator:
    def __init__(self, hass, logger, *, name, update_interval=None) -> None:
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval or timedelta(seconds=30)
        self.data = {}

    def __class_getitem__(cls, item):
        return cls

    async def async_config_entry_first_refresh(self) -> None:
        return None

    async def async_request_refresh(self) -> None:
        return None


class _UpdateFailed(Exception):
    pass


class _Platform:
    LAWN_MOWER = "lawn_mower"
    SENSOR = "sensor"


async def _async_get_clientsession(hass):
    return None


ha_config_entries = _ensure_module("homeassistant.config_entries")
ha_core = _ensure_module("homeassistant.core")
ha_const = _ensure_module("homeassistant.const")
ha_helpers_update = _ensure_module("homeassistant.helpers.update_coordinator")
ha_helpers_aiohttp = _ensure_module("homeassistant.helpers.aiohttp_client")

ha_config_entries.ConfigEntry = _ConfigEntry
ha_core.HomeAssistant = _HomeAssistant
ha_helpers_update.DataUpdateCoordinator = _DataUpdateCoordinator
ha_helpers_update.UpdateFailed = _UpdateFailed
ha_const.Platform = _Platform
ha_const.CONF_NAME = "name"
ha_helpers_aiohttp.async_get_clientsession = _async_get_clientsession
