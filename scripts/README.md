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
