"""Minimal Home Assistant stubs for pure unit tests."""

from __future__ import annotations

import sys
import types
from datetime import timedelta


def _ensure_module(name: str) -> types.ModuleType:
    if name in sys.modules:
        module = sys.modules[name]
    else:
        module = types.ModuleType(name)
        sys.modules[name] = module
        parent_name, _, child = name.rpartition(".")
        if parent_name:
            parent = _ensure_module(parent_name)
            setattr(parent, child, module)
    # Make namespace packages importable as packages
    if not hasattr(module, "__path__"):
        module.__path__ = []  # type: ignore[attr-defined]
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
    NUMBER = "number"
    SELECT = "select"
    SWITCH = "switch"


class _ConfigType(dict):
    pass


class _ConfigEntryError(Exception):
    pass


class _ConfigEntryNotReady(Exception):
    pass


for name in (
    "homeassistant",
    "homeassistant.config_entries",
    "homeassistant.core",
    "homeassistant.const",
    "homeassistant.exceptions",
    "homeassistant.helpers",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.typing",
    "homeassistant.util",
):
    _ensure_module(name)

sys.modules["homeassistant.config_entries"].ConfigEntry = _ConfigEntry
sys.modules["homeassistant.core"].HomeAssistant = _HomeAssistant
sys.modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = (
    _DataUpdateCoordinator
)
sys.modules["homeassistant.helpers.update_coordinator"].UpdateFailed = _UpdateFailed
sys.modules["homeassistant.const"].Platform = _Platform
sys.modules["homeassistant.const"].CONF_NAME = "name"
sys.modules["homeassistant.const"].CONF_USERNAME = "username"
sys.modules["homeassistant.const"].CONF_PASSWORD = "password"
sys.modules["homeassistant.const"].CONF_COUNTRY = "country"
sys.modules["homeassistant.helpers.aiohttp_client"].async_get_clientsession = (
    lambda hass: None
)
sys.modules["homeassistant.helpers.typing"].ConfigType = _ConfigType
sys.modules["homeassistant.exceptions"].ConfigEntryError = _ConfigEntryError
sys.modules["homeassistant.exceptions"].ConfigEntryNotReady = _ConfigEntryNotReady
sys.modules["homeassistant.util"].slugify = lambda value: str(value).lower()
