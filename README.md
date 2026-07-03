# Atrea DUPLEX (aMotion) — Home Assistant integration

Control an **Atrea DUPLEX** ventilation unit that uses the **aMotion** controller
(e.g. *DUPLEX Pro.aM* models) from Home Assistant over **Modbus TCP**, with a
standard UI setup: **Settings → Add Integration → Atrea → enter the IP address**.

> [!IMPORTANT]
> **This integration was "vibe-coded" with an AI assistant.** It was written
> from Atrea's public Modbus documentation and lightly tested. There are no
> automated tests and it is **not** an official Atrea product. Review the code
> before using it, and use it at your own risk — especially any of the write
> controls.

Built from Atrea's official document *"MODBUS Communication – RD5 and aMotion"*,
v04 (2025-04-25), section 3.2 (aMotion).

> **Why not other Atrea components?** Several existing Home Assistant components
> talk to the older **RD5** controller's HTTP/XML web API and do **not** work
> with aMotion. aMotion units are controlled over Modbus TCP, which this
> integration uses.

---

## Prerequisites

1. **Enable Modbus on the unit:** aMotion app/web interface or aTouch controller →
   **Settings → System → Modbus** (toggle on). Modbus is disabled from the factory.
2. **Find the unit's IP address:** check your router's DHCP client list, and set a
   **DHCP reservation** so the address does not change.

---

## Installation

### Option A — HACS (custom repository)

1. In HACS, open the ⋮ menu → **Custom repositories**.
2. Add this repository's URL with category **Integration**.
3. Search for **Atrea DUPLEX (aMotion)** and download it.
4. **Restart Home Assistant.**

### Option B — Manual

1. Copy the `custom_components/atrea_amotion/` folder from this repository into
   your Home Assistant configuration directory, so you have:
   ```
   <config>/custom_components/atrea_amotion/__init__.py
   <config>/custom_components/atrea_amotion/manifest.json
   ...
   ```
2. **Restart Home Assistant.**

---

## Adding the integration

1. **Settings → Devices & Services → Add Integration.**
2. Search for **Atrea DUPLEX (aMotion)**.
3. Enter:
   - **IP address** — the unit's LAN IP (required)
   - **Port** — `502` (default)
   - **Unit ID** — `1` (default)
   - **Scan interval** — `30` seconds (default)
4. Submit. The integration test-connects immediately and reports if the unit is
   unreachable. On success, an **Atrea DUPLEX** device is created with all
   entities grouped under it.

---

## Which fan control applies? (register I1201)

After setup, open the **Atrea DUPLEX** device and check the **Fan control mode**
diagnostic sensor:

| Value                | Control to use        | Ignore          |
|----------------------|-----------------------|-----------------|
| **Direct %**         | *Set fan power* (%)   | *Set airflow*   |
| **Constant airflow** | *Set airflow* (m³/h)  | *Set fan power* |
| **Constant pressure**| (not exposed yet)     | both            |

Both *Set fan power* and *Set airflow* entities are created; keep the one that
matches your unit's configured mode. The airflow control auto-limits itself to
the unit's own min/max (registers I1203 / I1202).

---

## Entities

Grouped under a single **Atrea DUPLEX** device:

- **Sensors:** Mode, Operating state, Setpoint temperature, Requested fan power,
  Requested airflow, five air temperatures (T-ODA / T-SUP / T-ETA / T-IDA / T-EHA),
  Airflow supply, Airflow extract.
- **Diagnostics:** Fan control mode, Min/Max settable airflow.
- **Binary sensors (alarms):** overheat, frost protection, unbalanced airflow,
  insufficient airflow, dirty filters, ethernet communication fault,
  device-not-ready, fans running.
- **Controls:** Set mode, Set temperature, Set fan power, Set airflow, Bypass,
  Zone.
- **Buttons:** Reset alarms, Reset filter counter.

---

## Rate limit

The aMotion controller allows a maximum of **30 Modbus sessions per 30 seconds**.
This integration batches reads (roughly 13 requests per polling cycle) and
defaults to a 30-second scan interval, keeping it comfortably under the limit.
If you set a much shorter scan interval and entities start showing `unavailable`,
increase it again.

---

## Troubleshooting

- **"Could not connect" during setup** — wrong IP address, Modbus not enabled on
  the unit, or TCP port 502 blocked. Verify with any Modbus client: reading input
  register `1001` should return the current mode.
- **Entities show `unavailable`** — the unit dropped off the network, or the rate
  limit was exceeded (see above).

---

## Notes

- **Writes are persistent.** Set a value once; the unit remembers it. There is no
  need to re-write periodically.
- **Weekly schedule interaction.** If the unit runs its own weekly program, a
  scheduled entry may later override a value set over Modbus. For pure Home
  Assistant control, run the unit in manual operation.
- **Bypass encoding.** The unit reports bypass state (I1009) using a different
  code order than it accepts for commands (H1009); the integration maps both
  correctly.

## Roadmap / ideas

- Combined `climate` / `fan` entity.
- Expose more of the full alarm/warning list (D6003–D6111).
- Write outdoor/indoor temperatures to the unit (H1500 / H1501) — this first
  requires setting the corresponding temperature source to "BMS" via Atrea's
  service tooling.

---

## Disclaimer

Not affiliated with or endorsed by Atrea. "Atrea" and "DUPLEX" are trademarks of
their respective owner. Provided as-is, without warranty of any kind.

## License

MIT
