"""Switch platform (edge / border / protect)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from deebot_client.capabilities import Capabilities, CapabilitySetEnable
from deebot_client.events import EnableEvent

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EcovacsOpenConfigEntry
from .const import CONF_MODE, MODE_CLOUD
from .entity import EcovacsMowerEntity


@dataclass(frozen=True, kw_only=True)
class MowerSwitchDescription(SwitchEntityDescription):
    """Switch description."""

    capability_fn: Callable[[Capabilities], CapabilitySetEnable | None]


SWITCHES: tuple[MowerSwitchDescription, ...] = (
    MowerSwitchDescription(
        key="border_switch",
        translation_key="border_switch",
        entity_category=EntityCategory.CONFIG,
        capability_fn=lambda c: c.settings.border_switch,
    ),
    MowerSwitchDescription(
        key="border_spin",
        translation_key="border_spin",
        entity_category=EntityCategory.CONFIG,
        capability_fn=lambda c: c.settings.border_spin,
    ),
    MowerSwitchDescription(
        key="true_detect",
        translation_key="true_detect",
        entity_category=EntityCategory.CONFIG,
        capability_fn=lambda c: c.settings.true_detect,
    ),
    MowerSwitchDescription(
        key="safe_protect",
        translation_key="safe_protect",
        entity_category=EntityCategory.CONFIG,
        capability_fn=lambda c: c.settings.safe_protect,
    ),
    MowerSwitchDescription(
        key="child_lock",
        translation_key="child_lock",
        entity_category=EntityCategory.CONFIG,
        capability_fn=lambda c: c.settings.child_lock,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EcovacsOpenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches."""
    if entry.data.get(CONF_MODE) != MODE_CLOUD:
        return
    controller = entry.runtime_data
    entities: list[MowerSwitch] = []
    for device in controller.devices:
        for description in SWITCHES:
            capability = description.capability_fn(device.capabilities)
            if capability:
                entities.append(MowerSwitch(device, description, capability))
    async_add_entities(entities)


class MowerSwitch(EcovacsMowerEntity, SwitchEntity):
    """Capability-backed switch."""

    entity_description: MowerSwitchDescription

    def __init__(
        self,
        device,
        description: MowerSwitchDescription,
        capability: CapabilitySetEnable,
    ) -> None:
        """Initialize."""
        self.entity_description = description
        super().__init__(device, description.key)
        self._capability = capability
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Subscribe."""
        await super().async_added_to_hass()

        async def on_event(event: EnableEvent) -> None:
            self._attr_is_on = event.enable
            self.async_write_ha_state()

        self._subscribe(self._capability.event, on_event)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on."""
        await self._device.execute_command(self._capability.set(True))

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off."""
        await self._device.execute_command(self._capability.set(False))
