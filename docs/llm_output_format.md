# LLM Output Format

This document defines the expected output format for all LLM-generated relational schemas.

All LLMs must return a valid JSON object.

The JSON must contain:

- schema metadata;
- tables;
- columns;
- primary keys;
- foreign keys;
- relationship tables;
- specialization mapping, when applicable;
- mapping decisions.

The output format follows the same structure as:

```text
docs/logical_relational_gold_template.json
```

The LLM must not include explanations outside the JSON object.

## Required Top-Level Fields

```json
{
  "schema_metadata": {},
  "tables": [],
  "relationship_tables": [],
  "specialization_mapping": [],
  "mapping_decisions": []
}
```

## Required Table Fields

Each table must include:

```json
{
  "name": "",
  "description": "",
  "origin": {
    "conceptual_elements": [],
    "mapping_rule": "",
    "notes": ""
  },
  "columns": [],
  "primary_key": {
    "name": "",
    "columns": []
  },
  "foreign_keys": [],
  "unique_constraints": [],
  "check_constraints": [],
  "notes": ""
}
```

## Validation Requirements

The generated JSON must be checked for:

- valid JSON syntax;
- presence of required top-level fields;
- valid table names;
- valid column names;
- primary key definition for each table;
- valid foreign key references;
- consistency with the conceptual EER input;
- consistency with relationship cardinalities;
- consistency with specialization/generalization mapping, when applicable.

## Output Rule

The LLM must return only the JSON object.

It must not return:

- Markdown explanations;
- comments before or after the JSON;
- natural language descriptions outside the JSON;
- code fences around the JSON.
