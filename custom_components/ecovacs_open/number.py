"""Number platform (cut direction, etc.)."""

from __future__ import annotations

from deebot_client.events import CutDirectionEvent

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import DEGREE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EcovacsOpenConfigEntry
from .const import CONF_MODE, MODE_CLOUD
from .entity import EcovacsMowerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EcovacsOpenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up numbers."""
    if entry.data.get(CONF_MODE) != MODE_CLOUD:
        return
    controller = entry.runtime_data
    entities: list[NumberEntity] = []
    for device in controller.devices:
        if device.capabilities.settings.cut_direction:
            entities.append(CutDirectionNumber(device))
    async_add_entities(entities)


class CutDirectionNumber(EcovacsMowerEntity, NumberEntity):
    """Cut direction angle (0-180)."""

    _attr_translation_key = "cut_direction"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0
    _attr_native_max_value = 180
    _attr_native_step = 1
    _attr_native_unit_of_measurement = DEGREE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, device) -> None:
        """Initialize."""
        super().__init__(device, "cut_direction")
        self._capability = device.capabilities.settings.cut_direction

    async def async_added_to_hass(self) -> None:
        """Subscribe."""
        await super().async_added_to_hass()

        async def on_event(event: CutDirectionEvent) -> None:
            self._attr_native_value = event.angle
            self.async_write_ha_state()

        self._subscribe(self._capability.event, on_event)

    async def async_set_native_value(self, value: float) -> None:
        """Set cut direction."""
        await self._device.execute_command(self._capability.set(int(value)))
