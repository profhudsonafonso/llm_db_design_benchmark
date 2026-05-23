#!/usr/bin/env python3
"""
Normalize LLM-generated relational schema outputs.

This script receives a raw LLM output file and produces normalized,
auditable, and reproducible artifacts for later evaluation.

Expected input:
- A raw LLM output file containing either pure JSON or JSON wrapped in text/code fences.

Main outputs:
- raw_input.txt
- extracted_json.json
- normalized_schema.json
- normalized_tables.csv
- normalized_columns.csv
- normalized_primary_keys.csv
- normalized_foreign_keys.csv
- normalization_warnings.json
- normalization_manifest.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def now_utc_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_name(value: Any) -> str:
    """
    Normalize schema element names for matching.

    The normalization:
    - converts to string;
    - removes accents;
    - lowercases;
    - removes spaces, underscores, hyphens, and non-alphanumeric characters.
    """
    if value is None:
        return ""

    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def strip_code_fences(text: str) -> str:
    """Remove common Markdown code fences around JSON."""
    text = text.strip()

    fence_pattern = r"^```(?:json|JSON|text|txt)?\s*(.*?)\s*```$"
    match = re.match(fence_pattern, text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()

    return text


def extract_json_text(text: str) -> Tuple[str, List[str]]:
    """
    Extract the first JSON object from a raw LLM output.

    Returns:
    - extracted JSON text;
    - warnings.
    """
    warnings: List[str] = []
    cleaned = strip_code_fences(text)

    try:
        json.loads(cleaned)
        return cleaned, warnings
    except Exception:
        warnings.append("Raw text is not directly valid JSON. Trying to extract first JSON object.")

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("Could not find a JSON object in the input file.")

    candidate = cleaned[start : end + 1]

    try:
        json.loads(candidate)
        warnings.append("JSON object was extracted from surrounding text.")
        return candidate, warnings
    except Exception as exc:
        raise ValueError(f"Could not parse extracted JSON object: {exc}") from exc


def as_list(value: Any) -> List[Any]:
    """Return value as list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def ensure_dict(value: Any) -> Dict[str, Any]:
    """Return value as dict when possible."""
    return value if isinstance(value, dict) else {}


def normalize_column(column: Dict[str, Any], table_name: str) -> Dict[str, Any]:
    """Normalize a column object."""
    name = column.get("name", "")

    return {
        "table_name": table_name,
        "table_name_norm": normalize_name(table_name),
        "name": name,
        "name_norm": normalize_name(name),
        "data_type": column.get("data_type", column.get("type", "")),
        "nullable": bool(column.get("nullable", False)),
        "required": bool(column.get("required", not bool(column.get("nullable", False)))),
        "is_primary_key": bool(column.get("is_primary_key", False)),
        "is_foreign_key": bool(column.get("is_foreign_key", False)),
        "is_unique": bool(column.get("is_unique", False)),
        "source_conceptual_attribute": column.get("source_conceptual_attribute", ""),
        "source_conceptual_entity": column.get("source_conceptual_entity", ""),
        "notes": column.get("notes", ""),
    }


def normalize_foreign_key(fk: Dict[str, Any], table_name: str) -> Dict[str, Any]:
    """Normalize a foreign key object."""
    columns = as_list(fk.get("columns"))
    referenced_table = fk.get("referenced_table", fk.get("refTable", ""))
    referenced_columns = as_list(fk.get("referenced_columns", fk.get("refColumns", [])))

    return {
        "table_name": table_name,
        "table_name_norm": normalize_name(table_name),
        "name": fk.get("name", ""),
        "name_norm": normalize_name(fk.get("name", "")),
        "columns": columns,
        "columns_norm": [normalize_name(c) for c in columns],
        "referenced_table": referenced_table,
        "referenced_table_norm": normalize_name(referenced_table),
        "referenced_columns": referenced_columns,
        "referenced_columns_norm": [normalize_name(c) for c in referenced_columns],
        "source_relationship": fk.get("source_relationship", ""),
        "mandatory": bool(fk.get("mandatory", False)),
        "nullable": bool(fk.get("nullable", True)),
        "notes": fk.get("notes", ""),
    }


def normalize_primary_key(pk: Any, table_name: str) -> Dict[str, Any]:
    """Normalize primary key object or list."""
    if isinstance(pk, dict):
        name = pk.get("name", "")
        columns = as_list(pk.get("columns"))
    else:
        name = ""
        columns = as_list(pk)

    return {
        "table_name": table_name,
        "table_name_norm": normalize_name(table_name),
        "name": name,
        "name_norm": normalize_name(name),
        "columns": columns,
        "columns_norm": [normalize_name(c) for c in columns],
    }


def normalize_schema(schema: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]], List[str]]:
    """
    Normalize relational schema JSON.

    Returns:
    - normalized schema;
    - flattened artifacts;
    - warnings.
    """
    warnings: List[str] = []

    tables = as_list(schema.get("tables"))
    relationship_tables = as_list(schema.get("relationship_tables"))
    specialization_mapping = as_list(schema.get("specialization_mapping"))
    mapping_decisions = as_list(schema.get("mapping_decisions"))
    mapping_alternatives = as_list(schema.get("mapping_alternatives"))

    normalized_tables: List[Dict[str, Any]] = []
    normalized_columns: List[Dict[str, Any]] = []
    normalized_primary_keys: List[Dict[str, Any]] = []
    normalized_foreign_keys: List[Dict[str, Any]] = []

    for table in tables:
        table = ensure_dict(table)
        table_name = table.get("name", "")

        if not table_name:
            warnings.append("Found table without name.")

        normalized_tables.append({
            "name": table_name,
            "name_norm": normalize_name(table_name),
            "description": table.get("description", ""),
            "origin": table.get("origin", {}),
            "notes": table.get("notes", ""),
        })

        for column in as_list(table.get("columns")):
            column = ensure_dict(column)
            normalized_columns.append(normalize_column(column, table_name))

        normalized_primary_keys.append(
            normalize_primary_key(table.get("primary_key", {}), table_name)
        )

        for fk in as_list(table.get("foreign_keys")):
            fk = ensure_dict(fk)
            normalized_foreign_keys.append(normalize_foreign_key(fk, table_name))

    normalized_schema = {
        "schema_metadata": schema.get("schema_metadata", {}),
        "tables": tables,
        "relationship_tables": relationship_tables,
        "specialization_mapping": specialization_mapping,
        "mapping_decisions": mapping_decisions,
        "mapping_alternatives": mapping_alternatives,
        "normalization": {
            "num_tables": len(normalized_tables),
            "num_columns": len(normalized_columns),
            "num_primary_keys": len(normalized_primary_keys),
            "num_foreign_keys": len(normalized_foreign_keys),
            "num_relationship_tables": len(relationship_tables),
            "num_specialization_mappings": len(specialization_mapping),
            "num_mapping_decisions": len(mapping_decisions),
            "num_mapping_alternatives": len(mapping_alternatives),
        },
    }

    flattened = {
        "tables": normalized_tables,
        "columns": normalized_columns,
        "primary_keys": normalized_primary_keys,
        "foreign_keys": normalized_foreign_keys,
    }

    return normalized_schema, flattened, warnings


def write_json(path: Path, data: Any) -> None:
    """Write JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    """Write CSV file from a list of dictionaries."""
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            cleaned = {}
            for key, value in row.items():
                if isinstance(value, (list, dict)):
                    cleaned[key] = json.dumps(value, ensure_ascii=False)
                else:
                    cleaned[key] = value
            writer.writerow(cleaned)


def build_run_id(dataset: str, model: str, condition: str) -> str:
    """Build deterministic-ish run id with timestamp."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_parts = [normalize_name(dataset), normalize_name(model), normalize_name(condition), timestamp]
    return "_".join(part for part in safe_parts if part)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize LLM-generated relational schema output."
    )

    parser.add_argument("--input", required=True, help="Path to raw LLM output file.")
    parser.add_argument("--dataset", required=True, help="Dataset name.")
    parser.add_argument("--model", required=True, help="Model name.")
    parser.add_argument("--condition", required=True, help="Experimental condition, e.g., C1, C2, C3, or C4.")
    parser.add_argument("--output-dir", default="results/normalization_runs", help="Base output directory.")
    parser.add_argument("--run-id", default=None, help="Optional run id.")
    parser.add_argument("--prompt-file", default=None, help="Prompt file used to generate the output.")
    parser.add_argument("--input-eer-file", default=None, help="Prompt-ready EER input file.")
    parser.add_argument("--notes", default="", help="Optional notes.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    run_id = args.run_id or build_run_id(args.dataset, args.model, args.condition)
    output_dir = Path(args.output_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_text = input_path.read_text(encoding="utf-8")
    extraction_warnings: List[str] = []

    json_text, extraction_warnings = extract_json_text(raw_text)
    parsed_schema = json.loads(json_text)

    normalized_schema, flattened, normalization_warnings = normalize_schema(parsed_schema)
    warnings = extraction_warnings + normalization_warnings

    raw_output_path = output_dir / "raw_input.txt"
    raw_output_path.write_text(raw_text, encoding="utf-8")

    extracted_json_path = output_dir / "extracted_json.json"
    extracted_json_path.write_text(json.dumps(parsed_schema, indent=2, ensure_ascii=False), encoding="utf-8")

    normalized_schema_path = output_dir / "normalized_schema.json"
    write_json(normalized_schema_path, normalized_schema)

    write_csv(output_dir / "normalized_tables.csv", flattened["tables"])
    write_csv(output_dir / "normalized_columns.csv", flattened["columns"])
    write_csv(output_dir / "normalized_primary_keys.csv", flattened["primary_keys"])
    write_csv(output_dir / "normalized_foreign_keys.csv", flattened["foreign_keys"])

    warnings_path = output_dir / "normalization_warnings.json"
    write_json(warnings_path, {"warnings": warnings})

    manifest = {
        "run_id": run_id,
        "created_at_utc": now_utc_iso(),
        "script": "scripts/normalize_output.py",
        "dataset": args.dataset,
        "model": args.model,
        "condition": args.condition,
        "input_file": str(input_path),
        "input_sha256": file_sha256(input_path),
        "prompt_file": args.prompt_file,
        "input_eer_file": args.input_eer_file,
        "output_dir": str(output_dir),
        "notes": args.notes,
        "generated_files": [
            "raw_input.txt",
            "extracted_json.json",
            "normalized_schema.json",
            "normalized_tables.csv",
            "normalized_columns.csv",
            "normalized_primary_keys.csv",
            "normalized_foreign_keys.csv",
            "normalization_warnings.json",
            "normalization_manifest.json",
        ],
        "normalization_summary": normalized_schema["normalization"],
        "num_warnings": len(warnings),
    }

    write_json(output_dir / "normalization_manifest.json", manifest)

    print(f"Normalization completed.")
    print(f"Run ID: {run_id}")
    print(f"Output directory: {output_dir}")
    print(f"Warnings: {len(warnings)}")


if __name__ == "__main__":
    main()
