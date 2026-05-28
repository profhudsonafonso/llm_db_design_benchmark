# Reproduction Pipeline

This document explains how to reproduce the LLM Database Design Benchmark pipeline.

The pipeline evaluates Large Language Models on conceptual-to-logical database design tasks.

It starts from expert-defined EER ground truths and ends with aggregate result tables used for analysis.

## 1. Pipeline Overview

The full pipeline is:

1. review expert ground truth files;
2. generate prompt-ready EER input;
3. configure models and providers;
4. run LLM experiments;
5. normalize LLM outputs;
6. evaluate generated schemas;
7. aggregate results;
8. analyze quality, errors, cost, and prompt effects.

Main workflow:

- `conceptual_eer.yaml`
- `generate_prompt_input.py`
- `eer_input_text.md`
- `run_llm_batch.py`
- `run_llm_experiments.py`
- raw LLM output
- `normalize_output.py`
- `evaluate_schema.py`
- `aggregate_results.py`
- aggregate result tables

## 2. Repository Setup

Clone the repository:

- `git clone git@github.com:profhudsonafonso/llm_db_design_benchmark.git`

Enter the repository:

- `cd llm-db-design-benchmark`

Install dependencies:

- `pip install -r requirements.txt`

Check Python scripts compile:

- `python -m py_compile scripts/generate_prompt_input.py`
- `python -m py_compile scripts/run_llm_experiments.py`
- `python -m py_compile scripts/run_llm_batch.py`
- `python -m py_compile scripts/normalize_output.py`
- `python -m py_compile scripts/evaluate_schema.py`
- `python -m py_compile scripts/aggregate_results.py`

## 3. Ground Truth Files

Each dataset must contain:

- `datasets/<dataset>/ground_truth/conceptual_eer.yaml`
- `datasets/<dataset>/ground_truth/logical_relational_gold.json`

Before running experiments, review each dataset using:

- `docs/ground_truth_review_checklist.md`

A dataset should only be enabled in the experiment matrix after the review decision is:

- `approved`; or
- `approved_with_minor_notes`.

## 4. Generate Prompt-Ready EER Input

Generate a prompt input from the conceptual EER file.

Example for the toy dataset:

- `python scripts/generate_prompt_input.py --conceptual-yaml datasets/toy_example/ground_truth/conceptual_eer.yaml --dataset toy_example --run-id toy_example_prompt_input --publish-to datasets/toy_example/prompt_inputs/eer_input_text.md --notes "Toy example prompt input generation"`

Expected outputs:

- `results/prompt_input_runs/toy_example_prompt_input/eer_input_text.md`
- `results/prompt_input_runs/toy_example_prompt_input/source_conceptual_eer.yaml`
- `results/prompt_input_runs/toy_example_prompt_input/prompt_input_manifest.json`
- `datasets/toy_example/prompt_inputs/eer_input_text.md`

For a real dataset, replace `toy_example` with the dataset name.

Example:

- `chinook`
- `imdb`
- `yelp`

## 5. Configure Models and Providers

Model definitions are stored in:

- `configs/models.yaml`

Provider settings are stored locally in:

- `configs/provider_settings.yaml`

Do not commit `configs/provider_settings.yaml`.

Create it from:

- `configs/provider_settings.example.yaml`

Remote API keys should be stored as environment variables, for example:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`

Ollama local models depend on the project server.

Check available Ollama models with:

- `ollama list`

Then update the Ollama model names in:

- `configs/models.yaml`

If a provider is unavailable, keep its models with:

- `enabled: false`

## 6. Configure the Experiment Matrix

The batch execution matrix is:

- `configs/experiment_matrix.yaml`

This file controls:

- enabled datasets;
- prompt input files;
- enabled conditions;
- prompt templates;
- model keys;
- dry-run behavior;
- output folders.

For initial testing, keep only `toy_example` enabled.

For final experiments, enable the reviewed datasets:

- `chinook`
- `imdb`
- `yelp`

The conditions are:

| Condition | Meaning |
|---|---|
| C1 | Basic generation |
| C2 | Rule-augmented generation |
| C3 | Self-check generation |
| C4 | Validation-guided repair |

C4 should remain disabled until previous outputs and validation reports are available.

## 7. Run LLM Experiments

### 7.1 Dry-Run Test

Before calling any real model, test the batch runner in dry-run mode.

Command:

- `python scripts/run_llm_batch.py --matrix configs/experiment_matrix.yaml --batch-id toy_batch_dryrun --dry-run --notes "Toy batch dry-run test"`

Expected batch outputs:

- `results/batch_runs/toy_batch_dryrun/batch_manifest.json`
- `results/batch_runs/toy_batch_dryrun/batch_runs.csv`
- `results/batch_runs/toy_batch_dryrun/logs/`

Expected LLM run outputs:

- `results/llm_runs/<run_id>/rendered_prompt.txt`
- `results/llm_runs/<run_id>/response_text.txt`
- `results/llm_runs/<run_id>/raw_response.json`
- `results/llm_runs/<run_id>/usage_and_cost.json`
- `results/llm_runs/<run_id>/llm_run_manifest.json`

### 7.2 Execute Real Provider Calls

After models and API keys are configured, run without `--dry-run`.

Use:

- `python scripts/run_llm_batch.py --matrix configs/experiment_matrix.yaml --batch-id real_batch_c1_c2_c3 --execute --notes "Real LLM execution"`

The script will call:

- `scripts/run_llm_experiments.py`

for each dataset, condition, and model combination.

## 8. Normalize LLM Outputs

Each LLM output must be normalized before evaluation.

Example command:

- `python scripts/normalize_output.py --input llm_outputs/toy_example/gpt_c1_raw.txt --dataset toy_example --model gpt --condition C1 --run-id toy_gpt_c1_raw_normalization --prompt-file prompts/prompt_1_basic.txt --input-eer-file datasets/toy_example/prompt_inputs/eer_input_text.md --notes "Toy normalization"`

Expected outputs:

- `raw_input.txt`
- `extracted_json.json`
- `normalized_schema.json`
- `normalized_tables.csv`
- `normalized_columns.csv`
- `normalized_primary_keys.csv`
- `normalized_foreign_keys.csv`
- `normalization_warnings.json`
- `normalization_manifest.json`

Output folder:

- `results/normalization_runs/<run_id>/`

## 9. Evaluate Generated Schemas

Evaluate each normalized schema against the expert logical gold.

Example command:

- `python scripts/evaluate_schema.py --gold datasets/toy_example/ground_truth/logical_relational_gold.json --prediction results/normalization_runs/toy_gpt_c1_raw_normalization/normalized_schema.json --dataset toy_example --model gpt --condition C1 --run-id toy_gpt_c1_raw_evaluation --normalization-run-dir results/normalization_runs/toy_gpt_c1_raw_normalization --notes "Toy evaluation"`

Expected outputs:

- `evaluation_metrics.json`
- `strict_component_results.json`
- `matched_component_results.json`
- `alternative_aware_component_results.json`
- `table_mapping_evidence.json`
- `mapping_alternative_report.json`
- `component_metrics.csv`
- `evaluation_errors.csv`
- `evaluation_errors.json`
- `evaluation_manifest.json`

Output folder:

- `results/evaluation_runs/<run_id>/`

## 10. Evaluation Modes

The evaluator reports three modes.

| Mode | Meaning |
|---|---|
| strict | Compares against the preferred gold schema using normalized names. |
| matched | Uses similarity and structural compatibility. |
| alternative_aware | Treats expert-documented acceptable alternatives as valid. |

Main metrics:

- `strict_f1`
- `matched_f1`
- `alternative_aware_f1`
- `strict_distance`
- `matched_distance`
- `alternative_aware_distance`
- `preferred_mapping_accuracy`
- `valid_mapping_accuracy`
- `invalid_mapping_rate`

## 11. Aggregate Results

After LLM runs, normalization, and evaluation, aggregate all results.

Command:

- `python scripts/aggregate_results.py --run-id final_aggregate --notes "Final aggregation"`

Expected output folder:

- `results/aggregate_runs/final_aggregate/`

Expected files:

- `aggregate_run_summary.csv`
- `aggregate_llm_runs.csv`
- `aggregate_normalization_summary.csv`
- `aggregate_component_metrics.csv`
- `aggregate_evaluation_errors_detail.csv`
- `aggregate_error_counts.csv`
- `aggregate_cost_quality.csv`
- `aggregate_by_model.csv`
- `aggregate_by_condition.csv`
- `aggregate_by_dataset_complexity.csv`
- `aggregate_by_dataset_condition.csv`
- `aggregate_by_model_condition.csv`
- `aggregate_manifest.json`

The main file for analysis is:

- `aggregate_run_summary.csv`

## 12. Main Analysis Tables

### 12.1 `aggregate_run_summary.csv`

One row per evaluated run.

Used to analyze:

- model quality;
- prompt condition effects;
- dataset complexity effects;
- strict vs. matched vs. alternative-aware gaps;
- cost and latency.

### 12.2 `aggregate_component_metrics.csv`

One row per component and evaluation mode.

Used to analyze:

- table correctness;
- attribute correctness;
- primary-key correctness;
- foreign-key correctness;
- relationship-table correctness;
- specialization mapping correctness.

### 12.3 `aggregate_cost_quality.csv`

Combines quality and cost.

Used to analyze:

- cost per run;
- cost per F1 point;
- latency;
- tokens per second;
- cost-quality trade-off.

### 12.4 `aggregate_by_model.csv`

Used to compare models.

### 12.5 `aggregate_by_condition.csv`

Used to compare C1, C2, C3, and C4.

### 12.6 `aggregate_by_dataset_complexity.csv`

Used to compare low, medium, and high complexity datasets.

## 13. Recommended Final Execution Order

For each real dataset:

1. review ground truth files;
2. generate `eer_input_text.md`;
3. enable the dataset in `configs/experiment_matrix.yaml`;
4. configure final models in `configs/models.yaml`;
5. run C1, C2, and C3;
6. normalize all outputs;
7. evaluate all outputs;
8. generate validation reports for C4;
9. run C4 repair;
10. normalize C4 outputs;
11. evaluate C4 outputs;
12. aggregate results;
13. analyze the aggregate tables.

## 14. Toy Example Validation

The toy example validates the pipeline before real experiments.

Toy files:

- `datasets/toy_example/`
- `llm_outputs/toy_example/`
- `paper_material/text_blocks/toy_pipeline_validation.md`

The toy example tests:

- naming mismatch;
- valid alternative mapping;
- invalid mapping;
- strict evaluation;
- matched evaluation;
- alternative-aware evaluation;
- strict/matched/alternative-aware Manhattan distance.

## 15. Reproducibility Rules

Every script must produce:

- a dedicated output folder;
- main outputs;
- intermediate artifacts when useful;
- warnings or error reports;
- a manifest file;
- input paths;
- input hashes;
- execution parameters.

Do not overwrite final experiment outputs unless explicitly intended.

Use stable run IDs for important reproducibility tests.

## 16. What to Commit

Commit:

- scripts;
- documentation;
- templates;
- toy example files;
- small toy outputs;
- aggregate test outputs when useful.

Do not commit:

- API keys;
- `configs/provider_settings.yaml`;
- large raw datasets;
- large generated files;
- private credentials;
- temporary debugging outputs.

## 17. Troubleshooting

### Problem: GitHub rejects large files

Remove large files from the repository and update `.gitignore`.

### Problem: LLM output has Markdown around JSON

Use `scripts/normalize_output.py`. It attempts to extract the first JSON object.

### Problem: Provider API key is missing

Check environment variables and `configs/provider_settings.yaml`.

### Problem: Ollama is unavailable

Keep Ollama models disabled and proceed with remote APIs. Local models can be added later.

### Problem: Evaluation gives low strict F1 but high matched F1

This often indicates naming mismatch rather than structural error.

### Problem: Matched F1 is lower than alternative-aware F1

This often indicates that the LLM selected a documented valid alternative mapping.

### Problem: Alternative-aware distance remains high

This indicates remaining structural errors that are not explained by naming mismatch or valid alternatives.

## 18. Final Outputs for the Paper

The main final outputs for paper analysis are:

- `aggregate_run_summary.csv`
- `aggregate_component_metrics.csv`
- `aggregate_error_counts.csv`
- `aggregate_cost_quality.csv`
- `aggregate_by_model.csv`
- `aggregate_by_condition.csv`
- `aggregate_by_dataset_complexity.csv`

These files support the experimental analysis and tables in the paper.
