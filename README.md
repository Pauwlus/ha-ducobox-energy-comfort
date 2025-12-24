
# DucoBox (Home Assistant Custom Integration) — v0.3.7 (Predefined Nodes)

This build **disables auto-discovery** and instead **loads nodes from a JSON file**.

- Preferred user-editable file: **`/config/ducobox/nodes.json`**
- Fallback (shipped): **`custom_components/ducobox/nodes.json`**

Each entry looks like:
```json
{
  "node": 67,
  "devtype": "VLV",
  "subtype": 0,
  "location": "Zone 1 - Beneden",
  "serialnb": "optional"
}
```

## Endpoints & behavior
- Box info: `GET /boxinfoget`
- Node info: `GET /nodeinfoget?node={id}`
- Set mode:  `POST /nodesetoperstate?node={id}&mode={AUTO|MAN1|MAN2|MAN3}`

## Entities
- BOX sensors: filter remaining time (**days**), fan speeds (**rpm**, no speed device_class), pressures (Pa), temperatures (°C).
- Per-node sensors (for UCRH/UCCO2/VLV): `mode`, `state`, `trgt` (%), `actl` (%), `snsr`, plus `rh` (%) and `co2` (ppm) if present.
- Per-node **Operation Mode** control (select) when the node reports `mode`.

## Options
- **Create node entities (controls & sensors)** — defaults **ON**.

## How to edit nodes
1. Copy `custom_components/ducobox/nodes.json` to `/config/ducobox/nodes.json`.
2. Edit the file with your node IDs / locations / devtypes (e.g., `UCRH`, `UCCO2`, `VLV`).
3. In HA, go to **Settings → Devices & Services → DucoBox → Reload** (or restart Core).

## Based on your earlier REST setup
The sample `nodes.json` reflects your legacy REST sensors:
- 67: Zone 1 beneden (VLV)
- 68: Zone 2 boven (VLV)
- 2:  Badkamer (UCRH)
- 3:  Slaapkamer (UCCO2)
- 4:  Woonkamer (UCCO2)

