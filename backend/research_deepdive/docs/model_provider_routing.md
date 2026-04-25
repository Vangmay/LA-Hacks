# Model Provider Routing

The deep-dive pipeline keeps model routing isolated from the v0.4 review
pipeline. Review agents still use `settings.openai_model`; research deep-dive
agents use `DeepDiveConfig.thinking_profile` and `DeepDiveConfig.light_profile`.

## Role Classes

Thinking profile:

- Director
- Investigator
- Critique
- Revision
- Finalization

Light profile:

- search subagents
- extraction helpers
- formatting helpers
- dedupe helpers
- metadata classification

## Default Deep-Dive Model

The default deep-dive provider is Google Gemini through the OpenAI-compatible
Gemini endpoint:

- thinking profile model: `gemini-3.1-pro-preview`
- thinking profile reasoning effort: `high`
- light/search profile model: `gemini-3.1-pro-preview`
- light/search profile reasoning effort: `medium`
- API key: `GEMINI_API_KEY`
- base URL: `https://generativelanguage.googleapis.com/v1beta/openai/`

This keeps Director, Investigator, Critique, Revision, and Finalization on a
high-reasoning model while search subagents and helper roles use the same model
with medium reasoning for tool-heavy work.

## OpenAI-Compatible Providers

Google documents an OpenAI-compatible Gemini API endpoint. The key settings are:

- API key: `GEMINI_API_KEY`
- base URL: `https://generativelanguage.googleapis.com/v1beta/openai/`
- model: a Gemini model enabled for the key

The deep-dive code uses the ordinary `openai.AsyncOpenAI` chat-completions
client with a configured `base_url`, so OpenAI and Google-compatible models use
the same application-level JSON action protocol.

The live tool loop does not depend on provider-native tool tokens. The model is
prompted to emit:

```json
{"action":"paper_bulk_search","arguments":{"query":"..."}}
```

or:

```json
{"action":"final","summary":"...","handoff_markdown":"# Hand-Off\n..."}
```

The orchestrator validates the tool name, runs the Python implementation, logs
the call, and appends durable markdown memory.

## Official References

- Google Gemini OpenAI compatibility:
  `https://ai.google.dev/gemini-api/docs/openai`
- Gemini function calling:
  `https://ai.google.dev/gemini-api/docs/function-calling`
- Gemma function calling behavior:
  `https://ai.google.dev/gemma/docs/capabilities/function-calling`
- Gemini model capability table:
  `https://ai.google.dev/gemini-api/docs/models`
