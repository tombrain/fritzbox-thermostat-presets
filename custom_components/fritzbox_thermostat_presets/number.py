"""Number entities for comfort and reduced temperature."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import FritzAuthError, FritzError
from .const import DOMAIN, MAX_TEMPERATURE, MIN_TEMPERATURE, TEMPERATURE_STEP
from .coordinator import ThermostatPresetsConfigEntry, ThermostatPresetsCoordinator

# translation_key -> field in thermostatInterface
TEMPERATURE_KEYS = {
    "comfort_temperature": "comfortTemperature",
    "reduced_temperature": "reducedTemperature",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThermostatPresetsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        ThermostatPresetNumber(coordinator, uid, translation_key, api_key)
        for uid in coordinator.data
        for translation_key, api_key in TEMPERATURE_KEYS.items()
    )


class ThermostatPresetNumber(CoordinatorEntity[ThermostatPresetsCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = MIN_TEMPERATURE
    _attr_native_max_value = MAX_TEMPERATURE
    _attr_native_step = TEMPERATURE_STEP

    def __init__(self, coordinator: ThermostatPresetsCoordinator, uid: str, translation_key: str, api_key: str) -> None:
        super().__init__(coordinator)
        self._uid = uid
        self._api_key = api_key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{uid}_{translation_key}"

        unit = coordinator.data[uid]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unit.get("ain", uid))},
            name=unit.get("name", uid),
            manufacturer="AVM",
        )

    @property
    def available(self) -> bool:
        return super().available and self._uid in self.coordinator.data

    @property
    def native_value(self) -> float | None:
        thermostat = self.coordinator.data[self._uid]["interfaces"]["thermostatInterface"]
        temperature = thermostat.get(self._api_key)
        if not temperature or temperature.get("mode") != "temperature":
            return None
        return temperature.get("celsius")

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self.coordinator.api.set_temperature(self._uid, self._api_key, value)
        except FritzAuthError as err:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="missing_rights") from err
        except FritzError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        await self.coordinator.async_request_refresh()
