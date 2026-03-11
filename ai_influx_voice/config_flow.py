"""Config flow for AI Influx Voice."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN, CONF_INFLUX_HOST, CONF_INFLUX_PORT, CONF_INFLUX_DB,
    CONF_INFLUX_USER, CONF_INFLUX_PASS, CONF_LLM_PROVIDER,
    CONF_API_KEY, CONF_MODEL_NAME, CONF_REFRESH_INTERVAL, CONF_DRY_RUN,
    CONF_OLLAMA_URL, DEFAULT_INFLUX_PORT, DEFAULT_REFRESH_INTERVAL, 
    DEFAULT_MODEL_OPENAI, DEFAULT_OLLAMA_URL
)

class AIInfluxVoiceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AI Influx Voice."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Create the entry and pass the data forward
            return self.async_create_entry(
                title=f"AI Influx ({user_input[CONF_INFLUX_DB]})", 
                data=user_input
            )

        # Build the UI form schema
        data_schema = vol.Schema({
            vol.Required(CONF_INFLUX_HOST): str,
            vol.Required(CONF_INFLUX_PORT, default=DEFAULT_INFLUX_PORT): int,
            vol.Required(CONF_INFLUX_DB): str,
            vol.Optional(CONF_INFLUX_USER): str,
            vol.Optional(CONF_INFLUX_PASS): str,
            vol.Required(CONF_LLM_PROVIDER, default="OpenAI"): vol.In(["OpenAI", "Gemini", "Ollama"]),
            vol.Optional(CONF_API_KEY, default=""): str,
            vol.Required(CONF_MODEL_NAME, default=DEFAULT_MODEL_OPENAI): str,
            vol.Optional(CONF_OLLAMA_URL, default=DEFAULT_OLLAMA_URL): str,
            vol.Required(CONF_REFRESH_INTERVAL, default=DEFAULT_REFRESH_INTERVAL): int,
            vol.Optional(CONF_DRY_RUN, default=False): bool,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )