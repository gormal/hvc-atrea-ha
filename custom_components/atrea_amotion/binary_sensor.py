"""Binary sensors (alarms / status) for Atrea aMotion."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AtreaCoordinator
from .entity import AtreaEntity


@dataclass(frozen=True, kw_only=True)
class AtreaBinaryDescription(BinarySensorEntityDescription):
    """Description keyed by the discrete-input dict key."""

    data_key: str


BINARY_SENSORS: tuple[AtreaBinaryDescription, ...] = (
    AtreaBinaryDescription(
        key="fans_running",
        data_key="fans_running",
        name="Fans running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:fan",
    ),
    AtreaBinaryDescription(
        key="alarm_overheat",
        data_key="alarm_overheat",
        name="Alarm: overheat",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    AtreaBinaryDescription(
        key="alarm_frost1",
        data_key="alarm_frost1",
        name="Alarm: frost protection",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    AtreaBinaryDescription(
        key="alarm_unbalanced",
        data_key="alarm_unbalanced",
        name="Alarm: unbalanced airflow",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    AtreaBinaryDescription(
        key="warn_lowflow",
        data_key="warn_lowflow",
        name="Warning: insufficient airflow",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    AtreaBinaryDescription(
        key="warn_filters",
        data_key="warn_filters",
        name="Warning: filters dirty",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:air-filter",
    ),
    AtreaBinaryDescription(
        key="alarm_ethernet",
        data_key="alarm_ethernet",
        name="Alarm: ethernet comm fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    AtreaBinaryDescription(
        key="alarm_not_ready",
        data_key="alarm_not_ready",
        name="Alarm: device not ready",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AtreaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AtreaBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class AtreaBinarySensor(AtreaEntity, BinarySensorEntity):
    entity_description: AtreaBinaryDescription

    def __init__(self, coordinator, entry, description: AtreaBinaryDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self._di.get(self.entity_description.data_key)
