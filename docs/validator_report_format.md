# Validator Report Format

This document defines the structure of the deterministic validation report used in the validation-guided repair condition.

The validator compares an LLM-generated relational JSON against the expected structure and produces a machine-readable error report.

## Expected Report Format

```json
{
  "dataset": "",
  "model": "",
  "prompt_condition": "",
  "json_valid": true,
  "errors": [
    {
      "error_id": "E001",
      "error_type": "",
      "severity": "",
      "location": "",
      "expected": "",
      "found": "",
      "message": ""
    }
  ],
  "summary": {
    "num_errors": 0,
    "num_warnings": 0,
    "missing_entities": 0,
    "missing_attributes": 0,
    "missing_primary_keys": 0,
    "missing_foreign_keys": 0,
    "wrong_foreign_keys": 0,
    "hallucinated_elements": 0
  }
}
```

## Severity Levels

| Severity | Meaning |
|---|---|
| critical | Invalid JSON or impossible schema structure |
| major | Missing table, missing primary key, missing foreign key, or wrong FK target |
| minor | Naming mismatch, optional attribute mismatch, or incomplete metadata |

## Use in C4

In C4, the report is sent back to the LLM together with:

1. the original textual EER input;
2. the previous LLM-generated relational JSON;
3. the deterministic validation report.

The LLM must repair the previous output based only on the report and the original EER input.

## Repair Rule

The LLM should:

- preserve correct parts of the previous output;
- correct reported errors;
- avoid introducing new unsupported schema elements;
- return only valid JSON.
