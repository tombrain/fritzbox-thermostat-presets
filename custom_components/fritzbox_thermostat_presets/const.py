"""Constants for the Thermostat Presets for Fritzbox integration."""

from datetime import timedelta
import logging

DOMAIN = "fritzbox_thermostat_presets"
LOGGER = logging.getLogger(__package__)

DEFAULT_HOST = "fritz.box"
UPDATE_INTERVAL = timedelta(seconds=60)

# Limits of the FRITZ! Smart Home REST API (helper_temperature schema)
MIN_TEMPERATURE = 8.0
MAX_TEMPERATURE = 28.0
TEMPERATURE_STEP = 0.5
