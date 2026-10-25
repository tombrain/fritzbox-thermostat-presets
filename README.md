<img src="custom_components/fritzbox_thermostat_presets/brand/icon.png" alt="" width="96" align="right">

# Thermostat Presets for Fritzbox

[![Validate](https://github.com/tombrain/fritzbox-thermostat-presets/actions/workflows/validate.yml/badge.svg)](https://github.com/tombrain/fritzbox-thermostat-presets/actions/workflows/validate.yml)
[![Tests](https://github.com/tombrain/fritzbox-thermostat-presets/actions/workflows/tests.yml/badge.svg)](https://github.com/tombrain/fritzbox-thermostat-presets/actions/workflows/tests.yml)
[![GitHub Release](https://img.shields.io/github/v/release/tombrain/fritzbox-thermostat-presets)](https://github.com/tombrain/fritzbox-thermostat-presets/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![License: MIT](https://img.shields.io/github/license/tombrain/fritzbox-thermostat-presets)](LICENSE)

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=tombrain&repository=fritzbox-thermostat-presets&category=integration)

🇩🇪 [Deutsche Anleitung](README.de.md)

A Home Assistant custom integration to change the **comfort** and **eco (reduced)**
temperature** of FRITZ!DECT radiator thermostats connected to a Fritzbox.

The built-in AVM FRITZ!SmartHome integration can only change the current target temperature.
The comfort and eco temperatures used by the thermostat's schedule can only be changed in
the Fritzbox web UI. This integration makes them available as entities, so you can change them
from dashboards, scripts and automations.

> **Disclaimer:** This is an independent community project. It is not affiliated with,
> endorsed by or supported by AVM / FRITZ!. FRITZ!, FRITZ!Box and FRITZ!DECT are trademarks
> of their respective owners.

## Features

- Two entities per thermostat: **Comfort temperature** and **Eco temperature**
  (8–28 °C, 0.5 °C steps)
- Uses the official, documented
  [FRITZ! Smart Home REST API](https://fritz.support/resources/SmarthomeRestApiFRITZOS82.html)
- Set up through the UI, no YAML required
- Local polling (every 60 seconds), no cloud
- Re-authentication when the password changes
- Diagnostics download for bug reports
- English and German translations

## Requirements

| | |
|---|---|
| Fritzbox | FRITZ!OS **8.20** or newer |
| Thermostats | FRITZ!DECT 301 (tested), 302 and other thermostats exposed by the REST API should work |
| Home Assistant | 2025.3 or newer |
| Fritzbox user | rights **Smart Home** and **FRITZ!Box Einstellungen** (FRITZ!Box settings) |

### Create a Fritzbox user

1. Open the Fritzbox web UI (http://fritz.box).
2. Go to **System → FRITZ!Box Users → Add User**.
3. Choose a name (e.g. `homeassistant`) and a strong password.
4. Enable the rights **Smart Home** and **FRITZ!Box Einstellungen**.
   The second right is required by the REST API to *change* thermostat settings.
   Reading works with **Smart Home** alone.
5. Save.

## Installation

### HACS (recommended)

1. In HACS open the menu (⋮) → **Custom repositories**.
2. Add `https://github.com/tombrain/fritzbox-thermostat-presets` with type **Integration**.
3. Search for **Thermostat Presets for Fritzbox** and download it.
4. Restart Home Assistant.

### Manual

1. Copy the folder `custom_components/fritzbox_thermostat_presets` into the
   `custom_components` folder of your Home Assistant configuration.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & services → Add integration**.
2. Search for **Thermostat Presets for Fritzbox**.
3. Enter:
   - **Host**: `fritz.box` or the IP address of your Fritzbox
   - **Username** and **Password** of the Fritzbox user created above

Every thermostat appears as a device with two entities in the **Configuration** section.

## Usage

### Entities

| Entity | Description |
|---|---|
| `number.<thermostat>_comfort_temperature` | Comfort temperature (schedule "heating" periods) |
| `number.<thermostat>_eco_temperature` | Eco temperature (schedule "setback" periods) |

The entity IDs depend on the thermostat name and the language of your Home Assistant at the
time of setup. With a German UI they are e.g. `number.living_room_komfort_temperatur`.

### Dashboard card

```yaml
type: entities
title: Heating living room
entities:
  - entity: number.living_room_comfort_temperature
  - entity: number.living_room_eco_temperature
```

### Action

```yaml
action: number.set_value
target:
  entity_id: number.living_room_comfort_temperature
data:
  value: 21.5
```

### Automation example: warmer comfort temperature on cold days

```yaml
automation:
  - alias: "Raise comfort temperature when it's freezing"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.outdoor_temperature
        below: 0
    actions:
      - action: number.set_value
        target:
          entity_id: number.living_room_comfort_temperature
        data:
          value: 22.5

  - alias: "Normal comfort temperature"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.outdoor_temperature
        above: 3
    actions:
      - action: number.set_value
        target:
          entity_id: number.living_room_comfort_temperature
        data:
          value: 21.5
```

## Troubleshooting

| Problem | Solution |
|---|---|
| *Invalid authentication or missing user rights* during setup | Check username and password. Make sure the user has the **Smart Home** right. |
| *Failed to connect* | Check the host. Try the IP address instead of `fritz.box`. Make sure FRITZ!OS is 8.20 or newer (older versions don't have the REST API). |
| *Access denied … needs the right 'FRITZ!Box settings'* when changing a value | Give the Fritzbox user the right **FRITZ!Box Einstellungen**. |
| Changing a value fails | If a **temperature limit** (*Temperaturgrenze*) is set for the thermostat in the Fritzbox, values outside this range may be rejected. |
| Value is shown in Home Assistant but the thermostat display hasn't changed yet | The Fritzbox sends the new value with the next radio contact of the thermostat, which can take a few minutes. |
| Thermostat shows up twice | This integration creates its own devices, separate from the built-in AVM FRITZ!SmartHome integration. |

### Debug logging

```yaml
logger:
  default: warning
  logs:
    custom_components.fritzbox_thermostat_presets: debug
```

### Diagnostics

**Settings → Devices & services → Thermostat Presets for Fritzbox → ⋮ → Download diagnostics.**
Username and password are removed. Please attach this file to bug reports.

## Development

### Probe script

A standalone script (Python standard library only) to test the Fritzbox API without
Home Assistant:

```bash
python tools/fritz_probe.py --user <user>                                # list thermostats
python tools/fritz_probe.py --user <user> --get "<UID>"                  # full unit config as JSON
python tools/fritz_probe.py --user <user> --uid "<UID>" --comfort 21.5   # set
```

### Local Home Assistant

```bash
cd ha-dev
docker compose up -d
```

Home Assistant runs at http://localhost:8123 and loads the integration from
`custom_components/`. Run `docker compose restart` after code changes.

### Tests

```bash
pip install -r requirements_test.txt
pytest
```

Or without a local Python, in Docker:

```bash
docker run --rm -v "$PWD:/repo" -w /repo python:3.14-slim \
  sh -c "pip install -q -r requirements_test.txt && pytest"
```

## License

[MIT](LICENSE)
