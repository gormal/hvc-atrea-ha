"""Constants and register maps for the Atrea DUPLEX (aMotion) integration.

All register indexes are taken from Atrea's official document
"Komunikace MODBUS - RD5 a aMotion", v04 (2025-04-25), section 3.2 (aMotion).
The index numbers in that document ARE the Modbus addresses.
"""

from __future__ import annotations

DOMAIN = "atrea_amotion"

CONF_SLAVE = "slave"

DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
DEFAULT_SCAN_INTERVAL = 30

# Small pause between Modbus requests. aMotion allows max 30 sessions / 30 s;
# one refresh does ~13 requests, so this keeps us comfortably under the limit.
REQUEST_DELAY = 0.2

# Contiguous input-register (I####) blocks read in one request each.
# (start_address, count) -- every address in each range is defined in the doc.
INPUT_BLOCKS: tuple[tuple[int, int], ...] = (
    (1001, 12),   # I1001..I1012  requests: mode, setpoint, zone, power, airflow, ...
    (1101, 6),    # I1101..I1106  temperatures T-ODA/SUP/ETA/IDA/EHA + avg
    (1109, 2),    # I1109..I1110  actual airflow SUP / ETA
    (1119, 1),    # I1119         operating state
    (1201, 3),    # I1201..I1203  fan-control mode, max/min settable airflow
)

# Discrete inputs (D####) read individually (guaranteed-valid addresses).
DISCRETE_ADDRESSES: dict[str, int] = {
    "fans_running": 2301,       # D2301
    "alarm_frost1": 6003,       # D6003 1. mrazova ochrana
    "alarm_overheat": 6012,     # D6012 Prehrati jednotky
    "alarm_unbalanced": 6014,   # D6014 Nevyrovnany prutok
    "warn_lowflow": 6015,       # D6015 Nedostatecny prutok
    "alarm_ethernet": 6073,     # D6073 Porucha komunikace na Ethernetu
    "alarm_not_ready": 6085,    # D6085 Zarizeni neni pripraveno
    "warn_filters": 6104,       # D6104 Zanesene filtry
}

# Holding registers (H####) we write to.
REG_MODE = 1001        # H1001 Pozadovany rezim
REG_TEMP = 1002        # H1002 Pozadovana teplota (value = degC * 10)
REG_ZONE = 1003        # H1003 Pozadovana zona
REG_POWER = 1004       # H1004 Pozadovany vykon ventilatoru (1-100 %)
REG_AIRFLOW = 1005     # H1005 Pozadovany prutok vetrani (value = m3/h / 10)
REG_BYPASS = 1009      # H1009 Povel na klapku bypassu

# Coils (C####) -- pulse commands.
COIL_RESET_ALARMS = 8001   # C8001
COIL_RESET_FILTER = 8002   # C8002

# Enum maps -------------------------------------------------------------------

# I1001 / H1001 operating mode
MODE_MAP: dict[int, str] = {
    0: "Off",
    1: "Auto",
    2: "Ventilation",
    3: "Circulation+Vent",
    4: "Circulation",
    5: "Night cooling",
    6: "Balancing",
    7: "Overpressure",
    8: "Ventilation Mix",
}
MODE_TO_VALUE: dict[str, int] = {v: k for k, v in MODE_MAP.items()}

# I1119 operating state
STATE_MAP: dict[int, str] = {
    0: "Off",
    1: "Condensate evaporation",
    2: "Run-down",
    3: "Normal",
    4: "Filter test",
    5: "Flow stabilization",
    6: "Substitute control",
    7: "Ventilation interval",
    8: "Reduced ventilation",
    9: "HX defrosting",
    10: "Forced circulation",
    11: "Start-up",
    12: "Preheating",
    13: "Frost protection",
    14: "Preventive stop",
    15: "Safety stop",
}

# I1201 fan-control mode
FAN_CTRL_MAP: dict[int, str] = {
    0: "Direct %",
    1: "Constant pressure",
    2: "Constant airflow",
    3: "External",
    4: "Direct % per fan",
    5: "Constant airflow per fan",
}

# Zone: read I1003 and write H1003 use the same encoding.
ZONE_MAP: dict[int, str] = {0: "Both zones", 1: "Zone 1", 2: "Zone 2"}
ZONE_TO_VALUE: dict[str, int] = {v: k for k, v in ZONE_MAP.items()}

# Bypass: read (I1009) and write (H1009) use DIFFERENT encodings per the doc!
#   Read  I1009: 0=Auto, 1=Open, 2=Closed
#   Write H1009: 0=Auto, 1=Closed, 2=Open
BYPASS_READ_MAP: dict[int, str] = {0: "Auto", 1: "Open", 2: "Closed"}
BYPASS_WRITE_TO_VALUE: dict[str, int] = {"Auto": 0, "Closed": 1, "Open": 2}


# I1201 fan-control modes grouped by which command register they use.
POWER_MODES = {0, 4}      # Direct % -> H1004
AIRFLOW_MODES = {2, 5}    # Constant airflow -> H1005


def signed16(raw: int) -> int:
    """Interpret an unsigned 16-bit register as signed int16."""
    return raw - 65536 if raw >= 32768 else raw


def airflow_m3h(raw: int | None) -> int | None:
    """Convert an airflow register (raw * 10 = m3/h) to m3/h.

    Registers that don't apply in the current fan-control mode return a large
    sentinel (e.g. 64536 = -1000 signed); treat those as unknown.
    """
    if raw is None or raw >= 32768:
        return None
    return raw * 10


def power_pct(raw: int | None) -> int | None:
    """Fan power in %. Non-applicable modes return a sentinel; treat as unknown."""
    if raw is None or raw > 100:
        return None
    return raw
