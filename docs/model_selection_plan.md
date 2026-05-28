# Model Selection Plan

This document defines the model selection strategy for the LLM Database Design Benchmark.

The benchmark evaluates how different LLM families perform on conceptual-to-logical database design tasks using textual EER input.

## 1. Goal

The goal is not to test a single model, but to compare representative models across different access and deployment scenarios.

The model selection should cover:

- strong commercial models;
- faster or cheaper commercial models;
- local open-weight models through Ollama;
- optional manual outputs when needed for debugging or fallback.

## 2. Model Selection Principles

Models are selected according to the following criteria:

1. Provider diversity.
2. Capability diversity.
3. Cost diversity.
4. Local vs. remote execution.
5. Reproducibility.
6. Availability at experiment time.
7. Ability to process long textual EER inputs.
8. Ability to return structured JSON.

## 3. Model Groups

The benchmark separates models into four groups.

| Group | Purpose |
|---|---|
| Commercial strong models | Measure high-end LLM performance. |
| Commercial efficient models | Measure lower-cost or faster API alternatives. |
| Local Ollama models | Measure offline/local execution feasibility. |
| Manual/debug provider | Support dry-run, debugging, or manually pasted outputs. |

## 4. Candidate Providers

The planned providers are:

| Provider | Execution type | Status |
|---|---|---|
| OpenAI | Remote API | Planned |
| Gemini | Remote API | Planned |
| Anthropic/Claude | Remote API | Planned |
| Ollama | Local HTTP API | Pending server access |
| Manual | Local file/manual output | Available |

## 5. Candidate Model Roles

The exact model IDs may change depending on API availability at execution time.

The benchmark should include at least one model per role when possible.

| Role | Example family | Purpose |
|---|---|---|
| Strong reasoning model | GPT / Claude / Gemini Pro | Best expected quality |
| Efficient model | mini / flash / haiku style model | Lower cost and latency |
| Local medium model | Llama / Qwen / Mistral through Ollama | Local reproducibility |
| Local coding/structured model | Code-oriented or instruction-tuned Ollama model | JSON/schema generation ability |

## 6. Initial Candidate Model Set

The final model names must be confirmed immediately before running the experiments.

### 6.1 OpenAI Candidates

Candidate roles:

- OpenAI strong model;
- OpenAI efficient model;
- optional OpenAI low-cost model.

The exact configured names should be stored in:

- `configs/models.yaml`

### 6.2 Gemini Candidates

Candidate roles:

- Gemini Pro or equivalent strong model;
- Gemini Flash or equivalent efficient model.

The exact configured names should be stored in:

- `configs/models.yaml`

### 6.3 Claude Candidates

Candidate roles:

- Claude Sonnet or Opus as strong model;
- Claude Haiku as efficient model.

The exact configured names should be stored in:

- `configs/models.yaml`

### 6.4 Ollama Candidates

Ollama candidates depend on the models available on the project server.

Before running local experiments, execute:

`ollama list`

Then update:

- `configs/models.yaml`

Possible local families include:

- Llama;
- Qwen;
- Mistral;
- CodeLlama or code-oriented models;
- other instruction-tuned local models available in the environment.

If Ollama is not available by the deadline, local models will be marked as optional.

## 7. Experimental Conditions per Model

Each selected model should run the following conditions:

| Condition | Required? |
|---|---|
| C1 Basic generation | yes |
| C2 Rule-augmented generation | yes |
| C3 Self-check generation | yes |
| C4 Validation-guided repair | yes, after validation report is available |

If the number of models is too high, C4 may be run only on selected representative models.

## 8. Cost Measurement Strategy

The benchmark records both quality metrics and execution cost metrics.

### 8.1 Financial Cost for Remote APIs

For paid APIs, financial cost is estimated from token usage and model pricing.

General formula:

`estimated_cost_usd = input_tokens / 1_000_000 * input_price_per_1m + output_tokens / 1_000_000 * output_price_per_1m`

If cached tokens are reported, the formula may include:

`cached_input_tokens / 1_000_000 * cached_input_price_per_1m`

If thinking or reasoning tokens are reported separately, they must be recorded and included according to the provider pricing rules.

### 8.2 Computational Cost for Remote APIs

For remote APIs, the benchmark cannot observe the provider's internal GPU, CPU, RAM, energy, or carbon cost.

The benchmark records observable proxies:

- input tokens;
- output tokens;
- total tokens;
- latency in seconds;
- tokens per second;
- estimated financial cost.

### 8.3 Computational Cost for Ollama

For Ollama/local models, the benchmark can record more detailed local metrics.

Basic metrics from Ollama response:

- total duration;
- load duration;
- prompt evaluation count;
- prompt evaluation duration;
- generation token count;
- generation duration;
- tokens per second.

Optional local monitoring may later include:

- CPU utilization;
- RAM usage;
- GPU utilization;
- GPU memory usage;
- power draw;
- estimated energy consumption.

### 8.4 Cost Normalization

The benchmark may report:

- cost per run;
- cost per dataset;
- cost per condition;
- cost per valid schema;
- cost per F1 point;
- latency per run;
- tokens per schema;
- tokens per correct mapping decision.

## 9. Reproducibility Requirements

For each LLM execution, the run manifest must record:

- provider;
- model name;
- model key;
- model configuration;
- temperature;
- max tokens;
- seed, when available;
- dataset;
- condition;
- prompt file;
- EER input file;
- output format file;
- start/end time or latency;
- raw provider response;
- token usage, when available;
- estimated cost, when available;
- error status, if any.

## 10. Model Selection for the Paper

The paper should avoid claiming that one model is universally best.

The analysis should focus on:

- how performance changes by model family;
- how performance changes by prompt condition;
- whether rule-augmented prompting improves results;
- whether self-check improves results;
- whether validation-guided repair improves results;
- the relationship between accuracy, latency, and estimated cost;
- whether local models are competitive enough for schema design tasks.

## 11. Fallback Plan

If some provider is unavailable:

- keep the model entry disabled in `configs/models.yaml`;
- record the reason in the experiment notes;
- run the remaining providers;
- avoid delaying the entire benchmark because of one unavailable provider.

If Ollama is unavailable:

- proceed with remote APIs;
- keep local models as optional or future work;
- run Ollama later if access is restored.

## 12. Current Status

The model execution script is implemented:

- `scripts/run_llm_experiments.py`

The model configuration file exists:

- `configs/models.yaml`

The provider settings example exists:

- `configs/provider_settings.example.yaml`

Ollama access is currently pending support from the project server.

## 13. Implementation of Usage and Cost Tracking

The LLM execution runner stores usage and cost metadata for each run.

Output file:

- `results/llm_runs/<run_id>/usage_and_cost.json`

The same information is also embedded in:

- `results/llm_runs/<run_id>/llm_run_manifest.json`

The cost estimation uses:

- `configs/model_pricing.yaml`

This file stores prices per one million tokens. Prices should be updated from official provider pricing pages immediately before running final experiments.

The runner attempts to extract token usage from each provider response.

For remote providers, the benchmark records observable cost proxies:

- input tokens;
- output tokens;
- total tokens;
- cached input tokens, when available;
- reasoning tokens, when available;
- latency;
- estimated financial cost.

For Ollama/local models, the benchmark records:

- prompt evaluation count;
- generation token count;
- total duration;
- prompt evaluation duration;
- generation duration;
- tokens per second.
