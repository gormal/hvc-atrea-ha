"""Select entities (mode, bypass, zone) for Atrea aMotion."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BYPASS_READ_MAP,
    BYPASS_WRITE_TO_VALUE,
    DOMAIN,
    MODE_MAP,
    MODE_TO_VALUE,
    REG_BYPASS,
    REG_MODE,
    REG_ZONE,
    ZONE_MAP,
    ZONE_TO_VALUE,
)
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
            AtreaModeSelect(coordinator, entry),
            AtreaBypassSelect(coordinator, entry),
            AtreaZoneSelect(coordinator, entry),
        ]
    )


class AtreaModeSelect(AtreaEntity, SelectEntity):
    _attr_name = "Set mode"
    _attr_icon = "mdi:hvac"
    _attr_options = list(MODE_TO_VALUE.keys())

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "set_mode")

    @property
    def current_option(self) -> str | None:
        return MODE_MAP.get(self._ir.get(REG_MODE))

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_write_register(REG_MODE, MODE_TO_VALUE[option])


class AtreaBypassSelect(AtreaEntity, SelectEntity):
    _attr_name = "Bypass"
    _attr_icon = "mdi:valve"
    _attr_options = list(BYPASS_WRITE_TO_VALUE.keys())

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "bypass")

    @property
    def current_option(self) -> str | None:
        # Read uses a different encoding than write (see const.py).
        return BYPASS_READ_MAP.get(self._ir.get(1009))

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_write_register(
            REG_BYPASS, BYPASS_WRITE_TO_VALUE[option]
        )


class AtreaZoneSelect(AtreaEntity, SelectEntity):
    _attr_name = "Zone"
    _attr_icon = "mdi:home-floor-a"
    _attr_options = list(ZONE_TO_VALUE.keys())

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "zone")

    @property
    def current_option(self) -> str | None:
        return ZONE_MAP.get(self._ir.get(REG_ZONE))

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_write_register(REG_ZONE, ZONE_TO_VALUE[option])
