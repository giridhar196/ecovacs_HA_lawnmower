"""Base entity for Ecovacs cloud mowers."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from deebot_client.device import Device
from deebot_client.events import AvailabilityEvent
from deebot_client.events.base import Event

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class EcovacsMowerEntity(Entity):
    """Base MQTT-backed mower entity."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, device: Device, key: str) -> None:
        """Initialize."""
        self._device = device
        self._attr_unique_id = f"{device.device_info['did']}_{key}"
        self._subscribed_events: set[type[Event]] = set()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        info = self._device.device_info
        device_info = DeviceInfo(
            identifiers={(DOMAIN, info["did"])},
            manufacturer="Ecovacs",
            sw_version=self._device.fw_version,
            serial_number=info.get("name"),
            model_id=info.get("class"),
            model=info.get("deviceName") or "GOAT",
            name=info.get("nick") or info.get("deviceName") or "Lawn mower",
        )
        if mac := self._device.mac:
            device_info["connections"] = {(dr.CONNECTION_NETWORK_MAC, mac)}
        return device_info

    async def async_added_to_hass(self) -> None:
        """Subscribe availability."""
        await super().async_added_to_hass()

        async def on_available(event: AvailabilityEvent) -> None:
            self._attr_available = event.available
            self.async_write_ha_state()

        self._subscribe(AvailabilityEvent, on_available)

    def _subscribe[EventT: Event](
        self,
        event_type: type[EventT],
        callback: Callable[[EventT], Coroutine[Any, Any, None]],
    ) -> None:
        """Subscribe to a deebot event."""
        self._subscribed_events.add(event_type)
        self.async_on_remove(self._device.events.subscribe(event_type, callback))
