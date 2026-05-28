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

## `experiment_matrix.yaml`

This file defines the batch execution matrix.

It specifies:

- enabled datasets;
- prompt input files;
- enabled conditions;
- prompt files;
- model keys;
- default output locations;
- dry-run behavior.

The batch runner reads this file through:

`python scripts/run_llm_batch.py --matrix configs/experiment_matrix.yaml`

For now, only `toy_example` is enabled by default. Real datasets should remain disabled until their expert ground truths and prompt inputs are finalized.

## Provisional Final Model Set

The provisional model set is stored in:

`configs/models.yaml`

The current groups are:

| Group | Examples | Purpose |
|---|---|---|
| OpenAI | `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini` | Strong and efficient commercial baselines. |
| Gemini | `gemini-3.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` | Google commercial model family. |
| Anthropic | `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5` | Claude strong, balanced, and efficient models. |
| Ollama | local placeholders such as `llama3.1:8b`, `llama3.2`, `mistral`, `qwen2.5` | Local/open-weight execution once server access is available. |
| Manual | `manual` | Debugging and manually pasted outputs. |

All paid and Ollama models are disabled by default.

Before final experiments:

1. confirm API access;
2. confirm model IDs;
3. update pricing in `configs/model_pricing.yaml`;
4. enable selected models;
5. update `configs/experiment_matrix.yaml` model keys.
