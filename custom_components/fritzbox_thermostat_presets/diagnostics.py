"""Diagnostics download (Settings → Devices & services → ⋮ → Download diagnostics)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .coordinator import ThermostatPresetsConfigEntry

TO_REDACT = {CONF_PASSWORD, CONF_USERNAME}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ThermostatPresetsConfigEntry
) -> dict[str, Any]:
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "thermostats": entry.runtime_data.data,
    }
