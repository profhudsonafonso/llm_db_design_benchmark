# Toy Pipeline Validation

This document summarizes the toy example used to validate the benchmark pipeline before running the real experiments on Chinook, IMDb, and Yelp.

The toy example is intentionally small, but it covers key methodological cases required by the benchmark:

- naming mismatch;
- similarity and structure-aware matching;
- preferred mapping;
- valid non-preferred alternative mapping;
- invalid mapping;
- strict, matched, and alternative-aware evaluation;
- strict, matched, and alternative-aware weighted structural Manhattan distances.

## 1. Goal

The goal of the toy example is to validate whether the benchmark pipeline can distinguish between:

1. real schema design errors;
2. harmless naming differences;
3. valid alternative logical mappings;
4. invalid logical mappings.

This is important because conceptual-to-logical database design may not have a single valid implementation, and LLMs may generate semantically equivalent schemas using different names.

## 2. Pipeline Tested

The toy example validates the following pipeline:

1. raw LLM-style output;
2. normalization with `scripts/normalize_output.py`;
3. normalized relational schema;
4. evaluation with `scripts/evaluate_schema.py`;
5. strict evaluation;
6. matched evaluation;
7. alternative-aware evaluation;
8. structural Manhattan distance comparison.

## 3. Toy Schema Summary

The toy schema contains four conceptual entities:

| Entity | Meaning |
|---|---|
| Customer | A customer who places orders |
| CustomerProfile | Optional profile information for a customer |
| Order | A purchase order placed by a customer |
| Product | A product that can appear in orders |

The schema contains three relationships:

| Relationship | Type | Preferred Mapping |
|---|---|---|
| CustomerPlacesOrder | 1:N | Foreign key `customer_id` in `Order` |
| OrderContainsProduct | M:N with attribute `quantity` | Relationship table `OrderProduct` |
| CustomerHasProfile | 1:1 | Separate `CustomerProfile` table with `customer_id` as PK and FK |

The relationship `CustomerHasProfile` also has one acceptable alternative:

| Alternative | Meaning |
|---|---|
| Merge profile attributes into `Customer` | Add `bio` and `birth_date` directly to `Customer` |

## 4. Toy Outputs

Three toy outputs were created.

| Output file | Purpose |
|---|---|
| `llm_outputs/toy_example/gpt_c1_raw.txt` | Tests naming mismatch |
| `llm_outputs/toy_example/gpt_c1_valid_alternative_raw.txt` | Tests valid non-preferred mapping |
| `llm_outputs/toy_example/gpt_c1_invalid_profile_raw.txt` | Tests invalid mapping |

## 5. Case 1 — Naming Mismatch

In this case, the preferred gold schema contains the relationship table:

| Gold table |
|---|
| `OrderProduct` |

The LLM-style output generates:

| Generated table |
|---|
| `OrdProd` |

Although the name differs, the generated table has the correct structure:

- `order_id`;
- `product_id`;
- `quantity`;
- foreign key to `Order`;
- foreign key to `Product`;
- composite primary key.

### Results

| Metric | Value |
|---|---:|
| strict_f1 | 0.7333 |
| matched_f1 | 1.0000 |
| alternative_aware_f1 | 1.0000 |
| strict_distance | 0.5455 |
| matched_distance | 0.0000 |
| alternative_aware_distance | 0.0000 |
| distance_reduction_from_matching | 0.5455 |
| distance_reduction_from_alternatives | 0.0000 |

### Interpretation

The strict evaluation penalizes the naming difference between `OrderProduct` and `OrdProd`.

The matched evaluation recognizes that the generated table is structurally equivalent to the preferred gold table.

This confirms that the benchmark should report both strict and matched metrics.

## 6. Case 2 — Valid Alternative Mapping

In this case, the LLM-style output does not create the preferred `CustomerProfile` table.

Instead, it merges the profile attributes into the `Customer` table:

| Merged attributes |
|---|
| `Customer.bio` |
| `Customer.birth_date` |

This differs from the preferred gold schema, but it is documented as an acceptable alternative.

### Results

| Metric | Value |
|---|---:|
| strict_f1 | 0.5714 |
| matched_f1 | 0.8571 |
| alternative_aware_f1 | 1.0000 |
| preferred_mapping_accuracy | 0.0000 |
| valid_mapping_accuracy | 1.0000 |
| alternative_mapping_rate | 1.0000 |
| invalid_mapping_rate | 0.0000 |
| strict_distance | 0.7273 |
| matched_distance | 0.1818 |
| alternative_aware_distance | 0.0000 |
| distance_reduction_from_matching | 0.5455 |
| distance_reduction_from_alternatives | 0.1818 |

### Interpretation

The LLM-style output does not follow the expert's preferred mapping, but it produces a valid logical alternative.

The alternative-aware evaluation correctly removes the residual penalty and reports a perfect score.

This confirms that the benchmark should not treat every deviation from the preferred gold schema as an error.

## 7. Case 3 — Invalid Mapping

In this case, the LLM-style output creates a `CustomerProfile` table, but removes the foreign key to `Customer`.

This creates a disconnected profile table, which is not a valid implementation of the `CustomerHasProfile` relationship.

### Results

| Metric | Value |
|---|---:|
| strict_f1 | 0.7119 |
| matched_f1 | 0.9831 |
| alternative_aware_f1 | 0.9831 |
| preferred_mapping_accuracy | 0.0000 |
| valid_mapping_accuracy | 0.0000 |
| alternative_mapping_rate | 0.0000 |
| invalid_mapping_rate | 1.0000 |
| strict_distance | 0.6667 |
| matched_distance | 0.1212 |
| alternative_aware_distance | 0.1212 |
| distance_reduction_from_matching | 0.5455 |
| distance_reduction_from_alternatives | 0.0000 |

### Interpretation

The matched score is high because most of the schema is correct.

However, the mapping is invalid because `CustomerProfile` is disconnected from `Customer`.

The alternative-aware score does not remove the penalty because this is not an acceptable alternative.

This confirms that the evaluator does not simply forgive any deviation. It accepts documented valid alternatives, but still penalizes invalid mappings.

## 8. Summary of Findings

| Case | strict_f1 | matched_f1 | alternative_aware_f1 | Main Interpretation |
|---|---:|---:|---:|---|
| Naming mismatch | 0.7333 | 1.0000 | 1.0000 | Name differs, structure is correct |
| Valid alternative | 0.5714 | 0.8571 | 1.0000 | Non-preferred but valid design |
| Invalid mapping | 0.7119 | 0.9831 | 0.9831 | Mostly correct schema, but invalid relationship mapping |

## 9. Methodological Implication

The toy example validates the need for three evaluation modes:

| Mode | Purpose |
|---|---|
| strict | Measures exact reproduction of the preferred gold schema |
| matched | Measures structural equivalence despite naming variation |
| alternative_aware | Measures logical validity considering expert-documented alternatives |

The toy example also validates the need for three distance measures:

| Distance | Purpose |
|---|---|
| strict distance | Captures apparent errors without structural matching |
| matched distance | Removes penalties caused by naming mismatch |
| alternative-aware distance | Removes penalties caused by valid non-preferred mappings |

## 10. Use in the Paper

This toy validation can support the methodology or appendix by showing why the benchmark reports more than a single F1-score.

The toy example demonstrates that:

- exact name matching can overestimate errors;
- similarity and structure-aware matching reduces false errors caused by naming differences;
- valid alternatives must be treated separately from invalid mappings;
- weighted structural Manhattan distance helps distinguish superficial mismatch from structural design mistakes.

## 11. Repository Locations

Toy dataset:

- `datasets/toy_example/`

Toy LLM-style outputs:

- `llm_outputs/toy_example/`

Normalization results:

- `results/normalization_runs/`

Evaluation results:

- `results/evaluation_runs/`

Scripts:

- `scripts/normalize_output.py`
- `scripts/evaluate_schema.py`
