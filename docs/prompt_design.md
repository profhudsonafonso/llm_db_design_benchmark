# Prompt Design

This document describes the prompting strategies used in the LLM Database Design Benchmark.

The benchmark evaluates how Large Language Models support conceptual-to-logical database design tasks. The input is a textual EER schema, and the expected output is a logical relational schema in JSON format.

## Prompting Conditions

The benchmark uses four experimental conditions.

| Condition | Name | Description |
|---|---|---|
| C1 | Basic generation | The LLM receives only the textual EER input and generates the relational JSON schema directly. |
| C2 | Rule-augmented generation | The LLM receives the textual EER input plus explicit EER-to-relational mapping rules. |
| C3 | Self-check generation | The LLM generates the schema, checks its own output, and returns a final corrected JSON. |
| C4 | Validation-guided repair | The LLM first generates a relational JSON; a deterministic validator reports errors; the LLM then repairs the output using the validation report. |

## C1 — Basic Generation

In C1, the model receives the EER input and the required JSON output format.

This condition evaluates the model's direct ability to perform conceptual-to-logical schema mapping without explicit mapping rules.

Expected input:

- textual EER schema;
- required relational JSON output format.

Expected output:

- relational schema in valid JSON.

## C2 — Rule-Augmented Generation

In C2, the model receives the EER input, the required output format, and explicit EER-to-relational mapping rules.

This condition evaluates whether explicit design rules improve the generation of:

- tables;
- attributes;
- primary keys;
- foreign keys;
- relationship tables;
- inheritance mappings.

## C3 — Self-Check Generation

In C3, the model receives the same information as C2, but it is also instructed to review its own output before returning the final JSON.

The model must check whether:

- all entities were mapped;
- all attributes were included;
- all primary keys were defined;
- all expected foreign keys were created;
- relationship cardinalities were respected;
- specialization/generalization was handled correctly;
- the final answer is valid JSON.

The model must return only the final JSON.

## C4 — Validation-Guided Repair

In C4, the model receives three inputs:

1. the original textual EER schema;
2. its previous generated relational JSON;
3. a deterministic validation report.

The validation report identifies problems such as:

- invalid JSON;
- missing tables;
- missing attributes;
- missing primary keys;
- missing foreign keys;
- wrong foreign key targets;
- wrong relationship tables;
- cardinality mapping errors;
- specialization mapping errors;
- hallucinated elements.

The model must repair only the reported errors and return a corrected relational JSON.

This condition evaluates whether structured feedback helps the model improve its output.

## Prompt Files

The prompt files are stored in the `prompts/` folder.

Expected files:

- `prompts/prompt_1_basic.txt`
- `prompts/prompt_2_cardinality_rules.txt`
- `prompts/prompt_3_rules_self_check.txt`
- `prompts/prompt_4_validation_guided_repair.txt`

## General Output Rules

For all prompting conditions, the model must:

- return only valid JSON;
- avoid explanations outside the JSON;
- avoid Markdown code fences;
- preserve names consistently;
- not invent unsupported entities, attributes, keys, or relationships;
- follow the required relational output format.

## Relation to the Evaluation Protocol

The four prompting conditions are evaluated using the same ground truth files:

- `datasets/<dataset>/ground_truth/conceptual_eer.yaml`
- `datasets/<dataset>/ground_truth/logical_relational_gold.json`

The conceptual EER file is used to generate the LLM input.

The logical relational gold file is used only for evaluation.

## Relation to C4 Validation-Guided Repair

The C4 condition depends on the deterministic validator and the validation report format.

Related files:

- `docs/validator_report_format.md`
- `docs/error_taxonomy.md`
- `docs/llm_output_format.md`
- `scripts/validation_report.py`

The validator does not replace the expert ground truth. It only produces structured feedback to guide the LLM repair step.

## Current Status

This document defines the prompt design protocol.

The detailed prompt templates are maintained separately in the `prompts/` folder.
