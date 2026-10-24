"""Tests for the number entities."""

from unittest.mock import AsyncMock

from homeassistant.components.number import ATTR_VALUE, DOMAIN as NUMBER_DOMAIN, SERVICE_SET_VALUE
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fritzbox_thermostat_presets.api import FritzAuthError, FritzConnectionError

from .conftest import UID

COMFORT = "number.living_room_comfort_temperature"
REDUCED = "number.living_room_reduced_temperature"


async def setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_entities(hass: HomeAssistant, mock_api: AsyncMock, config_entry: MockConfigEntry) -> None:
    await setup_integration(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get(COMFORT).state == "22.0"
    assert hass.states.get(REDUCED).state == "19.0"


async def test_set_value(hass: HomeAssistant, mock_api: AsyncMock, config_entry: MockConfigEntry) -> None:
    await setup_integration(hass, config_entry)
    await hass.services.async_call(
        NUMBER_DOMAIN, SERVICE_SET_VALUE, {ATTR_ENTITY_ID: COMFORT, ATTR_VALUE: 21.5}, blocking=True
    )
    mock_api.set_temperature.assert_awaited_once_with(UID, "comfortTemperature", 21.5)


@pytest.mark.parametrize("side_effect", [FritzAuthError, FritzConnectionError])
async def test_set_value_error(
    hass: HomeAssistant, mock_api: AsyncMock, config_entry: MockConfigEntry, side_effect: type[Exception]
) -> None:
    await setup_integration(hass, config_entry)
    mock_api.set_temperature.side_effect = side_effect("boom")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            NUMBER_DOMAIN, SERVICE_SET_VALUE, {ATTR_ENTITY_ID: REDUCED, ATTR_VALUE: 18}, blocking=True
        )


async def test_setup_auth_failure_starts_reauth(
    hass: HomeAssistant, mock_api: AsyncMock, config_entry: MockConfigEntry
) -> None:
    mock_api.get_thermostats.side_effect = FritzAuthError
    await setup_integration(hass, config_entry)
    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    assert any(flow["context"]["source"] == "reauth" for flow in hass.config_entries.flow.async_progress())
