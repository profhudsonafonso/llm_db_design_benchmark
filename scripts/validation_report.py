"""
Validation report utilities for the LLM Database Design Benchmark.

This module generates deterministic validation reports for LLM-generated
relational schemas.

The report is used in the C4 condition: validation-guided repair.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class ValidationError:
    """Single validation error found in an LLM-generated schema."""

    error_id: str
    error_type: str
    severity: str
    location: str
    expected: Any
    found: Any
    message: str


def build_validation_report(
    dataset: str,
    model: str,
    prompt_condition: str,
    json_valid: bool,
    errors: List[ValidationError],
) -> Dict[str, Any]:
    """
    Build a machine-readable validation report.

    Parameters
    ----------
    dataset:
        Dataset name.
    model:
        LLM name.
    prompt_condition:
        Experimental condition, e.g., C1, C2, C3, or C4.
    json_valid:
        Whether the LLM output is valid JSON.
    errors:
        List of validation errors.

    Returns
    -------
    dict
        Validation report dictionary.
    """

    error_dicts = [asdict(error) for error in errors]

    summary = {
        "num_errors": len(errors),
        "num_warnings": sum(1 for e in errors if e.severity == "minor"),
        "missing_entities": sum(1 for e in errors if e.error_type == "missing_table"),
        "missing_attributes": sum(1 for e in errors if e.error_type == "missing_attribute"),
        "missing_primary_keys": sum(1 for e in errors if e.error_type == "missing_primary_key"),
        "missing_foreign_keys": sum(1 for e in errors if e.error_type == "missing_foreign_key"),
        "wrong_foreign_keys": sum(1 for e in errors if e.error_type == "wrong_foreign_key_target"),
        "hallucinated_elements": sum(
            1
            for e in errors
            if e.error_type in {"hallucinated_table", "hallucinated_attribute"}
        ),
    }

    return {
        "dataset": dataset,
        "model": model,
        "prompt_condition": prompt_condition,
        "json_valid": json_valid,
        "errors": error_dicts,
        "summary": summary,
    }


def empty_validation_report(
    dataset: str,
    model: str,
    prompt_condition: str,
    json_valid: bool = True,
) -> Dict[str, Any]:
    """
    Create an empty validation report.

    This is useful when no errors are found.
    """

    return build_validation_report(
        dataset=dataset,
        model=model,
        prompt_condition=prompt_condition,
        json_valid=json_valid,
        errors=[],
    )
