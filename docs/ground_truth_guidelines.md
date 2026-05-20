# Ground Truth Guidelines for the LLM Database Design Benchmark

This document explains how to create the expert-defined ground truths used in the benchmark.

Each dataset must have two ground truth files:

```text
datasets/<dataset>/ground_truth/conceptual_eer.yaml
datasets/<dataset>/ground_truth/logical_relational_gold.json
```

## 1. Goal

The goal is to evaluate how well Large Language Models support conceptual-to-logical database design tasks.

The LLM receives a textual EER representation as input and must generate a logical relational schema.

The LLM must not see the logical ground truth.

## 2. Files to be Created by the Expert

### 2.1 Conceptual EER Ground Truth

File:

```text
conceptual_eer.yaml
```

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

```text
logical_relational_gold.json
```

This file represents the expected logical relational schema.

It must describe:

- tables;
- columns;
- primary keys;
- foreign keys;
- unique constraints;
- relationship tables;
- inheritance mapping decisions;
- mapping notes.

This file is used only for evaluation.

## 3. Why YAML for EER?

The benchmark uses YAML instead of Mermaid as the main conceptual representation because Mermaid does not fully capture all EER constructs.

Important EER constructs include:

- minimum and maximum cardinalities;
- total and partial participation;
- weak entities;
- identifying relationships;
- relationship attributes;
- specialization/generalization;
- disjoint and overlapping subtypes;
- total and partial specialization;
- composite and multivalued attributes.

Mermaid may be used only as an optional visualization.

## 4. Mandatory Conceptual Elements

The expert must fill the following elements whenever they exist in the dataset.

### 4.1 Entities

For each entity, specify:

- entity name;
- entity type: regular, weak, associative, or abstract;
- attributes;
- primary identifier;
- candidate identifiers, if any;
- description;
- source table, file, or collection.

### 4.2 Attributes

For each attribute, specify:

- name;
- data type;
- whether it is required or optional;
- whether it is simple, composite, multivalued, or derived;
- whether it belongs to a key;
- source field, if applicable.

### 4.3 Relationships

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

### 4.4 Weak Entities

For weak entities, specify:

- owner entity;
- identifying relationship;
- partial key;
- full identifier after mapping.

### 4.5 Specialization and Generalization

For each specialization/generalization, specify:

- supertype;
- subtypes;
- completeness: total or partial;
- disjointness: disjoint or overlapping;
- inheritance type: single or multiple;
- subtype predicate, when applicable.

### 4.6 Constraints

Specify relevant constraints such as:

- key constraints;
- uniqueness constraints;
- mandatory participation;
- cardinality constraints;
- inclusion constraints;
- exclusion constraints;
- semantic business rules.

## 5. Logical Relational Ground Truth

The logical relational gold standard must represent the correct target schema.

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

## 6. Rules for the Expert

Use stable and consistent names.

Do not invent attributes that are not supported by the dataset or the conceptual interpretation.

When there is ambiguity, record the decision in `expert_notes`.

Use `unknown` only when the information cannot be inferred reliably.

Use `not_applicable` when a field does not apply.

Prefer explicit cardinalities using `min` and `max`.

Use `many` for unbounded maximum cardinality.

## 7. Example Cardinality Format

```yaml
participants:
  - entity: Customer
    role: customer
    cardinality:
      min: 1
      max: 1
    participation: mandatory

  - entity: Order
    role: order
    cardinality:
      min: 0
      max: many
    participation: optional
```

## 8. Benchmark Datasets

The benchmark currently uses three datasets:

| Dataset | Complexity | Role |
|---|---|---|
| Chinook | Low | Small and controlled relational schema |
| IMDb | Medium | Real-world dataset with multiple interconnected entities |
| Yelp | High | Heterogeneous JSON-based dataset with complex relationships |

## 9. Final Check Before Submission

Before sending the ground truth files, verify:

- all entities have identifiers;
- all relationships have participants;
- all participants have min/max cardinalities;
- all weak entities have owners and partial keys;
- all specialization structures have completeness and disjointness;
- all logical tables have primary keys;
- all foreign keys reference existing tables and columns;
- all mapping decisions are documented.
