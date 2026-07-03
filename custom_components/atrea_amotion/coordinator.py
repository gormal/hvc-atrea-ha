"""Data update coordinator and shared Modbus client for Atrea aMotion."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from pymodbus.client import AsyncModbusTcpClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SLAVE,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    DISCRETE_ADDRESSES,
    DOMAIN,
    INPUT_BLOCKS,
    REQUEST_DELAY,
)

_LOGGER = logging.getLogger(__name__)


class AtreaCoordinator(DataUpdateCoordinator[dict]):
    """Polls the unit and serialises all Modbus access through one client."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data.get(CONF_PORT, DEFAULT_PORT)
        self.slave: int = entry.data.get(CONF_SLAVE, DEFAULT_SLAVE)
        scan = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        self._client = AsyncModbusTcpClient(self.host, port=self.port)
        self._lock = asyncio.Lock()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan),
        )

    # -- low-level helpers (tolerate pymodbus slave/device_id rename) ---------

    async def _ensure_connected(self) -> None:
        if not self._client.connected:
            await self._client.connect()
        if not self._client.connected:
            raise UpdateFailed(f"Cannot connect to Atrea unit at {self.host}:{self.port}")

    async def _read_input(self, address: int, count: int):
        try:
            return await self._client.read_input_registers(
                address, count=count, slave=self.slave
            )
        except TypeError:
            return await self._client.read_input_registers(
                address, count=count, device_id=self.slave
            )

    async def _read_discrete(self, address: int, count: int):
        try:
            return await self._client.read_discrete_inputs(
                address, count=count, slave=self.slave
            )
        except TypeError:
            return await self._client.read_discrete_inputs(
                address, count=count, device_id=self.slave
            )

    async def _write_register_raw(self, address: int, value: int):
        try:
            return await self._client.write_register(address, value, slave=self.slave)
        except TypeError:
            return await self._client.write_register(
                address, value, device_id=self.slave
            )

    async def _write_coil_raw(self, address: int, value: bool):
        try:
            return await self._client.write_coil(address, value, slave=self.slave)
        except TypeError:
            return await self._client.write_coil(address, value, device_id=self.slave)

    # -- polling --------------------------------------------------------------

    async def _async_update_data(self) -> dict:
        ir: dict[int, int] = {}
        di: dict[str, bool] = {}
        async with self._lock:
            await self._ensure_connected()

            for start, count in INPUT_BLOCKS:
                try:
                    rr = await self._read_input(start, count)
                    if rr and not rr.isError():
                        for offset, value in enumerate(rr.registers):
                            ir[start + offset] = value
                except Exception as err:  # noqa: BLE001 - degrade gracefully
                    _LOGGER.debug("Read of input block %s failed: %s", start, err)
                await asyncio.sleep(REQUEST_DELAY)

            for key, address in DISCRETE_ADDRESSES.items():
                try:
                    rr = await self._read_discrete(address, 1)
                    if rr and not rr.isError():
                        di[key] = bool(rr.bits[0])
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Read of discrete %s failed: %s", address, err)
                await asyncio.sleep(REQUEST_DELAY)

        if not ir:
            raise UpdateFailed("No data received from Atrea unit")
        return {"ir": ir, "di": di}

    # -- writes (called by number/select/button entities) --------------------

    async def async_write_register(self, address: int, value: int) -> None:
        async with self._lock:
            await self._ensure_connected()
            result = await self._write_register_raw(address, int(value))
            if result and result.isError():
                raise UpdateFailed(f"Write to H{address} failed")
        await self.async_request_refresh()

    async def async_write_coil(self, address: int, value: bool) -> None:
        async with self._lock:
            await self._ensure_connected()
            result = await self._write_coil_raw(address, value)
            if result and result.isError():
                raise UpdateFailed(f"Write to C{address} failed")
        await self.async_request_refresh()

    async def async_close(self) -> None:
        self._client.close()
