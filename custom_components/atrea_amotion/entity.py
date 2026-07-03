"""Shared base entity for Atrea aMotion."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AtreaCoordinator


class AtreaEntity(CoordinatorEntity[AtreaCoordinator]):
    """Base class wiring every entity to the shared device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: AtreaCoordinator, entry: ConfigEntry, key: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Atrea DUPLEX",
            manufacturer="Atrea",
            model="DUPLEX (aMotion)",
            configuration_url=f"http://{coordinator.host}",
        )

    @property
    def _ir(self) -> dict[int, int]:
        return (self.coordinator.data or {}).get("ir", {})

    @property
    def _di(self) -> dict[str, bool]:
        return (self.coordinator.data or {}).get("di", {})

    @property
    def fan_mode(self) -> int | None:
        """Current fan-control mode (register I1201), or None if unknown."""
        return self._ir.get(1201)
