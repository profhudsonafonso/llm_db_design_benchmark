# Ground Truth Guidelines for the LLM Database Design Benchmark

This document explains how to create the expert-defined ground truths used in the benchmark.

Each dataset must have two ground truth files:

- `datasets/<dataset>/ground_truth/conceptual_eer.yaml`
- `datasets/<dataset>/ground_truth/logical_relational_gold.json`

## 1. Goal

The goal is to evaluate how well Large Language Models support conceptual-to-logical database design tasks.

The LLM receives a textual EER representation as input and must generate a logical relational schema.

The LLM must not see the logical ground truth.

## 2. Files to be Created by the Expert

### 2.1 Conceptual EER Ground Truth

File:

- `conceptual_eer.yaml`

This file represents the conceptual EER model.

It must describe:

- entities;
- attributes;
- identifiers;
- weak entities;
- relationships;
- relationship attributes;
- cardinalities;
- participation constraints;
- specialization/generalization;
- relevant semantic constraints.

This file is used to generate the input given to the LLMs.

### 2.2 Logical Relational Gold Standard

File:

- `logical_relational_gold.json`

This file represents the expected logical relational schema.

It must describe:

- tables;
- columns;
- primary keys;
- foreign keys;
- unique constraints;
- relationship tables;
- inheritance mapping decisions;
- mapping notes;
- valid alternative mappings when more than one logical implementation is acceptable.

This file is used only for evaluation.

## 3. Important Methodological Decision: Preferred vs. Acceptable Mappings

Conceptual-to-logical database design does not always have a single correct answer.

Some EER constructs may be transformed into a relational schema in more than one valid way. For example, depending on cardinality and participation constraints, a relationship may be implemented as:

- a separate relationship table;
- a foreign key column;
- a table merge in specific one-to-one cases.

Therefore, the benchmark uses one main preferred gold schema plus local alternative valid mappings for discretionary cases.

The expert must define:

1. the preferred mapping;
2. other acceptable mappings, if any;
3. mappings that should not be used;
4. a short rationale for each decision.

This prevents penalizing an LLM as incorrect when it generates a logically valid alternative that differs from the preferred expert choice.

## 4. When to Register Alternative Mappings

The expert should register alternatives when the EER construct allows more than one valid relational implementation.

Common cases include:

- binary 1:1 relationships;
- binary 1:N relationships where a separate relationship table may be acceptable;
- optional relationships where nullable FK placement may vary;
- relationships with attributes;
- associative entities;
- weak entities with alternative key representation;
- specialization/generalization mapping strategies;
- multivalued attributes with alternative naming or key strategies.

The expert does not need to create a full second schema. Only the local discretionary mapping decision must be documented.

## 5. Mapping Status Values

Use the following status values:

| Status | Meaning |
|---|---|
| preferred | The expert's main recommended implementation. |
| acceptable | A logically valid alternative implementation. |
| not_allowed | An implementation that should be considered incorrect. |

## 6. Example of Alternative Mapping Documentation

Example for a relationship between `Pessoa` and `Compra`:

- preferred mapping: relationship table `PessoaCompra`;
- acceptable mapping: foreign key in `Compra`, if the cardinality permits it;
- not allowed: merging `Pessoa` and `Compra` into one table, if they are independent entity types.

In the JSON template, this must be documented in the `mapping_alternatives` section.

## 7. Mandatory Conceptual Elements

The expert must fill the following elements whenever they exist in the dataset.

### 7.1 Entities

For each entity, specify:

- entity name;
- entity type: regular, weak, associative, or abstract;
- attributes;
- primary identifier;
- candidate identifiers, if any;
- description;
- source table, file, or collection.

### 7.2 Attributes

For each attribute, specify:

- name;
- data type;
- whether it is required or optional;
- whether it is simple, composite, multivalued, or derived;
- whether it belongs to a key;
- source field, if applicable.

### 7.3 Relationships

For each relationship, specify:

- relationship name;
- arity: binary, ternary, n-ary, or recursive;
- participating entities;
- role names;
- minimum cardinality;
- maximum cardinality;
- participation: mandatory or optional;
- relationship attributes, if any;
- whether it is identifying;
- relationship semantics.

### 7.4 Weak Entities

For weak entities, specify:

- owner entity;
- identifying relationship;
- partial key;
- full identifier after mapping.

### 7.5 Specialization and Generalization

For each specialization/generalization, specify:

- supertype;
- subtypes;
- completeness: total or partial;
- disjointness: disjoint or overlapping;
- inheritance type: single or multiple;
- subtype predicate, when applicable.

## 8. Logical Relational Ground Truth

The logical relational gold standard must represent the preferred target schema.

For each table, specify:

- table name;
- origin conceptual elements;
- columns;
- primary key;
- foreign keys;
- unique constraints;
- check constraints, if any;
- mapping rule used.

For each foreign key, specify:

- local columns;
- referenced table;
- referenced columns;
- conceptual relationship that produced the FK;
- whether the FK is mandatory or nullable.

For each relationship table, specify:

- source relationship;
- participating entities;
- primary key;
- foreign keys;
- relationship attributes.

For each specialization, specify the chosen relational mapping strategy:

- single-table inheritance;
- class-table inheritance;
- concrete-table inheritance;
- other.

## 9. Alternative Valid Mappings

For each discretionary mapping decision, fill the `mapping_alternatives` section.

Each alternative group must include:

- conceptual element ID;
- conceptual element name;
- conceptual element type;
- preferred mapping;
- acceptable mappings;
- not allowed mappings;
- rationale.

The evaluator will classify an LLM output as:

| Classification | Meaning |
|---|---|
| preferred_correct | The LLM followed the preferred gold mapping. |
| valid_alternative | The LLM generated an acceptable but non-preferred mapping. |
| invalid_mapping | The LLM used a mapping explicitly marked as not allowed. |
| missing_mapping | The LLM omitted the required mapping. |
| hallucinated_mapping | The LLM invented a mapping not supported by the EER input. |

## 10. Rules for the Expert

Use stable and consistent names.

Do not invent attributes that are not supported by the dataset or the conceptual interpretation.

When there is ambiguity, record the decision in `expert_notes`.

Use `unknown` only when the information cannot be inferred reliably.

Use `not_applicable` when a field does not apply.

Prefer explicit cardinalities using `min` and `max`.

Use `many` for unbounded maximum cardinality.

When more than one logical implementation is valid, do not create multiple complete schemas. Instead, document the alternatives in `mapping_alternatives`.

## 11. Final Check Before Submission

Before sending the ground truth files, verify:

- all entities have identifiers;
- all relationships have participants;
- all participants have min/max cardinalities;
- all weak entities have owners and partial keys;
- all specialization structures have completeness and disjointness;
- all logical tables have primary keys;
- all foreign keys reference existing tables and columns;
- all mapping decisions are documented;
- all discretionary mappings have preferred, acceptable, and not allowed options when applicable.

## Ground Truth Review

After the expert prepares the ground truth files, each dataset must be reviewed using:

- `docs/ground_truth_review_checklist.md`

The checklist verifies whether the conceptual EER file and the logical relational gold file are complete, consistent, and ready for LLM experiments.

A dataset should only be enabled in `configs/experiment_matrix.yaml` after this review.

