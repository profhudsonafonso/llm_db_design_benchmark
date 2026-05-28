#!/usr/bin/env python3
"""
Aggregate benchmark results.

This script collects outputs from:

- results/llm_runs/
- results/normalization_runs/
- results/evaluation_runs/

and produces analysis-ready aggregate tables.

Main outputs:

- aggregate_run_summary.csv
- aggregate_llm_runs.csv
- aggregate_normalization_summary.csv
- aggregate_component_metrics.csv
- aggregate_error_counts.csv
- aggregate_cost_quality.csv
- aggregate_by_model.csv
- aggregate_by_condition.csv
- aggregate_by_dataset_complexity.csv
- aggregate_manifest.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_run_part(value: Any) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value)).strip("_")


def build_run_id(prefix: str = "aggregate") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{normalize_run_part(prefix)}_{timestamp}"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []

    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = sorted({key for row in rows for key in row.keys()})

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            cleaned = {}
            for key in fieldnames:
                value = row.get(key, "")
                if isinstance(value, (dict, list)):
                    cleaned[key] = json.dumps(value, ensure_ascii=False)
                else:
                    cleaned[key] = value
            writer.writerow(cleaned)


def to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def safe_div(num: Optional[float], den: Optional[float]) -> Optional[float]:
    if num is None or den is None or den == 0:
        return None
    return num / den


def mean(values: Iterable[Any]) -> Optional[float]:
    nums = [to_float(v) for v in values]
    nums = [v for v in nums if v is not None]
    if not nums:
        return None
    return sum(nums) / len(nums)


def sum_numeric(values: Iterable[Any]) -> Optional[float]:
    nums = [to_float(v) for v in values]
    nums = [v for v in nums if v is not None]
    if not nums:
        return None
    return sum(nums)


def get_nested(data: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def path_key(value: Optional[Any]) -> str:
    if not value:
        return ""
    return str(Path(str(value))).rstrip("/")


def find_json_files(base_dir: Path, filename: str) -> List[Path]:
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob(f"*/{filename}"))


def load_dataset_complexities(datasets_dir: Path) -> Dict[str, str]:
    """
    Load dataset complexity from logical_relational_gold.json or conceptual_eer.yaml when possible.
    Uses simple fallback for known project datasets.
    """
    fallback = {
        "toy_example": "low",
        "chinook": "low",
        "imdb": "medium",
        "yelp": "high",
    }

    complexities = dict(fallback)

    if not datasets_dir.exists():
        return complexities

    for dataset_dir in datasets_dir.iterdir():
        if not dataset_dir.is_dir():
            continue

        dataset = dataset_dir.name
        logical = dataset_dir / "ground_truth" / "logical_relational_gold.json"

        if logical.exists():
            try:
                data = read_json(logical)
                complexity = get_nested(data, ["schema_metadata", "dataset_complexity"])
                if complexity:
                    complexities[dataset] = str(complexity)
            except Exception:
                pass

    return complexities


def collect_llm_runs(llm_runs_dir: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    by_run_id: Dict[str, Dict[str, Any]] = {}
    by_published_output: Dict[str, Dict[str, Any]] = {}

    for manifest_path in find_json_files(llm_runs_dir, "llm_run_manifest.json"):
        try:
            manifest = read_json(manifest_path)
        except Exception as exc:
            rows.append({
                "source_file": str(manifest_path),
                "status": "read_error",
                "error_message": str(exc),
            })
            continue

        usage_path = manifest_path.parent / "usage_and_cost.json"
        usage = {}
        if usage_path.exists():
            try:
                usage = read_json(usage_path)
            except Exception:
                usage = {}

        run_id = manifest.get("run_id", manifest_path.parent.name)
        usage_manifest = manifest.get("usage_and_cost", {}) or {}
        usage_combined = {**usage_manifest, **usage}

        row = {
            "llm_run_id": run_id,
            "llm_run_dir": str(manifest_path.parent),
            "dataset": manifest.get("dataset"),
            "condition": manifest.get("condition"),
            "model_key": manifest.get("model_key"),
            "provider": manifest.get("provider"),
            "model": manifest.get("model"),
            "llm_status": manifest.get("status"),
            "dry_run": manifest.get("dry_run"),
            "latency_seconds": usage_combined.get("latency_seconds", manifest.get("latency_seconds")),
            "input_tokens": usage_combined.get("input_tokens"),
            "output_tokens": usage_combined.get("output_tokens"),
            "total_tokens": usage_combined.get("total_tokens"),
            "cached_input_tokens": usage_combined.get("cached_input_tokens"),
            "reasoning_tokens": usage_combined.get("reasoning_tokens"),
            "tokens_per_second": usage_combined.get("tokens_per_second"),
            "estimated_cost_usd": usage_combined.get("estimated_cost_usd"),
            "cost_source": usage_combined.get("cost_source"),
            "prompt_file": manifest.get("prompt_file"),
            "eer_input_file": manifest.get("eer_input_file"),
            "output_format_file": manifest.get("output_format_file"),
            "published_output_file": manifest.get("published_output_file"),
            "source_file": str(manifest_path),
        }

        rows.append(row)
        by_run_id[str(run_id)] = row

        published = path_key(manifest.get("published_output_file"))
        if published:
            by_published_output[published] = row

    return rows, by_run_id, by_published_output


def collect_normalization_runs(
    normalization_runs_dir: Path,
    llm_by_published_output: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    by_run_id: Dict[str, Dict[str, Any]] = {}
    by_dir: Dict[str, Dict[str, Any]] = {}

    for manifest_path in find_json_files(normalization_runs_dir, "normalization_manifest.json"):
        try:
            manifest = read_json(manifest_path)
        except Exception as exc:
            rows.append({
                "source_file": str(manifest_path),
                "normalization_status": "read_error",
                "error_message": str(exc),
            })
            continue

        warnings_path = manifest_path.parent / "normalization_warnings.json"
        warnings = {}
        if warnings_path.exists():
            try:
                warnings = read_json(warnings_path)
            except Exception:
                warnings = {}

        run_id = manifest.get("run_id", manifest_path.parent.name)
        input_file = path_key(manifest.get("input_file"))
        linked_llm = llm_by_published_output.get(input_file, {})

        summary = manifest.get("normalization_summary", {}) or {}

        row = {
            "normalization_run_id": run_id,
            "normalization_run_dir": str(manifest_path.parent),
            "linked_llm_run_id": linked_llm.get("llm_run_id"),
            "dataset": manifest.get("dataset") or linked_llm.get("dataset"),
            "condition": manifest.get("condition") or linked_llm.get("condition"),
            "model": manifest.get("model") or linked_llm.get("model"),
            "model_key": linked_llm.get("model_key"),
            "provider": linked_llm.get("provider"),
            "input_file": manifest.get("input_file"),
            "input_sha256": manifest.get("input_sha256"),
            "num_tables": summary.get("num_tables"),
            "num_columns": summary.get("num_columns"),
            "num_primary_keys": summary.get("num_primary_keys"),
            "num_foreign_keys": summary.get("num_foreign_keys"),
            "num_relationship_tables": summary.get("num_relationship_tables"),
            "num_specialization_mappings": summary.get("num_specialization_mappings"),
            "num_mapping_decisions": summary.get("num_mapping_decisions"),
            "num_mapping_alternatives": summary.get("num_mapping_alternatives"),
            "num_warnings": manifest.get("num_warnings"),
            "warnings": warnings.get("warnings", []),
            "source_file": str(manifest_path),
        }

        rows.append(row)
        by_run_id[str(run_id)] = row
        by_dir[path_key(manifest_path.parent)] = row

    return rows, by_run_id, by_dir


def load_evaluation_entry(
    metrics_path: Path,
    normalization_by_dir: Dict[str, Dict[str, Any]],
    llm_by_run_id: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    metrics = read_json(metrics_path)
    eval_dir = metrics_path.parent
    manifest_path = eval_dir / "evaluation_manifest.json"

    manifest = {}
    if manifest_path.exists():
        manifest = read_json(manifest_path)

    run_id = manifest.get("run_id", eval_dir.name)
    norm_dir = path_key(manifest.get("normalization_run_dir"))
    norm_row = normalization_by_dir.get(norm_dir, {})

    llm_row = {}
    linked_llm_run_id = norm_row.get("linked_llm_run_id")
    if linked_llm_run_id:
        llm_row = llm_by_run_id.get(str(linked_llm_run_id), {})

    dataset = metrics.get("dataset") or manifest.get("dataset") or norm_row.get("dataset") or llm_row.get("dataset")
    model = metrics.get("model") or manifest.get("model") or norm_row.get("model") or llm_row.get("model")
    condition = metrics.get("condition") or manifest.get("condition") or norm_row.get("condition") or llm_row.get("condition")

    strict_global = metrics.get("strict", {}).get("global", {}) or {}
    matched_global = metrics.get("matched", {}).get("global", {}) or {}
    alt_global = metrics.get("alternative_aware", {}).get("global", {}) or {}

    mapping = metrics.get("mapping_alternatives", {}) or {}
    dist = metrics.get("structural_distance", {}) or {}

    strict_dist = dist.get("strict", {}) or {}
    matched_dist = dist.get("matched", {}) or {}
    alt_dist = dist.get("alternative_aware", {}) or {}

    row = {
        "evaluation_run_id": run_id,
        "evaluation_run_dir": str(eval_dir),
        "normalization_run_id": norm_row.get("normalization_run_id"),
        "llm_run_id": llm_row.get("llm_run_id"),
        "dataset": dataset,
        "condition": condition,
        "provider": llm_row.get("provider") or norm_row.get("provider"),
        "model_key": llm_row.get("model_key") or norm_row.get("model_key"),
        "model": model,
        "llm_status": llm_row.get("llm_status"),
        "dry_run": llm_row.get("dry_run"),
        "strict_precision": strict_global.get("precision"),
        "strict_recall": strict_global.get("recall"),
        "strict_f1": strict_global.get("f1"),
        "strict_tp": strict_global.get("tp"),
        "strict_fp": strict_global.get("fp"),
        "strict_fn": strict_global.get("fn"),
        "matched_precision": matched_global.get("precision"),
        "matched_recall": matched_global.get("recall"),
        "matched_f1": matched_global.get("f1"),
        "matched_tp": matched_global.get("tp"),
        "matched_fp": matched_global.get("fp"),
        "matched_fn": matched_global.get("fn"),
        "alternative_aware_precision": alt_global.get("precision"),
        "alternative_aware_recall": alt_global.get("recall"),
        "alternative_aware_f1": alt_global.get("f1"),
        "alternative_aware_tp": alt_global.get("tp"),
        "alternative_aware_fp": alt_global.get("fp"),
        "alternative_aware_fn": alt_global.get("fn"),
        "preferred_correct": mapping.get("preferred_correct"),
        "valid_alternative": mapping.get("valid_alternative"),
        "invalid_mapping": mapping.get("invalid_mapping"),
        "missing_mapping": mapping.get("missing_mapping"),
        "hallucinated_mapping": mapping.get("hallucinated_mapping"),
        "total_alternative_groups": mapping.get("total_alternative_groups"),
        "preferred_mapping_accuracy": mapping.get("preferred_mapping_accuracy"),
        "valid_mapping_accuracy": mapping.get("valid_mapping_accuracy"),
        "alternative_mapping_rate": mapping.get("alternative_mapping_rate"),
        "invalid_mapping_rate": mapping.get("invalid_mapping_rate"),
        "strict_distance": strict_dist.get("normalized_weighted_structural_distance"),
        "matched_distance": matched_dist.get("normalized_weighted_structural_distance"),
        "alternative_aware_distance": alt_dist.get("normalized_weighted_structural_distance"),
        "strict_weighted_distance": strict_dist.get("weighted_structural_manhattan_distance"),
        "matched_weighted_distance": matched_dist.get("weighted_structural_manhattan_distance"),
        "alternative_aware_weighted_distance": alt_dist.get("weighted_structural_manhattan_distance"),
        "distance_reduction_from_matching": dist.get("distance_reduction_from_matching"),
        "distance_reduction_from_alternatives": dist.get("distance_reduction_from_alternatives"),
        "input_tokens": llm_row.get("input_tokens"),
        "output_tokens": llm_row.get("output_tokens"),
        "total_tokens": llm_row.get("total_tokens"),
        "cached_input_tokens": llm_row.get("cached_input_tokens"),
        "reasoning_tokens": llm_row.get("reasoning_tokens"),
        "latency_seconds": llm_row.get("latency_seconds"),
        "tokens_per_second": llm_row.get("tokens_per_second"),
        "estimated_cost_usd": llm_row.get("estimated_cost_usd"),
        "num_tables": norm_row.get("num_tables"),
        "num_columns": norm_row.get("num_columns"),
        "num_primary_keys": norm_row.get("num_primary_keys"),
        "num_foreign_keys": norm_row.get("num_foreign_keys"),
        "num_relationship_tables": norm_row.get("num_relationship_tables"),
        "num_warnings": norm_row.get("num_warnings"),
        "metrics_file": str(metrics_path),
        "manifest_file": str(manifest_path) if manifest_path.exists() else "",
    }

    return row


def collect_evaluation_runs(
    evaluation_runs_dir: Path,
    normalization_by_dir: Dict[str, Dict[str, Any]],
    llm_by_run_id: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    summary_rows: List[Dict[str, Any]] = []
    component_rows: List[Dict[str, Any]] = []
    error_detail_rows: List[Dict[str, Any]] = []

    for metrics_path in find_json_files(evaluation_runs_dir, "evaluation_metrics.json"):
        try:
            row = load_evaluation_entry(metrics_path, normalization_by_dir, llm_by_run_id)
            summary_rows.append(row)
        except Exception as exc:
            summary_rows.append({
                "evaluation_run_dir": str(metrics_path.parent),
                "metrics_file": str(metrics_path),
                "evaluation_status": "read_error",
                "error_message": str(exc),
            })
            continue

        eval_dir = metrics_path.parent
        component_path = eval_dir / "component_metrics.csv"
        for comp_row in read_csv(component_path):
            comp_row = dict(comp_row)
            comp_row.update({
                "evaluation_run_id": row.get("evaluation_run_id"),
                "dataset": row.get("dataset"),
                "condition": row.get("condition"),
                "provider": row.get("provider"),
                "model_key": row.get("model_key"),
                "model": row.get("model"),
            })
            component_rows.append(comp_row)

        errors_path = eval_dir / "evaluation_errors.csv"
        for err_row in read_csv(errors_path):
            err_row = dict(err_row)
            err_row.update({
                "evaluation_run_id": row.get("evaluation_run_id"),
                "dataset": row.get("dataset"),
                "condition": row.get("condition"),
                "provider": row.get("provider"),
                "model_key": row.get("model_key"),
                "model": row.get("model"),
            })
            error_detail_rows.append(err_row)

    return summary_rows, component_rows, error_detail_rows


def build_error_counts(summary_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for row in summary_rows:
        for mode in ["strict", "matched", "alternative_aware"]:
            rows.append({
                "evaluation_run_id": row.get("evaluation_run_id"),
                "dataset": row.get("dataset"),
                "condition": row.get("condition"),
                "provider": row.get("provider"),
                "model_key": row.get("model_key"),
                "model": row.get("model"),
                "mode": mode,
                "tp": row.get(f"{mode}_tp"),
                "fp": row.get(f"{mode}_fp"),
                "fn": row.get(f"{mode}_fn"),
                "precision": row.get(f"{mode}_precision"),
                "recall": row.get(f"{mode}_recall"),
                "f1": row.get(f"{mode}_f1"),
                "distance": row.get(f"{mode}_distance"),
                "weighted_distance": row.get(f"{mode}_weighted_distance"),
                "invalid_mapping_rate": row.get("invalid_mapping_rate"),
                "valid_mapping_accuracy": row.get("valid_mapping_accuracy"),
            })

    return rows


def build_cost_quality(summary_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for row in summary_rows:
        cost = to_float(row.get("estimated_cost_usd"))
        alt_f1 = to_float(row.get("alternative_aware_f1"))
        matched_f1 = to_float(row.get("matched_f1"))
        valid_acc = to_float(row.get("valid_mapping_accuracy"))

        rows.append({
            "evaluation_run_id": row.get("evaluation_run_id"),
            "llm_run_id": row.get("llm_run_id"),
            "dataset": row.get("dataset"),
            "condition": row.get("condition"),
            "provider": row.get("provider"),
            "model_key": row.get("model_key"),
            "model": row.get("model"),
            "alternative_aware_f1": alt_f1,
            "matched_f1": matched_f1,
            "valid_mapping_accuracy": valid_acc,
            "alternative_aware_distance": row.get("alternative_aware_distance"),
            "estimated_cost_usd": cost,
            "latency_seconds": row.get("latency_seconds"),
            "tokens_per_second": row.get("tokens_per_second"),
            "input_tokens": row.get("input_tokens"),
            "output_tokens": row.get("output_tokens"),
            "total_tokens": row.get("total_tokens"),
            "cost_per_alternative_aware_f1": safe_div(cost, alt_f1),
            "cost_per_matched_f1": safe_div(cost, matched_f1),
            "cost_per_valid_mapping_accuracy": safe_div(cost, valid_acc),
        })

    return rows


def group_rows(rows: List[Dict[str, Any]], keys: List[str]) -> Dict[Tuple[Any, ...], List[Dict[str, Any]]]:
    grouped: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = tuple(row.get(k) for k in keys)
        grouped[key].append(row)
    return grouped


def summarize_group(rows: List[Dict[str, Any]], key_values: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **key_values,
        "num_runs": len(rows),
        "mean_strict_f1": mean(row.get("strict_f1") for row in rows),
        "mean_matched_f1": mean(row.get("matched_f1") for row in rows),
        "mean_alternative_aware_f1": mean(row.get("alternative_aware_f1") for row in rows),
        "mean_strict_distance": mean(row.get("strict_distance") for row in rows),
        "mean_matched_distance": mean(row.get("matched_distance") for row in rows),
        "mean_alternative_aware_distance": mean(row.get("alternative_aware_distance") for row in rows),
        "mean_distance_reduction_from_matching": mean(row.get("distance_reduction_from_matching") for row in rows),
        "mean_distance_reduction_from_alternatives": mean(row.get("distance_reduction_from_alternatives") for row in rows),
        "mean_preferred_mapping_accuracy": mean(row.get("preferred_mapping_accuracy") for row in rows),
        "mean_valid_mapping_accuracy": mean(row.get("valid_mapping_accuracy") for row in rows),
        "mean_alternative_mapping_rate": mean(row.get("alternative_mapping_rate") for row in rows),
        "mean_invalid_mapping_rate": mean(row.get("invalid_mapping_rate") for row in rows),
        "mean_latency_seconds": mean(row.get("latency_seconds") for row in rows),
        "mean_input_tokens": mean(row.get("input_tokens") for row in rows),
        "mean_output_tokens": mean(row.get("output_tokens") for row in rows),
        "mean_total_tokens": mean(row.get("total_tokens") for row in rows),
        "mean_estimated_cost_usd": mean(row.get("estimated_cost_usd") for row in rows),
        "sum_estimated_cost_usd": sum_numeric(row.get("estimated_cost_usd") for row in rows),
    }


def build_group_summary(rows: List[Dict[str, Any]], keys: List[str]) -> List[Dict[str, Any]]:
    output = []
    grouped = group_rows(rows, keys)

    for key_tuple, group in grouped.items():
        key_values = {k: v for k, v in zip(keys, key_tuple)}
        output.append(summarize_group(group, key_values))

    return sorted(output, key=lambda r: tuple(str(r.get(k, "")) for k in keys))


def add_dataset_complexity(rows: List[Dict[str, Any]], complexities: Dict[str, str]) -> None:
    for row in rows:
        dataset = row.get("dataset")
        if dataset and "dataset_complexity" not in row:
            row["dataset_complexity"] = complexities.get(str(dataset), "")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate benchmark result files.")
    parser.add_argument("--llm-runs-dir", default="results/llm_runs", help="LLM runs directory.")
    parser.add_argument("--normalization-runs-dir", default="results/normalization_runs", help="Normalization runs directory.")
    parser.add_argument("--evaluation-runs-dir", default="results/evaluation_runs", help="Evaluation runs directory.")
    parser.add_argument("--datasets-dir", default="datasets", help="Datasets directory.")
    parser.add_argument("--output-dir", default="results/aggregate_runs", help="Aggregate output base directory.")
    parser.add_argument("--run-id", default=None, help="Optional aggregate run id.")
    parser.add_argument("--notes", default="", help="Optional notes.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    llm_runs_dir = Path(args.llm_runs_dir)
    normalization_runs_dir = Path(args.normalization_runs_dir)
    evaluation_runs_dir = Path(args.evaluation_runs_dir)
    datasets_dir = Path(args.datasets_dir)

    run_id = args.run_id or build_run_id("aggregate")
    output_dir = Path(args.output_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    complexities = load_dataset_complexities(datasets_dir)

    llm_rows, llm_by_run_id, llm_by_published = collect_llm_runs(llm_runs_dir)
    norm_rows, norm_by_run_id, norm_by_dir = collect_normalization_runs(normalization_runs_dir, llm_by_published)
    summary_rows, component_rows, error_detail_rows = collect_evaluation_runs(evaluation_runs_dir, norm_by_dir, llm_by_run_id)

    for table in [llm_rows, norm_rows, summary_rows, component_rows, error_detail_rows]:
        add_dataset_complexity(table, complexities)

    error_counts_rows = build_error_counts(summary_rows)
    cost_quality_rows = build_cost_quality(summary_rows)

    by_model_rows = build_group_summary(summary_rows, ["provider", "model_key", "model"])
    by_condition_rows = build_group_summary(summary_rows, ["condition"])
    by_dataset_complexity_rows = build_group_summary(summary_rows, ["dataset_complexity"])
    by_dataset_condition_rows = build_group_summary(summary_rows, ["dataset", "condition"])
    by_model_condition_rows = build_group_summary(summary_rows, ["provider", "model_key", "model", "condition"])

    write_csv(output_dir / "aggregate_llm_runs.csv", llm_rows)
    write_csv(output_dir / "aggregate_normalization_summary.csv", norm_rows)
    write_csv(output_dir / "aggregate_run_summary.csv", summary_rows)
    write_csv(output_dir / "aggregate_component_metrics.csv", component_rows)
    write_csv(output_dir / "aggregate_evaluation_errors_detail.csv", error_detail_rows)
    write_csv(output_dir / "aggregate_error_counts.csv", error_counts_rows)
    write_csv(output_dir / "aggregate_cost_quality.csv", cost_quality_rows)
    write_csv(output_dir / "aggregate_by_model.csv", by_model_rows)
    write_csv(output_dir / "aggregate_by_condition.csv", by_condition_rows)
    write_csv(output_dir / "aggregate_by_dataset_complexity.csv", by_dataset_complexity_rows)
    write_csv(output_dir / "aggregate_by_dataset_condition.csv", by_dataset_condition_rows)
    write_csv(output_dir / "aggregate_by_model_condition.csv", by_model_condition_rows)

    manifest = {
        "run_id": run_id,
        "created_at_utc": now_utc_iso(),
        "script": "scripts/aggregate_results.py",
        "llm_runs_dir": str(llm_runs_dir),
        "normalization_runs_dir": str(normalization_runs_dir),
        "evaluation_runs_dir": str(evaluation_runs_dir),
        "datasets_dir": str(datasets_dir),
        "output_dir": str(output_dir),
        "notes": args.notes,
        "counts": {
            "llm_runs": len(llm_rows),
            "normalization_runs": len(norm_rows),
            "evaluation_runs": len(summary_rows),
            "component_metric_rows": len(component_rows),
            "error_detail_rows": len(error_detail_rows),
            "error_count_rows": len(error_counts_rows),
            "cost_quality_rows": len(cost_quality_rows),
            "by_model_rows": len(by_model_rows),
            "by_condition_rows": len(by_condition_rows),
            "by_dataset_complexity_rows": len(by_dataset_complexity_rows),
        },
        "generated_files": [
            "aggregate_llm_runs.csv",
            "aggregate_normalization_summary.csv",
            "aggregate_run_summary.csv",
            "aggregate_component_metrics.csv",
            "aggregate_evaluation_errors_detail.csv",
            "aggregate_error_counts.csv",
            "aggregate_cost_quality.csv",
            "aggregate_by_model.csv",
            "aggregate_by_condition.csv",
            "aggregate_by_dataset_complexity.csv",
            "aggregate_by_dataset_condition.csv",
            "aggregate_by_model_condition.csv",
            "aggregate_manifest.json",
        ],
    }

    write_json(output_dir / "aggregate_manifest.json", manifest)

    print("Aggregation completed.")
    print(f"Run ID: {run_id}")
    print(f"Output directory: {output_dir}")
    print(f"LLM runs: {len(llm_rows)}")
    print(f"Normalization runs: {len(norm_rows)}")
    print(f"Evaluation runs: {len(summary_rows)}")
    print(f"Component rows: {len(component_rows)}")
    print(f"Error detail rows: {len(error_detail_rows)}")


if __name__ == "__main__":
    main()
