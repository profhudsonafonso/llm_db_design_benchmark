# LLM Database Design Benchmark

This repository contains the experimental artifacts for evaluating how Large Language Models support conceptual-to-logical database design tasks.

The benchmark uses textual EER representations, manually validated by a domain expert, as controlled inputs for LLMs. The generated logical schemas are compared against expert-defined logical ground truths.

## Goal

The goal of this project is to evaluate whether Large Language Models can support database design tasks beyond simple ER-to-JSON conversion.

Instead of using only image-based ER diagrams, this benchmark uses textual conceptual models. This allows the evaluation of both multimodal LLMs and text-only LLMs.

The study focuses on the transformation from conceptual EER models to logical relational schemas.

## Motivation

Previous experiments used images of EER diagrams as input. This approach is useful for testing multimodal models, but it limits the number of LLMs that can be evaluated.

In this new experimental design, the input is a controlled textual representation of the EER schema. This makes the benchmark more reproducible and allows the inclusion of different types of models, including commercial APIs and local text-based models.

## Research Direction

This benchmark investigates the following question:

> How accurately can LLMs support conceptual-to-logical database design tasks under different schema complexity levels and prompting conditions?

The benchmark evaluates whether LLMs can correctly identify and transform:

- entities;
- attributes;
- primary keys;
- foreign keys;
- relationships;
- cardinalities;
- specialization/generalization structures, when present;
- relationship tables;
- logical relational schema structures.

## Datasets

The benchmark includes three datasets with increasing complexity.

| Dataset | Complexity | Role |
|---|---|---|
| Chinook | Low | Small relational schema with clear entities and relationships |
| IMDb | Medium | Real-world dataset with multiple interconnected entities |
| Yelp | High | Heterogeneous JSON-based dataset with more complex relationships |

## Dataset Selection Rationale

### Chinook

Chinook is used as the low-complexity dataset. It has a compact and well-known relational structure, making it suitable for validating whether LLMs can correctly perform basic conceptual-to-logical mapping.

### IMDb

IMDb is used as the medium-complexity dataset. It contains several interconnected entities, such as titles, people, roles, ratings, and episodes. It is more complex than Chinook but still manageable for controlled evaluation.

### Yelp

Yelp is used as the high-complexity dataset. It contains heterogeneous JSON-based structures and several connected concepts, such as businesses, users, reviews, tips, and check-ins. It is useful for testing how LLMs behave with larger and more complex schema structures.

## Preferred and Alternative Valid Mappings

Conceptual-to-logical database design may have more than one valid implementation.

For this reason, the benchmark uses:

- one preferred logical relational gold standard;
- local alternative valid mappings for discretionary design decisions.

Examples of discretionary decisions include:

- mapping a relationship as a separate relationship table;
- mapping a relationship as a foreign key column;
- merging tables in specific one-to-one cases;
- choosing a strategy for specialization/generalization.

The file `logical_relational_gold.json` contains a `mapping_alternatives` section where the expert documents:

- the preferred mapping;
- other acceptable mappings;
- mappings that should not be used;
- the rationale for each decision.

During evaluation, an LLM output can be classified as:

- `preferred_correct`;
- `valid_alternative`;
- `invalid_mapping`;
- `missing_mapping`;
- `hallucinated_mapping`.

This avoids penalizing a model when it produces a logically valid alternative that differs from the preferred expert choice.

## Ground Truth Strategy

Each dataset has two main reference files.

```text
datasets/<dataset>/ground_truth/conceptual_eer.yaml
datasets/<dataset>/ground_truth/logical_relational_gold.json
```

The `conceptual_eer.yaml` file represents the conceptual EER schema. This file is used to generate the textual input given to the LLMs.

The `logical_relational_gold.json` file represents the expected logical relational schema. This file is not shown to the LLMs. It is used only for evaluation.

Both files are manually created or validated by a domain expert.

## Why Not Only Mermaid?

Mermaid can be useful for visualization, but it does not fully represent all EER features required in this benchmark.

Some EER features are difficult to represent completely in Mermaid, such as:

- specialization;
- generalization;
- inheritance;
- total or partial specialization;
- disjoint or overlapping specialization;
- minimum and maximum cardinalities;
- weak entities;
- relationship attributes;
- semantic constraints.

For this reason, the main conceptual ground truth is represented in YAML. Mermaid may be used only as an optional visualization format.

## Reproducible Script Outputs

All benchmark scripts must save their outputs in dedicated folders.

Each script execution should produce:

- the main output files;
- intermediate files when useful;
- warnings or error reports;
- a manifest file with execution metadata.

This rule supports reproducibility and makes it possible to inspect each step of the benchmark pipeline.

The normalization script is documented in `scripts/README.md`.

Default normalization outputs are saved in:

- `results/normalization_runs/<run_id>/`

## Paper Material

The repository stores reusable paper-support text blocks in:

- `paper_material/text_blocks/`

The current text block:

- `paper_material/text_blocks/toy_pipeline_validation.md`

summarizes the toy example used to validate the normalization and evaluation pipeline. It explains the strict, matched, and alternative-aware evaluation modes and reports the toy validation results.


## Repository Structure

```text
docs/             Documentation of protocol, prompts, ground truth, and metrics
datasets/         Dataset-specific metadata, ground truths, and prompt inputs
prompts/          Prompt templates used in the experiments
notebooks/        Jupyter notebooks executed on the project server
scripts/          Evaluation and normalization scripts
llm_outputs/      Raw outputs generated by each model
results/          Metrics, tables, figures, and error analyses
paper_material/   Tables, figures, and text blocks for the paper
```

## Main Folders

### docs/

This folder contains documentation about the experiment protocol, ground truth guidelines, prompt design, and scoring metrics.

Expected files:

```text
docs/experiment_protocol.md
docs/ground_truth_guidelines.md
docs/prompt_design.md
docs/scoring_metrics.md
```

### datasets/

This folder contains the dataset-specific files.

Each dataset follows the same internal structure:

```text
datasets/<dataset>/
├── README.md
├── source_metadata/
├── ground_truth/
└── prompt_inputs/
```

The `source_metadata/` folder stores information about the original dataset.

The `ground_truth/` folder stores the expert-defined conceptual and logical schemas.

The `prompt_inputs/` folder stores the textual inputs prepared for the LLMs.

### prompts/

This folder contains the prompt templates used in the experiments.

Expected prompt files:

```text
prompts/prompt_1_basic.txt
prompts/prompt_2_cardinality_rules.txt
prompts/prompt_3_rules_self_check.txt
```

### notebooks/

This folder contains the Jupyter notebooks used to prepare datasets, generate prompt inputs, run LLM experiments, and evaluate outputs.

Expected notebooks:

```text
notebooks/01_prepare_datasets.ipynb
notebooks/02_generate_prompt_inputs.ipynb
notebooks/03_run_llm_experiments.ipynb
notebooks/04_evaluate_outputs.ipynb
```

### scripts/

This folder contains Python scripts for output normalization, schema evaluation, error classification, and batch evaluation.

Expected scripts:

```text
scripts/normalize_output.py
scripts/evaluate_schema.py
scripts/error_taxonomy.py
scripts/run_all_evaluations.py
```

### llm_outputs/

This folder stores raw outputs generated by the LLMs.

The expected structure is:

```text
llm_outputs/
├── chinook/
├── imdb/
└── yelp/
```

### results/

This folder stores the evaluation results.

The expected structure is:

```text
results/
├── raw_metrics/
├── aggregate_tables/
├── figures/
└── error_analysis/
```

### paper_material/

This folder stores tables, figures, and text blocks prepared for the paper.

The expected structure is:

```text
paper_material/
├── tables/
├── figures/
└── text_blocks/
```


## Experimental Protocol

The full experimental protocol is documented in `docs/experiment_protocol.md`.

It defines:

- the benchmark goal;
- the datasets and complexity levels;
- the expert ground truth strategy;
- the four experimental conditions C1-C4;
- the validation-guided repair workflow;
- the evaluation components;
- the metrics;
- the error taxonomy;
- the reproducibility requirements.

## Experiment Conditions

The experiments compare:

- multiple datasets;
- multiple schema complexity levels;
- multiple LLMs;
- multiple prompting strategies;
- multiple schema components.

The evaluated schema components include:

- entities;
- attributes;
- primary keys;
- foreign keys;
- relationships;
- cardinality decisions;
- relationship tables;
- specialization/generalization mapping, when present.


## Experimental Conditions

The benchmark evaluates four experimental conditions.

| Condition | Name | Description |
|---|---|---|
| C1 | Basic generation | The LLM receives the textual EER input and directly generates the relational JSON schema |
| C2 | Rule-augmented generation | The LLM receives the textual EER input plus explicit EER-to-relational mapping rules |
| C3 | Self-check generation | The LLM generates the schema, reviews its own output, and returns a final corrected JSON |
| C4 | Validation-guided repair | The LLM first generates a relational JSON; a deterministic validator reports errors; the LLM then repairs the output using the validation report |

The C4 condition is a lightweight hybrid strategy. It does not use fine-tuning, GNNs, or a complex multi-agent architecture. Instead, it combines LLM generation with deterministic validation and repair.

This allows the benchmark to measure not only the initial quality of LLM-generated schemas, but also whether LLMs can correct their own outputs when given structured feedback.

## Prompting Strategies

The benchmark currently considers three prompt types.

| Prompt | Description |
|---|---|
| Prompt 1 | Basic schema extraction |
| Prompt 2 | Schema extraction with cardinality mapping rules |
| Prompt 3 | Schema extraction with cardinality rules and self-check validation |

## LLM Execution

The script `scripts/run_llm_experiments.py` runs one LLM experiment by combining:

- a prompt template;
- a prompt-ready textual EER input;
- the required logical relational JSON output format;
- a configured model/provider.

Supported providers:

- `ollama`;
- `openai`;
- `gemini`;
- `anthropic`;
- `manual`.

Model definitions are stored in:

- `configs/models.yaml`

Provider settings are stored locally in:

- `configs/provider_settings.yaml`

The local provider settings file must not be committed.

Each LLM execution saves:

- the rendered prompt;
- the raw provider response;
- the extracted response text;
- a reproducibility manifest.

Default output folder:

- `results/llm_runs/<run_id>/`

Published raw text output:

- `llm_outputs/<dataset>/<run_id>_raw.txt`


## Prompt Input Generation

The script `scripts/generate_prompt_input.py` converts an expert-defined `conceptual_eer.yaml` file into a prompt-ready Markdown file.

Input:

- `datasets/<dataset>/ground_truth/conceptual_eer.yaml`

Main output:

- `results/prompt_input_runs/<run_id>/eer_input_text.md`

Optional published copy:

- `datasets/<dataset>/prompt_inputs/eer_input_text.md`

The script also saves:

- a snapshot of the source conceptual YAML;
- a reproducibility manifest;
- schema counts.

This generated Markdown file is later inserted into the C1-C4 prompt templates as the textual EER input.


## Prompt Templates

The benchmark uses four prompt templates corresponding to the four experimental conditions.

| Condition | Prompt file | Purpose |
|---|---|---|
| C1 | prompts/prompt_1_basic.txt | Direct conceptual-to-logical generation without explicit mapping rules |
| C2 | prompts/prompt_2_cardinality_rules.txt | Generation with explicit EER-to-relational mapping rules |
| C3 | prompts/prompt_3_rules_self_check.txt | Generation with mapping rules and internal self-check |
| C4 | prompts/prompt_4_validation_guided_repair.txt | Repair of a previous LLM output using a deterministic validation report |

The prompt design is documented in `docs/prompt_design.md`.

## Evaluation Script

The first schema evaluation script is:

- `scripts/evaluate_schema.py`

It compares an LLM-generated schema against the expert logical relational gold standard.

It produces:

- strict matching metrics;
- similarity and structure-aware matching metrics;
- component-level Precision, Recall, and F1;
- preferred and alternative valid mapping classification;
- weighted structural Manhattan distance;
- error reports;
- reproducibility manifest.

Default outputs are saved in:

- `results/evaluation_runs/<run_id>/`

The script is documented in `scripts/README.md`.


## Scoring Metrics

The benchmark scoring strategy is documented in `docs/scoring_metrics.md`.

The evaluation uses:

- strict matching;
- similarity and structure-aware matching;
- preferred and alternative valid mapping evaluation;
- component-level Precision, Recall, and F1-score;
- hallucination and omission rates;
- naming mismatch rate;
- preferred mapping accuracy;
- valid mapping accuracy;
- normalized weighted structural Manhattan distance;
- strict, matched, and alternative-aware weighted structural Manhattan distances;
- distance reduction from matching;
- distance reduction from documented valid alternatives;
- C4 repair metrics.

This design avoids over-penalizing LLM outputs that use different names for semantically equivalent schema elements and also accounts for discretionary conceptual-to-logical mapping decisions.

## Evaluation Metrics

The evaluation compares the LLM-generated logical schema against the expert-defined logical ground truth.

The main metrics include:

- precision;
- recall;
- F1-score;
- entity-level score;
- attribute-level score;
- primary-key score;
- foreign-key score;
- relationship score;
- hallucination rate;
- omission rate.

## Error Analysis

The benchmark also records typical error categories.

Examples include:

| Error Type | Description |
|---|---|
| Entity omission | The model fails to generate an expected entity |
| Entity hallucination | The model creates an entity not present in the ground truth |
| Attribute omission | The model omits an expected attribute |
| Attribute hallucination | The model creates an attribute not present in the ground truth |
| Wrong primary key | The model assigns an incorrect primary key |
| Missing foreign key | The model fails to create an expected foreign key |
| Wrong foreign key target | The model creates a foreign key pointing to the wrong table or column |
| Naming mismatch | The model uses inconsistent names for equivalent schema elements |
| Relationship table error | The model fails to create or incorrectly creates an associative table |
| Cardinality error | The model applies an incorrect cardinality mapping decision |

## Execution Environment

The experiments are executed in a Jupyter server associated with the research project.

This GitHub repository stores the reproducible artifacts, including:

- documentation;
- dataset metadata;
- ground truth files;
- prompt templates;
- notebooks;
- scripts;
- LLM outputs;
- evaluation results;
- paper-ready tables and figures.

## Reproducibility Notes

API keys and private configuration files must not be committed to the repository.

Sensitive files should be stored locally using files such as:

```text
.env
config/private_config.yaml
```

These files are ignored by `.gitignore`.

## Current Experimental Plan

The current plan is organized as follows:

1. Prepare the GitHub repository structure.
2. Define the official ground truth format.
3. Create guidelines for the domain expert.
4. Prepare Chinook, IMDb, and Yelp metadata.
5. Create expert-validated conceptual EER ground truths.
6. Create expert-validated logical relational ground truths.
7. Generate prompt-ready textual inputs.
8. Run LLM experiments.
9. Normalize LLM outputs.
10. Evaluate outputs against the logical ground truth.
11. Analyze errors by dataset, prompt, and model.
12. Prepare tables and figures for the paper.
13. Rewrite the methodology, experiments, results, and discussion sections.

## Status

Initial repository structure created.

The next step is to define the official format for:

```text
conceptual_eer.yaml
logical_relational_gold.json
```

## Toy Example

The repository includes a synthetic toy example used to test the benchmark pipeline before running experiments on the real datasets.

Location:

- `datasets/toy_example/`

The toy example includes:

- a conceptual EER ground truth;
- a logical relational gold standard;
- a prompt-ready EER input;
- an example raw LLM output;
- a discretionary one-to-one mapping with an acceptable alternative;
- a relationship table naming mismatch used to test similarity/structure-aware evaluation.

The example raw output is stored in:

- `llm_outputs/toy_example/gpt_c1_raw.txt`

The toy example can be normalized with:

`python scripts/normalize_output.py --input llm_outputs/toy_example/gpt_c1_raw.txt --dataset toy_example --model gpt --condition C1 --prompt-file prompts/prompt_1_basic.txt --input-eer-file datasets/toy_example/prompt_inputs/eer_input_text.md`

