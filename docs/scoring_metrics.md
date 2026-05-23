# Scoring Metrics

This document defines the scoring strategy used in the LLM Database Design Benchmark.

The benchmark evaluates LLM-generated logical relational schemas against expert-defined logical relational ground truths.

The evaluation is designed to handle three important issues:

- exact matching may unfairly penalize valid outputs with different names;
- conceptual-to-logical mapping may have more than one valid relational implementation;
- schema errors have different structural severity.

Therefore, the benchmark uses:

- strict evaluation;
- similarity and structure-aware evaluation;
- preferred and alternative valid mapping evaluation;
- component-level Precision, Recall, and F1-score;
- hallucination and omission metrics;
- weighted structural distance based on Manhattan distance;
- repair metrics for the validation-guided repair condition.

## 1. Evaluation Inputs

The evaluator receives:

- the expert conceptual EER file: `conceptual_eer.yaml`;
- the expert logical relational gold file: `logical_relational_gold.json`;
- the LLM-generated relational JSON output;
- optional validation reports for the C4 condition.

The LLM output is compared against the logical relational gold standard.

## 2. Evaluation Units

The benchmark evaluates the following units:

- tables;
- columns;
- primary keys;
- candidate keys;
- foreign keys;
- relationship tables;
- relationship attributes;
- specialization/generalization mappings;
- mapping decisions;
- constraints.

Each unit may be evaluated under strict matching and under similarity/structure-aware matching.

## 3. Name Normalization

Before comparing names, the evaluator normalizes schema element names.

The normalization step should:

- lowercase names;
- remove spaces;
- remove underscores;
- remove hyphens;
- remove accents when applicable;
- remove repeated separators;
- optionally singularize/pluralize simple forms;
- optionally expand known aliases from expert notes.

Examples:

| Original name | Normalized name |
|---|---|
| PessoaCompra | pessoacompra |
| pessoa_compra | pessoacompra |
| Pessoa-Compra | pessoacompra |
| PESSOA COMPRA | pessoacompra |

Name normalization avoids unnecessary errors caused by formatting differences.

## 4. Strict Evaluation

Strict evaluation compares normalized names and structures directly.

An element is counted as correct only when it matches the expected element after normalization.

Strict evaluation is useful because it measures exact reproducibility of the preferred expert schema.

However, strict evaluation may over-penalize outputs that are semantically valid but use different naming conventions.

## 5. Similarity and Structure-Aware Evaluation

Similarity and structure-aware evaluation is used to avoid over-penalizing valid outputs with different names.

This evaluation mode uses two kinds of evidence:

- textual similarity;
- structural compatibility.

### 5.1 Textual Similarity

Textual similarity compares normalized names.

Possible algorithms include:

- Levenshtein similarity;
- Jaro-Winkler similarity;
- token sort ratio;
- token set ratio.

The implementation may use libraries such as RapidFuzz.

### 5.2 Structural Compatibility

Structural compatibility checks whether two schema elements play the same role.

For tables, structural evidence may include:

- same origin conceptual entity;
- same main attributes;
- same primary key structure;
- same foreign key endpoints;
- same participating entities for relationship tables.

For attributes, structural evidence may include:

- same source conceptual attribute;
- same data type;
- same table context;
- same key role.

For foreign keys, structural evidence is more important than name similarity.

A generated foreign key should be considered compatible when:

- its local table matches the expected table or a valid alternative table;
- its referenced table matches the expected referenced table;
- its referenced columns match the expected referenced columns;
- it represents the same conceptual relationship.

### 5.3 Matching Decision

An element may be matched when one of the following conditions holds:

- exact normalized name match;
- high textual similarity and compatible structure;
- moderate textual similarity and strong structural compatibility;
- explicit alias documented by the expert;
- match against an acceptable alternative mapping.

A name-only match should not be enough for high-impact structures such as foreign keys, relationship tables, and specialization mappings.

## 6. Naming Mismatch

A naming mismatch happens when the generated element is structurally correct but has a different name from the preferred gold element.

Naming mismatch should be recorded separately.

It should not automatically be counted as a structural error in the similarity/structure-aware evaluation.

Example:

| Gold element | LLM output | Classification |
|---|---|---|
| PessoaCompra | PesComp | naming_mismatch if structure is compatible |
| PersonPurchase | PurchasePerson | naming_mismatch if FKs and role semantics are compatible |

## 7. Preferred and Alternative Valid Mappings

Conceptual-to-logical mapping may have more than one valid implementation.

The benchmark therefore distinguishes:

- preferred mapping;
- acceptable alternative mapping;
- not allowed mapping.

The expert defines these cases in `mapping_alternatives`.

### 7.1 Mapping Classifications

| Classification | Meaning |
|---|---|
| preferred_correct | The output follows the preferred expert mapping. |
| valid_alternative | The output follows an acceptable non-preferred mapping. |
| invalid_mapping | The output uses a mapping marked as not allowed. |
| missing_mapping | The output omits a required mapping. |
| hallucinated_mapping | The output creates an unsupported mapping. |

A valid alternative should not be counted as a structural error, but it should be reported separately from the preferred mapping.

## 8. Precision, Recall, and F1-Score

For each component type, the evaluator computes:

Precision = TP / (TP + FP)

Recall = TP / (TP + FN)

F1 = 2 * Precision * Recall / (Precision + Recall)

Where:

- TP means expected element correctly generated;
- FP means generated element not supported by the gold standard or acceptable alternatives;
- FN means expected element missing from the generated schema.

If the denominator is zero, the metric should be reported as not applicable.

## 9. Component-Level Metrics

The benchmark reports Precision, Recall, and F1 for each component.

| Metric | Description |
|---|---|
| table_f1 | F1-score for tables |
| attribute_f1 | F1-score for columns/attributes |
| primary_key_f1 | F1-score for primary keys |
| foreign_key_f1 | F1-score for foreign keys |
| relationship_table_f1 | F1-score for relationship tables |
| specialization_mapping_score | Correctness of specialization/generalization mapping |
| mapping_decision_score | Correctness of conceptual-to-logical mapping decisions |

The global F1-score should be computed from the aggregated TP, FP, and FN counts across components.

## 10. Strict vs. Matched Scores

The benchmark reports two versions of the main scores.

| Score Type | Meaning |
|---|---|
| strict_score | Uses exact normalized matching. |
| matched_score | Uses similarity and structure-aware matching. |

This allows the paper to separate exact reproduction errors from semantically acceptable naming variations.

Example interpretation:

- low strict F1 but high matched F1 suggests many naming mismatches;
- low strict F1 and low matched F1 suggest structural design errors.

## 11. Hallucination and Omission Metrics

### 11.1 Hallucination Rate

Hallucination rate measures unsupported generated elements.

Hallucination Rate = hallucinated_elements / generated_elements

Examples of hallucinated elements:

- invented table;
- invented column;
- invented relationship table;
- invented foreign key;
- invented constraint.

### 11.2 Omission Rate

Omission rate measures expected elements that were not generated.

Omission Rate = missing_expected_elements / expected_elements

Examples of omitted elements:

- missing table;
- missing attribute;
- missing primary key;
- missing foreign key;
- missing relationship table.

## 12. Mapping-Specific Metrics

### 12.1 Preferred Mapping Accuracy

Preferred Mapping Accuracy = preferred_correct / total_mapping_decisions

This metric measures how often the LLM follows the expert's preferred design.

### 12.2 Valid Mapping Accuracy

Valid Mapping Accuracy = (preferred_correct + valid_alternative) / total_mapping_decisions

This metric measures how often the LLM produces a logically valid design, even if it differs from the expert's preferred design.

### 12.3 Alternative Mapping Rate

Alternative Mapping Rate = valid_alternative / total_mapping_decisions

This metric measures how often the LLM chooses a valid but non-preferred design.

### 12.4 Invalid Mapping Rate

Invalid Mapping Rate = invalid_mapping / total_mapping_decisions

This metric measures how often the LLM chooses a design explicitly marked as not allowed.

## 13. Constraint Violation Metrics

Constraint violations include:

- missing primary key;
- invalid foreign key reference;
- nullable foreign key for mandatory participation;
- missing unique constraint required by a one-to-one relationship;
- incorrect relationship table for many-to-many relationships;
- incorrect specialization/generalization mapping.

Constraint Violation Rate = constraint_violations / applicable_constraints

## 14. Structural Manhattan Distance

Precision, Recall, and F1 treat errors as binary matches or mismatches.

However, schema design errors have different severity.

For this reason, the benchmark also reports a structural distance based on Manhattan distance over an error vector.

### 14.1 Error Vector

For each generated schema, define an error vector:

E = [
  missing_tables,
  hallucinated_tables,
  missing_attributes,
  hallucinated_attributes,
  wrong_primary_keys,
  missing_foreign_keys,
  wrong_foreign_key_targets,
  wrong_relationship_tables,
  cardinality_errors,
  specialization_errors,
  invalid_mappings
]

### 14.2 Unweighted Structural Manhattan Distance

Unweighted Distance = sum(abs(E_i))

Because the values are non-negative error counts, this is equivalent to the sum of all error counts.

### 14.3 Weighted Structural Distance

Not all errors have the same severity.

The benchmark uses weighted distance:

Weighted Structural Distance = sum(weight_i * E_i)

Recommended initial weights:

| Error Category | Weight |
|---|---:|
| hallucinated_attribute | 1 |
| missing_attribute | 1 |
| missing_table | 2 |
| hallucinated_table | 2 |
| wrong_primary_key | 2 |
| missing_foreign_key | 3 |
| wrong_foreign_key_target | 4 |
| wrong_relationship_table | 4 |
| cardinality_error | 4 |
| specialization_error | 5 |
| invalid_mapping | 5 |

These weights can be adjusted, but changes must be documented.

### 14.4 Normalized Weighted Structural Distance

To compare datasets of different sizes, the weighted distance must be normalized.

Normalized Weighted Structural Distance = Weighted Structural Distance / Expected Structural Mass

Expected Structural Mass is a weighted estimate of the gold schema size.

Recommended initial formula:

Expected Structural Mass =
2 * expected_tables
+ 1 * expected_attributes
+ 2 * expected_primary_keys
+ 3 * expected_foreign_keys
+ 4 * expected_relationship_tables
+ 5 * expected_specialization_mappings
+ 5 * expected_mapping_decisions

A lower normalized distance means a better schema.

## 15. Alternative-Aware Minimum Distance

When the expert defines acceptable alternative mappings, the evaluator should avoid penalizing valid alternatives.

Therefore, distance can be computed as the minimum distance between the LLM output and the preferred or acceptable mappings.

Alternative-Aware Distance = min(distance(output, valid_mapping_i))

Where valid_mapping_i includes the preferred mapping and all acceptable alternatives.

This metric is important for discretionary conceptual-to-logical design decisions.

## 16. C4 Repair Metrics

The validation-guided repair condition C4 requires additional metrics.

### 16.1 Repair Gain

Repair Gain = Score_after_repair - Score_before_repair

The score may be global F1, matched F1, valid mapping accuracy, or normalized distance.

For distance-based metrics, improvement means distance reduction.

### 16.2 Error Reduction

Error Reduction = (Errors_before - Errors_after) / Errors_before

This measures the proportion of errors removed by the repair step.

### 16.3 New Error Rate

New Error Rate = New_errors_after_repair / Errors_after_repair

This measures whether the repair step introduces new errors.

### 16.4 Remaining Constraint Violation Rate

Remaining Constraint Violation Rate = Remaining_constraint_violations / Applicable_constraints

This measures how many structural violations remain after repair.

## 17. JSON Validity Rate

JSON Validity Rate = valid_json_outputs / total_outputs

This metric is important because invalid JSON cannot be directly evaluated without repair or normalization.

## 18. Reporting Requirements

Each experiment should report:

- strict Precision, Recall, and F1;
- matched Precision, Recall, and F1;
- component-level F1 scores;
- hallucination rate;
- omission rate;
- naming mismatch rate;
- preferred mapping accuracy;
- valid mapping accuracy;
- alternative mapping rate;
- invalid mapping rate;
- normalized weighted structural distance;
- C4 repair gain when applicable;
- JSON validity rate.

## 19. Interpretation Guide

High strict F1 and high matched F1:

- the model reproduced the preferred schema closely.

Low strict F1 but high matched F1:

- the model produced many naming variations but preserved structure.

High valid mapping accuracy but low preferred mapping accuracy:

- the model produced valid alternatives but did not follow the expert's preferred decisions.

Low normalized weighted structural distance:

- the schema has few severe structural errors.

High hallucination rate:

- the model invented unsupported schema elements.

High omission rate:

- the model failed to recover expected schema elements.

Positive repair gain in C4:

- validation feedback helped the model improve its schema.

Negative repair gain in C4:

- repair introduced more problems than it solved.
