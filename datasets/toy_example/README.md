# Toy Example Dataset

This folder contains a minimal toy example used to test the benchmark pipeline before running experiments on Chinook, IMDb, and Yelp.

The toy example is intentionally small but includes important schema design situations:

- regular entities;
- one-to-many relationship;
- many-to-many relationship;
- relationship table;
- foreign keys;
- relationship attributes;
- one-to-one discretionary mapping;
- preferred and acceptable alternative mappings;
- naming mismatch in an LLM output.

## Purpose

The toy example is used to test:

- prompt input generation;
- raw LLM output normalization;
- name normalization;
- JSON extraction from Markdown/code fences;
- flattened table/column/PK/FK outputs;
- future schema evaluation scripts;
- alternative valid mapping logic.

## Files

Ground truth files:

- `ground_truth/conceptual_eer.yaml`
- `ground_truth/logical_relational_gold.json`

Prompt input:

- `prompt_inputs/eer_input_text.md`

Example LLM raw output:

- `llm_outputs/toy_example/gpt_c1_raw.txt`

## Conceptual Summary

The toy schema contains:

- `Customer`
- `CustomerProfile`
- `Order`
- `Product`

Relationships:

- `CustomerPlacesOrder`: one customer can place many orders.
- `OrderContainsProduct`: many-to-many relationship between orders and products, with relationship attribute `quantity`.
- `CustomerHasProfile`: one-to-one relationship between customer and customer profile.

## Discretionary Mapping Example

The relationship `CustomerHasProfile` can be mapped in more than one valid way.

Preferred mapping:

- create a separate `CustomerProfile` table with `customer_id` as both primary key and foreign key.

Acceptable alternative:

- merge profile attributes into the `Customer` table.

Not allowed:

- create an unrelated profile table without a foreign key to `Customer`.

## Normalizer Test

Example command:

`python scripts/normalize_output.py --input llm_outputs/toy_example/gpt_c1_raw.txt --dataset toy_example --model gpt --condition C1 --prompt-file prompts/prompt_1_basic.txt --input-eer-file datasets/toy_example/prompt_inputs/eer_input_text.md`

The outputs are saved under:

`results/normalization_runs/<run_id>/`

## Additional Toy Outputs

The toy example includes three raw LLM-style outputs.

| File | Purpose | Expected behavior |
|---|---|---|
| `llm_outputs/toy_example/gpt_c1_raw.txt` | Naming mismatch case | `OrderProduct` is generated as `OrdProd`; strict score should decrease, matched score should recover. |
| `llm_outputs/toy_example/gpt_c1_valid_alternative_raw.txt` | Valid alternative mapping case | `CustomerProfile` is merged into `Customer`; expected classification is `valid_alternative`. |
| `llm_outputs/toy_example/gpt_c1_invalid_profile_raw.txt` | Invalid mapping case | `CustomerProfile` exists but has no FK to `Customer`; expected classification is `invalid_mapping`. |

These files are used to test whether the evaluator distinguishes:

- naming mismatch;
- valid non-preferred mapping;
- invalid mapping.
