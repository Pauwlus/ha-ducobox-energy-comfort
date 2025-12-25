
# DucoBox Home Assistant Integration (HACS)

A custom Home Assistant integration for **Duco Box** ventilation systems, installable via **HACS**. It automatically discovers nodes from the DucoBox configuration page and creates sensor entities with **stable, hardware-derived unique IDs** and friendly names.

> Documentation: https://github.com/Pauwlus/ha-ducobox-energy-comfort

---

## ✨ Features

- **Automatic discovery** of nodes from `http://ducobox.localdomain/index.html` during setup
- Per-node data read from `http://ducobox.localdomain/nodeinfoget?node={node}`
- **Stable IDs** derived from hardware fields: `devtype`, `subtype`, `node/zone id`, `serial`
  - Lowercase ASCII; separators: `_` or `-`
  - Unique per entity and **stable** across restarts/updates
- **Devices** created for nodes of type **UCHR**, **UCCO2**, **VLV** with the name `DucoBox node - {location}`
- **BOX** device named `DucoBox - {nodenumber}`
- **Sensors** created with friendly names:
  - Node friendly name: `{Location description}`
  - Entity friendly name: `{Location description} {item name}`
- Entities by type:
  - **BOX**: all attributes inside categories `energyinfo` and `energyfan`
  - **UCHR**: `temp`, `rh`, `snsr`, `state`
  - **UCCO2**: `temp`, `co2`, `snsr`
  - **VLV**: `trgt`, `actl`, `snsr`
- Installation + configuration via **HACS** with:
  - Hostname
  - Friendly device name (default: `DucoBox Energy Comfort`)
  - Scan interval
  - Area selection per discovered node

---

## 📦 Installation (HACS)

1. In HACS, go to **Integrations** → **⋮** → **Custom repositories**.
2. Add this repository URL and select category **Integration**.
3. Install **DucoBox**.
4. In Home Assistant, go to **Settings → Devices & services → + Add Integration → DucoBox**.
5. Enter:
   - **Hostname**: e.g., `ducobox.localdomain` or IP
   - **Friendly name**: e.g., `DucoBox Energy Comfort`
   - **Scan interval** (seconds)
6. Select an **Area** for each discovered node (optional). Areas can be changed later from **Devices**.

---

## 🔧 Configuration Details

- **Entity IDs** are explicitly created following the spec, e.g.: `sensor.ducobox_uchr_12_123456_temp`
- **Unique IDs** are derived at installation: `devtype_subtype_node_serial` (lowercase ASCII)
- **Device names**:
  - `DucoBox node - {location}` for UCHR/UCCO2/VLV
  - `DucoBox - {nodenumber}` for BOX
- **Units**:
  - `temp` → °C
  - `rh`  → %
  - `co2` → ppm

---

## 🧠 How it works

- A background coordinator polls the DucoBox on the configured interval.
- Node discovery is done by scraping the index HTML and fetching per-node info.
- Sensors are created and linked to the proper device with friendly names.
- The integration enforces **entity_id** in the entity registry so IDs stay consistent.

---

## 🛡️ Notes & Caveats

- The integration uses local HTTP (`aiohttp`) and does not require cloud access.
- If your DucoBox pages differ in format, discovery uses best-effort parsing of tables and key-value lines.
- Areas can be assigned during setup; you can change them any time in **Settings → Areas**.

---

## 📁 Repository Structure

```
custom_components/ducobox/
├── __init__.py
├── api.py
├── config_flow.py
├── const.py
├── coordinator.py
├── manifest.json
├── sensor.py
hacs.json
README.md
```

---

## 🧪 Testing

- Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.ducobox: debug
```

---

## 📜 License

MIT License.
```
Copyright (c) 2025 Pauwlus

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
