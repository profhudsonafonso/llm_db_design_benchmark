# Scripts

This folder contains the scripts used to execute and reproduce the benchmark pipeline.

Each script must follow the same reproducibility rule:

- receive inputs through command-line arguments;
- write all outputs to a dedicated output folder;
- save intermediate artifacts when useful;
- save a manifest file with execution metadata;
- avoid overwriting previous runs unless explicitly requested.

## Current Scripts

| Script | Purpose |
|---|---|
| `normalize_output.py` | Normalizes raw LLM-generated relational JSON outputs before evaluation. |
| `validation_report.py` | Provides utilities for creating deterministic validation reports for C4. |

## `normalize_output.py`

### Goal

Normalize a raw LLM output into auditable files that can be used by the evaluator.

The script handles:

- raw JSON outputs;
- JSON wrapped in Markdown code fences;
- JSON surrounded by explanatory text;
- name normalization;
- table flattening;
- column flattening;
- primary key flattening;
- foreign key flattening;
- manifest generation.

### Inputs

Required inputs:

- `--input`: path to the raw LLM output file;
- `--dataset`: dataset name;
- `--model`: model name;
- `--condition`: experimental condition, such as C1, C2, C3, or C4.

Optional inputs:

- `--output-dir`: base output folder;
- `--run-id`: custom run identifier;
- `--prompt-file`: prompt template used;
- `--input-eer-file`: prompt-ready EER input file;
- `--notes`: execution notes.

### Example

Command:

`python scripts/normalize_output.py --input llm_outputs/chinook/gpt_c1_raw.txt --dataset chinook --model gpt --condition C1`

### Outputs

By default, outputs are saved under:

`results/normalization_runs/<run_id>/`

Expected output files:

- `raw_input.txt`;
- `extracted_json.json`;
- `normalized_schema.json`;
- `normalized_tables.csv`;
- `normalized_columns.csv`;
- `normalized_primary_keys.csv`;
- `normalized_foreign_keys.csv`;
- `normalization_warnings.json`;
- `normalization_manifest.json`.

### Processing Steps

The script performs the following steps:

1. reads the raw LLM output;
2. removes Markdown code fences if present;
3. extracts the first valid JSON object;
4. parses the JSON;
5. normalizes schema element names;
6. flattens tables, columns, primary keys, and foreign keys;
7. saves all outputs and warnings;
8. saves an execution manifest.

### Reproducibility

The manifest records:

- run id;
- timestamp;
- input file;
- input SHA256 hash;
- dataset;
- model;
- condition;
- prompt file;
- EER input file;
- generated files;
- normalization summary;
- warning count.

## `evaluate_schema.py`

### Goal

Evaluate an LLM-generated relational schema against the expert logical relational gold standard.

This script compares the generated schema with the gold schema using:

- strict matching;
- similarity and structure-aware matching;
- component-level Precision, Recall, and F1;
- preferred and alternative valid mapping classification;
- weighted structural Manhattan distance.

### Inputs

Required inputs:

- `--gold`: path to `logical_relational_gold.json`;
- `--prediction`: path to the generated schema JSON, preferably `normalized_schema.json`;
- `--dataset`: dataset name;
- `--model`: model name;
- `--condition`: experimental condition, such as C1, C2, C3, or C4.

Optional inputs:

- `--output-dir`: base output folder;
- `--run-id`: custom run identifier;
- `--normalization-run-dir`: path to the normalization run folder;
- `--notes`: execution notes.

### Example

Command:

`python scripts/evaluate_schema.py --gold datasets/toy_example/ground_truth/logical_relational_gold.json --prediction results/normalization_runs/<normalization_run_id>/normalized_schema.json --dataset toy_example --model gpt --condition C1`

### Outputs

By default, outputs are saved under:

`results/evaluation_runs/<run_id>/`

Expected output files:

- `evaluation_metrics.json`;
- `strict_component_results.json`;
- `matched_component_results.json`;
- `table_mapping_evidence.json`;
- `mapping_alternative_report.json`;
- `component_metrics.csv`;
- `evaluation_errors.csv`;
- `evaluation_errors.json`;
- `evaluation_manifest.json`.

### Processing Steps

The script performs the following steps:

1. loads the expert gold schema;
2. loads the generated schema;
3. extracts comparable schema units;
4. computes strict matching metrics;
5. computes similarity and structure-aware matching metrics;
6. classifies preferred and acceptable alternative mappings;
7. computes weighted structural Manhattan distance;
8. saves metrics, errors, mapping evidence, and manifest.

### Reproducibility

The manifest records:

- run id;
- timestamp;
- input files;
- input file hashes;
- dataset;
- model;
- condition;
- normalization run directory;
- generated files.

The evaluator reports both strict and matched weighted structural Manhattan distances.

This makes it possible to measure how much apparent structural error is removed by similarity and structure-aware matching.


The evaluator also reports an `alternative_aware` mode.

This mode treats expert-documented acceptable non-preferred mappings as correct. It is useful for cases where the LLM chooses a valid design that differs from the preferred gold schema.

Additional output file:

- `alternative_aware_component_results.json`

Additional metrics:

- alternative-aware global F1;
- alternative-aware normalized weighted structural distance;
- distance reduction from alternatives.

## `generate_prompt_input.py`

### Goal

Generate a prompt-ready Markdown input from an expert-defined `conceptual_eer.yaml` file.

This script converts the structured EER-YAML representation into a readable textual EER description that can be inserted into the prompt templates.

### Inputs

Required inputs:

- `--conceptual-yaml`: path to the expert-defined `conceptual_eer.yaml`;
- `--dataset`: dataset name.

Optional inputs:

- `--output-dir`: base output folder;
- `--run-id`: custom run identifier;
- `--publish-to`: optional path to copy the generated `eer_input_text.md`;
- `--notes`: execution notes.

### Example

Command:

`python scripts/generate_prompt_input.py --conceptual-yaml datasets/toy_example/ground_truth/conceptual_eer.yaml --dataset toy_example --run-id toy_example_prompt_input --publish-to datasets/toy_example/prompt_inputs/eer_input_text.md`

### Outputs

By default, outputs are saved under:

`results/prompt_input_runs/<run_id>/`

Expected output files:

- `eer_input_text.md`;
- `source_conceptual_eer.yaml`;
- `prompt_input_manifest.json`.

If `--publish-to` is used, a copy of `eer_input_text.md` is also written to the selected dataset prompt input folder.

### Processing Steps

The script performs the following steps:

1. reads the expert `conceptual_eer.yaml`;
2. extracts metadata, entities, attributes, identifiers, relationships, cardinalities, specializations, constraints, and expert notes;
3. renders a Markdown textual EER input;
4. saves the generated prompt input;
5. saves a snapshot of the source YAML;
6. saves a manifest with input hash, dataset, output directory, and schema counts.

### Reproducibility

The manifest records:

- run id;
- timestamp;
- source conceptual YAML path;
- source YAML SHA256 hash;
- dataset;
- generated files;
- optional published prompt input path;
- schema counts.

## `run_llm_experiments.py`

### Goal

Run one LLM experiment by combining:

- a prompt template;
- a prompt-ready EER input file;
- the required logical relational JSON output format;
- a configured model/provider.

The script supports:

- `ollama`;
- `openai`;
- `gemini`;
- `anthropic`;
- `manual`;
- `dry-run`.

### Inputs

Required inputs:

- `--dataset`: dataset name;
- `--condition`: experimental condition, such as C1, C2, C3, or C4;
- `--model-key`: key from `configs/models.yaml`;
- `--prompt-file`: prompt template file;
- `--eer-input-file`: prompt-ready EER Markdown file.

Optional inputs:

- `--models-config`: model configuration YAML;
- `--provider-settings`: provider settings YAML;
- `--output-format-file`: required output JSON format;
- `--previous-output-file`: previous relational JSON for C4;
- `--validation-report-file`: validation report for C4;
- `--output-dir`: base run output folder;
- `--publish-dir`: base folder for published raw outputs;
- `--run-id`: custom run identifier;
- `--dry-run`: render prompt without calling a provider;
- `--notes`: execution notes.

### Example: Dry Run

`python scripts/run_llm_experiments.py --dataset toy_example --condition C1 --model-key manual_placeholder --prompt-file prompts/prompt_1_basic.txt --eer-input-file datasets/toy_example/prompt_inputs/eer_input_text.md --dry-run --run-id toy_example_manual_c1_dryrun`

### Outputs

By default, outputs are saved under:

`results/llm_runs/<run_id>/`

Expected files:

- `rendered_prompt.txt`;
- `response_text.txt`;
- `raw_response.json`;
- `llm_run_manifest.json`.

If the provider returns text, the script also publishes a copy under:

`llm_outputs/<dataset>/<run_id>_raw.txt`

### Reproducibility

The manifest records:

- dataset;
- condition;
- model key;
- provider;
- model name;
- model configuration;
- prompt file and hash;
- EER input file and hash;
- output format file and hash;
- latency;
- status;
- generated files.

### Usage and Cost Tracking

`run_llm_experiments.py` writes a standardized usage and cost file:

- `usage_and_cost.json`

This file may include:

- input tokens;
- output tokens;
- total tokens;
- cached input tokens;
- reasoning tokens;
- latency in seconds;
- tokens per second;
- estimated cost in USD;
- raw provider usage metadata;
- Ollama duration metrics when available.

Cost estimation uses:

- `configs/model_pricing.yaml`

Prices in `configs/model_pricing.yaml` must be checked and updated before final experiments.

For remote APIs, cost is estimated from token usage and configured prices.

For Ollama/local models, financial cost is normally zero, but runtime metrics such as duration and tokens per second can be recorded.

## `run_llm_batch.py`

### Goal

Run multiple LLM experiments from an experiment matrix.

This script expands combinations of:

- datasets;
- prompt conditions;
- model keys;

and calls `scripts/run_llm_experiments.py` for each run.

### Inputs

Required or default inputs:

- `--matrix`: experiment matrix YAML, default `configs/experiment_matrix.yaml`;
- `--models-config`: model configuration YAML;
- `--provider-settings`: provider settings YAML;
- `--pricing-config`: pricing configuration YAML.

Optional filters:

- `--only-dataset`;
- `--only-condition`;
- `--only-model`;
- `--max-runs`.

Execution control:

- `--dry-run`: force all runs to dry-run mode;
- `--execute`: execute provider calls instead of matrix dry-run defaults.

### Example

Dry-run all enabled toy example combinations:

`python scripts/run_llm_batch.py --matrix configs/experiment_matrix.yaml --batch-id toy_batch_dryrun --dry-run`

Run only C1:

`python scripts/run_llm_batch.py --matrix configs/experiment_matrix.yaml --batch-id toy_c1_dryrun --only-condition C1 --dry-run`

### Outputs

By default, outputs are saved under:

`results/batch_runs/<batch_id>/`

Expected files:

- `batch_manifest.json`;
- `batch_runs.csv`;
- `logs/<run_id>.stdout.txt`;
- `logs/<run_id>.stderr.txt`.

Each individual LLM run also writes its own folder under:

`results/llm_runs/<run_id>/`

### Reproducibility

The batch manifest records:

- matrix file and hash;
- models config path;
- provider settings path;
- pricing config path;
- filters;
- number of runs;
- number of successes, errors, and skipped runs.

## `aggregate_results.py`

### Goal

Aggregate result files from LLM runs, normalization runs, and evaluation runs into analysis-ready tables.

### Inputs

Default input folders:

- `results/llm_runs/`
- `results/normalization_runs/`
- `results/evaluation_runs/`
- `datasets/`

### Example

Command:

`python scripts/aggregate_results.py --run-id toy_aggregate_test --notes "Toy aggregation test"`

### Outputs

Outputs are saved under:

`results/aggregate_runs/<run_id>/`

Expected output files:

- `aggregate_run_summary.csv`;
- `aggregate_llm_runs.csv`;
- `aggregate_normalization_summary.csv`;
- `aggregate_component_metrics.csv`;
- `aggregate_evaluation_errors_detail.csv`;
- `aggregate_error_counts.csv`;
- `aggregate_cost_quality.csv`;
- `aggregate_by_model.csv`;
- `aggregate_by_condition.csv`;
- `aggregate_by_dataset_complexity.csv`;
- `aggregate_by_dataset_condition.csv`;
- `aggregate_by_model_condition.csv`;
- `aggregate_manifest.json`.

### Main Analysis Table

The main table is:

`aggregate_run_summary.csv`

It contains one row per evaluated run and includes:

- dataset;
- condition;
- provider;
- model;
- strict F1;
- matched F1;
- alternative-aware F1;
- strict/matched/alternative-aware distances;
- mapping alternative metrics;
- token usage;
- latency;
- estimated cost.

### Reproducibility

The aggregation manifest records:

- input directories;
- number of LLM runs;
- number of normalization runs;
- number of evaluation runs;
- number of generated rows;
- generated files.

## `run_evaluation_batch.py`

### Goal

Run normalization and evaluation in batch for LLM outputs.

The script reads LLM run manifests from:

`results/llm_runs/`

Then it calls:

1. `scripts/normalize_output.py`
2. `scripts/evaluate_schema.py`

### Inputs

Default input folder:

- `results/llm_runs/`

Default gold path pattern:

- `datasets/{dataset}/ground_truth/logical_relational_gold.json`

Optional filters:

- `--only-dataset`;
- `--only-condition`;
- `--only-model`;
- `--max-runs`.

### Example

`python scripts/run_evaluation_batch.py --batch-id toy_eval_batch --include-dry-run --only-dataset toy_example --notes "Toy evaluation batch test"`

### Outputs

Outputs are saved under:

`results/evaluation_batch_runs/<batch_id>/`

Expected files:

- `evaluation_batch_manifest.json`;
- `evaluation_batch_runs.csv`;
- `logs/*.stdout.txt`;
- `logs/*.stderr.txt`.

The script also creates normalization runs under:

`results/normalization_runs/<run_id>/`

and evaluation runs under:

`results/evaluation_runs/<run_id>/`.

### Notes

Dry-run outputs are skipped by default.

Use `--include-dry-run` only when a dry-run folder contains a non-empty `response_text.txt`.

