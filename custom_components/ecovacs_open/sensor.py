"""Sensor platform for Ecovacs Open work-state details."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EcovacsOpenConfigEntry
from .const import DOMAIN
from .coordinator import EcovacsOpenCoordinator
from .models import MowerDeviceData


@dataclass(frozen=True, kw_only=True)
class EcovacsOpenSensorEntityDescription(SensorEntityDescription):
    """Describe an Ecovacs Open sensor."""

    value_fn: Callable[[MowerDeviceData], str | None]


SENSORS: tuple[EcovacsOpenSensorEntityDescription, ...] = (
    EcovacsOpenSensorEntityDescription(
        key="mow_status",
        translation_key="mow_status",
        value_fn=lambda d: d.clean_st,
    ),
    EcovacsOpenSensorEntityDescription(
        key="charge_status",
        translation_key="charge_status",
        value_fn=lambda d: d.charge_st,
    ),
    EcovacsOpenSensorEntityDescription(
        key="station_status",
        translation_key="station_status",
        value_fn=lambda d: d.station_st,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EcovacsOpenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    entities: list[EcovacsOpenSensor] = []
    for nickname in coordinator.data:
        for description in SENSORS:
            entities.append(EcovacsOpenSensor(coordinator, nickname, description))
    async_add_entities(entities)


class EcovacsOpenSensor(
    CoordinatorEntity[EcovacsOpenCoordinator], SensorEntity
):
    """Sensor exposing a raw Open Platform status field."""

    entity_description: EcovacsOpenSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcovacsOpenCoordinator,
        nickname: str,
        description: EcovacsOpenSensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description
        self._nickname = nickname
        self._attr_unique_id = f"{DOMAIN}_{nickname}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, nickname)},
            name=nickname,
            manufacturer="Ecovacs",
            model="GOAT / Open Platform",
        )

    @property
    def native_value(self) -> str | None:
        """Return sensor value."""
        data = self.coordinator.data.get(self._nickname)
        if data is None:
            return None
        return self.entity_description.value_fn(data)
