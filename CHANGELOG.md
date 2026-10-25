# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.1] - 2026-10-25

### Changed

- Renamed "Reduced temperature" to "Eco temperature" (German: "Komfort-Temperatur" /
  "Eco-Temperatur") to match the built-in AVM FRITZ!SmartHome integration.
- **Breaking:** the eco entity has a new unique ID and entity ID
  (`number.<thermostat>_eco_temperature`). If you installed 0.1.0, remove and re-add
  the integration.
- Probe script: `--reduced` is now `--eco`.

## [0.1.0] - 2026-10-24

### Added

- Comfort and reduced (eco) temperature as `number` entities for every thermostat
- Config flow with connection check
- Re-authentication flow
- Diagnostics
- English and German translations
- Integration icon (`brand/`, shown in Home Assistant 2026.3+)
