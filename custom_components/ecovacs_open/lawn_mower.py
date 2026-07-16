"""Lawn mower platform."""

from __future__ import annotations

from deebot_client.capabilities import DeviceType
from deebot_client.events import StateEvent
from deebot_client.models import CleanAction, State

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
from .const import CONF_MODE, DOMAIN, MODE_CLOUD, MODE_OPEN
from .coordinator import EcovacsOpenCoordinator
from .entity import EcovacsMowerEntity
from .models import MowerDeviceData

_STATE_MAP = {
    State.IDLE: LawnMowerActivity.PAUSED,
    State.CLEANING: LawnMowerActivity.MOWING,
    State.RETURNING: LawnMowerActivity.RETURNING,
    State.DOCKED: LawnMowerActivity.DOCKED,
    State.ERROR: LawnMowerActivity.ERROR,
    State.PAUSED: LawnMowerActivity.PAUSED,
}

_OPEN_ACTIVITY = {
    "mowing": LawnMowerActivity.MOWING,
    "paused": LawnMowerActivity.PAUSED,
    "docked": LawnMowerActivity.DOCKED,
    "returning": LawnMowerActivity.RETURNING,
    "error": LawnMowerActivity.ERROR,
}

_FEATURES = (
    LawnMowerEntityFeature.START_MOWING
    | LawnMowerEntityFeature.PAUSE
    | LawnMowerEntityFeature.DOCK
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EcovacsOpenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up lawn mower entities."""
    mode = entry.data.get(CONF_MODE, MODE_OPEN)
    if mode == MODE_CLOUD:
        controller = entry.runtime_data
        async_add_entities(
            [
                EcovacsCloudLawnMower(device)
                for device in controller.devices
                if device.capabilities.device_type is DeviceType.MOWER
                or "GOAT" in str(device.device_info.get("deviceName", "")).upper()
            ]
        )
        return

    coordinator: EcovacsOpenCoordinator = entry.runtime_data
    async_add_entities(
        EcovacsOpenLawnMower(coordinator, nickname) for nickname in coordinator.data
    )


class EcovacsCloudLawnMower(EcovacsMowerEntity, LawnMowerEntity):
    """Cloud MQTT lawn mower."""

    _attr_name = None
    _attr_supported_features = _FEATURES

    def __init__(self, device) -> None:
        """Initialize."""
        super().__init__(device, "mower")
        self._attr_activity = LawnMowerActivity.DOCKED

    async def async_added_to_hass(self) -> None:
        """Subscribe state."""
        await super().async_added_to_hass()

        async def on_status(event: StateEvent) -> None:
            self._attr_activity = _STATE_MAP.get(event.state, LawnMowerActivity.ERROR)
            self.async_write_ha_state()

        self._subscribe(self._device.capabilities.state.event, on_status)

    async def async_start_mowing(self) -> None:
        """Start or resume mowing."""
        cmd = self._device.capabilities.clean.action.command(CleanAction.START)
        await self._device.execute_command(cmd)

    async def async_pause(self) -> None:
        """Pause mowing."""
        cmd = self._device.capabilities.clean.action.command(CleanAction.PAUSE)
        await self._device.execute_command(cmd)

    async def async_dock(self) -> None:
        """Return to dock."""
        await self._device.execute_command(self._device.capabilities.charge.execute())


class EcovacsOpenLawnMower(
    CoordinatorEntity[EcovacsOpenCoordinator], LawnMowerEntity
):
    """Limited Open Platform lawn mower."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = _FEATURES

    def __init__(self, coordinator: EcovacsOpenCoordinator, nickname: str) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._nickname = nickname
        self._attr_unique_id = f"open_{nickname}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, nickname)},
            name=nickname,
            manufacturer="Ecovacs",
            model="Open Platform (limited)",
        )
        self._apply_activity()

    @property
    def device_data(self) -> MowerDeviceData | None:
        """Coordinator snapshot."""
        return self.coordinator.data.get(self._nickname)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._apply_activity()
        super()._handle_coordinator_update()

    def _apply_activity(self) -> None:
        data = self.device_data
        if data is None:
            self._attr_available = False
            return
        self._attr_available = True
        self._attr_activity = _OPEN_ACTIVITY.get(data.activity, LawnMowerActivity.ERROR)

    async def async_start_mowing(self) -> None:
        data = self.device_data
        if data and data.activity == "paused":
            await self.coordinator.api.async_resume_mowing(self._nickname)
        else:
            await self.coordinator.api.async_start_mowing(self._nickname)
        await self.coordinator.async_request_refresh()

    async def async_pause(self) -> None:
        await self.coordinator.api.async_pause(self._nickname)
        await self.coordinator.async_request_refresh()

    async def async_dock(self) -> None:
        await self.coordinator.api.async_dock(self._nickname)
        await self.coordinator.async_request_refresh()
