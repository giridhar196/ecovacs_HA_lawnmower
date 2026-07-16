"""Diagnostics."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant

from . import EcovacsOpenConfigEntry
from .const import CONF_API_KEY, CONF_MODE, MODE_CLOUD

TO_REDACT = {CONF_API_KEY, CONF_PASSWORD, "ak", "token"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: EcovacsOpenConfigEntry
) -> dict[str, Any]:
    """Return diagnostics."""
    data: dict[str, Any] = {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "mode": entry.data.get(CONF_MODE),
    }
    if entry.data.get(CONF_MODE) == MODE_CLOUD:
        controller = entry.runtime_data
        data["devices"] = [
            {
                "did": d.device_info.get("did"),
                "nick": d.device_info.get("nick"),
                "deviceName": d.device_info.get("deviceName"),
                "class": d.device_info.get("class"),
                "device_type": str(d.capabilities.device_type),
            }
            for d in controller.devices
        ]
    else:
        coordinator = entry.runtime_data
        data["devices"] = {
            nickname: {
                "activity": item.activity,
                "work_state": item.work_state,
            }
            for nickname, item in coordinator.data.items()
        }
    return data
