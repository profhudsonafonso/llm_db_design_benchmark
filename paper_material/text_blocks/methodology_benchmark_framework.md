# Methodology: Benchmark Framework for LLM-Based Conceptual-to-Logical Database Design

This document describes the experimental methodology used to evaluate Large Language Models on conceptual-to-logical database design tasks.

The benchmark evaluates whether LLMs can transform a textual EER conceptual schema into a logical relational schema while preserving structural and semantic modeling constraints.

## 1. Motivation

Conceptual-to-logical database design is not a simple text generation task.

A correct logical schema must preserve:

- entities;
- attributes;
- identifiers;
- weak entities;
- relationships;
- cardinalities;
- participation constraints;
- relationship attributes;
- specialization/generalization structures;
- primary keys;
- foreign keys;
- valid mapping decisions.

LLMs may generate plausible schemas, but they may also:

- omit entities or attributes;
- invent unsupported elements;
- place foreign keys on the wrong side;
- ignore many-to-many relationship tables;
- fail to preserve relationship attributes;
- mishandle weak entities;
- mishandle specialization/generalization;
- produce invalid JSON;
- produce valid designs using different names;
- produce valid alternative mappings different from the expert preferred schema.

For this reason, the benchmark evaluates LLM outputs using a structured, reproducible, and alternative-aware methodology.

## 2. Overview of the Pipeline

The benchmark pipeline has the following stages:

1. expert conceptual ground truth creation;
2. expert logical relational gold creation;
3. prompt-ready EER input generation;
4. LLM schema generation under different prompt conditions;
5. output normalization;
6. schema evaluation;
7. result aggregation;
8. analysis by model, prompt condition, dataset complexity, error type, and cost.

The full workflow is:

- `conceptual_eer.yaml`
- `generate_prompt_input.py`
- `eer_input_text.md`
- `run_llm_batch.py` or `run_llm_experiments.py`
- raw LLM relational JSON output
- `normalize_output.py`
- `normalized_schema.json`
- `evaluate_schema.py`
- strict, matched, and alternative-aware metrics
- `aggregate_results.py`
- analysis-ready aggregate tables

## 3. Ground Truth Design

Each dataset contains two expert-defined ground truth files:

- `datasets/<dataset>/ground_truth/conceptual_eer.yaml`
- `datasets/<dataset>/ground_truth/logical_relational_gold.json`

### 3.1 Conceptual EER Ground Truth

The file `conceptual_eer.yaml` describes the conceptual schema.

It includes:

- entities;
- attributes;
- identifiers;
- weak entities;
- relationships;
- relationship attributes;
- cardinalities;
- participation constraints;
- specialization/generalization;
- global constraints;
- expert assumptions;
- ambiguities and exclusions.

This file is the source used to generate the textual input given to the LLM.

### 3.2 Logical Relational Gold Standard

The file `logical_relational_gold.json` describes the expected logical relational schema.

It includes:

- tables;
- columns;
- primary keys;
- foreign keys;
- candidate keys;
- unique constraints;
- relationship tables;
- specialization mapping decisions;
- mapping decisions;
- evaluation units;
- alternative valid mappings.

This file is not shown to the LLM. It is used only for evaluation.

## 4. Preferred and Alternative Valid Mappings

Conceptual-to-logical design may have more than one valid implementation.

For example, a one-to-one relationship may be mapped as:

- a foreign key in one of the participating tables;
- a separate table;
- a table merge, when semantically justified.

Therefore, the benchmark does not assume that a single logical schema is the only valid answer.

Each dataset has:

1. a preferred expert mapping;
2. acceptable alternative mappings for discretionary cases;
3. not allowed mappings.

The evaluator classifies mapping decisions as follows:

| Classification | Meaning |
|---|---|
| `preferred_correct` | The LLM followed the preferred expert mapping. |
| `valid_alternative` | The LLM generated an acceptable but non-preferred mapping. |
| `invalid_mapping` | The LLM generated a mapping explicitly marked as not allowed. |
| `missing_mapping` | The LLM omitted the required mapping. |
| `hallucinated_mapping` | The LLM invented a mapping unsupported by the EER input. |

This distinction is important because a valid logical design should not be penalized as incorrect only because it differs from the preferred expert design.

## 5. Prompt Input Generation

The script `scripts/generate_prompt_input.py` converts `conceptual_eer.yaml` into `eer_input_text.md`.

The generated Markdown file is the controlled textual EER input used in the prompts.

It includes:

- schema metadata;
- dataset scope;
- entities;
- attributes;
- identifiers;
- relationships;
- cardinalities;
- participation constraints;
- relationship attributes;
- specialization/generalization structures;
- global constraints;
- expert notes.

Each generation run saves outputs under `results/prompt_input_runs/<run_id>/`.

The generated files are:

- `eer_input_text.md`;
- `source_conceptual_eer.yaml`;
- `prompt_input_manifest.json`.

## 6. Prompting Conditions

The benchmark evaluates four prompting conditions.

| Condition | Name | Description |
|---|---|---|
| C1 | Basic generation | The model receives the EER input and output format only. |
| C2 | Rule-augmented generation | The model receives explicit EER-to-relational mapping rules. |
| C3 | Self-check generation | The model generates and internally checks its output before returning JSON. |
| C4 | Validation-guided repair | The model repairs a previous output using a deterministic validation report. |

### 6.1 C1 — Basic Generation

C1 measures the model's direct ability to transform a textual EER schema into a logical relational schema.

### 6.2 C2 — Rule-Augmented Generation

C2 adds explicit EER-to-relational mapping rules.

These rules cover:

- regular entities;
- weak entities;
- one-to-one relationships;
- one-to-many relationships;
- many-to-many relationships;
- ternary and n-ary relationships;
- relationship attributes;
- multivalued attributes;
- specialization/generalization;
- mandatory and optional participation.

### 6.3 C3 — Self-Check Generation

C3 asks the model to internally verify its output before returning the final JSON.

The self-check focuses on:

- missing entities;
- missing attributes;
- primary keys;
- foreign keys;
- relationship tables;
- relationship attributes;
- unsupported hallucinations;
- JSON validity.

The model returns only the final JSON.

### 6.4 C4 — Validation-Guided Repair

C4 evaluates whether deterministic validation feedback can improve LLM outputs.

The model receives:

- the original EER input;
- a previous relational JSON output;
- a validation report;
- the expected output format.

It must repair the schema while preserving correct parts.

## 7. LLM Execution

The script `scripts/run_llm_experiments.py` runs one LLM experiment.

It combines:

- a prompt template;
- a prompt-ready EER input file;
- the required logical relational JSON format;
- a selected model/provider.

Supported providers include:

- Ollama;
- OpenAI;
- Gemini;
- Anthropic/Claude;
- manual/debug mode.

Each run saves outputs under `results/llm_runs/<run_id>/`.

The generated files are:

- `rendered_prompt.txt`;
- `response_text.txt`;
- `raw_response.json`;
- `usage_and_cost.json`;
- `llm_run_manifest.json`.

Batch execution is handled by `scripts/run_llm_batch.py`.

The batch runner expands combinations of dataset, condition, and model based on `configs/experiment_matrix.yaml`.

## 8. Output Normalization

LLM outputs may not be directly evaluable.

They may contain:

- Markdown code fences;
- explanatory text around JSON;
- inconsistent naming;
- formatting differences;
- invalid or partial JSON.

The script `scripts/normalize_output.py` extracts and normalizes the generated schema.

It saves outputs under `results/normalization_runs/<run_id>/`.

The generated files are:

- `raw_input.txt`;
- `extracted_json.json`;
- `normalized_schema.json`;
- `normalized_tables.csv`;
- `normalized_columns.csv`;
- `normalized_primary_keys.csv`;
- `normalized_foreign_keys.csv`;
- `normalization_warnings.json`;
- `normalization_manifest.json`.

Name normalization includes:

- lowercasing;
- removing spaces;
- removing underscores;
- removing hyphens;
- removing accents;
- normalizing alphanumeric forms.

This avoids treating superficial name formatting differences as schema design errors.

## 9. Evaluation Methodology

Evaluation is handled by `scripts/evaluate_schema.py`.

The evaluator compares `logical_relational_gold.json` against `normalized_schema.json`.

The benchmark reports three evaluation modes:

- strict evaluation;
- matched evaluation;
- alternative-aware evaluation.

## 10. Strict Evaluation

Strict evaluation compares the generated schema against the preferred gold schema using normalized names.

It answers:

- Did the model reproduce the expert preferred schema exactly, after basic name normalization?

This mode is useful but can over-penalize valid outputs that use different names.

For example:

- Gold table: `OrderProduct`
- LLM table: `OrdProd`

A strict comparison may count this as an error, even if the structure is correct.

## 11. Matched Evaluation

Matched evaluation uses similarity and structural compatibility.

It answers:

- Did the model generate a structurally equivalent schema, even if names differ?

The matching considers:

- textual similarity;
- table structure;
- attributes;
- primary keys;
- foreign key endpoints;
- relationship table structure;
- source relationship information when available.

This mode helps distinguish real structural errors from naming mismatch.

## 12. Alternative-Aware Evaluation

Alternative-aware evaluation considers expert-documented acceptable alternatives.

It answers:

- Did the model generate a logically valid schema, even if it differs from the preferred expert mapping?

This mode is necessary because conceptual-to-logical database design may have multiple valid implementations.

For example, if the preferred mapping uses a separate `CustomerProfile` table, but an acceptable alternative merges `bio` and `birth_date` into `Customer`, the alternative-aware score should not penalize that design.

## 13. Main Quality Metrics

The benchmark reports:

- Precision;
- Recall;
- F1-score;
- component-level metrics;
- mapping decision metrics;
- structural distances.

The main global metrics are:

| Metric | Meaning |
|---|---|
| `strict_f1` | Exact reproduction of the preferred schema. |
| `matched_f1` | Structural correctness after name/structure-aware matching. |
| `alternative_aware_f1` | Logical validity considering acceptable alternatives. |

Component-level metrics include:

- table F1;
- attribute F1;
- primary-key F1;
- foreign-key F1;
- relationship-table F1;
- specialization-mapping score.

## 14. Structural Manhattan Distance

F1-score alone does not capture the severity of schema errors.

The benchmark therefore reports weighted structural Manhattan distance.

The error vector includes:

- missing tables;
- hallucinated tables;
- missing attributes;
- hallucinated attributes;
- wrong primary keys;
- missing foreign keys;
- wrong foreign key targets;
- wrong relationship tables;
- cardinality errors;
- specialization errors;
- invalid mappings.

Each error category has a weight according to severity.

The benchmark reports:

| Distance | Meaning |
|---|---|
| `strict_distance` | Distance before structural matching. |
| `matched_distance` | Distance after similarity/structure-aware matching. |
| `alternative_aware_distance` | Distance after considering valid alternatives. |

It also reports:

| Reduction | Meaning |
|---|---|
| `distance_reduction_from_matching` | Apparent error removed by structural matching. |
| `distance_reduction_from_alternatives` | Apparent error removed by valid alternative mappings. |

Interpretation:

- high strict distance and low matched distance suggest naming mismatch;
- high matched distance and low alternative-aware distance suggest valid alternative mapping;
- high alternative-aware distance suggests real structural error.

## 15. Mapping-Specific Metrics

The evaluator also reports:

| Metric | Meaning |
|---|---|
| `preferred_mapping_accuracy` | Fraction of mapping decisions following the preferred expert choice. |
| `valid_mapping_accuracy` | Fraction of mapping decisions that are valid, including alternatives. |
| `alternative_mapping_rate` | Frequency of valid but non-preferred mappings. |
| `invalid_mapping_rate` | Frequency of invalid mappings. |

These metrics are important because a model may not reproduce the preferred schema but may still generate a valid logical design.

## 16. Usage and Cost Metrics

The benchmark records execution cost proxies.

For remote APIs, the runner records when available:

- input tokens;
- output tokens;
- total tokens;
- cached input tokens;
- reasoning tokens;
- latency;
- estimated financial cost.

For Ollama/local models, the runner records when available:

- prompt evaluation count;
- generation token count;
- total duration;
- prompt evaluation duration;
- generation duration;
- tokens per second.

Cost estimates are stored in `usage_and_cost.json` and use pricing information from `configs/model_pricing.yaml`.

This allows cost-quality analysis.

## 17. Aggregation

The script `scripts/aggregate_results.py` collects outputs from:

- LLM runs;
- normalization runs;
- evaluation runs.

It writes aggregate tables to `results/aggregate_runs/<run_id>/`.

The main aggregate table is `aggregate_run_summary.csv`.

It contains one row per evaluated run, including:

- dataset;
- model;
- provider;
- condition;
- strict F1;
- matched F1;
- alternative-aware F1;
- strict/matched/alternative-aware distances;
- mapping alternative metrics;
- token usage;
- latency;
- estimated cost.

Other aggregate tables summarize results by:

- model;
- condition;
- dataset complexity;
- model and condition;
- dataset and condition;
- component type;
- error type;
- cost-quality trade-off.

## 18. Planned Analysis

The aggregated results will support the following analyses.

### 18.1 Model Comparison

Models will be compared using:

- alternative-aware F1;
- matched F1;
- structural distance;
- valid mapping accuracy;
- invalid mapping rate;
- JSON and normalization quality.

### 18.2 Prompt Condition Comparison

The benchmark will compare C1, C2, C3, and C4.

The goal is to measure whether:

- explicit mapping rules improve schema quality;
- self-check improves correctness;
- validation-guided repair reduces errors;
- improvements justify additional cost.

### 18.3 Dataset Complexity Analysis

The benchmark uses datasets of different complexity levels.

The analysis will test whether performance decreases as schema complexity increases.

Expected dimensions include:

- low-complexity dataset;
- medium-complexity dataset;
- high-complexity dataset.

### 18.4 Error Analysis

The error analysis will examine:

- missing entities;
- hallucinated elements;
- missing attributes;
- wrong primary keys;
- missing foreign keys;
- wrong foreign key targets;
- missing relationship tables;
- invalid mappings;
- specialization/generalization errors.

### 18.5 Naming Mismatch Analysis

The gap between strict and matched metrics measures the effect of naming differences.

Useful measures include:

- `matched_f1 - strict_f1`;
- `distance_reduction_from_matching`.

### 18.6 Alternative Mapping Analysis

The gap between matched and alternative-aware metrics measures the effect of valid non-preferred mappings.

Useful measures include:

- `alternative_aware_f1 - matched_f1`;
- `distance_reduction_from_alternatives`;
- `alternative_mapping_rate`.

### 18.7 Cost-Quality Analysis

The benchmark will compare quality against:

- estimated cost;
- latency;
- token usage;
- tokens per second.

This supports analysis of whether expensive models provide enough quality improvement to justify their cost.

## 19. Reproducibility

Every major script produces:

- a dedicated output folder;
- output files;
- intermediate artifacts when useful;
- a manifest file;
- input paths;
- input hashes;
- execution metadata.

This supports reproducibility and makes it possible to audit each stage of the pipeline.

## 20. Expected Contribution

The methodology contributes an evaluation framework for LLM-based database design that goes beyond exact string matching.

The main methodological contributions are:

1. textual EER input instead of image-based diagrams;
2. expert-defined conceptual and logical ground truths;
3. preferred plus alternative valid logical mappings;
4. strict, matched, and alternative-aware evaluation;
5. weighted structural Manhattan distance;
6. component-level schema metrics;
7. mapping decision metrics;
8. cost and latency tracking;
9. reproducible scripts and aggregate outputs.

Together, these elements allow a more faithful evaluation of LLMs for conceptual-to-logical database design.
