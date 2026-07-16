"""Sensor platform."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from deebot_client.events import BatteryEvent, ErrorEvent, NetworkInfoEvent

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EcovacsOpenConfigEntry
from .const import CONF_MODE, DOMAIN, MODE_CLOUD, MODE_OPEN
from .coordinator import EcovacsOpenCoordinator
from .entity import EcovacsMowerEntity
from .models import MowerDeviceData


@dataclass(frozen=True, kw_only=True)
class OpenSensorDescription(SensorEntityDescription):
    """Open Platform status sensor."""

    value_fn: Callable[[MowerDeviceData], str | None]


OPEN_SENSORS: tuple[OpenSensorDescription, ...] = (
    OpenSensorDescription(
        key="mow_status",
        translation_key="mow_status",
        value_fn=lambda d: d.clean_st,
    ),
    OpenSensorDescription(
        key="charge_status",
        translation_key="charge_status",
        value_fn=lambda d: d.charge_st,
    ),
    OpenSensorDescription(
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
    mode = entry.data.get(CONF_MODE, MODE_OPEN)
    if mode == MODE_CLOUD:
        controller = entry.runtime_data
        entities: list[SensorEntity] = []
        for device in controller.devices:
            if device.capabilities.battery:
                entities.append(BatterySensor(device))
            if device.capabilities.error:
                entities.append(ErrorSensor(device))
            if device.capabilities.network:
                entities.append(WifiSensor(device))
        async_add_entities(entities)
        return

    coordinator: EcovacsOpenCoordinator = entry.runtime_data
    async_add_entities(
        OpenStatusSensor(coordinator, nickname, description)
        for nickname in coordinator.data
        for description in OPEN_SENSORS
    )


class BatterySensor(EcovacsMowerEntity, SensorEntity):
    """Battery level."""

    _attr_translation_key = "battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, device) -> None:
        """Initialize."""
        super().__init__(device, "battery")

    async def async_added_to_hass(self) -> None:
        """Subscribe."""
        await super().async_added_to_hass()

        async def on_battery(event: BatteryEvent) -> None:
            self._attr_native_value = event.value
            self.async_write_ha_state()

        self._subscribe(self._device.capabilities.battery.event, on_battery)


class ErrorSensor(EcovacsMowerEntity, SensorEntity):
    """Last error code."""

    _attr_translation_key = "error"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device) -> None:
        """Initialize."""
        super().__init__(device, "error")

    async def async_added_to_hass(self) -> None:
        """Subscribe."""
        await super().async_added_to_hass()

        async def on_error(event: ErrorEvent) -> None:
            self._attr_native_value = event.code
            self._attr_extra_state_attributes = {"description": event.description}
            self.async_write_ha_state()

        self._subscribe(self._device.capabilities.error.event, on_error)


class WifiSensor(EcovacsMowerEntity, SensorEntity):
    """Wi-Fi RSSI."""

    _attr_translation_key = "wifi_rssi"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"

    def __init__(self, device) -> None:
        """Initialize."""
        super().__init__(device, "wifi_rssi")

    async def async_added_to_hass(self) -> None:
        """Subscribe."""
        await super().async_added_to_hass()

        async def on_net(event: NetworkInfoEvent) -> None:
            self._attr_native_value = event.rssi
            self._attr_extra_state_attributes = {
                "ssid": event.ssid,
                "ip": event.ip,
            }
            self.async_write_ha_state()

        self._subscribe(self._device.capabilities.network.event, on_net)


class OpenStatusSensor(
    CoordinatorEntity[EcovacsOpenCoordinator], SensorEntity
):
    """Open Platform raw status sensor."""

    entity_description: OpenSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EcovacsOpenCoordinator,
        nickname: str,
        description: OpenSensorDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description
        self._nickname = nickname
        self._attr_unique_id = f"open_{nickname}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, nickname)},
            name=nickname,
            manufacturer="Ecovacs",
            model="Open Platform (limited)",
        )

    @property
    def native_value(self) -> str | None:
        """Return value."""
        data = self.coordinator.data.get(self._nickname)
        if data is None:
            return None
        return self.entity_description.value_fn(data)
