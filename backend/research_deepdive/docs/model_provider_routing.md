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

The default deep-dive provider is hosted Gemma through Google's
OpenAI-compatible endpoint:

- thinking profile model: `gemma-4-26b-a4b-it`
- thinking profile reasoning effort: `high`
- light/search profile model: `gemma-4-26b-a4b-it`
- light/search profile reasoning effort: `high`
- API key: `GEMMA_API_KEY`
- base URL: `https://generativelanguage.googleapis.com/v1beta/openai/`

This keeps Director, Investigator, Critique, Revision, and Finalization on a
high-reasoning model while search subagents and helper roles use the same
thinking-enabled model for tool-heavy work.

## OpenAI-Compatible Providers

Google documents an OpenAI-compatible Gemini API endpoint. The key settings are:

- API key: `GEMMA_API_KEY` or another configured Google AI Studio key env var
- base URL: `https://generativelanguage.googleapis.com/v1beta/openai/`
- model: a Gemini/Gemma model enabled for the key

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

All tool parameters must remain inside `arguments`. Provider models sometimes
drift toward top-level `query` or `limit` keys after long tool contexts, so the
runtime repeats valid and invalid action examples in the live loop.

Workspace write actions are intentionally bounded by
`DEEPDIVE_WORKSPACE_WRITE_CHAR_BUDGET`. Long notes should be split across
multiple append actions so the model returns one complete JSON object instead
of a response that is cut off mid-payload. Paper notes should be compact: one
paper per append action, with IDs/titles/years/source/relevance notes rather
than pasted abstracts. This is not a cap on the final artifact detail; agents
should keep appending chunks until the markdown files are substantively filled.

## Official References

- Google Gemini OpenAI compatibility:
  `https://ai.google.dev/gemini-api/docs/openai`
- Gemini function calling:
  `https://ai.google.dev/gemini-api/docs/function-calling`
- Gemma function calling behavior:
  `https://ai.google.dev/gemma/docs/capabilities/function-calling`
- Gemini model capability table:
  `https://ai.google.dev/gemini-api/docs/models`
