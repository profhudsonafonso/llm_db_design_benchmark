#!/usr/bin/env python3
"""
Run a batch of LLM experiments from an experiment matrix.

This script expands combinations of:

- datasets;
- model keys;
- prompt conditions;

and calls scripts/run_llm_experiments.py for each run.

It writes a reproducible batch folder with:

- batch_manifest.json;
- batch_runs.csv;
- stdout/stderr logs for each run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a dictionary: {path}")
    return data


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
            writer.writerow(row)


def normalize_run_part(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value)).strip("_")


def build_batch_id(prefix: str = "batch") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{normalize_run_part(prefix)}_{timestamp}"


def filter_enabled(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [item for item in items if item.get("enabled", True)]


def should_keep(value: str, allowed: Optional[str]) -> bool:
    if not allowed:
        return True
    return normalize_run_part(value) == normalize_run_part(allowed)


def build_run_id(batch_id: str, dataset: str, model_key: str, condition: str) -> str:
    return "_".join([
        normalize_run_part(batch_id),
        normalize_run_part(dataset),
        normalize_run_part(model_key),
        normalize_run_part(condition),
    ])


def command_to_string(cmd: List[str]) -> str:
    return " ".join(cmd)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run batch LLM experiments from a matrix.")
    parser.add_argument("--matrix", default="configs/experiment_matrix.yaml", help="Experiment matrix YAML.")
    parser.add_argument("--models-config", default="configs/models.yaml", help="Models config YAML.")
    parser.add_argument("--provider-settings", default="configs/provider_settings.yaml", help="Provider settings YAML.")
    parser.add_argument("--pricing-config", default="configs/model_pricing.yaml", help="Pricing config YAML.")
    parser.add_argument("--output-dir", default="results/batch_runs", help="Batch output base directory.")
    parser.add_argument("--batch-id", default=None, help="Optional batch id.")
    parser.add_argument("--only-dataset", default=None, help="Run only one dataset.")
    parser.add_argument("--only-condition", default=None, help="Run only one condition.")
    parser.add_argument("--only-model", default=None, help="Run only one model key.")
    parser.add_argument("--max-runs", type=int, default=None, help="Maximum number of runs.")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode for all runs.")
    parser.add_argument("--execute", action="store_true", help="Execute provider calls instead of dry-run defaults.")
    parser.add_argument("--notes", default="", help="Optional notes.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    matrix_path = Path(args.matrix)
    if not matrix_path.exists():
        raise FileNotFoundError(f"Matrix file not found: {matrix_path}")

    matrix = load_yaml(matrix_path)

    batch_id = args.batch_id or build_batch_id("llm_batch")
    batch_dir = Path(args.output_dir) / batch_id
    logs_dir = batch_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    datasets = filter_enabled(matrix.get("datasets", []))
    conditions_dict = matrix.get("conditions", {}) or {}
    model_keys = matrix.get("model_keys", []) or []
    defaults = matrix.get("defaults", {}) or {}

    rows: List[Dict[str, Any]] = []
    planned_runs = []

    for dataset in datasets:
        dataset_name = dataset.get("name")
        eer_input_file = dataset.get("eer_input_file")

        if not should_keep(dataset_name, args.only_dataset):
            continue

        for condition_name, condition_cfg in conditions_dict.items():
            if not condition_cfg.get("enabled", True):
                continue

            if not should_keep(condition_name, args.only_condition):
                continue

            prompt_file = condition_cfg.get("prompt_file")

            for model_key in model_keys:
                if not should_keep(model_key, args.only_model):
                    continue

                planned_runs.append({
                    "dataset": dataset_name,
                    "eer_input_file": eer_input_file,
                    "condition": condition_name,
                    "prompt_file": prompt_file,
                    "model_key": model_key,
                    "requires_previous_output": condition_cfg.get("requires_previous_output", False),
                    "requires_validation_report": condition_cfg.get("requires_validation_report", False),
                })

    if args.max_runs is not None:
        planned_runs = planned_runs[: args.max_runs]

    started_at = now_utc_iso()

    for idx, run in enumerate(planned_runs, start=1):
        dataset = run["dataset"]
        condition = run["condition"]
        model_key = run["model_key"]
        run_id = build_run_id(batch_id, dataset, model_key, condition)

        stdout_path = logs_dir / f"{run_id}.stdout.txt"
        stderr_path = logs_dir / f"{run_id}.stderr.txt"

        status = "planned"
        return_code = None
        error_message = ""

        if run["requires_previous_output"] or run["requires_validation_report"]:
            status = "skipped"
            error_message = "C4 requires previous output and validation report. Configure these before batch execution."
        elif not Path(run["eer_input_file"]).exists():
            status = "skipped"
            error_message = f"EER input file not found: {run['eer_input_file']}"
        elif not Path(run["prompt_file"]).exists():
            status = "skipped"
            error_message = f"Prompt file not found: {run['prompt_file']}"
        else:
            dry_run_flag = args.dry_run or (defaults.get("dry_run", False) and not args.execute)

            cmd = [
                sys.executable,
                "scripts/run_llm_experiments.py",
                "--dataset", dataset,
                "--condition", condition,
                "--model-key", model_key,
                "--models-config", args.models_config,
                "--provider-settings", args.provider_settings,
                "--pricing-config", args.pricing_config,
                "--prompt-file", run["prompt_file"],
                "--eer-input-file", run["eer_input_file"],
                "--output-format-file", defaults.get("output_format_file", "docs/logical_relational_gold_template.json"),
                "--output-dir", defaults.get("llm_output_dir", "results/llm_runs"),
                "--publish-dir", defaults.get("published_output_dir", "llm_outputs"),
                "--run-id", run_id,
                "--notes", f"Batch run {batch_id}. {args.notes}".strip(),
            ]

            if dry_run_flag:
                cmd.append("--dry-run")

            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            stdout_path.write_text(completed.stdout, encoding="utf-8")
            stderr_path.write_text(completed.stderr, encoding="utf-8")

            return_code = completed.returncode
            status = "success" if completed.returncode == 0 else "error"
            error_message = completed.stderr.strip() if completed.returncode != 0 else ""

        row = {
            "batch_id": batch_id,
            "run_index": idx,
            "run_id": run_id,
            "dataset": dataset,
            "condition": condition,
            "model_key": model_key,
            "prompt_file": run["prompt_file"],
            "eer_input_file": run["eer_input_file"],
            "status": status,
            "return_code": return_code,
            "error_message": error_message,
            "stdout_log": str(stdout_path) if stdout_path.exists() else "",
            "stderr_log": str(stderr_path) if stderr_path.exists() else "",
            "llm_run_dir": str(Path(defaults.get("llm_output_dir", "results/llm_runs")) / run_id),
        }

        rows.append(row)

        print(f"[{idx}/{len(planned_runs)}] {run_id}: {status}")
        if error_message:
            print(f"  {error_message}")

    finished_at = now_utc_iso()

    write_csv(batch_dir / "batch_runs.csv", rows)

    manifest = {
        "batch_id": batch_id,
        "created_at_utc": started_at,
        "finished_at_utc": finished_at,
        "script": "scripts/run_llm_batch.py",
        "matrix_file": str(matrix_path),
        "matrix_sha256": file_sha256(matrix_path),
        "models_config": args.models_config,
        "provider_settings": args.provider_settings,
        "pricing_config": args.pricing_config,
        "num_planned_runs": len(planned_runs),
        "num_recorded_rows": len(rows),
        "num_success": sum(1 for row in rows if row["status"] == "success"),
        "num_error": sum(1 for row in rows if row["status"] == "error"),
        "num_skipped": sum(1 for row in rows if row["status"] == "skipped"),
        "filters": {
            "only_dataset": args.only_dataset,
            "only_condition": args.only_condition,
            "only_model": args.only_model,
            "max_runs": args.max_runs,
            "dry_run": args.dry_run,
            "execute": args.execute,
        },
        "notes": args.notes,
        "generated_files": [
            "batch_manifest.json",
            "batch_runs.csv",
            "logs/*.stdout.txt",
            "logs/*.stderr.txt",
        ],
    }

    write_json(batch_dir / "batch_manifest.json", manifest)

    print("Batch completed.")
    print(f"Batch ID: {batch_id}")
    print(f"Batch directory: {batch_dir}")
    print(f"Success: {manifest['num_success']}")
    print(f"Errors: {manifest['num_error']}")
    print(f"Skipped: {manifest['num_skipped']}")


if __name__ == "__main__":
    main()
