"""Select platform for mowing zones."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import EcovacsOpenConfigEntry
from .const import CONF_MODE, MODE_CLOUD
from .entity import EcovacsMowerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EcovacsOpenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up zone select entities."""
    if entry.data.get(CONF_MODE) != MODE_CLOUD:
        return
    controller = entry.runtime_data
    async_add_entities(ZoneSelect(device, controller) for device in controller.devices)


class ZoneSelect(EcovacsMowerEntity, RestoreEntity, SelectEntity):
    """Select a zone id for start_zones / edge trim services.

    Zone ids come from the Ecovacs app (map areas). Use the refresh_zones
    service or set options via start_zones with explicit ids; this select
    remembers the last chosen zone for quick UI starts.
    """

    _attr_translation_key = "mowing_zone"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options: list[str] = []

    def __init__(self, device, controller) -> None:
        """Initialize."""
        super().__init__(device, "mowing_zone")
        self._controller = controller
        self._attr_current_option = None
        did = device.device_info["did"]
        zones = controller.zone_ids.get(did, [])
        self._attr_options = zones or ["1", "2", "3", "4"]

    async def async_added_to_hass(self) -> None:
        """Restore last option."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) and last.state in self._attr_options:
            self._attr_current_option = last.state

    async def async_select_option(self, option: str) -> None:
        """Select zone."""
        self._attr_current_option = option
        self.async_write_ha_state()

    def set_zone_options(self, zones: list[str]) -> None:
        """Update available zones from a refresh."""
        self._attr_options = zones or self._attr_options
        if self._attr_current_option not in self._attr_options:
            self._attr_current_option = self._attr_options[0] if self._attr_options else None
        self.async_write_ha_state()
