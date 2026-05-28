# Experimental Protocol

This document defines the experimental protocol for the LLM Database Design Benchmark.

The benchmark evaluates how Large Language Models support conceptual-to-logical database design tasks. The task is to transform an expert-defined textual EER schema into a logical relational schema represented in JSON.

## 1. Goal

The main goal is to evaluate whether LLMs can support database design tasks beyond simple ER-to-JSON conversion.

The benchmark focuses on the conceptual-to-logical design step, where an EER model is transformed into a logical relational schema.

The evaluation considers:

- different schema complexity levels;
- different LLMs;
- different prompting conditions;
- different schema components;
- different error categories;
- the ability of LLMs to repair their outputs using structured validation feedback.

## 2. Motivation

Previous experiments used images of EER diagrams as input. Although image-based input is useful for testing multimodal models, it limits the number of LLMs that can be evaluated.

This benchmark uses textual EER representations instead of images. This makes the experiment more reproducible and allows the evaluation of both multimodal and text-only LLMs.

The textual EER representation is manually defined or validated by a domain expert.

## 3. Research Questions

The benchmark is guided by the following research questions.

RQ1. How accurately can LLMs transform textual EER schemas into logical relational schemas?

RQ2. How does schema complexity affect LLM performance in conceptual-to-logical database design?

RQ3. Which schema components are easier or harder for LLMs to generate correctly?

RQ4. Do explicit mapping rules improve LLM performance?

RQ5. Does self-checking improve LLM-generated logical schemas?

RQ6. Can deterministic validation feedback help LLMs repair their own outputs?

RQ7. What types of errors and hallucinations are most common in LLM-generated database schemas?

## 4. Benchmark Datasets

The benchmark uses three datasets with increasing complexity.

| Dataset | Complexity | Role |
|---|---|---|
| Chinook | Low | Small and controlled relational schema |
| IMDb | Medium | Real-world dataset with multiple interconnected entities |
| Yelp | High | Heterogeneous JSON-based dataset with more complex relationships |

### 4.1 Chinook

Chinook is used as the low-complexity dataset.

It is expected to contain a compact set of entities and relationships, making it suitable for evaluating basic conceptual-to-logical mapping.

### 4.2 IMDb

IMDb is used as the medium-complexity dataset.

It contains multiple interconnected concepts, such as titles, people, roles, ratings, and episodes.

### 4.3 Yelp

Yelp is used as the high-complexity dataset.

It contains heterogeneous JSON-based structures and connected concepts, such as businesses, users, reviews, tips, and check-ins.

## 5. Ground Truth Strategy

Each dataset has two ground truth files.

- conceptual EER ground truth: datasets/<dataset>/ground_truth/conceptual_eer.yaml
- logical relational gold standard: datasets/<dataset>/ground_truth/logical_relational_gold.json

### 5.1 Conceptual EER Ground Truth

The conceptual EER ground truth represents the input schema.

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
- semantic constraints.

This file is used to generate the prompt input for the LLMs.

### 5.2 Logical Relational Gold Standard

The logical relational gold standard represents the expected output.

It includes:

- tables;
- columns;
- primary keys;
- foreign keys;
- relationship tables;
- unique constraints;
- inheritance mapping decisions;
- mapping notes.

This file is not shown to the LLMs. It is used only for evaluation.

## 6. Role of the Expert

A domain expert creates or validates both ground truth files for each dataset.

The expert must:

- define the conceptual EER schema;
- define the logical relational gold standard;
- document assumptions;
- document ambiguities;
- document alternative valid mappings, when applicable;
- ensure that each relationship has explicit cardinalities;
- ensure that each logical table has a primary key;
- ensure that all foreign keys reference valid tables and columns.

## 7. Experimental Conditions

The benchmark evaluates four experimental conditions.

| Condition | Name | Description |
|---|---|---|
| C1 | Basic generation | The LLM receives only the textual EER input and directly generates the relational JSON schema. |
| C2 | Rule-augmented generation | The LLM receives the textual EER input plus explicit EER-to-relational mapping rules. |
| C3 | Self-check generation | The LLM generates the schema, checks its own output, and returns a final corrected JSON. |
| C4 | Validation-guided repair | The LLM first generates a relational JSON; a deterministic validator reports errors; the LLM then repairs the output using the validation report. |

## 8. Prompting Workflow

### 8.1 C1 — Basic Generation

Input:

- textual EER schema;
- required JSON output format.

Output:

- logical relational schema in JSON.

Purpose:

- evaluate direct LLM generation without explicit design rules.

### 8.2 C2 — Rule-Augmented Generation

Input:

- textual EER schema;
- required JSON output format;
- explicit EER-to-relational mapping rules.

Output:

- logical relational schema in JSON.

Purpose:

- evaluate whether explicit mapping rules improve the result.

### 8.3 C3 — Self-Check Generation

Input:

- textual EER schema;
- required JSON output format;
- explicit mapping rules;
- self-check instruction.

Output:

- final logical relational schema in JSON after self-review.

Purpose:

- evaluate whether LLM self-review improves correctness.

### 8.4 C4 — Validation-Guided Repair

Input:

- original textual EER schema;
- previous LLM-generated relational JSON;
- deterministic validation report.

Output:

- repaired logical relational schema in JSON.

Purpose:

- evaluate whether structured validation feedback helps the LLM repair its own output.

## 9. C4 Validation-Guided Repair Workflow

The C4 workflow is:

1. Run one of the generation conditions, usually C2 or C3.
2. Save the generated relational JSON.
3. Run the deterministic validator.
4. Generate a validation report.
5. Send the original EER input, the previous output, and the validation report to the LLM.
6. Ask the LLM to repair only the reported errors.
7. Evaluate the repaired output against the logical relational gold standard.

The validator does not replace the expert gold standard. It only produces structured feedback for the repair step.

## Prompt Template Implementation

The four experimental conditions are implemented as separate prompt templates.

| Condition | Prompt file | Status |
|---|---|---|
| C1 | prompts/prompt_1_basic.txt | created |
| C2 | prompts/prompt_2_cardinality_rules.txt | created |
| C3 | prompts/prompt_3_rules_self_check.txt | created |
| C4 | prompts/prompt_4_validation_guided_repair.txt | created |

The detailed prompt design is documented in `docs/prompt_design.md`.

## LLM Execution Script

LLM executions are handled by:

- `scripts/run_llm_experiments.py`

The script renders a prompt from:

- a prompt template;
- a prompt-ready EER input file;
- the logical relational output format specification;
- optional C4 repair inputs.

The script supports local and remote providers, including:

- Ollama local models;
- OpenAI models;
- Gemini models;
- Claude/Anthropic models;
- manual outputs;
- dry-run execution.

Each execution produces a dedicated run folder under:

- `results/llm_runs/<run_id>/`

The run folder contains:

- `rendered_prompt.txt`;
- `response_text.txt`;
- `raw_response.json`;
- `llm_run_manifest.json`.

The response text is also published under:

- `llm_outputs/<dataset>/<run_id>_raw.txt`

when a provider returns text.


## 10. Models

The benchmark can evaluate different LLMs, including commercial APIs and local text-only models.

The initial target model groups are:

- GPT-family models;
- Gemini-family models;
- Claude-family models;
- optional local models, if available through the project environment.

The exact model versions must be recorded in the experiment logs.

## Prompt Input Generation Script

The prompt-ready textual EER input is generated by:

- `scripts/generate_prompt_input.py`

The script receives the expert-defined `conceptual_eer.yaml` file and produces a Markdown file that is inserted into the C1-C4 prompt templates.

For each dataset, the expected generated prompt input is:

- `datasets/<dataset>/prompt_inputs/eer_input_text.md`

Each generation run also produces a reproducibility folder under:

- `results/prompt_input_runs/<run_id>/`

This folder contains:

- generated `eer_input_text.md`;
- a snapshot of the source `conceptual_eer.yaml`;
- `prompt_input_manifest.json`.


## 11. Input Format

The LLM input is generated from the conceptual EER YAML file.

The input must include:

- dataset name;
- schema complexity level;
- entities;
- attributes;
- identifiers;
- relationships;
- cardinalities;
- participation constraints;
- specialization/generalization, when applicable;
- relevant expert notes.

The LLM must not receive the logical relational gold standard.

## 12. Output Format

All LLMs must return only valid JSON.

The expected output format is defined in:

- docs/llm_output_format.md
- docs/logical_relational_gold_template.json

The LLM must not return:

- Markdown code fences;
- explanations outside the JSON;
- comments before or after the JSON.

## 13. Evaluation Components

The evaluation is performed by comparing the LLM-generated schema against the logical relational gold standard.

The main evaluated components are:

- tables;
- columns;
- primary keys;
- foreign keys;
- relationship tables;
- specialization/generalization mappings;
- constraints;
- mapping decisions.

## Preferred and Alternative Valid Mappings

The benchmark recognizes that conceptual-to-logical database design may have multiple valid implementations.

Therefore, the expert-defined logical gold standard contains:

- a preferred mapping;
- acceptable alternative mappings for discretionary cases;
- not allowed mappings.

The evaluator must first compare the LLM output against the preferred mapping. If the output does not match the preferred mapping, the evaluator must compare it against the acceptable alternatives.

The final mapping classification can be:

| Classification | Meaning |
|---|---|
| preferred_correct | The LLM generated the preferred expert mapping. |
| valid_alternative | The LLM generated a valid but non-preferred mapping. |
| invalid_mapping | The LLM generated a mapping explicitly marked as not allowed. |
| missing_mapping | The LLM omitted the required mapping. |
| hallucinated_mapping | The LLM invented a mapping unsupported by the EER input. |

This distinction is important because a non-preferred but valid logical design should not be counted as a structural error.

The evaluation will report both:

- preferred mapping accuracy;
- valid mapping accuracy.

## 14. Metrics

The benchmark uses component-level and global metrics.

Main metrics:

- precision;
- recall;
- F1-score;
- table-level F1;
- attribute-level F1;
- primary-key F1;
- foreign-key F1;
- relationship-table F1;
- specialization-mapping score;
- hallucination rate;
- omission rate;
- JSON validity rate.

C4-specific metrics:

- repair gain;
- error reduction;
- new error rate;
- remaining constraint violation rate.

## Detailed Scoring Strategy

The detailed scoring strategy is documented in `docs/scoring_metrics.md`.

The evaluator reports both strict and matched scores.

Strict scores use exact normalized matching.

Matched scores use similarity and structure-aware matching. This avoids penalizing a generated schema only because the LLM used a different but semantically compatible name.

The benchmark also supports preferred and alternative valid mappings. This is necessary because conceptual-to-logical database design may have more than one valid implementation.

The main score groups are:

- component-level Precision, Recall, and F1-score;
- strict and matched F1;
- hallucination rate;
- omission rate;
- naming mismatch rate;
- preferred mapping accuracy;
- valid mapping accuracy;
- normalized weighted structural Manhattan distance;
- validation-guided repair metrics for C4.

The evaluator also computes an alternative-aware score.

Alternative-aware evaluation treats expert-documented acceptable non-preferred mappings as valid. This prevents a valid logical design from being penalized only because it differs from the preferred expert mapping.

The evaluator therefore reports:

- strict scores and distance;
- matched scores and distance;
- alternative-aware scores and distance.

The difference between matched distance and alternative-aware distance is reported as distance reduction from alternatives.

The evaluator computes structural Manhattan distance in two ways:

- strict distance, before similarity/structure-aware matching;
- matched distance, after similarity/structure-aware matching.

The difference between them is reported as distance reduction from matching. This helps distinguish naming mismatch from real structural design errors.

The normalized weighted structural Manhattan distance is used as a complementary metric. It measures not only the number of errors, but also their structural severity.

The C4 condition additionally reports:

- repair gain;
- error reduction;
- new error rate;
- remaining constraint violation rate.

## 15. Error Taxonomy

Errors are classified according to the taxonomy defined in:

- docs/error_taxonomy.md

Main error groups:

- formatting errors;
- structural errors;
- attribute errors;
- key errors;
- relationship errors;
- constraint errors;
- hallucination errors;
- specialization/generalization errors.

## 16. Validation Report

The deterministic validation report format is defined in:

- docs/validator_report_format.md

The validation report includes:

- dataset;
- model;
- prompt condition;
- JSON validity;
- list of errors;
- error severity;
- expected value;
- found value;
- summary counts.

## Evaluation Script Implementation

The initial evaluator is implemented in:

- `scripts/evaluate_schema.py`

The evaluator compares each generated schema with the expert logical relational gold standard.

It reports:

- strict component metrics;
- matched component metrics;
- table mapping evidence;
- mapping alternative classifications;
- evaluation errors;
- weighted structural Manhattan distance;
- normalized weighted structural distance;
- execution manifest.

The evaluator writes all outputs to:

- `results/evaluation_runs/<run_id>/`

This implementation follows the reproducibility rule that every script execution must produce a dedicated output folder and a manifest file.


## Script Output Reproducibility

All scripts used in the benchmark must save their outputs in a dedicated run folder.

Each run folder should include:

- main output files;
- intermediate artifacts;
- warnings or error reports;
- a manifest file with execution metadata.

The manifest should record:

- script name;
- timestamp;
- dataset;
- model;
- condition;
- input files;
- input file hashes;
- prompt file;
- output directory;
- generated files;
- relevant parameters.

The first script following this rule is `scripts/normalize_output.py`.

Its outputs are saved by default under:

- `results/normalization_runs/<run_id>/`

## Toy Example for Pipeline Testing

Before running the benchmark on Chinook, IMDb, and Yelp, the repository includes a synthetic toy example.

Location:

- `datasets/toy_example/`

The toy example is used to test:

- ground truth structure;
- prompt input format;
- raw LLM output normalization;
- JSON extraction from Markdown code fences;
- name normalization;
- flattened table, column, primary-key, and foreign-key outputs;
- alternative valid mapping representation;
- future schema matching and evaluation scripts.

The toy example contains a naming mismatch in the generated output: the preferred relationship table is `OrderProduct`, while the LLM output uses `OrdProd`. This case is useful for testing similarity and structure-aware matching.


## 17. Reproducibility

Each experiment must record:

- dataset name;
- dataset complexity;
- model name;
- model version;
- prompt condition;
- prompt file;
- input file;
- output file;
- timestamp;
- execution environment;
- parsing status;
- validation status.

API keys and private configuration files must not be committed to the repository.

## 18. Expected Repository Locations

Ground truth files:

- datasets/<dataset>/ground_truth/conceptual_eer.yaml
- datasets/<dataset>/ground_truth/logical_relational_gold.json

Prompt input files:

- datasets/<dataset>/prompt_inputs/eer_input_text.md

Prompt templates:

- prompts/prompt_1_basic.txt
- prompts/prompt_2_cardinality_rules.txt
- prompts/prompt_3_rules_self_check.txt
- prompts/prompt_4_validation_guided_repair.txt

LLM outputs:

- llm_outputs/<dataset>/

Evaluation results:

- results/raw_metrics/
- results/aggregate_tables/
- results/error_analysis/
- results/figures/

Paper material:

- paper_material/tables/
- paper_material/figures/
- paper_material/text_blocks/

## 19. Threats to Validity

Potential threats include:

- limited number of datasets;
- expert subjectivity in ground truth construction;
- multiple valid logical mappings for the same conceptual schema;
- model version changes over time;
- prompt sensitivity;
- ambiguity in source datasets;
- difficulty of evaluating semantically equivalent but syntactically different schemas;
- possible bias introduced by explicit mapping rules;
- possible over-correction in validation-guided repair.

## 20. Current Status

The repository structure has been created.

The ground truth templates and expert guidelines have been prepared and sent to the expert.

The current next steps are:

1. finalize the prompt templates;
2. define the scoring metrics in detail;
3. implement the normalization and validation scripts;
4. wait for expert-validated ground truth files;
5. generate prompt inputs;
6. run the LLM experiments;
7. evaluate and analyze results.
