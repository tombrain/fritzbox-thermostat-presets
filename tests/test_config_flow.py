"""Tests for the config flow."""

from unittest.mock import AsyncMock

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fritzbox_thermostat_presets.api import FritzAuthError, FritzConnectionError
from custom_components.fritzbox_thermostat_presets.const import DOMAIN

from .conftest import CONFIG


async def test_user_flow(hass: HomeAssistant, mock_api: AsyncMock) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], CONFIG)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "fritz.box"
    assert result["data"] == CONFIG


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (FritzAuthError, "invalid_auth"),
        (FritzConnectionError, "cannot_connect"),
        (ValueError, "unknown"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant, mock_api: AsyncMock, side_effect: type[Exception], error: str
) -> None:
    mock_api.get_thermostats.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], CONFIG)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    # Recovers once the problem is fixed
    mock_api.get_thermostats.side_effect = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], CONFIG)
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_already_configured(hass: HomeAssistant, mock_api: AsyncMock, config_entry: MockConfigEntry) -> None:
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], CONFIG)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(hass: HomeAssistant, mock_api: AsyncMock, config_entry: MockConfigEntry) -> None:
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "homeassistant", CONF_PASSWORD: "new-secret"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[CONF_PASSWORD] == "new-secret"
