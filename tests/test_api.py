"""Tests for the API client."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.fritzbox_thermostat_presets.api import (
    FritzAuthError,
    FritzSmartHomeApi,
    _solve_pbkdf2_challenge,
)

from .conftest import THERMOSTAT, UID

LOGIN_URL = "http://fritz.box/login_sid.lua?version=2"
CHALLENGE_XML = (
    "<SessionInfo><SID>0000000000000000</SID><Challenge>2$10000$5A1711$2000$5A1722</Challenge></SessionInfo>"
)


def test_pbkdf2_challenge() -> None:
    # Example from AVM's "Technical Note - Session ID"
    assert (
        _solve_pbkdf2_challenge("2$10000$5A1711$2000$5A1722", "1example!")
        == "5A1722$1798a1672bca7c6463d6b245f82b53703b0f50813401b03e4045a5861e689adb"
    )


async def test_get_thermostats_filters_units(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(LOGIN_URL, text=CHALLENGE_XML)
    aioclient_mock.post(LOGIN_URL, text="<SessionInfo><SID>abcdef0123456789</SID></SessionInfo>")
    aioclient_mock.get(
        "http://fritz.box/api/v0/smarthome/overview/units",
        json=[THERMOSTAT, {"UID": "11111 2222222-1", "interfaces": {"onOffInterface": {}}}],
    )

    api = FritzSmartHomeApi(async_get_clientsession(hass), "fritz.box", "user", "1example!")
    assert await api.get_thermostats() == {UID: THERMOSTAT}
    assert aioclient_mock.mock_calls[-1][3]["Authorization"] == "AVM-SID abcdef0123456789"


async def test_login_invalid(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(LOGIN_URL, text=CHALLENGE_XML)
    aioclient_mock.post(LOGIN_URL, text=CHALLENGE_XML)

    api = FritzSmartHomeApi(async_get_clientsession(hass), "fritz.box", "user", "wrong")
    with pytest.raises(FritzAuthError):
        await api.login()


async def test_set_temperature_payload(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.get(LOGIN_URL, text=CHALLENGE_XML)
    aioclient_mock.post(LOGIN_URL, text="<SessionInfo><SID>abcdef0123456789</SID></SessionInfo>")
    aioclient_mock.put("http://fritz.box/api/v0/smarthome/configuration/units/12345%200000001-1")

    api = FritzSmartHomeApi(async_get_clientsession(hass), "fritz.box", "user", "1example!")
    await api.set_temperature(UID, "comfortTemperature", 21.5)

    assert aioclient_mock.mock_calls[-1][2] == {
        "interfaces": {"thermostatInterface": {"comfortTemperature": {"mode": "temperature", "celsius": 21.5}}}
    }
