#!/usr/bin/env python3
"""
Run normalization and evaluation in batch for LLM outputs.

This script reads LLM run manifests from results/llm_runs/, then calls:

1. scripts/normalize_output.py
2. scripts/evaluate_schema.py

for each eligible LLM output.

Main outputs:
- evaluation_batch_manifest.json
- evaluation_batch_runs.csv
- logs/*.stdout.txt
- logs/*.stderr.txt
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


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_run_part(value: Any) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value)).strip("_")


def build_batch_id(prefix: str = "evaluation_batch") -> str:
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


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = sorted({k for row in rows for k in row.keys()})

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def find_llm_manifests(llm_runs_dir: Path) -> List[Path]:
    if not llm_runs_dir.exists():
        return []
    return sorted(llm_runs_dir.glob("*/llm_run_manifest.json"))


def should_keep(value: Optional[str], only_value: Optional[str]) -> bool:
    if not only_value:
        return True
    return normalize_run_part(value or "") == normalize_run_part(only_value)


def resolve_response_file(manifest: Dict[str, Any], manifest_dir: Path) -> Path:
    published = manifest.get("published_output_file")

    if published:
        published_path = Path(str(published))
        if published_path.exists():
            return published_path

    return manifest_dir / "response_text.txt"


def build_gold_path(pattern: str, dataset: str) -> Path:
    return Path(pattern.format(dataset=dataset))


def build_child_run_id(batch_id: str, llm_run_id: str, suffix: str) -> str:
    return f"{normalize_run_part(batch_id)}_{normalize_run_part(llm_run_id)}_{suffix}"


def run_command(cmd: List[str], stdout_path: Path, stderr_path: Path) -> int:
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    return completed.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize and evaluate LLM outputs in batch."
    )

    parser.add_argument("--llm-runs-dir", default="results/llm_runs", help="Directory containing LLM run folders.")
    parser.add_argument("--output-dir", default="results/evaluation_batch_runs", help="Batch output base directory.")
    parser.add_argument("--normalization-output-dir", default="results/normalization_runs", help="Normalization output base directory.")
    parser.add_argument("--evaluation-output-dir", default="results/evaluation_runs", help="Evaluation output base directory.")
    parser.add_argument("--gold-pattern", default="datasets/{dataset}/ground_truth/logical_relational_gold.json", help="Pattern for gold file path.")
    parser.add_argument("--batch-id", default=None, help="Optional batch id.")
    parser.add_argument("--only-dataset", default=None, help="Only process one dataset.")
    parser.add_argument("--only-condition", default=None, help="Only process one condition.")
    parser.add_argument("--only-model", default=None, help="Only process one model key.")
    parser.add_argument("--max-runs", type=int, default=None, help="Maximum number of LLM runs to process.")
    parser.add_argument("--include-dry-run", action="store_true", help="Process dry-run outputs if they have response text.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing normalization/evaluation run folders.")
    parser.add_argument("--notes", default="", help="Optional notes.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    llm_runs_dir = Path(args.llm_runs_dir)
    batch_id = args.batch_id or build_batch_id()

    batch_dir = Path(args.output_dir) / batch_id
    logs_dir = batch_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    manifests = find_llm_manifests(llm_runs_dir)

    rows: List[Dict[str, Any]] = []
    selected_count = 0

    started_at = now_utc_iso()

    for manifest_path in manifests:
        manifest_dir = manifest_path.parent

        try:
            manifest = read_json(manifest_path)
        except Exception as exc:
            rows.append({
                "llm_manifest_file": str(manifest_path),
                "status": "read_error",
                "error_message": str(exc),
            })
            continue

        llm_run_id = manifest.get("run_id", manifest_dir.name)
        dataset = manifest.get("dataset")
        condition = manifest.get("condition")
        model_key = manifest.get("model_key")
        model = manifest.get("model") or model_key
        provider = manifest.get("provider")
        llm_status = manifest.get("status")
        dry_run = bool(manifest.get("dry_run"))

        if not should_keep(dataset, args.only_dataset):
            continue
        if not should_keep(condition, args.only_condition):
            continue
        if not should_keep(model_key, args.only_model):
            continue
        if dry_run and not args.include_dry_run:
            rows.append({
                "llm_run_id": llm_run_id,
                "dataset": dataset,
                "condition": condition,
                "model_key": model_key,
                "provider": provider,
                "status": "skipped",
                "reason": "dry_run_output_skipped",
            })
            continue

        response_file = resolve_response_file(manifest, manifest_dir)

        if not response_file.exists():
            rows.append({
                "llm_run_id": llm_run_id,
                "dataset": dataset,
                "condition": condition,
                "model_key": model_key,
                "provider": provider,
                "status": "skipped",
                "reason": f"response_file_not_found: {response_file}",
            })
            continue

        if response_file.stat().st_size == 0:
            rows.append({
                "llm_run_id": llm_run_id,
                "dataset": dataset,
                "condition": condition,
                "model_key": model_key,
                "provider": provider,
                "status": "skipped",
                "reason": "empty_response_text",
                "response_file": str(response_file),
            })
            continue

        gold_path = build_gold_path(args.gold_pattern, str(dataset))

        if not gold_path.exists():
            rows.append({
                "llm_run_id": llm_run_id,
                "dataset": dataset,
                "condition": condition,
                "model_key": model_key,
                "provider": provider,
                "status": "skipped",
                "reason": f"gold_file_not_found: {gold_path}",
                "response_file": str(response_file),
            })
            continue

        selected_count += 1

        if args.max_runs is not None and selected_count > args.max_runs:
            break

        normalization_run_id = build_child_run_id(batch_id, str(llm_run_id), "normalization")
        evaluation_run_id = build_child_run_id(batch_id, str(llm_run_id), "evaluation")

        normalization_dir = Path(args.normalization_output_dir) / normalization_run_id
        evaluation_dir = Path(args.evaluation_output_dir) / evaluation_run_id

        if not args.force and normalization_dir.exists() and evaluation_dir.exists():
            rows.append({
                "llm_run_id": llm_run_id,
                "dataset": dataset,
                "condition": condition,
                "model_key": model_key,
                "provider": provider,
                "normalization_run_id": normalization_run_id,
                "evaluation_run_id": evaluation_run_id,
                "status": "skipped",
                "reason": "normalization_and_evaluation_outputs_already_exist",
            })
            continue

        norm_stdout = logs_dir / f"{normalization_run_id}.stdout.txt"
        norm_stderr = logs_dir / f"{normalization_run_id}.stderr.txt"
        eval_stdout = logs_dir / f"{evaluation_run_id}.stdout.txt"
        eval_stderr = logs_dir / f"{evaluation_run_id}.stderr.txt"

        norm_cmd = [
            sys.executable,
            "scripts/normalize_output.py",
            "--input", str(response_file),
            "--dataset", str(dataset),
            "--model", str(model_key or model),
            "--condition", str(condition),
            "--output-dir", args.normalization_output_dir,
            "--run-id", normalization_run_id,
            "--prompt-file", str(manifest.get("prompt_file") or ""),
            "--input-eer-file", str(manifest.get("eer_input_file") or ""),
            "--notes", f"Evaluation batch {batch_id}. Source LLM run: {llm_run_id}. {args.notes}".strip(),
        ]

        norm_return_code = run_command(norm_cmd, norm_stdout, norm_stderr)

        if norm_return_code != 0:
            rows.append({
                "llm_run_id": llm_run_id,
                "dataset": dataset,
                "condition": condition,
                "model_key": model_key,
                "provider": provider,
                "normalization_run_id": normalization_run_id,
                "evaluation_run_id": evaluation_run_id,
                "status": "normalization_error",
                "normalization_return_code": norm_return_code,
                "normalization_stdout": str(norm_stdout),
                "normalization_stderr": str(norm_stderr),
                "response_file": str(response_file),
            })
            continue

        normalized_schema = normalization_dir / "normalized_schema.json"

        eval_cmd = [
            sys.executable,
            "scripts/evaluate_schema.py",
            "--gold", str(gold_path),
            "--prediction", str(normalized_schema),
            "--dataset", str(dataset),
            "--model", str(model_key or model),
            "--condition", str(condition),
            "--output-dir", args.evaluation_output_dir,
            "--run-id", evaluation_run_id,
            "--normalization-run-dir", str(normalization_dir),
            "--notes", f"Evaluation batch {batch_id}. Source LLM run: {llm_run_id}. {args.notes}".strip(),
        ]

        eval_return_code = run_command(eval_cmd, eval_stdout, eval_stderr)

        if eval_return_code != 0:
            rows.append({
                "llm_run_id": llm_run_id,
                "dataset": dataset,
                "condition": condition,
                "model_key": model_key,
                "provider": provider,
                "normalization_run_id": normalization_run_id,
                "evaluation_run_id": evaluation_run_id,
                "status": "evaluation_error",
                "normalization_return_code": norm_return_code,
                "evaluation_return_code": eval_return_code,
                "normalization_stdout": str(norm_stdout),
                "normalization_stderr": str(norm_stderr),
                "evaluation_stdout": str(eval_stdout),
                "evaluation_stderr": str(eval_stderr),
                "response_file": str(response_file),
            })
            continue

        rows.append({
            "llm_run_id": llm_run_id,
            "dataset": dataset,
            "condition": condition,
            "model_key": model_key,
            "model": model,
            "provider": provider,
            "llm_status": llm_status,
            "dry_run": dry_run,
            "normalization_run_id": normalization_run_id,
            "evaluation_run_id": evaluation_run_id,
            "status": "success",
            "normalization_return_code": norm_return_code,
            "evaluation_return_code": eval_return_code,
            "response_file": str(response_file),
            "gold_file": str(gold_path),
            "normalization_run_dir": str(normalization_dir),
            "evaluation_run_dir": str(evaluation_dir),
            "normalization_stdout": str(norm_stdout),
            "normalization_stderr": str(norm_stderr),
            "evaluation_stdout": str(eval_stdout),
            "evaluation_stderr": str(eval_stderr),
        })

        print(f"{llm_run_id}: success")

    finished_at = now_utc_iso()

    write_csv(batch_dir / "evaluation_batch_runs.csv", rows)

    manifest = {
        "batch_id": batch_id,
        "created_at_utc": started_at,
        "finished_at_utc": finished_at,
        "script": "scripts/run_evaluation_batch.py",
        "llm_runs_dir": str(llm_runs_dir),
        "normalization_output_dir": args.normalization_output_dir,
        "evaluation_output_dir": args.evaluation_output_dir,
        "gold_pattern": args.gold_pattern,
        "output_dir": str(batch_dir),
        "filters": {
            "only_dataset": args.only_dataset,
            "only_condition": args.only_condition,
            "only_model": args.only_model,
            "max_runs": args.max_runs,
            "include_dry_run": args.include_dry_run,
            "force": args.force,
        },
        "notes": args.notes,
        "counts": {
            "rows": len(rows),
            "success": sum(1 for row in rows if row.get("status") == "success"),
            "skipped": sum(1 for row in rows if row.get("status") == "skipped"),
            "normalization_error": sum(1 for row in rows if row.get("status") == "normalization_error"),
            "evaluation_error": sum(1 for row in rows if row.get("status") == "evaluation_error"),
            "read_error": sum(1 for row in rows if row.get("status") == "read_error"),
        },
        "generated_files": [
            "evaluation_batch_manifest.json",
            "evaluation_batch_runs.csv",
            "logs/*.stdout.txt",
            "logs/*.stderr.txt",
        ],
    }

    write_json(batch_dir / "evaluation_batch_manifest.json", manifest)

    print("Evaluation batch completed.")
    print(f"Batch ID: {batch_id}")
    print(f"Batch directory: {batch_dir}")
    print(f"Success: {manifest['counts']['success']}")
    print(f"Skipped: {manifest['counts']['skipped']}")
    print(f"Normalization errors: {manifest['counts']['normalization_error']}")
    print(f"Evaluation errors: {manifest['counts']['evaluation_error']}")


if __name__ == "__main__":
    main()
