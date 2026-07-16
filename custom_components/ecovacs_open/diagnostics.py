"""Diagnostics support for Ecovacs Open."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import EcovacsOpenConfigEntry
from .const import CONF_API_KEY

TO_REDACT = {CONF_API_KEY, "ak"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: EcovacsOpenConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    devices = {
        nickname: {
            "activity": data.activity,
            "work_state": data.work_state,
            "raw_device": data.raw_device,
        }
        for nickname, data in coordinator.data.items()
    }
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "devices": devices,
    }
