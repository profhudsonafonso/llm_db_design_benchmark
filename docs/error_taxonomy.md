# Error Taxonomy

This document defines the error categories used in the benchmark.

The taxonomy is used to evaluate LLM-generated relational schemas against the expert-defined logical relational gold standard.

## Main Error Categories

| Error Type | Description |
|---|---|
| invalid_json | The model output is not valid JSON |
| missing_table | An expected table is absent |
| hallucinated_table | The model creates a table not supported by the EER input |
| missing_attribute | An expected attribute is absent |
| hallucinated_attribute | The model creates an unsupported attribute |
| wrong_primary_key | The primary key is incorrect |
| missing_primary_key | A table has no primary key |
| missing_foreign_key | An expected foreign key is absent |
| wrong_foreign_key_target | A foreign key points to the wrong table or column |
| wrong_relationship_table | A relationship table is missing or incorrectly generated |
| cardinality_mapping_error | The mapping does not respect relationship cardinality |
| specialization_mapping_error | The inheritance or generalization mapping is incorrect |
| naming_mismatch | The schema element is semantically correct but named inconsistently |
| nullable_constraint_error | Mandatory or optional participation is mapped incorrectly |
| unsupported_extra_constraint | The model adds a constraint not supported by the EER input |

## Error Groups

Errors are grouped into:

- structural errors;
- attribute errors;
- key errors;
- relationship errors;
- constraint errors;
- hallucination errors;
- formatting errors.

## Structural Errors

Structural errors affect the existence of tables and relationship tables.

Examples:

- missing expected table;
- extra hallucinated table;
- wrong associative table;
- wrong table created for a 1:N relationship.

## Attribute Errors

Attribute errors affect columns and properties.

Examples:

- missing expected attribute;
- extra unsupported attribute;
- wrong data type;
- wrong nullable value;
- wrong handling of multivalued attributes.

## Key Errors

Key errors affect primary keys, candidate keys, and unique constraints.

Examples:

- missing primary key;
- incorrect primary key;
- missing composite key;
- wrong unique constraint.

## Relationship Errors

Relationship errors affect foreign keys and relationship tables.

Examples:

- missing foreign key;
- wrong foreign key target;
- wrong FK column;
- wrong relationship table;
- relationship attribute placed in the wrong table.

## Constraint Errors

Constraint errors affect cardinality, participation, and specialization/generalization decisions.

Examples:

- mandatory participation mapped as nullable;
- optional participation mapped as not nullable;
- many-to-many relationship not mapped as relationship table;
- total specialization mapped as partial;
- disjoint specialization mapped as overlapping.

## Hallucination Errors

Hallucination errors happen when the model creates elements not supported by the conceptual EER input.

Examples:

- invented table;
- invented column;
- invented FK;
- invented relationship;
- invented constraint.

## Use in Evaluation

The taxonomy is used to produce:

- per-component scores;
- hallucination rate;
- omission rate;
- FK error rate;
- repair gain;
- error reduction after validation-guided repair;
- new error rate after repair.
