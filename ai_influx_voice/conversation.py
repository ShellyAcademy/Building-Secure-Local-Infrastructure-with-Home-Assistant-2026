"""Conversation support for AI Influx Voice."""
from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the conversation agent."""
    manager = hass.data[DOMAIN][entry.entry_id]
    agent = AIInfluxConversationEntity(manager, entry)
    async_add_entities([agent])

class AIInfluxConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent
):
    """AI Influx conversational agent."""

    def __init__(self, manager, entry: ConfigEntry):
        """Initialize the agent."""
        self.manager = manager
        self.entry = entry
        self._attr_name = f"AI Influx Voice ({entry.data['influx_db']})"
        self._attr_unique_id = f"{entry.entry_id}_agent"

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return ["en"]

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence and return a safe intent response."""
        intent_response = conversation.intent.IntentResponse(language=user_input.language)

        try:
            # Send question through our pipeline
            answer = await self.manager.process_user_query(user_input.text)
            intent_response.async_set_speech(answer)
        except Exception as e:
            # The pipeline must NEVER bubble an unexpected error to Assist.
            self.manager.hass.logger.error("Assist pipeline unexpected error: %s", e)
            intent_response.async_set_speech("I'm sorry, an internal error occurred.")

        return conversation.ConversationResult(
            response=intent_response, conversation_id=user_input.conversation_id
        )