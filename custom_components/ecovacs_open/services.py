"""Custom services for zone mowing and edge trim."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from deebot_client.commands.json.clean import CleanAreaV2
from deebot_client.commands.json.custom import CustomCommand
from deebot_client.models import CleanMode

from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import (
    ATTR_AREA_IDS,
    CONF_MODE,
    DOMAIN,
    MODE_CLOUD,
    SERVICE_REFRESH_ZONES,
    SERVICE_START_EDGE_TRIM,
    SERVICE_START_ZONES,
)
from .controller import EcovacsCloudController

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Optional(ATTR_AREA_IDS): vol.Any(cv.string, [vol.Coerce(str)]),
    }
)


def _parse_area_ids(value: Any) -> list[int]:
    if value is None:
        raise ServiceValidationError("area_ids is required")
    if isinstance(value, str):
        parts = [p.strip() for p in value.replace(";", ",").split(",") if p.strip()]
    else:
        parts = [str(p).strip() for p in value if str(p).strip()]
    if not parts:
        raise ServiceValidationError("No area ids provided")
    try:
        return [int(p.replace("reid:", "")) for p in parts]
    except ValueError as err:
        raise ServiceValidationError(f"Invalid area ids: {value}") from err


def _device_from_call(
    hass: HomeAssistant, call: ServiceCall
) -> tuple[EcovacsCloudController, Any]:
    device_id = call.data[ATTR_DEVICE_ID]
    registry = dr.async_get(hass)
    device_entry = registry.async_get(device_id)
    if device_entry is None:
        raise ServiceValidationError(f"Unknown device_id: {device_id}")

    did = None
    for domain, identifier in device_entry.identifiers:
        if domain == DOMAIN:
            did = identifier
            break
    if not did:
        raise ServiceValidationError("Device is not an Ecovacs lawn mower")

    for entry_id, runtime in hass.data.get(DOMAIN, {}).items():
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.data.get(CONF_MODE) != MODE_CLOUD:
            continue
        controller: EcovacsCloudController = runtime
        device = controller.get_device(did)
        if device is not None:
            return controller, device

    raise HomeAssistantError("Mower device is not loaded (use Cloud account mode)")


async def _async_start_zones(hass: HomeAssistant, call: ServiceCall) -> None:
    """Start mowing specific zones via spotArea."""
    _, device = _device_from_call(hass, call)
    area_ids = _parse_area_ids(call.data.get(ATTR_AREA_IDS))
    clean_cap = device.capabilities.clean
    if clean_cap and clean_cap.action.area:
        command = clean_cap.action.area(CleanMode.SPOT_AREA, area_ids)
    else:
        # Fallback payload used by GOAT app captures
        command = CleanAreaV2(CleanMode.SPOT_AREA, area_ids)
    _LOGGER.debug("Starting zones %s on %s", area_ids, device.device_info.get("nick"))
    await device.execute_command(command)


async def _async_start_edge_trim(hass: HomeAssistant, call: ServiceCall) -> None:
    """Start edge / borderrotate trim for zones."""
    _, device = _device_from_call(hass, call)
    area_ids = _parse_area_ids(call.data.get(ATTR_AREA_IDS))
    reid = ";".join(f"reid:{i}" for i in area_ids)
    # Prefer clean_V2 for G1-line; O-series often uses clean.
    name = "clean_V2"
    clean = device.capabilities.clean
    if clean and getattr(clean.action.command, "NAME", "") == "clean":
        name = "clean"
    command = CustomCommand(
        name,
        {"act": "start", "content": {"type": "borderrotate", "value": reid}},
    )
    _LOGGER.debug("Starting edge trim %s on %s", reid, device.device_info.get("nick"))
    await device.execute_command(command)


async def _async_refresh_zones(hass: HomeAssistant, call: ServiceCall) -> None:
    """Ask the mower for map set / area list (best effort)."""
    controller, device = _device_from_call(hass, call)
    did = device.device_info["did"]
    # Best-effort: many GOAT models answer getMapSet_V2 with type ar (rooms).
    for name, args in (
        ("getMapSet_V2", {"type": "ar"}),
        ("getMapSet", {"type": "ar"}),
        ("getAreaSet", {}),
    ):
        try:
            await device.execute_command(CustomCommand(name, args))
            break
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Zone refresh command %s failed", name, exc_info=True)
    # Keep existing defaults if the device does not push subset ids we can parse yet.
    controller.zone_ids.setdefault(did, ["1", "2", "3", "4"])


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register integration services once."""

    async def handle_start_zones(call: ServiceCall) -> None:
        await _async_start_zones(hass, call)

    async def handle_start_edge(call: ServiceCall) -> None:
        await _async_start_edge_trim(hass, call)

    async def handle_refresh(call: ServiceCall) -> None:
        await _async_refresh_zones(hass, call)

    hass.services.async_register(
        DOMAIN, SERVICE_START_ZONES, handle_start_zones, schema=SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_START_EDGE_TRIM, handle_start_edge, schema=SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_ZONES,
        handle_refresh,
        schema=vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string}),
    )
