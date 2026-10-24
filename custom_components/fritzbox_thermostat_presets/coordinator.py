"""Polls the Fritzbox for thermostat data."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FritzAuthError, FritzError, FritzSmartHomeApi
from .const import DOMAIN, LOGGER, UPDATE_INTERVAL

type ThermostatPresetsConfigEntry = ConfigEntry[ThermostatPresetsCoordinator]


class ThermostatPresetsCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Holds the thermostat units keyed by UID."""

    def __init__(self, hass: HomeAssistant, entry: ThermostatPresetsConfigEntry, api: FritzSmartHomeApi) -> None:
        super().__init__(hass, LOGGER, config_entry=entry, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            return await self.api.get_thermostats()
        except FritzAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except FritzError as err:
            raise UpdateFailed(str(err)) from err
