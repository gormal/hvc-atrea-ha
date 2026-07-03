"""Number entities (temperature, fan power, airflow) for Atrea aMotion."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    AIRFLOW_MODES,
    DOMAIN,
    POWER_MODES,
    REG_AIRFLOW,
    REG_POWER,
    REG_TEMP,
    airflow_m3h,
    power_pct,
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
            AtreaTemperatureNumber(coordinator, entry),
            AtreaPowerNumber(coordinator, entry),
            AtreaAirflowNumber(coordinator, entry),
        ]
    )


class AtreaTemperatureNumber(AtreaEntity, NumberEntity):
    _attr_name = "Set temperature"
    _attr_icon = "mdi:thermometer"
    _attr_native_min_value = 10
    _attr_native_max_value = 40
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "set_temperature")

    @property
    def native_value(self) -> float | None:
        raw = self._ir.get(REG_TEMP)
        return round(raw * 0.1, 1) if raw is not None else None

    async def async_set_native_value(self, value: float) -> None:
        # H1002 expects degrees * 10.
        await self.coordinator.async_write_register(REG_TEMP, round(value * 10))


class AtreaPowerNumber(AtreaEntity, NumberEntity):
    """Fan power in %. Use when Fan control mode (I1201) = Direct %."""

    _attr_name = "Set fan power"
    _attr_icon = "mdi:fan"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "set_power")

    @property
    def available(self) -> bool:
        return super().available and (
            self.fan_mode is None or self.fan_mode in POWER_MODES
        )

    @property
    def native_value(self) -> float | None:
        return power_pct(self._ir.get(REG_POWER))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_register(REG_POWER, round(value))


class AtreaAirflowNumber(AtreaEntity, NumberEntity):
    """Airflow in m3/h. Use when Fan control mode (I1201) = Constant airflow.

    Min/max follow the unit's own limits (I1203 / I1202) when available.
    """

    _attr_name = "Set airflow"
    _attr_icon = "mdi:weather-windy"
    _attr_native_step = 10
    _attr_native_unit_of_measurement = UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "set_airflow")

    @property
    def available(self) -> bool:
        return super().available and (
            self.fan_mode is None or self.fan_mode in AIRFLOW_MODES
        )

    @property
    def native_min_value(self) -> float:
        return airflow_m3h(self._ir.get(1203)) or 0

    @property
    def native_max_value(self) -> float:
        return airflow_m3h(self._ir.get(1202)) or 1000

    @property
    def native_value(self) -> float | None:
        return airflow_m3h(self._ir.get(REG_AIRFLOW))

    async def async_set_native_value(self, value: float) -> None:
        # H1005 expects m3/h / 10.
        await self.coordinator.async_write_register(REG_AIRFLOW, round(value / 10))
