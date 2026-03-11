# AI Influx Voice (Home Assistant Custom Component)

This custom component allows you to natively query historical sensor data from **InfluxDB 1.8.x** via Home Assistant Assist using natural language.

## Home Assistant Version Compatibility ⚠️
This integration relies on `conversation.ConversationEntity` and `conversation.AbstractConversationAgent`. These abstractions were heavily formalized in HA `2023.x` and `2024.x`. You must be running Home Assistant **2024.1 or later** to ensure standard compatibility with `ConversationInput` and `ConversationResult` objects.

## Security & Logging
- **Untrusted Output:** LLM outputs are treated as untrusted. Every query is validated against destructive keywords (`DROP`, `DELETE`, etc.), must include a `WHERE time` clause, and enforces a safety `LIMIT`.
- **Secret Redaction:** Passwords and API keys are strictly excluded from logging.

## Example Voice Queries

**1. Energy Consumption (Cumulative)**
> *"How much energy did sensor.washing_machine_energy consume last week?"*
> **Expected Action:** Introspects schema, generates `SELECT max(value) - min(value) FROM "state" WHERE entity_id='washing_machine_energy' AND time >= now() - 14d AND time <= now() - 7d`. 

**2. Peak Power**
> *"What was the peak power for EM1 in the last 7 days?"*
> **Expected Action:** Generates `SELECT max(value) FROM "state" WHERE entity_id='em1_power' AND time >= now() - 7d`.

**3. Week-over-Week Comparison**
> *"Compare EM1 energy usage in the last 7 days vs the previous 7 days."*
> **Expected Action:** The LLM constructs a query fetching the two distinct time boundaries, mathematically compares the bounds, and returns a natural English synthesis of both values.