# DucoBox (Home Assistant Custom Integration)

A Home Assistant custom integration for **Itho Daalderop DucoBox** ventilation units. It discovers Duco nodes from the built-in web API and exposes sensors plus an **Operation Mode** handler (AUTO/MAN1/MAN2/MAN3).

## Features

- UI-based setup via Config Flow (hostname, friendly device name, scan interval)
- Automatic discovery of nodes based on DucoBox configuration
- Device & Entity IDs derived from hardware IDs (stable, user-friendly)
- Sensors: Supply/Exhaust fan RPM, filter hours, temperatures (ODA/SUP/ETA/EHA)
- Per-zone entity to set operation mode (AUTO, MAN1, MAN2, MAN3)
- HACS-ready repository

## Installation (HACS)
1. In HACS → Integrations → **Custom repositories**, add the URL of this repo and select type **Integration**.
2. Install **DucoBox**.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add Integration → DucoBox** and follow the wizard.

## Configuration
- **Hostname**: e.g. `ducobox.localdomain` or IP.
- **Friendly device name**: Used as the device label.
- **Scan interval**: Polling interval in seconds.

## Entity IDs & Unique IDs
- **Device identifiers**: `(ducobox, ducobox-<rfhomeid>-<serial|unknown>)`
- **Entity unique_id**: `{base_device_id}_{devtype}_{subtype}_{node_id}_{serial}_{metric}`.
- Friendly names use the **location** defined in the DucoBox (e.g. `Zone 1 - Beneden`).

## Endpoints (examples)
- `http://ducobox.localdomain/boxinfoget`
- `http://ducobox.localdomain/nodeinfoget?node=67`

## License
MIT
