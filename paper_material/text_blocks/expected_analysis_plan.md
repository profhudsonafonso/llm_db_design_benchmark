# Expected Analysis Plan

This document defines how the final benchmark results should be analyzed after running the LLM experiments.

The goal is to avoid a purely descriptive experimental section. The analysis should explain what the results mean for LLM-based database design.

## 1. Main Analysis Goal

The main goal is to evaluate whether LLMs can transform textual EER conceptual schemas into valid logical relational schemas.

The analysis should not only report scores.

It should explain:

- which models perform better;
- which prompt conditions improve performance;
- which schema components are most difficult;
- how dataset complexity affects performance;
- how often apparent errors are only naming mismatches;
- how often LLMs choose valid alternative mappings;
- where real semantic errors remain;
- whether higher cost leads to better schema quality.

## 2. Main Aggregate Files

The analysis should mainly use the following files:

| File | Purpose |
|---|---|
| `aggregate_run_summary.csv` | Main table with one row per evaluated run. |
| `aggregate_component_metrics.csv` | Component-level metrics by mode and component. |
| `aggregate_error_counts.csv` | Error and distance summary by evaluation mode. |
| `aggregate_cost_quality.csv` | Cost, latency, token usage, and quality metrics. |
| `aggregate_by_model.csv` | Average results grouped by model. |
| `aggregate_by_condition.csv` | Average results grouped by prompt condition. |
| `aggregate_by_dataset_complexity.csv` | Average results grouped by dataset complexity. |
| `aggregate_by_model_condition.csv` | Average results grouped by model and condition. |
| `aggregate_by_dataset_condition.csv` | Average results grouped by dataset and condition. |

## 3. Core Metrics to Report

The main quality metrics are:

| Metric | Interpretation |
|---|---|
| `strict_f1` | Reproduction of the preferred expert schema. |
| `matched_f1` | Structural correctness after name and structure-aware matching. |
| `alternative_aware_f1` | Logical validity considering documented valid alternatives. |
| `strict_distance` | Structural error before matching. |
| `matched_distance` | Structural error after matching. |
| `alternative_aware_distance` | Structural error after considering valid alternatives. |
| `valid_mapping_accuracy` | Fraction of mapping decisions that are valid. |
| `invalid_mapping_rate` | Fraction of mapping decisions that are invalid. |
| `estimated_cost_usd` | Estimated financial cost of the run. |
| `latency_seconds` | Execution latency. |

The main score for final model comparison should be:

- `alternative_aware_f1`

The secondary quality score should be:

- `matched_f1`

The main error-severity metric should be:

- `alternative_aware_distance`

## 4. Analysis 1 — Overall Model Quality

Question:

Which models produce the best logical relational schemas?

Use:

- `aggregate_by_model.csv`
- `aggregate_run_summary.csv`

Compare:

- mean `strict_f1`;
- mean `matched_f1`;
- mean `alternative_aware_f1`;
- mean `alternative_aware_distance`;
- mean `valid_mapping_accuracy`;
- mean `invalid_mapping_rate`.

Expected interpretation:

- A high `alternative_aware_f1` means the model produces valid logical schemas.
- A large gap between `strict_f1` and `matched_f1` suggests naming variation.
- A large gap between `matched_f1` and `alternative_aware_f1` suggests valid non-preferred mappings.
- A high `invalid_mapping_rate` indicates semantic mapping problems.

Possible writing pattern:

"The strongest models are not necessarily those with the highest strict score. In database design, a model may deviate from the preferred gold schema while still preserving logical validity. Therefore, alternative-aware F1 is used as the primary quality indicator."

## 5. Analysis 2 — Prompt Condition Effect

Question:

Do C2, C3, and C4 improve over C1?

Use:

- `aggregate_by_condition.csv`
- `aggregate_by_model_condition.csv`
- `aggregate_run_summary.csv`

Compare:

- C1 vs C2;
- C2 vs C3;
- C3 vs C4.

Metrics:

- `alternative_aware_f1`;
- `matched_f1`;
- `valid_mapping_accuracy`;
- `invalid_mapping_rate`;
- `alternative_aware_distance`;
- `estimated_cost_usd`;
- `latency_seconds`.

Expected interpretation:

- If C2 improves over C1, explicit EER-to-relational mapping rules help.
- If C3 improves over C2, self-check helps the model detect its own schema errors.
- If C4 improves over C3, validation-guided repair is useful.
- If quality improves but cost increases sharply, discuss cost-benefit trade-off.

Possible writing pattern:

"Rule-augmented prompting primarily improves structural decisions such as foreign keys and relationship tables, while self-check may reduce omissions or formatting errors. Validation-guided repair should be evaluated not only by its final score but by the amount of error reduction relative to its additional cost."

## 6. Analysis 3 — Dataset Complexity Effect

Question:

Does performance decrease as schema complexity increases?

Use:

- `aggregate_by_dataset_complexity.csv`
- `aggregate_by_dataset_condition.csv`
- `aggregate_run_summary.csv`

Compare:

- low-complexity dataset;
- medium-complexity dataset;
- high-complexity dataset.

Metrics:

- `alternative_aware_f1`;
- `alternative_aware_distance`;
- `invalid_mapping_rate`;
- component-level F1;
- normalization warnings.

Expected interpretation:

- Lower scores on high-complexity datasets may indicate difficulty with richer schemas.
- More FK and relationship-table errors may appear as complexity increases.
- Specialization/generalization errors may appear only in datasets that contain inheritance structures.

Possible writing pattern:

"Dataset complexity affects the type of errors observed. While low-complexity schemas mainly expose naming and formatting variation, higher-complexity schemas are expected to stress foreign-key placement, relationship-table generation, and specialization mapping."

## 7. Analysis 4 — Component-Level Weaknesses

Question:

Which schema components are hardest for LLMs?

Use:

- `aggregate_component_metrics.csv`

Analyze components:

- tables;
- attributes;
- primary keys;
- foreign keys;
- relationship tables;
- specialization mappings.

Metrics:

- precision;
- recall;
- F1;
- mode: strict, matched, alternative-aware.

Expected interpretation:

- High table F1 but lower FK F1 means the model identifies entities but struggles with relationship semantics.
- Low relationship-table F1 means difficulty with many-to-many or associative relationships.
- Low specialization-mapping F1 means difficulty with inheritance/generalization.
- High attribute F1 but low key F1 means the model copies fields but fails design constraints.

Possible writing pattern:

"Component-level metrics reveal whether errors are superficial or semantic. For example, a model may recover most tables and attributes but still fail to produce correct foreign keys, which is more damaging for logical database design."

## 8. Analysis 5 — Naming Mismatch

Question:

How much of the strict error is caused by name variation?

Use:

- `aggregate_run_summary.csv`
- `aggregate_error_counts.csv`

Metrics:

- `matched_f1 - strict_f1`;
- `distance_reduction_from_matching`;
- strict vs matched component metrics.

Interpretation:

- Large positive difference means the model preserved structure but changed names.
- Small difference means strict and matched agree.
- If matched still remains low, the problem is not just naming.

Possible writing pattern:

"The gap between strict and matched evaluation quantifies the extent to which exact-name comparison overestimates errors. This is important because LLMs often produce semantically reasonable but differently named schema elements."

## 9. Analysis 6 — Alternative Valid Mappings

Question:

How often do LLMs generate valid alternatives rather than the preferred expert design?

Use:

- `aggregate_run_summary.csv`
- `mapping_alternative_report.json` files when qualitative inspection is needed.

Metrics:

- `alternative_aware_f1 - matched_f1`;
- `distance_reduction_from_alternatives`;
- `alternative_mapping_rate`;
- `valid_mapping_accuracy`;
- `preferred_mapping_accuracy`.

Interpretation:

- High preferred accuracy means the model follows the expert mapping.
- High valid accuracy but lower preferred accuracy means the model often chooses acceptable alternatives.
- High invalid mapping rate means true semantic errors.

Possible writing pattern:

"Alternative-aware evaluation is necessary because not every deviation from the preferred gold schema is incorrect. Some outputs represent legitimate design choices that should be distinguished from invalid mappings."

## 10. Analysis 7 — Invalid Mappings and Semantic Errors

Question:

Where do LLMs make real database design mistakes?

Use:

- `aggregate_error_counts.csv`
- `aggregate_evaluation_errors_detail.csv`
- `mapping_alternative_report.json`

Look for:

- missing FKs;
- wrong FK direction;
- missing relationship tables;
- disconnected tables;
- missing relationship attributes;
- wrong specialization mapping;
- unsupported hallucinated tables or columns.

Interpretation:

- These errors are more serious than naming differences.
- Missing FK errors indicate failure to preserve relationship semantics.
- Missing relationship tables indicate failure to handle many-to-many relationships.
- Disconnected tables indicate invalid logical design.

Possible writing pattern:

"The most important errors are those that break semantic constraints from the EER model. In particular, missing or incorrectly placed foreign keys directly affect whether the logical schema preserves conceptual relationships."

## 11. Analysis 8 — Cost-Quality Trade-Off

Question:

Is the most expensive model also the best model?

Use:

- `aggregate_cost_quality.csv`
- `aggregate_by_model.csv`
- `aggregate_by_model_condition.csv`

Metrics:

- `estimated_cost_usd`;
- `latency_seconds`;
- `input_tokens`;
- `output_tokens`;
- `tokens_per_second`;
- `cost_per_alternative_aware_f1`;
- `alternative_aware_f1`.

Interpretation:

- A model with slightly lower F1 but much lower cost may be attractive.
- C3 and C4 may improve quality but increase token usage and latency.
- Local models may have no API cost but higher latency or lower quality.

Possible writing pattern:

"Cost-quality analysis helps identify whether stronger models justify their additional cost. This is especially relevant for benchmark workflows where multiple datasets, prompts, and repair iterations are executed."

## 12. Analysis 9 — Remote vs Local Models

Question:

Are local models competitive with commercial models?

Use this analysis only after Ollama results are available.

Use:

- `aggregate_by_model.csv`
- `aggregate_cost_quality.csv`
- `aggregate_component_metrics.csv`

Compare:

- API models;
- Ollama/local models.

Metrics:

- `alternative_aware_f1`;
- component F1;
- JSON/normalization warnings;
- latency;
- tokens per second;
- cost.

Interpretation:

- Local models may be attractive if they achieve acceptable quality with no API cost.
- Local models may fail more often on structured JSON or complex constraints.
- This analysis should be cautious if hardware differs or model sizes are not comparable.

## 13. Analysis 10 — C4 Repair Effect

Question:

Does validation-guided repair improve previous outputs?

Use:

- C3 vs C4 comparison;
- original output vs repaired output;
- error count changes;
- distance changes.

Metrics:

- `alternative_aware_f1` gain;
- `alternative_aware_distance` reduction;
- invalid mapping reduction;
- FK error reduction;
- new error count;
- additional cost.

Interpretation:

- C4 is useful if it reduces semantic errors without creating many new errors.
- Repair should not be judged only by final score; it should also be judged by error reduction and cost.

Possible writing pattern:

"Validation-guided repair transforms evaluation from passive scoring into an iterative correction process. Its usefulness depends on whether deterministic feedback helps the model reduce structural errors without introducing new inconsistencies."

## 14. Recommended Tables for the Paper

Recommended tables:

1. Dataset summary table.
2. Model/provider summary table.
3. Prompt condition comparison table.
4. Main quality table by model and condition.
5. Component-level error table.
6. Strict vs matched vs alternative-aware comparison table.
7. Cost-quality table.
8. Representative error cases table.

## 15. Recommended Figures

Possible figures:

1. Pipeline diagram.
2. Bar chart of alternative-aware F1 by model.
3. Bar chart of F1 by prompt condition.
4. Line or grouped chart showing score drop by dataset complexity.
5. Stacked error-type chart.
6. Cost vs quality scatter plot.
7. Strict/matched/alternative-aware comparison plot.

## 16. Expected Discussion Points

The discussion should address:

- LLMs are promising for schema design but require database-aware evaluation.
- Exact match is too strict for schema evaluation.
- Matched evaluation separates naming mismatch from structural error.
- Alternative-aware evaluation separates valid design variation from invalid design.
- FKs and relationship tables are likely more difficult than entity/table recovery.
- Prompting strategies may improve quality but increase cost.
- Validation-guided repair may be a practical direction for future tools.
- Local models may be useful if quality is acceptable and privacy/cost matter.

## 17. Claims to Validate Carefully

The paper should only claim what the results support.

Avoid saying:

- LLMs automate database design completely.
- A single model is best for all cases.
- Prompting solves all errors.
- Local models are always competitive.
- Exact match is useless.

Safer claims:

- Exact match alone is insufficient.
- Database-aware evaluation reveals different types of error.
- Alternative-aware evaluation is necessary for discretionary design decisions.
- Prompt condition effects vary across models and datasets.
- LLM-based design requires validation and repair mechanisms.

## 18. Final Narrative

The final experimental narrative should follow this logic:

1. LLMs can generate plausible relational schemas.
2. Strict evaluation alone underestimates some valid outputs.
3. Structure-aware matching identifies naming-equivalent schemas.
4. Alternative-aware evaluation identifies valid non-preferred designs.
5. Remaining errors reveal true semantic design failures.
6. Prompt strategies and repair can reduce some errors.
7. Cost and latency matter when scaling the benchmark.
8. Therefore, evaluating LLMs for database design requires specialized metrics and reproducible pipelines.
