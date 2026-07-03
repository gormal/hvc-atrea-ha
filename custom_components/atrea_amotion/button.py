"""Button entities (reset alarms / filter counter) for Atrea aMotion."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COIL_RESET_ALARMS, COIL_RESET_FILTER, DOMAIN
from .coordinator import AtreaCoordinator
from .entity import AtreaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AtreaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AtreaResetAlarmsButton(coordinator, entry),
            AtreaResetFilterButton(coordinator, entry),
        ]
    )


class AtreaResetAlarmsButton(AtreaEntity, ButtonEntity):
    _attr_name = "Reset alarms"
    _attr_icon = "mdi:alarm-light"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "reset_alarms")

    async def async_press(self) -> None:
        await self.coordinator.async_write_coil(COIL_RESET_ALARMS, True)


class AtreaResetFilterButton(AtreaEntity, ButtonEntity):
    _attr_name = "Reset filter counter"
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "reset_filter")

    async def async_press(self) -> None:
        await self.coordinator.async_write_coil(COIL_RESET_FILTER, True)
