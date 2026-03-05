# Home Assistant AI Influx Voice Integration --- Master Prompt

## Context

You are a **senior Home Assistant custom integration developer
(Python)** with strong **InfluxDB 1.8 (InfluxQL)** and **LLM**
experience.

### IMPORTANT

-   This project uses **InfluxDB 1.8.x (NOT InfluxDB 2.x)**.
-   Query language is **InfluxQL (NOT Flux)**.
-   All responses must be **in English**.

------------------------------------------------------------------------

# Goal

Build a **Home Assistant Custom Component** that enables **advanced
historical energy analytics via Assist (voice/text)**.

The component converts **natural language energy questions into safe
InfluxQL queries**, executes them in **InfluxDB 1.x**, and returns a
**short voice‑friendly answer**.

------------------------------------------------------------------------

# High-Level Flow

## 1. User Question

The user asks a natural language question via **Home Assistant Assist**,
for example:

-   "How much energy did EM1 consume between 2026-02-01 and 2026-02-08?"
-   "Compare EM1 energy usage in the last 7 days vs the previous 7
    days."
-   "What was the peak power for EM1 in the last 7 days?"

------------------------------------------------------------------------

## 2. Schema Introspection

The integration performs **real InfluxDB 1.x schema introspection
(InfluxQL)**.

It builds a **compact schema snapshot**, caches it in memory, and
refreshes only if expired or via a service call.

Use the following queries:

``` sql
SHOW MEASUREMENTS
SHOW FIELD KEYS FROM "<measurement>"
SHOW TAG KEYS FROM "<measurement>"
SHOW TAG VALUES FROM "<measurement>" WITH KEY = "entity_id"


Assume Home Assistant often uses:

- measurement `"state"`
- tag `"entity_id"`
- field `"value"`

But **do not hardcode these assumptions**. Always rely on the **actual introspection results**.

---

## 3. LLM Query Plan

The integration sends the following to an LLM:

- the **user question**
- the **compact schema snapshot**

The LLM must return **STRICT JSON ONLY**, with **no markdown** and **no additional text**.

```json
{
  "influxql": "...",
  "reasoning_brief": "...",
  "time_range": "...",
  "entities": ["..."],
  "aggregation": "..."
}
```

------------------------------------------------------------------------

## 4. Query Validation

The generated **InfluxQL must be treated as untrusted input** and
validated.

Rules:

-   Must be a **single SELECT query only**.
-   Must include a **WHERE time clause**.
-   Must reference **only known measurements** from schema
    introspection.
-   Must reject destructive or administrative keywords:

```{=html}
<!-- -->
```
    DROP, DELETE, ALTER, CREATE, GRANT, REVOKE, KILL

-   If returning raw points, enforce a **LIMIT safety cap**.

------------------------------------------------------------------------

## 5. Execute Query

Execute the validated InfluxQL against **InfluxDB 1.x** using the HTTP:

    /query endpoint

Return the results as **compact JSON**.

------------------------------------------------------------------------

## 6. Generate Natural Language Answer

Send the results JSON back to the LLM with the instruction:

> Produce a short, clear, voice‑friendly answer in English.\
> Mention numbers and the time range.\
> If no data exists, clearly state that.

------------------------------------------------------------------------

## 7. Return Result

Return the final answer to **Home Assistant Assist**.

------------------------------------------------------------------------

# Consumption / Energy Logic

For **cumulative energy sensors**:

    consumption = max(value) − min(value)

within the requested time range.

Guidelines:

-   Use `GROUP BY time()` only when needed (for example daily
    summaries).
-   For comparisons like **this week vs last week**, the integration may
    run multiple queries.

All queries must remain **validated and safe**.

------------------------------------------------------------------------

# Technical Requirements

Integration folder:

    custom_components/ai_influx_voice/

Required files:

-   manifest.json
-   const.py
-   **init**.py
-   config_flow.py
-   conversation.py
-   services.yaml (service: refresh schema)
-   translations/en.json
-   README.md

------------------------------------------------------------------------

# Config Flow (UI Only --- No YAML)

Collect the following settings:

-   InfluxDB host
-   InfluxDB port
-   Database name
-   Username
-   Password
-   LLM provider: `"OpenAI"` or `"Gemini"`
-   API key
-   Model name
-   Schema refresh interval (hours, default = 12)
-   Dry‑run mode (boolean)

------------------------------------------------------------------------

# Implementation Guidance

Use Home Assistant's **supported conversation integration patterns**:

-   `ConversationEntity`
-   agent platform

Ensure compatibility across **Home Assistant versions**.

### Important

-   Implement required abstract members such as `supported_languages`.
-   Use the officially supported response object for conversation
    results.
-   Prefer **IntentResponse‑based replies** for compatibility.
-   Do not rely on non‑existent helper classes.

------------------------------------------------------------------------

# Error Handling

All exceptions must be handled gracefully.

The Assist pipeline must **never produce**:

    Unexpected error during intent recognition

------------------------------------------------------------------------

# Logging Rules

Never log:

-   API keys
-   passwords
-   tokens

Sensitive values must be **redacted**.

------------------------------------------------------------------------

# HTTP Requirements

Use:

    aiohttp

For HTTP basic authentication use:

``` python
aiohttp.BasicAuth(...)
```

Do **NOT** use raw tuples.

------------------------------------------------------------------------

# LLM Behavior Constraints

The LLM must:

-   Generate **InfluxQL only**
-   Never generate Flux or SQL
-   Always include:

```{=html}
<!-- -->
```
    WHERE time >= ...
    AND time <= ...

or relative time such as:

    now() - 7d

Prefer filtering by:

    entity_id tag

when appropriate.

------------------------------------------------------------------------

# Security

The integration must treat **LLM output as untrusted**.

Rules:

-   Reject queries without time filter
-   Reject destructive keywords
-   Enforce LIMIT on raw points
-   Never execute multiple statements
-   Ensure safe logging

------------------------------------------------------------------------

# Deliverables

The generated output must include:

1.  Full file tree
2.  Full code for every file
3.  Clear comments explaining logic
4.  Explanation where **Home Assistant version compatibility matters**
5.  Example voice queries and expected behavior

Example scenarios:

-   peak power
-   energy consumption
-   date range queries
-   week‑over‑week comparisons

------------------------------------------------------------------------

# Critical Requirement

Do **NOT** generate:

-   Flux queries
-   InfluxDB 2.x APIs

Use **InfluxQL only**.

------------------------------------------------------------------------

# Final Instruction

Generate the **complete Home Assistant custom integration** following
the specifications above.
