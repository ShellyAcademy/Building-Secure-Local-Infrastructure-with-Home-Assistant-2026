"""Initialize the AI Influx Voice integration."""
import logging
import json
import re
from datetime import datetime
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN, CONF_INFLUX_HOST, CONF_INFLUX_PORT, CONF_INFLUX_DB,
    CONF_INFLUX_USER, CONF_INFLUX_PASS, CONF_LLM_PROVIDER,
    CONF_API_KEY, CONF_MODEL_NAME, CONF_DRY_RUN, CONF_OLLAMA_URL,
    DESTRUCTIVE_KEYWORDS, MAX_RAW_POINTS
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AI Influx Voice from a config entry."""
    manager = AIInfluxManager(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager

    # Perform initial schema fetch
    await manager.async_refresh_schema()

    # Register HA service to manually refresh schema
    async def handle_refresh_schema(call: ServiceCall):
        await manager.async_refresh_schema()
    
    hass.services.async_register(DOMAIN, "refresh_schema", handle_refresh_schema)

    # Forward to conversation platform
    await hass.config_entries.async_forward_entry_setups(entry, ["conversation"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["conversation"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class AIInfluxManager:
    """Manages InfluxDB 1.x connection and LLM API calls."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self.config = entry.data
        self.session = async_get_clientsession(hass)
        self.schema_snapshot = {}
        self.base_url = f"http://{self.config[CONF_INFLUX_HOST]}:{self.config[CONF_INFLUX_PORT]}/query"

    @property
    def auth(self):
        """Return basic auth if configured."""
        user = self.config.get(CONF_INFLUX_USER)
        pwd = self.config.get(CONF_INFLUX_PASS)
        if user and pwd:
            return aiohttp.BasicAuth(user, pwd)
        return None

    async def _execute_influx_query(self, query: str) -> dict:
        """Execute a raw InfluxQL query against InfluxDB 1.8."""
        params = {"db": self.config[CONF_INFLUX_DB], "q": query}
        try:
            async with self.session.get(self.base_url, params=params, auth=self.auth) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as e:
            _LOGGER.error("InfluxDB Request Failed. Query: %s", query)
            raise e

    async def async_refresh_schema(self):
        """Introspect InfluxDB 1.x schema and cache it."""
        _LOGGER.debug("Refreshing InfluxDB schema snapshot")
        try:
            measurements_data = await self._execute_influx_query("SHOW MEASUREMENTS")
            measurements = [m[0] for m in measurements_data.get("results", [{}])[0].get("series", [{}])[0].get("values", [])]

            schema = {}
            for m in measurements:
                schema[m] = {"fields": [], "tags": [], "entities": []}
                
                fields_data = await self._execute_influx_query(f'SHOW FIELD KEYS FROM "{m}"')
                if "series" in fields_data["results"][0]:
                    schema[m]["fields"] = [f[0] for f in fields_data["results"][0]["series"][0].get("values", [])]
                
                tags_data = await self._execute_influx_query(f'SHOW TAG KEYS FROM "{m}"')
                if "series" in tags_data["results"][0]:
                    schema[m]["tags"] = [t[0] for t in tags_data["results"][0]["series"][0].get("values", [])]

                if "entity_id" in schema[m]["tags"]:
                    entity_data = await self._execute_influx_query(f'SHOW TAG VALUES FROM "{m}" WITH KEY = "entity_id"')
                    if "series" in entity_data["results"][0]:
                        schema[m]["entities"] = [e[1] for e in entity_data["results"][0]["series"][0].get("values", [])]

            self.schema_snapshot = schema
            _LOGGER.debug("Schema refreshed successfully.")
        except Exception as e:
            _LOGGER.error("Failed to refresh schema: %s", e)

    def validate_and_secure_query(self, query: str) -> str:
        """Ensure the generated InfluxQL is safe and strictly follows constraints."""
        q_upper = query.upper()

        if ";" in query:
            raise ValueError("Multiple statements are forbidden.")
        
        for kw in DESTRUCTIVE_KEYWORDS:
            if re.search(rf"\b{kw}\b", q_upper):
                raise ValueError(f"Destructive keyword '{kw}' detected and rejected.")
        
        if "WHERE" not in q_upper or "TIME" not in q_upper:
            raise ValueError("Missing 'WHERE time' clause. Time boundaries are required.")

        if "GROUP BY" not in q_upper and "LIMIT" not in q_upper:
             query = f"{query} LIMIT {MAX_RAW_POINTS}"

        return query

    def _safe_log_query(self, query: str, success: bool, empty: bool, error: str = None):
        """Log the query execution details safely without secrets."""
        db_name = self.config.get(CONF_INFLUX_DB, "unknown")
        time_match = re.search(r"(time\s*[>=<]\s*[^and]+)", query, re.IGNORECASE)
        time_range = time_match.group(1) if time_match else "unknown"

        log_msg = (
            f"AI_INFLUX_EXECUTION | DB: {db_name} | Success: {success} | "
            f"Empty Result: {empty} | Time Range: {time_range} | "
            f"Query: {query} | Error: {error}"
        )
        _LOGGER.info(log_msg)

    async def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the selected LLM via REST to avoid library conflicts."""
        provider = self.config[CONF_LLM_PROVIDER]
        api_key = self.config.get(CONF_API_KEY, "")
        model = self.config[CONF_MODEL_NAME]
        
        if provider == "OpenAI":
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.0
            }
            async with self.session.post(url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
                
        elif provider == "Gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": [{"text": user_prompt}]}],
                "generationConfig": {"temperature": 0.0}
            }
            async with self.session.post(url, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
                
        elif provider == "Ollama":
            base_url = self.config.get(CONF_OLLAMA_URL, "http://localhost:11434").rstrip("/")
            url = f"{base_url}/api/chat"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {"temperature": 0.0}
            }
            async with self.session.post(url, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["message"]["content"]
        
        raise ValueError(f"Unsupported LLM provider: {provider}")

    def extract_json_from_llm(self, text: str) -> dict:
        """Extract JSON from LLM response (handles markdown wrappers)."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())

    async def process_user_query(self, user_question: str) -> str:
        """End-to-end processing of a natural language question."""
        current_time = datetime.now().isoformat()
        
        t2q_system = (
            "You are an InfluxDB 1.8 expert. Return ONLY valid JSON containing a query plan. "
            "No markdown, no explanation. Output format:\n"
            '{"influxql": "...", "reasoning_brief": "...", "time_range": "...", "entities": ["..."], "aggregation": "..."}\n\n'
            "RULES:\n"
            "- Use ONLY InfluxQL (NOT Flux, NOT SQL).\n"
            "- ALWAYS include a WHERE time clause (e.g. time >= now() - 7d).\n"
            "- For cumulative energy: max(value) - min(value).\n"
            "- Only use measurements and tags provided in the schema."
        )
        
        t2q_user = (
            f"Current Time: {current_time}\n"
            f"Schema Snapshot: {json.dumps(self.schema_snapshot)}\n"
            f"User Question: {user_question}"
        )

        try:
            llm_response = await self.call_llm(t2q_system, t2q_user)
            plan = self.extract_json_from_llm(llm_response)
            raw_query = plan["influxql"]
        except Exception as e:
            _LOGGER.error("Failed to generate/parse LLM query plan: %s", e)
            return "I'm sorry, I couldn't understand how to build a query for that."

        try:
            secure_query = self.validate_and_secure_query(raw_query)
        except ValueError as e:
            self._safe_log_query(raw_query, False, False, str(e))
            return "I'm sorry, the generated query was deemed unsafe or invalid."

        if self.config.get(CONF_DRY_RUN):
            self._safe_log_query(secure_query, True, False, "DRY RUN")
            return f"Dry run mode. Query: {secure_query}"

        try:
            db_results = await self._execute_influx_query(secure_query)
            is_empty = "series" not in db_results.get("results", [{}])[0]
            self._safe_log_query(secure_query, True, is_empty)
        except Exception as e:
            self._safe_log_query(secure_query, False, False, str(e))
            return "I'm sorry, I encountered a database error while retrieving the data."

        d2t_system = (
            "You are a helpful home energy assistant. Based on the user's question, "
            "the executed InfluxQL query, and the JSON results, provide a short, clear, "
            "voice-friendly answer in English. Mention numbers and time ranges. "
            "If the result is empty, clearly state no data exists for that range."
        )
        d2t_user = (
            f"Question: {user_question}\n"
            f"Query: {secure_query}\n"
            f"Results: {json.dumps(db_results)}\n"
        )

        try:
            final_answer = await self.call_llm(d2t_system, d2t_user)
            return final_answer
        except Exception as e:
            _LOGGER.error("Failed to generate final voice response: %s", e)
            return "I found the data, but encountered an error formatting it for you."