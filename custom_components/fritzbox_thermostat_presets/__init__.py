"""Thermostat Presets for Fritzbox: comfort and eco temperature of FRITZ!DECT thermostats."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FritzSmartHomeApi
from .coordinator import ThermostatPresetsConfigEntry, ThermostatPresetsCoordinator

PLATFORMS = [Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ThermostatPresetsConfigEntry) -> bool:
    api = FritzSmartHomeApi(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = ThermostatPresetsCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ThermostatPresetsConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
