"""Shared fixtures."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fritzbox_thermostat_presets.const import DOMAIN

UID = "12345 0000001-1"
CONFIG = {CONF_HOST: "fritz.box", CONF_USERNAME: "homeassistant", CONF_PASSWORD: "secret"}

THERMOSTAT = {
    "UID": UID,
    "ain": "12345 0000001",
    "name": "Living room",
    "interfaces": {
        "thermostatInterface": {
            "setPointTemperature": {"mode": "temperature", "celsius": 21.0},
            "comfortTemperature": {"mode": "temperature", "celsius": 22.0},
            "reducedTemperature": {"mode": "temperature", "celsius": 19.0},
        }
    },
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow loading custom_components in every test."""


@pytest.fixture
def mock_api() -> Generator[AsyncMock]:
    """Patch the API client in setup and config flow."""
    with (
        patch("custom_components.fritzbox_thermostat_presets.FritzSmartHomeApi", autospec=True) as api_cls,
        patch("custom_components.fritzbox_thermostat_presets.config_flow.FritzSmartHomeApi", new=api_cls),
    ):
        api = api_cls.return_value
        api.get_thermostats.return_value = {UID: THERMOSTAT}
        yield api


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(domain=DOMAIN, title="fritz.box", unique_id="fritz.box", data=CONFIG)
