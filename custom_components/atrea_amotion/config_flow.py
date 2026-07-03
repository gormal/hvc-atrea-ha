"""Config flow for Atrea DUPLEX (aMotion)."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from pymodbus.client import AsyncModbusTcpClient

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL

from .const import (
    CONF_SLAVE,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def _test_connection(host: str, port: int, slave: int) -> bool:
    """Try to connect and read register I1001 to prove the unit is reachable."""
    client = AsyncModbusTcpClient(host, port=port)
    try:
        await client.connect()
        if not client.connected:
            return False
        try:
            rr = await client.read_input_registers(1001, count=1, slave=slave)
        except TypeError:
            rr = await client.read_input_registers(1001, count=1, device_id=slave)
        return bool(rr) and not rr.isError()
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Atrea connection test failed: %s", err)
        return False
    finally:
        client.close()


class AtreaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the UI setup: user types the unit's IP address."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            slave = user_input[CONF_SLAVE]

            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            if await _test_connection(host, port, slave):
                return self.async_create_entry(
                    title=f"Atrea DUPLEX ({host})", data=user_input
                )
            errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_SLAVE, default=DEFAULT_SLAVE): int,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): int,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
