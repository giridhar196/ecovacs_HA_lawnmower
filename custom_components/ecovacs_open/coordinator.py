"""Data update coordinator for Ecovacs Open."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EcovacsOpenApi, EcovacsOpenApiError, device_nickname
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import MowerDeviceData

_LOGGER = logging.getLogger(__name__)

__all__ = ["EcovacsOpenCoordinator", "MowerDeviceData"]


class EcovacsOpenCoordinator(DataUpdateCoordinator[dict[str, MowerDeviceData]]):
    """Poll device list and work state from Ecovacs Open Platform."""

    def __init__(self, hass: HomeAssistant, api: EcovacsOpenApi) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, MowerDeviceData]:
        """Fetch devices and per-device work state."""
        try:
            devices = await self.api.async_get_devices()
        except EcovacsOpenApiError as err:
            raise UpdateFailed(str(err)) from err

        result: dict[str, MowerDeviceData] = {}
        for device in devices:
            try:
                nickname = device_nickname(device)
            except EcovacsOpenApiError:
                _LOGGER.debug("Skipping device without nickname: %s", device)
                continue

            work_state: dict[str, Any] = {}
            try:
                work_state = await self.api.async_get_work_state(nickname)
            except EcovacsOpenApiError as err:
                # Keep the device visible even if status query fails (some
                # models return 5009 unsupported control logic).
                _LOGGER.warning(
                    "Work state unavailable for %s: %s", nickname, err
                )

            result[nickname] = MowerDeviceData(
                nickname=nickname,
                raw_device=device,
                work_state=work_state,
            )

        if not result:
            raise UpdateFailed("No robots found for this API key")

        return result
