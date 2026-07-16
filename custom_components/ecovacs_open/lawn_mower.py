"""Lawn mower platform for Ecovacs Open."""

from __future__ import annotations

import logging

from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EcovacsOpenConfigEntry
from .api import EcovacsOpenApiError
from .const import DOMAIN
from .coordinator import EcovacsOpenCoordinator
from .models import MowerDeviceData

_LOGGER = logging.getLogger(__name__)

SUPPORTED_FEATURES = (
    LawnMowerEntityFeature.START_MOWING
    | LawnMowerEntityFeature.PAUSE
    | LawnMowerEntityFeature.DOCK
)

ACTIVITY_MAP = {
    "mowing": LawnMowerActivity.MOWING,
    "paused": LawnMowerActivity.PAUSED,
    "docked": LawnMowerActivity.DOCKED,
    "returning": LawnMowerActivity.RETURNING,
    "error": LawnMowerActivity.ERROR,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EcovacsOpenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up lawn mower entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        EcovacsOpenLawnMower(coordinator, nickname)
        for nickname in coordinator.data
    )


class EcovacsOpenLawnMower(
    CoordinatorEntity[EcovacsOpenCoordinator], LawnMowerEntity
):
    """Representation of an Ecovacs Open Platform lawn mower."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = SUPPORTED_FEATURES

    def __init__(self, coordinator: EcovacsOpenCoordinator, nickname: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._nickname = nickname
        self._attr_unique_id = f"{DOMAIN}_{nickname}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, nickname)},
            name=nickname,
            manufacturer="Ecovacs",
            model="GOAT / Open Platform",
        )
        self._apply_activity()

    @property
    def device_data(self) -> MowerDeviceData | None:
        """Return coordinator data for this mower."""
        return self.coordinator.data.get(self._nickname)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._apply_activity()
        super()._handle_coordinator_update()

    def _apply_activity(self) -> None:
        """Set activity from coordinator snapshot."""
        data = self.device_data
        if data is None:
            self._attr_available = False
            return
        self._attr_available = True
        self._attr_activity = ACTIVITY_MAP.get(data.activity, LawnMowerActivity.ERROR)

    async def async_start_mowing(self) -> None:
        """Start or resume mowing."""
        data = self.device_data
        try:
            if data and data.activity == "paused":
                await self.coordinator.api.async_resume_mowing(self._nickname)
            else:
                await self.coordinator.api.async_start_mowing(self._nickname)
        except EcovacsOpenApiError as err:
            _LOGGER.error("Failed to start mowing %s: %s", self._nickname, err)
            raise
        await self.coordinator.async_request_refresh()

    async def async_pause(self) -> None:
        """Pause mowing."""
        try:
            await self.coordinator.api.async_pause(self._nickname)
        except EcovacsOpenApiError as err:
            _LOGGER.error("Failed to pause %s: %s", self._nickname, err)
            raise
        await self.coordinator.async_request_refresh()

    async def async_dock(self) -> None:
        """Send the mower back to the dock."""
        try:
            await self.coordinator.api.async_dock(self._nickname)
        except EcovacsOpenApiError as err:
            _LOGGER.error("Failed to dock %s: %s", self._nickname, err)
            raise
        await self.coordinator.async_request_refresh()
