"""Sensor entities for Atrea aMotion."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    AIRFLOW_MODES,
    BYPASS_DAMPER_MAP,
    CIRC_DAMPER_MAP,
    DOMAIN,
    FAN_CTRL_MAP,
    MODE_MAP,
    POWER_MODES,
    STATE_MAP,
    airflow_m3h,
    power_pct,
    signed16,
)
from .coordinator import AtreaCoordinator
from .entity import AtreaEntity


def _temp(ir: dict[int, int], addr: int) -> float | None:
    if addr not in ir:
        return None
    return round(signed16(ir[addr]) * 0.1, 1)


@dataclass(frozen=True, kw_only=True)
class AtreaSensorDescription(SensorEntityDescription):
    """Sensor description with a value function over the input-register dict."""

    value_fn: Callable[[dict[int, int]], float | str | None]
    # Optional gate: entity is available only when this returns True.
    available_fn: Callable[[dict[int, int]], bool] | None = None


SENSORS: tuple[AtreaSensorDescription, ...] = (
    AtreaSensorDescription(
        key="mode",
        name="Mode",
        icon="mdi:hvac",
        value_fn=lambda ir: MODE_MAP.get(ir.get(1001), None),
    ),
    AtreaSensorDescription(
        key="operating_state",
        name="Operating state",
        icon="mdi:state-machine",
        value_fn=lambda ir: STATE_MAP.get(ir.get(1119), None),
    ),
    AtreaSensorDescription(
        key="setpoint_temperature",
        name="Setpoint temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda ir: round(ir[1002] * 0.1, 1) if 1002 in ir else None,
    ),
    AtreaSensorDescription(
        key="requested_power",
        name="Requested fan power",
        icon="mdi:fan",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda ir: power_pct(ir.get(1004)),
        available_fn=lambda ir: ir.get(1201) is None or ir.get(1201) in POWER_MODES,
    ),
    AtreaSensorDescription(
        key="requested_airflow",
        name="Requested airflow",
        icon="mdi:weather-windy",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda ir: airflow_m3h(ir.get(1005)),
        available_fn=lambda ir: ir.get(1201) is None or ir.get(1201) in AIRFLOW_MODES,
    ),
    AtreaSensorDescription(
        key="fan_control_mode",
        name="Fan control mode",
        icon="mdi:cog",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda ir: FAN_CTRL_MAP.get(ir.get(1201), None),
    ),
    AtreaSensorDescription(
        key="bypass_damper",
        name="Bypass damper",
        icon="mdi:valve",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda ir: BYPASS_DAMPER_MAP.get(ir.get(1206), None),
    ),
    # Raw value of I1009 (current bypass command) for diagnosis: we want to see
    # exactly what the unit reports in automatic mode (0=Auto, 1=Open, 2=Closed,
    # or a sentinel). Once confirmed, this can drive a proper open/closed state.
    AtreaSensorDescription(
        key="bypass_command_raw",
        name="Bypass command (raw)",
        icon="mdi:numeric",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda ir: ir.get(1009),
    ),
    AtreaSensorDescription(
        key="circulation_damper",
        name="Circulation damper",
        icon="mdi:valve",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda ir: CIRC_DAMPER_MAP.get(ir.get(1205), None),
    ),
    AtreaSensorDescription(
        key="max_airflow",
        name="Max settable airflow",
        icon="mdi:arrow-up-bold",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        value_fn=lambda ir: airflow_m3h(ir.get(1202)),
    ),
    AtreaSensorDescription(
        key="min_airflow",
        name="Min settable airflow",
        icon="mdi:arrow-down-bold",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        value_fn=lambda ir: airflow_m3h(ir.get(1203)),
    ),
    AtreaSensorDescription(
        key="t_oda",
        name="Outdoor air (T-ODA)",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda ir: _temp(ir, 1101),
    ),
    AtreaSensorDescription(
        key="t_sup",
        name="Supply air (T-SUP)",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda ir: _temp(ir, 1102),
    ),
    AtreaSensorDescription(
        key="t_eta",
        name="Extract air (T-ETA)",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda ir: _temp(ir, 1103),
    ),
    AtreaSensorDescription(
        key="t_ida",
        name="Indoor air (T-IDA)",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda ir: _temp(ir, 1104),
    ),
    AtreaSensorDescription(
        key="t_eha",
        name="Exhaust air (T-EHA)",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda ir: _temp(ir, 1105),
    ),
    AtreaSensorDescription(
        key="airflow_supply",
        name="Airflow supply (M-SUP)",
        icon="mdi:fan",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda ir: airflow_m3h(ir.get(1109)),
    ),
    AtreaSensorDescription(
        key="airflow_extract",
        name="Airflow extract (M-ETA)",
        icon="mdi:fan",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda ir: airflow_m3h(ir.get(1110)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AtreaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AtreaSensor(coordinator, entry, description) for description in SENSORS
    )


class AtreaSensor(AtreaEntity, SensorEntity):
    """A single Atrea sensor."""

    entity_description: AtreaSensorDescription

    def __init__(self, coordinator, entry, description: AtreaSensorDescription) -> None:
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | str | None:
        return self.entity_description.value_fn(self._ir)

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        if self.entity_description.available_fn is not None:
            return self.entity_description.available_fn(self._ir)
        return True
