#!/usr/bin/env python3
"""
Evaluate an LLM-generated relational schema against an expert gold schema.

This script compares a generated schema with the expert logical relational gold
standard and writes all outputs to a reproducible run folder.

Inputs:
- gold logical relational schema JSON;
- generated schema JSON, preferably normalized_schema.json from normalize_output.py.

Outputs:
- evaluation_metrics.json
- component_counts.csv
- component_metrics.csv
- mapping_alternative_report.json
- evaluation_errors.json
- evaluation_manifest.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_name(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
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
                if isinstance(value, (list, dict, set, tuple)):
                    cleaned[key] = json.dumps(list(value) if isinstance(value, set) else value, ensure_ascii=False)
                else:
                    cleaned[key] = value
            writer.writerow(cleaned)


def string_similarity(a: str, b: str) -> float:
    a_norm = normalize_name(a)
    b_norm = normalize_name(b)
    if not a_norm and not b_norm:
        return 1.0
    if not a_norm or not b_norm:
        return 0.0
    if a_norm == b_norm:
        return 1.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def safe_div(num: float, den: float) -> Optional[float]:
    if den == 0:
        return None
    return num / den


def f1_score(precision: Optional[float], recall: Optional[float]) -> Optional[float]:
    if precision is None or recall is None:
        return None
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def metric_dict(tp: int, fp: int, fn: int) -> Dict[str, Any]:
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = f1_score(precision, recall)

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def get_tables(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [t for t in as_list(schema.get("tables")) if isinstance(t, dict)]


def get_table_name(table: Dict[str, Any]) -> str:
    return str(table.get("name", ""))


def get_columns(table: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [c for c in as_list(table.get("columns")) if isinstance(c, dict)]


def get_column_names(table: Dict[str, Any]) -> Set[str]:
    return {normalize_name(c.get("name", "")) for c in get_columns(table) if c.get("name")}


def get_pk_columns(table: Dict[str, Any]) -> Tuple[str, ...]:
    pk = table.get("primary_key", {})
    if isinstance(pk, dict):
        cols = as_list(pk.get("columns"))
    else:
        cols = as_list(pk)
    return tuple(sorted(normalize_name(c) for c in cols if c))


def get_foreign_keys(table: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [fk for fk in as_list(table.get("foreign_keys")) if isinstance(fk, dict)]


def fk_signature(table_name: str, fk: Dict[str, Any]) -> str:
    cols = tuple(sorted(normalize_name(c) for c in as_list(fk.get("columns"))))
    ref_table = normalize_name(fk.get("referenced_table", fk.get("refTable", "")))
    ref_cols = tuple(sorted(normalize_name(c) for c in as_list(fk.get("referenced_columns", fk.get("refColumns", [])))))
    return f"{normalize_name(table_name)}:{cols}->{ref_table}:{ref_cols}"


def fk_endpoint_signature(fk: Dict[str, Any]) -> str:
    ref_table = normalize_name(fk.get("referenced_table", fk.get("refTable", "")))
    ref_cols = tuple(sorted(normalize_name(c) for c in as_list(fk.get("referenced_columns", fk.get("refColumns", [])))))
    local_cols = tuple(sorted(normalize_name(c) for c in as_list(fk.get("columns"))))
    return f"{local_cols}->{ref_table}:{ref_cols}"


def table_structural_signature(table: Dict[str, Any]) -> Dict[str, Any]:
    name = get_table_name(table)
    return {
        "name": name,
        "name_norm": normalize_name(name),
        "columns": get_column_names(table),
        "pk": set(get_pk_columns(table)),
        "fk_endpoints": {fk_endpoint_signature(fk) for fk in get_foreign_keys(table)},
        "fk_ref_tables": {normalize_name(fk.get("referenced_table", fk.get("refTable", ""))) for fk in get_foreign_keys(table)},
        "source_relationships": {
            normalize_name(fk.get("source_relationship", "")) for fk in get_foreign_keys(table) if fk.get("source_relationship")
        },
    }


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def table_structural_similarity(gold_table: Dict[str, Any], pred_table: Dict[str, Any]) -> float:
    g = table_structural_signature(gold_table)
    p = table_structural_signature(pred_table)

    column_score = jaccard(g["columns"], p["columns"])
    pk_score = jaccard(g["pk"], p["pk"])
    fk_endpoint_score = jaccard(g["fk_endpoints"], p["fk_endpoints"])
    fk_ref_score = jaccard(g["fk_ref_tables"], p["fk_ref_tables"])

    # Relationship tables are often better recognized by FK structure than by name.
    return (
        0.35 * column_score
        + 0.20 * pk_score
        + 0.30 * fk_endpoint_score
        + 0.15 * fk_ref_score
    )


def is_table_match(
    gold_table: Dict[str, Any],
    pred_table: Dict[str, Any],
    name_threshold: float = 0.85,
    structural_threshold: float = 0.70,
) -> Tuple[bool, Dict[str, float]]:
    name_score = string_similarity(get_table_name(gold_table), get_table_name(pred_table))
    structural_score = table_structural_similarity(gold_table, pred_table)

    matched = name_score >= name_threshold or structural_score >= structural_threshold

    return matched, {
        "name_similarity": name_score,
        "structural_similarity": structural_score,
    }


def build_table_mapping(
    gold_tables: List[Dict[str, Any]],
    pred_tables: List[Dict[str, Any]],
    mode: str,
) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
    """
    Build mapping from gold table normalized name to predicted table normalized name.

    mode:
    - strict: exact normalized name matching;
    - matched: name similarity or structural compatibility.
    """
    mapping: Dict[str, str] = {}
    evidence: List[Dict[str, Any]] = []

    used_pred: Set[str] = set()

    for g in gold_tables:
        g_name = get_table_name(g)
        g_norm = normalize_name(g_name)

        best_pred = None
        best_score = -1.0
        best_evidence = {}

        for p in pred_tables:
            p_name = get_table_name(p)
            p_norm = normalize_name(p_name)

            if p_norm in used_pred:
                continue

            if mode == "strict":
                matched = g_norm == p_norm
                scores = {
                    "name_similarity": 1.0 if matched else string_similarity(g_name, p_name),
                    "structural_similarity": table_structural_similarity(g, p),
                }
            else:
                matched, scores = is_table_match(g, p)

            combined_score = max(scores["name_similarity"], scores["structural_similarity"])

            if matched and combined_score > best_score:
                best_score = combined_score
                best_pred = p_norm
                best_evidence = {
                    "gold_table": g_name,
                    "pred_table": p_name,
                    "mode": mode,
                    "combined_score": combined_score,
                    **scores,
                }

        if best_pred:
            mapping[g_norm] = best_pred
            used_pred.add(best_pred)
            evidence.append(best_evidence)

    return mapping, evidence


def extract_units(schema: Dict[str, Any], table_mapping: Optional[Dict[str, str]] = None, reverse_mapping: bool = False) -> Dict[str, Set[str]]:
    """
    Extract comparable schema units.

    If table_mapping is provided:
    - for gold units, table_mapping maps gold table norm -> pred table norm;
    - for predicted units with reverse_mapping=True, it maps pred table norm -> gold table norm.
    """
    units: Dict[str, Set[str]] = defaultdict(set)

    for table in get_tables(schema):
        table_name = get_table_name(table)
        table_norm = normalize_name(table_name)

        effective_table = table_norm

        if table_mapping:
            if reverse_mapping:
                effective_table = table_mapping.get(table_norm, table_norm)
            else:
                effective_table = table_mapping.get(table_norm, table_norm)

        units["tables"].add(effective_table)

        for col in get_columns(table):
            col_norm = normalize_name(col.get("name", ""))
            if col_norm:
                units["attributes"].add(f"{effective_table}.{col_norm}")

        pk_cols = get_pk_columns(table)
        if pk_cols:
            units["primary_keys"].add(f"{effective_table}:{'+'.join(pk_cols)}")

        for fk in get_foreign_keys(table):
            local_cols = tuple(sorted(normalize_name(c) for c in as_list(fk.get("columns"))))
            ref_table = normalize_name(fk.get("referenced_table", fk.get("refTable", "")))
            ref_cols = tuple(sorted(normalize_name(c) for c in as_list(fk.get("referenced_columns", fk.get("refColumns", [])))))
            if local_cols and ref_table and ref_cols:
                units["foreign_keys"].add(f"{effective_table}:{'+'.join(local_cols)}->{ref_table}:{'+'.join(ref_cols)}")

    for rt in as_list(schema.get("relationship_tables")):
        if isinstance(rt, dict):
            table_name = rt.get("table_name", "")
            rt_norm = normalize_name(table_name)
            if table_mapping:
                if reverse_mapping:
                    rt_norm = table_mapping.get(rt_norm, rt_norm)
                else:
                    rt_norm = table_mapping.get(rt_norm, rt_norm)
            if rt_norm:
                units["relationship_tables"].add(rt_norm)

    for sp in as_list(schema.get("specialization_mapping")):
        if isinstance(sp, dict):
            sp_id = normalize_name(sp.get("specialization_id", ""))
            strategy = normalize_name(sp.get("strategy", ""))
            if sp_id or strategy:
                units["specialization_mappings"].add(f"{sp_id}:{strategy}")

    return units


def compare_sets(gold: Set[str], pred: Set[str]) -> Dict[str, Any]:
    tp_set = gold & pred
    fp_set = pred - gold
    fn_set = gold - pred

    metrics = metric_dict(len(tp_set), len(fp_set), len(fn_set))
    metrics.update({
        "tp_items": sorted(tp_set),
        "fp_items": sorted(fp_set),
        "fn_items": sorted(fn_set),
    })
    return metrics


def evaluate_components(gold_schema: Dict[str, Any], pred_schema: Dict[str, Any], mode: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    gold_tables = get_tables(gold_schema)
    pred_tables = get_tables(pred_schema)

    table_mapping, mapping_evidence = build_table_mapping(gold_tables, pred_tables, mode=mode)

    if mode == "strict":
        gold_units = extract_units(gold_schema)
        pred_units = extract_units(pred_schema)
    else:
        reverse = {v: k for k, v in table_mapping.items()}
        gold_units = extract_units(gold_schema)
        pred_units = extract_units(pred_schema, table_mapping=reverse, reverse_mapping=True)

    components = [
        "tables",
        "attributes",
        "primary_keys",
        "foreign_keys",
        "relationship_tables",
        "specialization_mappings",
    ]

    result = {}
    for comp in components:
        result[comp] = compare_sets(gold_units.get(comp, set()), pred_units.get(comp, set()))

    # Global metrics from aggregate counts.
    total_tp = sum(result[c]["tp"] for c in components)
    total_fp = sum(result[c]["fp"] for c in components)
    total_fn = sum(result[c]["fn"] for c in components)
    result["global"] = metric_dict(total_tp, total_fp, total_fn)

    return result, mapping_evidence


def normalize_qualified_reference(value: str) -> str:
    """
    Normalize strings like:
    CustomerProfile.customer_id -> Customer.customer_id
    """
    value = str(value).strip()
    value = value.replace(" ", "")
    if "->" not in value:
        return normalize_name(value)

    left, right = value.split("->", 1)

    def norm_side(side: str) -> str:
        if "." in side:
            table, col = side.split(".", 1)
            return f"{normalize_name(table)}.{normalize_name(col)}"
        return normalize_name(side)

    return f"{norm_side(left)}->{norm_side(right)}"


def predicted_fk_references(schema: Dict[str, Any]) -> Set[str]:
    """
    Return normalized FK references from a schema.

    Format:
    table.column -> referenced_table.referenced_column
    """
    refs = set()

    for table in get_tables(schema):
        table_name = get_table_name(table)
        table_norm = normalize_name(table_name)

        for fk in get_foreign_keys(table):
            local_cols = as_list(fk.get("columns"))
            ref_table = fk.get("referenced_table", fk.get("refTable", ""))
            ref_cols = as_list(fk.get("referenced_columns", fk.get("refColumns", [])))

            # Pair columns positionally when possible.
            if len(local_cols) == len(ref_cols):
                for local, ref in zip(local_cols, ref_cols):
                    refs.add(
                        f"{table_norm}.{normalize_name(local)}->{normalize_name(ref_table)}.{normalize_name(ref)}"
                    )
            else:
                local_join = "+".join(normalize_name(c) for c in local_cols)
                ref_join = "+".join(normalize_name(c) for c in ref_cols)
                refs.add(
                    f"{table_norm}.{local_join}->{normalize_name(ref_table)}.{ref_join}"
                )

    return refs


def expected_columns_hit(expected_columns: List[Any], pred_columns: Set[str]) -> bool:
    expected_norm = set()
    for c in expected_columns:
        if "." in str(c):
            t, col = str(c).split(".", 1)
            expected_norm.add(f"{normalize_name(t)}.{normalize_name(col)}")
    return expected_norm.issubset(pred_columns) if expected_norm else True


def expected_fks_hit(expected_fks: List[Any], pred_fks: Set[str]) -> bool:
    expected_norm = {normalize_qualified_reference(str(fk)) for fk in expected_fks if str(fk).strip()}
    return expected_norm.issubset(pred_fks) if expected_norm else True


def classify_mapping_alternatives(gold_schema: Dict[str, Any], pred_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify discretionary mapping decisions.

    The classifier distinguishes:
    - preferred_correct;
    - valid_alternative;
    - invalid_mapping;
    - missing_mapping;
    - hallucinated_mapping.

    This version checks expected tables, expected columns, and expected FKs.
    """
    pred_tables = {normalize_name(get_table_name(t)) for t in get_tables(pred_schema)}
    pred_columns = set()

    for table in get_tables(pred_schema):
        table_norm = normalize_name(get_table_name(table))
        for col in get_columns(table):
            col_norm = normalize_name(col.get("name", ""))
            if table_norm and col_norm:
                pred_columns.add(f"{table_norm}.{col_norm}")

    pred_fks = predicted_fk_references(pred_schema)

    reports = []
    counts = {
        "preferred_correct": 0,
        "valid_alternative": 0,
        "invalid_mapping": 0,
        "missing_mapping": 0,
        "hallucinated_mapping": 0,
    }

    for alt in as_list(gold_schema.get("mapping_alternatives")):
        if not isinstance(alt, dict):
            continue

        alt_id = alt.get("id", "")
        preferred = alt.get("preferred_mapping", {})
        acceptable = as_list(alt.get("acceptable_mappings"))

        preferred_tables = {normalize_name(t) for t in as_list(preferred.get("expected_tables")) if t}
        preferred_table_hit = preferred_tables.issubset(pred_tables) if preferred_tables else True
        preferred_column_hit = expected_columns_hit(as_list(preferred.get("expected_columns")), pred_columns)
        preferred_fk_hit = expected_fks_hit(as_list(preferred.get("expected_foreign_keys")), pred_fks)

        classification = "missing_mapping"
        matched_detail = None
        reason = ""

        if preferred_table_hit and preferred_column_hit and preferred_fk_hit:
            classification = "preferred_correct"
            matched_detail = preferred
            reason = "Generated mapping satisfies the preferred mapping."
        else:
            for acc in acceptable:
                if not isinstance(acc, dict):
                    continue

                acc_tables = {normalize_name(t) for t in as_list(acc.get("expected_tables")) if t}
                acc_table_hit = acc_tables.issubset(pred_tables) if acc_tables else True
                acc_column_hit = expected_columns_hit(as_list(acc.get("expected_columns")), pred_columns)
                acc_fk_hit = expected_fks_hit(as_list(acc.get("expected_foreign_keys")), pred_fks)

                if acc_table_hit and acc_column_hit and acc_fk_hit:
                    classification = "valid_alternative"
                    matched_detail = acc
                    reason = "Generated mapping satisfies an acceptable non-preferred mapping."
                    break

            # If the preferred table exists but its required FK is missing, this is not simply missing;
            # it is an invalid/disconnected implementation.
            if classification == "missing_mapping":
                if preferred_tables and (preferred_tables & pred_tables) and not preferred_fk_hit:
                    classification = "invalid_mapping"
                    reason = "A table related to the preferred mapping exists, but required FK structure is missing."
                else:
                    reason = "No preferred or acceptable mapping was detected."

        counts[classification] += 1

        reports.append({
            "alternative_group_id": alt_id,
            "conceptual_element_id": alt.get("conceptual_element_id", ""),
            "conceptual_element_name": alt.get("conceptual_element_name", ""),
            "classification": classification,
            "reason": reason,
            "matched_detail": matched_detail,
            "preferred_table_hit": preferred_table_hit,
            "preferred_column_hit": preferred_column_hit,
            "preferred_fk_hit": preferred_fk_hit,
        })

    total = sum(counts.values())

    summary = dict(counts)
    summary["total_alternative_groups"] = total
    summary["preferred_mapping_accuracy"] = safe_div(counts["preferred_correct"], total) if total else None
    summary["valid_mapping_accuracy"] = safe_div(counts["preferred_correct"] + counts["valid_alternative"], total) if total else None
    summary["alternative_mapping_rate"] = safe_div(counts["valid_alternative"], total) if total else None
    summary["invalid_mapping_rate"] = safe_div(counts["invalid_mapping"], total) if total else None

    return {
        "summary": summary,
        "groups": reports,
    }


def structural_distance(error_counts: Dict[str, int]) -> Dict[str, Any]:
    weights = {
        "missing_attributes": 1,
        "hallucinated_attributes": 1,
        "missing_tables": 2,
        "hallucinated_tables": 2,
        "wrong_primary_keys": 2,
        "missing_foreign_keys": 3,
        "wrong_foreign_key_targets": 4,
        "wrong_relationship_tables": 4,
        "cardinality_errors": 4,
        "specialization_errors": 5,
        "invalid_mappings": 5,
    }

    unweighted = sum(abs(v) for v in error_counts.values())
    weighted = sum(weights.get(k, 1) * abs(v) for k, v in error_counts.items())

    return {
        "unweighted_structural_manhattan_distance": unweighted,
        "weighted_structural_manhattan_distance": weighted,
        "weights": weights,
    }


def build_error_counts(matched_results: Dict[str, Any], mapping_report: Dict[str, Any]) -> Dict[str, int]:
    return {
        "missing_tables": matched_results["tables"]["fn"],
        "hallucinated_tables": matched_results["tables"]["fp"],
        "missing_attributes": matched_results["attributes"]["fn"],
        "hallucinated_attributes": matched_results["attributes"]["fp"],
        "wrong_primary_keys": matched_results["primary_keys"]["fn"] + matched_results["primary_keys"]["fp"],
        "missing_foreign_keys": matched_results["foreign_keys"]["fn"],
        "wrong_foreign_key_targets": matched_results["foreign_keys"]["fp"],
        "wrong_relationship_tables": matched_results["relationship_tables"]["fn"] + matched_results["relationship_tables"]["fp"],
        "cardinality_errors": 0,
        "specialization_errors": matched_results["specialization_mappings"]["fn"] + matched_results["specialization_mappings"]["fp"],
        "invalid_mappings": mapping_report["summary"].get("invalid_mapping", 0),
    }


def expected_structural_mass(gold_schema: Dict[str, Any]) -> int:
    gold_units = extract_units(gold_schema)

    mass = (
        2 * len(gold_units.get("tables", set()))
        + 1 * len(gold_units.get("attributes", set()))
        + 2 * len(gold_units.get("primary_keys", set()))
        + 3 * len(gold_units.get("foreign_keys", set()))
        + 4 * len(gold_units.get("relationship_tables", set()))
        + 5 * len(gold_units.get("specialization_mappings", set()))
        + 5 * len(as_list(gold_schema.get("mapping_decisions")))
    )

    return max(mass, 1)


def build_rows_from_component_results(mode: str, results: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for component, data in results.items():
        if component == "global":
            continue
        rows.append({
            "mode": mode,
            "component": component,
            "tp": data["tp"],
            "fp": data["fp"],
            "fn": data["fn"],
            "precision": data["precision"],
            "recall": data["recall"],
            "f1": data["f1"],
        })
    rows.append({
        "mode": mode,
        "component": "global",
        "tp": results["global"]["tp"],
        "fp": results["global"]["fp"],
        "fn": results["global"]["fn"],
        "precision": results["global"]["precision"],
        "recall": results["global"]["recall"],
        "f1": results["global"]["f1"],
    })
    return rows


def build_error_items(mode: str, results: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for component, data in results.items():
        if component == "global":
            continue
        for item in data.get("fp_items", []):
            rows.append({
                "mode": mode,
                "component": component,
                "error_type": "false_positive",
                "item": item,
            })
        for item in data.get("fn_items", []):
            rows.append({
                "mode": mode,
                "component": component,
                "error_type": "false_negative",
                "item": item,
            })
    return rows


def normalize_column_reference(value: Any) -> Optional[str]:
    """
    Normalize a table.column reference.

    Example:
    CustomerProfile.customer_id -> customerprofile.customerid
    """
    value = str(value).strip()
    if "." not in value:
        return None

    table, column = value.split(".", 1)
    table_norm = normalize_name(table)
    column_norm = normalize_name(column)

    if not table_norm or not column_norm:
        return None

    return f"{table_norm}.{column_norm}"


def normalize_fk_reference_to_unit(value: Any) -> Optional[str]:
    """
    Normalize an expected FK reference into the same unit format used by extract_units.

    Example:
    CustomerProfile.customer_id -> Customer.customer_id

    Becomes:
    customerprofile:customerid->customer:customerid
    """
    value = str(value).strip().replace(" ", "")

    if "->" not in value:
        return None

    left, right = value.split("->", 1)

    if "." not in left or "." not in right:
        return None

    left_table, left_col = left.split(".", 1)
    right_table, right_col = right.split(".", 1)

    left_table_norm = normalize_name(left_table)
    left_col_norm = normalize_name(left_col)
    right_table_norm = normalize_name(right_table)
    right_col_norm = normalize_name(right_col)

    if not all([left_table_norm, left_col_norm, right_table_norm, right_col_norm]):
        return None

    return f"{left_table_norm}:{left_col_norm}->{right_table_norm}:{right_col_norm}"


def copy_units(units: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """Deep-copy unit sets."""
    return {component: set(values) for component, values in units.items()}


def remove_table_from_units(units: Dict[str, Set[str]], table_norm: str) -> None:
    """
    Remove a table and all units that depend on it from comparable units.
    """
    if not table_norm:
        return

    units.setdefault("tables", set()).discard(table_norm)

    units.setdefault("attributes", set()).difference_update({
        item for item in units.get("attributes", set())
        if item.startswith(f"{table_norm}.")
    })

    units.setdefault("primary_keys", set()).difference_update({
        item for item in units.get("primary_keys", set())
        if item.startswith(f"{table_norm}:")
    })

    units.setdefault("foreign_keys", set()).difference_update({
        item for item in units.get("foreign_keys", set())
        if item.startswith(f"{table_norm}:")
    })

    units.setdefault("relationship_tables", set()).discard(table_norm)


def apply_valid_alternatives_to_gold_units(
    gold_units: Dict[str, Set[str]],
    gold_schema: Dict[str, Any],
    mapping_report: Dict[str, Any],
) -> Dict[str, Set[str]]:
    """
    Adjust gold units when the LLM output follows an acceptable non-preferred mapping.

    This creates the alternative-aware gold view.

    If a mapping group is classified as valid_alternative:
    - remove preferred mapping units from the gold view;
    - add acceptable alternative units to the gold view.
    """
    adjusted = copy_units(gold_units)

    report_by_id = {
        group.get("alternative_group_id"): group
        for group in mapping_report.get("groups", [])
        if group.get("alternative_group_id")
    }

    for alt in as_list(gold_schema.get("mapping_alternatives")):
        if not isinstance(alt, dict):
            continue

        alt_id = alt.get("id", "")
        report = report_by_id.get(alt_id)

        if not report:
            continue

        if report.get("classification") != "valid_alternative":
            continue

        preferred = alt.get("preferred_mapping", {})
        matched_detail = report.get("matched_detail") or {}

        # Remove preferred tables and dependent units.
        for table in as_list(preferred.get("expected_tables")):
            remove_table_from_units(adjusted, normalize_name(table))

        # Remove preferred columns explicitly.
        for col in as_list(preferred.get("expected_columns")):
            col_ref = normalize_column_reference(col)
            if col_ref:
                adjusted.setdefault("attributes", set()).discard(col_ref)

        # Remove preferred foreign keys explicitly.
        for fk in as_list(preferred.get("expected_foreign_keys")):
            fk_ref = normalize_fk_reference_to_unit(fk)
            if fk_ref:
                adjusted.setdefault("foreign_keys", set()).discard(fk_ref)

        # Add acceptable alternative tables.
        for table in as_list(matched_detail.get("expected_tables")):
            table_norm = normalize_name(table)
            if table_norm:
                adjusted.setdefault("tables", set()).add(table_norm)

        # Add acceptable alternative columns.
        for col in as_list(matched_detail.get("expected_columns")):
            col_ref = normalize_column_reference(col)
            if col_ref:
                adjusted.setdefault("attributes", set()).add(col_ref)

        # Add acceptable alternative foreign keys.
        for fk in as_list(matched_detail.get("expected_foreign_keys")):
            fk_ref = normalize_fk_reference_to_unit(fk)
            if fk_ref:
                adjusted.setdefault("foreign_keys", set()).add(fk_ref)

    return adjusted


def evaluate_components_alternative_aware(
    gold_schema: Dict[str, Any],
    pred_schema: Dict[str, Any],
    mapping_report: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Evaluate using similarity/structure-aware table matching and acceptable alternatives.

    This mode treats valid non-preferred mappings as correct.
    """
    gold_tables = get_tables(gold_schema)
    pred_tables = get_tables(pred_schema)

    table_mapping, mapping_evidence = build_table_mapping(gold_tables, pred_tables, mode="matched")
    reverse = {v: k for k, v in table_mapping.items()}

    gold_units = extract_units(gold_schema)
    pred_units = extract_units(pred_schema, table_mapping=reverse, reverse_mapping=True)

    adjusted_gold_units = apply_valid_alternatives_to_gold_units(
        gold_units=gold_units,
        gold_schema=gold_schema,
        mapping_report=mapping_report,
    )

    components = [
        "tables",
        "attributes",
        "primary_keys",
        "foreign_keys",
        "relationship_tables",
        "specialization_mappings",
    ]

    result = {}
    for comp in components:
        result[comp] = compare_sets(
            adjusted_gold_units.get(comp, set()),
            pred_units.get(comp, set()),
        )

    total_tp = sum(result[c]["tp"] for c in components)
    total_fp = sum(result[c]["fp"] for c in components)
    total_fn = sum(result[c]["fn"] for c in components)
    result["global"] = metric_dict(total_tp, total_fp, total_fn)

    return result, mapping_evidence


def build_run_id(dataset: str, model: str, condition: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parts = [normalize_name(dataset), normalize_name(model), normalize_name(condition), timestamp]
    return "_".join(p for p in parts if p)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate LLM-generated schema against gold schema.")
    parser.add_argument("--gold", required=True, help="Path to logical_relational_gold.json.")
    parser.add_argument("--prediction", required=True, help="Path to generated or normalized schema JSON.")
    parser.add_argument("--dataset", required=True, help="Dataset name.")
    parser.add_argument("--model", required=True, help="Model name.")
    parser.add_argument("--condition", required=True, help="Condition, e.g., C1, C2, C3, C4.")
    parser.add_argument("--output-dir", default="results/evaluation_runs", help="Base output directory.")
    parser.add_argument("--run-id", default=None, help="Optional run id.")
    parser.add_argument("--normalization-run-dir", default=None, help="Optional normalization run directory.")
    parser.add_argument("--notes", default="", help="Optional notes.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    gold_path = Path(args.gold)
    pred_path = Path(args.prediction)

    if not gold_path.exists():
        raise FileNotFoundError(f"Gold file not found: {gold_path}")
    if not pred_path.exists():
        raise FileNotFoundError(f"Prediction file not found: {pred_path}")

    gold_schema = load_json(gold_path)
    pred_schema = load_json(pred_path)

    strict_results, strict_mapping_evidence = evaluate_components(gold_schema, pred_schema, mode="strict")
    matched_results, matched_mapping_evidence = evaluate_components(gold_schema, pred_schema, mode="matched")

    mapping_report = classify_mapping_alternatives(gold_schema, pred_schema)

    alternative_aware_results, alternative_aware_mapping_evidence = evaluate_components_alternative_aware(
        gold_schema,
        pred_schema,
        mapping_report,
    )

    strict_error_counts = build_error_counts(strict_results, mapping_report)
    matched_error_counts = build_error_counts(matched_results, mapping_report)
    alternative_aware_error_counts = build_error_counts(alternative_aware_results, mapping_report)

    strict_distance = structural_distance(strict_error_counts)
    matched_distance = structural_distance(matched_error_counts)
    alternative_aware_distance = structural_distance(alternative_aware_error_counts)

    mass = expected_structural_mass(gold_schema)

    strict_normalized_weighted_distance = (
        strict_distance["weighted_structural_manhattan_distance"] / mass
    )
    matched_normalized_weighted_distance = (
        matched_distance["weighted_structural_manhattan_distance"] / mass
    )
    alternative_aware_normalized_weighted_distance = (
        alternative_aware_distance["weighted_structural_manhattan_distance"] / mass
    )

    distance_reduction_from_matching = (
        strict_normalized_weighted_distance - matched_normalized_weighted_distance
    )
    distance_reduction_from_alternatives = (
        matched_normalized_weighted_distance - alternative_aware_normalized_weighted_distance
    )

    metrics = {
        "dataset": args.dataset,
        "model": args.model,
        "condition": args.condition,
        "strict": {
            "global": strict_results["global"],
        },
        "matched": {
            "global": matched_results["global"],
        },
        "alternative_aware": {
            "global": alternative_aware_results["global"],
        },
        "mapping_alternatives": mapping_report["summary"],
        "error_counts_for_distance": {
            "strict": strict_error_counts,
            "matched": matched_error_counts,
            "alternative_aware": alternative_aware_error_counts,
        },
        "structural_distance": {
            "strict": {
                **strict_distance,
                "expected_structural_mass": mass,
                "normalized_weighted_structural_distance": strict_normalized_weighted_distance,
            },
            "matched": {
                **matched_distance,
                "expected_structural_mass": mass,
                "normalized_weighted_structural_distance": matched_normalized_weighted_distance,
            },
            "alternative_aware": {
                **alternative_aware_distance,
                "expected_structural_mass": mass,
                "normalized_weighted_structural_distance": alternative_aware_normalized_weighted_distance,
            },
            "distance_reduction_from_matching": distance_reduction_from_matching,
            "distance_reduction_from_alternatives": distance_reduction_from_alternatives,
        },
    }

    run_id = args.run_id or build_run_id(args.dataset, args.model, args.condition)
    output_dir = Path(args.output_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "evaluation_metrics.json", metrics)
    write_json(output_dir / "strict_component_results.json", strict_results)
    write_json(output_dir / "matched_component_results.json", matched_results)
    write_json(output_dir / "alternative_aware_component_results.json", alternative_aware_results)
    write_json(output_dir / "table_mapping_evidence.json", {
        "strict": strict_mapping_evidence,
        "matched": matched_mapping_evidence,
        "alternative_aware": alternative_aware_mapping_evidence,
    })
    write_json(output_dir / "mapping_alternative_report.json", mapping_report)

    component_rows = []
    component_rows.extend(build_rows_from_component_results("strict", strict_results))
    component_rows.extend(build_rows_from_component_results("matched", matched_results))
    component_rows.extend(build_rows_from_component_results("alternative_aware", alternative_aware_results))
    write_csv(output_dir / "component_metrics.csv", component_rows)

    error_rows = []
    error_rows.extend(build_error_items("strict", strict_results))
    error_rows.extend(build_error_items("matched", matched_results))
    error_rows.extend(build_error_items("alternative_aware", alternative_aware_results))
    write_csv(output_dir / "evaluation_errors.csv", error_rows)
    write_json(output_dir / "evaluation_errors.json", error_rows)

    manifest = {
        "run_id": run_id,
        "created_at_utc": now_utc_iso(),
        "script": "scripts/evaluate_schema.py",
        "dataset": args.dataset,
        "model": args.model,
        "condition": args.condition,
        "gold_file": str(gold_path),
        "gold_sha256": file_sha256(gold_path),
        "prediction_file": str(pred_path),
        "prediction_sha256": file_sha256(pred_path),
        "normalization_run_dir": args.normalization_run_dir,
        "output_dir": str(output_dir),
        "notes": args.notes,
        "generated_files": [
            "evaluation_metrics.json",
            "strict_component_results.json",
            "matched_component_results.json",
            "alternative_aware_component_results.json",
            "table_mapping_evidence.json",
            "mapping_alternative_report.json",
            "component_metrics.csv",
            "evaluation_errors.csv",
            "evaluation_errors.json",
            "evaluation_manifest.json",
        ],
    }

    write_json(output_dir / "evaluation_manifest.json", manifest)

    print("Evaluation completed.")
    print(f"Run ID: {run_id}")
    print(f"Output directory: {output_dir}")
    print(f"Strict global F1: {strict_results['global']['f1']}")
    print(f"Matched global F1: {matched_results['global']['f1']}")
    print(f"Alternative-aware global F1: {alternative_aware_results['global']['f1']}")
    print(f"Strict normalized weighted distance: {strict_normalized_weighted_distance}")
    print(f"Matched normalized weighted distance: {matched_normalized_weighted_distance}")
    print(f"Alternative-aware normalized weighted distance: {alternative_aware_normalized_weighted_distance}")
    print(f"Distance reduction from matching: {distance_reduction_from_matching}")
    print(f"Distance reduction from alternatives: {distance_reduction_from_alternatives}")


if __name__ == "__main__":
    main()
