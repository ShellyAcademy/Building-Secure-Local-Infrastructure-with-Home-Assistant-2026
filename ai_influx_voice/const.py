"""Constants for the AI Influx Voice integration."""

DOMAIN = "ai_influx_voice"

# Config Flow Keys
CONF_INFLUX_HOST = "influx_host"
CONF_INFLUX_PORT = "influx_port"
CONF_INFLUX_DB = "influx_db"
CONF_INFLUX_USER = "influx_user"
CONF_INFLUX_PASS = "influx_pass"
CONF_LLM_PROVIDER = "llm_provider"
CONF_API_KEY = "api_key"
CONF_MODEL_NAME = "model_name"
CONF_REFRESH_INTERVAL = "refresh_interval"
CONF_DRY_RUN = "dry_run"
CONF_OLLAMA_URL = "ollama_url"

# Defaults
DEFAULT_INFLUX_PORT = 8086
DEFAULT_REFRESH_INTERVAL = 12
DEFAULT_MODEL_OPENAI = "gpt-4o"
DEFAULT_MODEL_GEMINI = "gemini-1.5-pro-latest"
DEFAULT_OLLAMA_URL = "http://localhost:11434"

# Security: Destructive / Admin keywords to reject
DESTRUCTIVE_KEYWORDS = [
    "DROP", "DELETE", "ALTER", "CREATE", "GRANT", 
    "REVOKE", "KILL", "INSERT", "UPDATE", "INTO"
]

# Validation
MAX_RAW_POINTS = 1000