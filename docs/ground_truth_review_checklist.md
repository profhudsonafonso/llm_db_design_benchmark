# Ground Truth Review Checklist

This checklist is used to review expert-defined ground truth files before running the LLM experiments.

Each dataset must contain:

- `datasets/<dataset>/ground_truth/conceptual_eer.yaml`
- `datasets/<dataset>/ground_truth/logical_relational_gold.json`

The goal of this checklist is to verify completeness, consistency, and evaluation readiness.

## 1. Dataset-Level Review

For each dataset, verify:

| Item | Check |
|---|---|
| Dataset folder exists | `datasets/<dataset>/` exists |
| Ground truth folder exists | `datasets/<dataset>/ground_truth/` exists |
| Conceptual EER file exists | `conceptual_eer.yaml` exists |
| Logical gold file exists | `logical_relational_gold.json` exists |
| Prompt input folder exists | `datasets/<dataset>/prompt_inputs/` exists or can be generated |
| Dataset complexity is declared | low, medium, or high |
| Expert notes are included | assumptions, ambiguities, exclusions |

## 2. Conceptual EER YAML Review

File:

- `conceptual_eer.yaml`

### 2.1 Metadata

Verify:

- schema ID is present;
- dataset name is present;
- dataset complexity is present;
- version is present;
- creation/review information is present when possible;
- source description is present;
- notes are present when relevant.

### 2.2 Model Scope

Verify:

- included entities are listed;
- excluded entities are listed or explicitly empty;
- inclusion criteria are documented;
- exclusion criteria are documented;
- scope matches the intended benchmark dataset.

### 2.3 Entities

For each entity, verify:

| Item | Check |
|---|---|
| Entity ID | present and unique |
| Entity name | present and stable |
| Entity type | regular, weak, associative, or abstract |
| Description | present |
| Aliases | present or empty |
| Attributes | present |
| Primary identifier | present |
| Candidate identifiers | present or empty |
| Alternate keys | present or empty |
| Weak entity block | present, even if `is_weak: false` |

### 2.4 Attributes

For each attribute, verify:

| Item | Check |
|---|---|
| Attribute name | present |
| Data type | present |
| Required/nullable | declared |
| Attribute kind | simple, composite, multivalued, or derived |
| Cardinality | min and max declared |
| Identifier flag | declared |
| Source field | present when known |
| Notes | present when needed |

Special checks:

- multivalued attributes must be clearly marked;
- composite attributes must list components;
- derived attributes must be marked and explained;
- identifier attributes must match the entity identifier.

### 2.5 Relationships

For each relationship, verify:

| Item | Check |
|---|---|
| Relationship ID | present and unique |
| Relationship name | present and stable |
| Relationship type | association, containment, identifying, etc. |
| Arity | binary, ternary, n-ary, or recursive |
| Description | present |
| Participants | present |
| Role names | present |
| Cardinality min/max | present for each participant |
| Participation | mandatory or optional |
| Relationship attributes | present or explicitly empty |
| Constraints | present |

Special checks:

- 1:1, 1:N, and M:N relationships must be clear;
- relationship attributes must be explicitly listed;
- identifying relationships must be marked;
- recursive relationships must preserve role names;
- ternary/n-ary relationships must include all participants.

### 2.6 Weak Entities

For each weak entity, verify:

- owner entity is declared;
- identifying relationship is declared;
- partial key is declared;
- full identifier can be derived;
- participation in identifying relationship is clear.

### 2.7 Specialization and Generalization

For each specialization/generalization, verify:

| Item | Check |
|---|---|
| Supertype | present |
| Subtypes | present |
| Completeness | total or partial |
| Disjointness | disjoint or overlapping |
| Inheritance type | single or multiple |
| Subtype predicates | present when applicable |
| Notes | present when needed |

Special checks:

- abstract supertypes must be marked;
- overlapping subtypes must be explicitly allowed;
- total specialization must be distinguished from partial specialization.

### 2.8 Global Constraints

Verify:

- key constraints are listed;
- participation constraints are listed;
- cardinality constraints are listed;
- inclusion/exclusion constraints are listed or empty;
- business rules are listed or empty.

## 3. Logical Relational Gold JSON Review

File:

- `logical_relational_gold.json`

### 3.1 Metadata

Verify:

- schema ID matches conceptual file;
- dataset name matches conceptual file;
- complexity level matches conceptual file;
- target model is relational;
- version is present;
- notes are present.

### 3.2 Tables

For each table, verify:

| Item | Check |
|---|---|
| Table name | present and stable |
| Description | present |
| Origin conceptual elements | present |
| Mapping rule | present |
| Columns | present |
| Primary key | present |
| Foreign keys | present or empty |
| Unique constraints | present or empty |
| Check constraints | present or empty |
| Notes | present when needed |

Special checks:

- every table must have a primary key;
- every column must have a name and data type;
- nullable/required values must be consistent;
- source conceptual entity/attribute should be filled when possible;
- table names should be consistent with conceptual elements or documented aliases.

### 3.3 Columns

For each column, verify:

| Item | Check |
|---|---|
| Column name | present |
| Data type | present |
| Nullable | true or false |
| Required | true or false |
| Primary key flag | true or false |
| Foreign key flag | true or false |
| Unique flag | true or false |
| Source conceptual attribute | present when applicable |
| Source conceptual entity | present when applicable |

Special checks:

- PK columns must be marked as `is_primary_key: true`;
- FK columns must be marked as `is_foreign_key: true`;
- mandatory relationship FKs should be nullable false;
- optional relationship FKs may be nullable true.

### 3.4 Primary Keys

Verify:

- every table has a `primary_key` block;
- primary key columns exist in the table columns;
- composite keys list all columns;
- weak entities include owner key plus partial key when applicable;
- relationship tables have correct composite or declared keys.

### 3.5 Foreign Keys

For each foreign key, verify:

| Item | Check |
|---|---|
| FK name | present |
| Local columns | exist in local table |
| Referenced table | exists |
| Referenced columns | exist in referenced table |
| Source relationship | present |
| Mandatory | true or false |
| Nullable | consistent with participation |
| Notes | present when needed |

Special checks:

- no FK should reference a missing table;
- no FK should reference a missing column;
- FK direction must match relationship cardinality;
- 1:N relationships normally place FK on the N side;
- 1:1 relationships must justify FK placement;
- M:N relationships must use relationship tables.

### 3.6 Relationship Tables

For each relationship table, verify:

- source relationship is declared;
- participating entities are listed;
- table exists in `tables`;
- FKs point to all participating entities;
- relationship attributes are included;
- primary key is correct;
- relationship type is declared.

Special checks:

- M:N relationships should normally have relationship tables;
- ternary/n-ary relationships should have relationship tables;
- associative entities should be represented consistently.

### 3.7 Specialization Mapping

For each specialization/generalization, verify:

- specialization ID is present;
- supertype is present;
- subtypes are present;
- mapping strategy is declared;
- affected tables are listed;
- discriminator column is present when single-table inheritance is used;
- class-table inheritance uses supertype PK as subtype PK/FK;
- completeness/disjointness constraints are documented.

## 4. Preferred and Alternative Valid Mappings

Verify the `mapping_alternatives` section.

For each discretionary mapping decision, check:

| Item | Check |
|---|---|
| Alternative group ID | present and unique |
| Conceptual element ID | present |
| Conceptual element name | present |
| Conceptual element type | present |
| Decision context | explained |
| Preferred mapping | present |
| Acceptable mappings | present or empty |
| Not allowed mappings | present or empty |
| Rationale | present for each option |

### 4.1 Preferred Mapping

Verify:

- mapping type is declared;
- expected tables are listed;
- expected columns are listed when relevant;
- expected FKs are listed when relevant;
- expected constraints are listed when relevant;
- rationale explains why it is preferred.

### 4.2 Acceptable Mappings

Verify:

- each acceptable alternative is logically valid;
- conditions are explicitly described;
- expected tables/columns/FKs are listed;
- rationale explains why it should not be penalized as wrong.

### 4.3 Not Allowed Mappings

Verify:

- invalid options are documented when relevant;
- rationale explains why they violate EER semantics;
- examples include disconnected tables, wrong FK direction, or M:N mapped without a relationship table.

## 5. Mapping Decisions

Verify:

- every important mapping decision has an ID;
- conceptual element is referenced;
- decision type is declared;
- status is `preferred`, `acceptable`, or `not_allowed`;
- affected tables are listed;
- affected columns are listed;
- affected FKs are listed;
- alternative group ID is linked when applicable.

## 6. Evaluation Units

Verify:

- expected entities are listed;
- expected attributes are listed;
- expected primary keys are listed;
- expected foreign keys are listed;
- expected relationship tables are listed;
- expected specialization mappings are listed;
- expected mapping decisions are listed;
- alternative mapping groups are listed.

These units help the evaluator compare LLM outputs consistently.

## 7. Cross-File Consistency

Check consistency between `conceptual_eer.yaml` and `logical_relational_gold.json`.

| Conceptual element | Logical expectation |
|---|---|
| Regular entity | table or documented merged mapping |
| Weak entity | table with owner FK and partial key |
| Multivalued attribute | separate table or justified alternative |
| 1:1 relationship | FK, table merge, or relationship table with rationale |
| 1:N relationship | FK on correct side or justified alternative |
| M:N relationship | relationship table |
| Relationship attribute | preserved in relationship table or FK-side table |
| Specialization | documented relational strategy |

## 8. Common Problems to Flag

Flag the ground truth if you find:

- entity without identifier;
- relationship without cardinality;
- relationship participant without role name;
- relationship with ambiguous max cardinality;
- table without primary key;
- FK referencing missing table;
- FK referencing missing column;
- M:N relationship without relationship table;
- relationship attribute omitted from logical schema;
- alternative mapping without rationale;
- acceptable mapping that is not actually valid;
- not allowed mapping missing for ambiguous cases;
- mismatch between conceptual names and logical origin fields;
- missing expert notes for ambiguous decisions.

## 9. Review Status Template

Use the following status table for each dataset.

| Review Area | Status | Notes |
|---|---|---|
| Dataset metadata | pending |  |
| Conceptual entities | pending |  |
| Conceptual attributes | pending |  |
| Conceptual relationships | pending |  |
| Cardinalities | pending |  |
| Participation constraints | pending |  |
| Weak entities | pending |  |
| Specialization/generalization | pending |  |
| Logical tables | pending |  |
| Logical columns | pending |  |
| Primary keys | pending |  |
| Foreign keys | pending |  |
| Relationship tables | pending |  |
| Mapping decisions | pending |  |
| Alternative mappings | pending |  |
| Evaluation units | pending |  |
| Cross-file consistency | pending |  |
| Ready for prompt generation | pending |  |
| Ready for LLM execution | pending |  |

Allowed status values:

- pending;
- ok;
- needs_fix;
- not_applicable.

## 10. Final Decision

After review, assign one of the following decisions:

| Decision | Meaning |
|---|---|
| approved | Ready for prompt generation and experiments |
| approved_with_minor_notes | Can be used, but minor notes should be documented |
| needs_revision | Must be corrected before experiments |
| rejected | Not usable in current form |

## 11. Reviewer Notes

For each issue found, record:

- dataset;
- file;
- location;
- issue type;
- severity;
- description;
- suggested correction;
- whether specialist input is needed.

