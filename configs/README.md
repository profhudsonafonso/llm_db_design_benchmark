# Configs

This folder stores configuration files for model execution.

## Files

| File | Purpose |
|---|---|
| `models.yaml` | Defines model keys, providers, model names, temperatures, token limits, and local/remote settings. |
| `provider_settings.example.yaml` | Example provider configuration. Copy it to `provider_settings.yaml` for local use. |

## Private Configuration

Create a local file:

`configs/provider_settings.yaml`

This file should contain local provider settings and environment variable names for API keys.

Do not commit `configs/provider_settings.yaml`.

## API Keys

API keys should be stored as environment variables, for example:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`

The benchmark scripts read the environment variable names from `provider_settings.yaml`.

## Ollama

Ollama models are called through a local HTTP endpoint.

Default:

`http://localhost:11434`

The model names in `models.yaml` must match the names returned by:

`ollama list`

If Ollama is not available yet, keep the Ollama model entries with `enabled: false`.

## Reproducibility

Model names, provider names, temperature, token limits, and seed values are recorded in each LLM run manifest.
