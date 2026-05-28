#!/usr/bin/env python3
"""
Run LLM experiments for the LLM Database Design Benchmark.

This script renders a prompt template using:
- a prompt-ready EER input Markdown file;
- the required output format specification;
- optional previous output and validation report for C4.

It supports multiple providers through adapter functions:
- ollama
- openai
- gemini
- anthropic
- manual
- dry-run mode

Every execution writes a reproducible run folder with:
- rendered_prompt.txt
- response_text.txt
- raw_response.json
- llm_run_manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import requests
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
        raise ValueError(f"Expected YAML root dictionary: {path}")
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_run_part(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value)).strip("_")


def build_run_id(dataset: str, model_key: str, condition: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return "_".join([
        normalize_run_part(dataset),
        normalize_run_part(model_key),
        normalize_run_part(condition),
        timestamp,
    ])


def render_prompt(
    prompt_template: str,
    eer_input_text: str,
    output_format_spec: str,
    previous_relational_json: Optional[str] = None,
    validation_report: Optional[str] = None,
) -> str:
    rendered = prompt_template
    rendered = rendered.replace("{{EER_INPUT_TEXT}}", eer_input_text)
    rendered = rendered.replace("{{OUTPUT_FORMAT_SPEC}}", output_format_spec)
    rendered = rendered.replace("{{PREVIOUS_RELATIONAL_JSON}}", previous_relational_json or "")
    rendered = rendered.replace("{{VALIDATION_REPORT}}", validation_report or "")
    return rendered


def read_required_file(path: Optional[str], label: str) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{label} file not found: {p}")
    return p.read_text(encoding="utf-8")


def get_provider_settings(settings: Dict[str, Any], provider: str) -> Dict[str, Any]:
    return (settings.get("providers") or {}).get(provider, {}) or {}


def get_api_key(provider_settings: Dict[str, Any]) -> Optional[str]:
    env_name = provider_settings.get("api_key_env")
    if not env_name:
        return None
    return os.environ.get(env_name)


def load_pricing_config(path: Optional[str]) -> Dict[str, Any]:
    """Load pricing configuration if available."""
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    return load_yaml(p)


def get_pricing_entry(
    pricing_config: Dict[str, Any],
    provider: str,
    model_name: str,
) -> Dict[str, Any]:
    """Return pricing entry for a provider/model pair."""
    pricing = pricing_config.get("pricing", {}) or {}
    provider_prices = pricing.get(provider, {}) or {}
    return provider_prices.get(model_name, {}) or {}


def ns_to_seconds(value: Any) -> Optional[float]:
    """Convert nanoseconds to seconds when possible."""
    if value is None:
        return None
    try:
        return float(value) / 1_000_000_000
    except Exception:
        return None


def extract_usage_openai(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract token usage from an OpenAI Responses API response."""
    usage = raw.get("usage", {}) or {}

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")

    input_details = usage.get("input_tokens_details", {}) or {}
    output_details = usage.get("output_tokens_details", {}) or {}

    cached_input_tokens = input_details.get("cached_tokens")
    reasoning_tokens = output_details.get("reasoning_tokens")

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": cached_input_tokens,
        "reasoning_tokens": reasoning_tokens,
        "provider_usage_raw": usage,
    }


def extract_usage_gemini(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract token usage from a Gemini generateContent response."""
    usage = raw.get("usageMetadata", {}) or {}

    input_tokens = usage.get("promptTokenCount")
    output_tokens = usage.get("candidatesTokenCount")
    reasoning_tokens = usage.get("thoughtsTokenCount")
    total_tokens = usage.get("totalTokenCount")

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": None,
        "reasoning_tokens": reasoning_tokens,
        "provider_usage_raw": usage,
    }


def extract_usage_anthropic(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract token usage from an Anthropic Messages API response."""
    usage = raw.get("usage", {}) or {}

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")

    cache_creation = usage.get("cache_creation_input_tokens")
    cache_read = usage.get("cache_read_input_tokens")

    cached_input_tokens = None
    if cache_creation is not None or cache_read is not None:
        cached_input_tokens = (cache_creation or 0) + (cache_read or 0)

    total_tokens = None
    if input_tokens is not None or output_tokens is not None:
        total_tokens = (input_tokens or 0) + (output_tokens or 0)

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": cached_input_tokens,
        "reasoning_tokens": None,
        "provider_usage_raw": usage,
    }


def extract_usage_ollama(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract token and timing usage from an Ollama /api/generate response."""
    input_tokens = raw.get("prompt_eval_count")
    output_tokens = raw.get("eval_count")

    total_tokens = None
    if input_tokens is not None or output_tokens is not None:
        total_tokens = (input_tokens or 0) + (output_tokens or 0)

    total_duration_seconds = ns_to_seconds(raw.get("total_duration"))
    load_duration_seconds = ns_to_seconds(raw.get("load_duration"))
    prompt_eval_duration_seconds = ns_to_seconds(raw.get("prompt_eval_duration"))
    eval_duration_seconds = ns_to_seconds(raw.get("eval_duration"))

    tokens_per_second = None
    if output_tokens and eval_duration_seconds and eval_duration_seconds > 0:
        tokens_per_second = output_tokens / eval_duration_seconds

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": None,
        "reasoning_tokens": None,
        "ollama_total_duration_seconds": total_duration_seconds,
        "ollama_load_duration_seconds": load_duration_seconds,
        "ollama_prompt_eval_duration_seconds": prompt_eval_duration_seconds,
        "ollama_eval_duration_seconds": eval_duration_seconds,
        "tokens_per_second": tokens_per_second,
        "provider_usage_raw": {
            "prompt_eval_count": raw.get("prompt_eval_count"),
            "eval_count": raw.get("eval_count"),
            "total_duration": raw.get("total_duration"),
            "load_duration": raw.get("load_duration"),
            "prompt_eval_duration": raw.get("prompt_eval_duration"),
            "eval_duration": raw.get("eval_duration"),
        },
    }


def extract_usage_by_provider(provider: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract usage metadata according to provider."""
    if provider == "openai":
        return extract_usage_openai(raw)
    if provider == "gemini":
        return extract_usage_gemini(raw)
    if provider == "anthropic":
        return extract_usage_anthropic(raw)
    if provider == "ollama":
        return extract_usage_ollama(raw)

    return {
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "cached_input_tokens": None,
        "reasoning_tokens": None,
        "provider_usage_raw": {},
    }


def estimate_cost_usd(
    usage: Dict[str, Any],
    pricing_entry: Dict[str, Any],
) -> Optional[float]:
    """Estimate API cost in USD from usage and prices per 1M tokens."""
    if not pricing_entry:
        return None

    input_price = pricing_entry.get("input_price_per_1m_usd")
    output_price = pricing_entry.get("output_price_per_1m_usd")
    cached_price = pricing_entry.get("cached_input_price_per_1m_usd")
    reasoning_price = pricing_entry.get("reasoning_price_per_1m_usd")

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    cached_tokens = usage.get("cached_input_tokens")
    reasoning_tokens = usage.get("reasoning_tokens")

    cost = 0.0
    has_any_price = False

    if input_tokens is not None and input_price is not None:
        uncached_input = input_tokens - (cached_tokens or 0)
        cost += max(uncached_input, 0) / 1_000_000 * float(input_price)
        has_any_price = True

    if cached_tokens is not None and cached_price is not None:
        cost += cached_tokens / 1_000_000 * float(cached_price)
        has_any_price = True

    if output_tokens is not None and output_price is not None:
        cost += output_tokens / 1_000_000 * float(output_price)
        has_any_price = True

    if reasoning_tokens is not None and reasoning_price is not None:
        cost += reasoning_tokens / 1_000_000 * float(reasoning_price)
        has_any_price = True

    if not has_any_price:
        return None

    return cost


def build_usage_and_cost(
    provider: str,
    model_name: str,
    raw_response: Dict[str, Any],
    latency_seconds: float,
    pricing_config: Dict[str, Any],
    pricing_config_path: Optional[str],
) -> Dict[str, Any]:
    """Build standardized usage and cost record."""
    usage = extract_usage_by_provider(provider, raw_response)
    pricing_entry = get_pricing_entry(pricing_config, provider, model_name)

    estimated_cost = estimate_cost_usd(usage, pricing_entry)

    tokens_per_second = usage.get("tokens_per_second")
    if tokens_per_second is None:
        output_tokens = usage.get("output_tokens")
        if output_tokens is not None and latency_seconds and latency_seconds > 0:
            tokens_per_second = output_tokens / latency_seconds

    return {
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "cached_input_tokens": usage.get("cached_input_tokens"),
        "reasoning_tokens": usage.get("reasoning_tokens"),
        "latency_seconds": latency_seconds,
        "tokens_per_second": tokens_per_second,
        "estimated_cost_usd": estimated_cost,
        "cost_source": pricing_config_path,
        "pricing_entry": pricing_entry,
        "provider_usage_raw": usage.get("provider_usage_raw", {}),
        "ollama_total_duration_seconds": usage.get("ollama_total_duration_seconds"),
        "ollama_load_duration_seconds": usage.get("ollama_load_duration_seconds"),
        "ollama_prompt_eval_duration_seconds": usage.get("ollama_prompt_eval_duration_seconds"),
        "ollama_eval_duration_seconds": usage.get("ollama_eval_duration_seconds"),
    }


def extract_openai_text(raw: Dict[str, Any]) -> str:
    if "output_text" in raw and raw["output_text"]:
        return str(raw["output_text"])

    chunks = []
    for item in raw.get("output", []) or []:
        for content in item.get("content", []) or []:
            if isinstance(content, dict):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    chunks.append(str(content["text"]))

    return "\n".join(chunks).strip()


def call_openai(prompt: str, model_cfg: Dict[str, Any], provider_settings: Dict[str, Any]) -> Dict[str, Any]:
    api_key = get_api_key(provider_settings)
    if not api_key:
        raise RuntimeError("Missing OpenAI API key. Set the environment variable configured in provider_settings.yaml.")

    base_url = provider_settings.get("base_url", "https://api.openai.com/v1").rstrip("/")
    url = f"{base_url}/responses"

    payload: Dict[str, Any] = {
        "model": model_cfg["model"],
        "input": prompt,
    }

    if model_cfg.get("temperature") is not None:
        payload["temperature"] = model_cfg.get("temperature")

    if model_cfg.get("max_tokens"):
        payload["max_output_tokens"] = model_cfg.get("max_tokens")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    timeout = int(provider_settings.get("timeout_seconds", 300))
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    raw = response.json()

    return {
        "provider": "openai",
        "raw_response": raw,
        "response_text": extract_openai_text(raw),
    }


def extract_gemini_text(raw: Dict[str, Any]) -> str:
    chunks = []
    for candidate in raw.get("candidates", []) or []:
        content = candidate.get("content", {}) or {}
        for part in content.get("parts", []) or []:
            if "text" in part:
                chunks.append(str(part["text"]))
    return "\n".join(chunks).strip()


def call_gemini(prompt: str, model_cfg: Dict[str, Any], provider_settings: Dict[str, Any]) -> Dict[str, Any]:
    api_key = get_api_key(provider_settings)
    if not api_key:
        raise RuntimeError("Missing Gemini API key. Set the environment variable configured in provider_settings.yaml.")

    base_url = provider_settings.get("base_url", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    model_name = model_cfg["model"]
    url = f"{base_url}/models/{model_name}:generateContent"

    generation_config: Dict[str, Any] = {}

    if model_cfg.get("temperature") is not None:
        generation_config["temperature"] = model_cfg.get("temperature")

    if model_cfg.get("max_tokens"):
        generation_config["maxOutputTokens"] = model_cfg.get("max_tokens")

    if model_cfg.get("response_mime_type"):
        generation_config["responseMimeType"] = model_cfg.get("response_mime_type")

    payload: Dict[str, Any] = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    if generation_config:
        payload["generationConfig"] = generation_config

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    timeout = int(provider_settings.get("timeout_seconds", 300))
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    raw = response.json()

    return {
        "provider": "gemini",
        "raw_response": raw,
        "response_text": extract_gemini_text(raw),
    }


def extract_anthropic_text(raw: Dict[str, Any]) -> str:
    chunks = []
    for item in raw.get("content", []) or []:
        if isinstance(item, dict) and item.get("type") == "text":
            chunks.append(str(item.get("text", "")))
    return "\n".join(chunks).strip()


def call_anthropic(prompt: str, model_cfg: Dict[str, Any], provider_settings: Dict[str, Any]) -> Dict[str, Any]:
    api_key = get_api_key(provider_settings)
    if not api_key:
        raise RuntimeError("Missing Anthropic API key. Set the environment variable configured in provider_settings.yaml.")

    base_url = provider_settings.get("base_url", "https://api.anthropic.com/v1").rstrip("/")
    url = f"{base_url}/messages"

    payload: Dict[str, Any] = {
        "model": model_cfg["model"],
        "max_tokens": int(model_cfg.get("max_tokens", 8192)),
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    if model_cfg.get("temperature") is not None:
        payload["temperature"] = model_cfg.get("temperature")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": provider_settings.get("anthropic_version", "2023-06-01"),
    }

    timeout = int(provider_settings.get("timeout_seconds", 300))
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    raw = response.json()

    return {
        "provider": "anthropic",
        "raw_response": raw,
        "response_text": extract_anthropic_text(raw),
    }


def call_ollama(prompt: str, model_cfg: Dict[str, Any], provider_settings: Dict[str, Any]) -> Dict[str, Any]:
    base_url = model_cfg.get("base_url") or provider_settings.get("base_url", "http://localhost:11434")
    url = f"{base_url.rstrip('/')}/api/generate"

    options: Dict[str, Any] = {}

    if model_cfg.get("temperature") is not None:
        options["temperature"] = model_cfg.get("temperature")

    if model_cfg.get("seed") is not None:
        options["seed"] = model_cfg.get("seed")

    if model_cfg.get("max_tokens"):
        options["num_predict"] = model_cfg.get("max_tokens")

    payload: Dict[str, Any] = {
        "model": model_cfg["model"],
        "prompt": prompt,
        "stream": False,
    }

    if options:
        payload["options"] = options

    if model_cfg.get("format"):
        payload["format"] = model_cfg.get("format")

    timeout = int(provider_settings.get("timeout_seconds", 300))
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    raw = response.json()

    return {
        "provider": "ollama",
        "raw_response": raw,
        "response_text": str(raw.get("response", "")).strip(),
    }


def call_manual(prompt: str, model_cfg: Dict[str, Any], provider_settings: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "provider": "manual",
        "raw_response": {
            "message": "Manual provider selected. No API call was made.",
            "model": model_cfg.get("model", "manual"),
        },
        "response_text": "",
    }


def call_provider(prompt: str, model_cfg: Dict[str, Any], provider_settings: Dict[str, Any]) -> Dict[str, Any]:
    provider = model_cfg.get("provider")

    if provider == "openai":
        return call_openai(prompt, model_cfg, provider_settings)
    if provider == "gemini":
        return call_gemini(prompt, model_cfg, provider_settings)
    if provider == "anthropic":
        return call_anthropic(prompt, model_cfg, provider_settings)
    if provider == "ollama":
        return call_ollama(prompt, model_cfg, provider_settings)
    if provider == "manual":
        return call_manual(prompt, model_cfg, provider_settings)

    raise ValueError(f"Unsupported provider: {provider}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one LLM experiment.")
    parser.add_argument("--dataset", required=True, help="Dataset name.")
    parser.add_argument("--condition", required=True, help="Condition: C1, C2, C3, or C4.")
    parser.add_argument("--model-key", required=True, help="Model key from configs/models.yaml.")
    parser.add_argument("--models-config", default="configs/models.yaml", help="Models config YAML.")
    parser.add_argument("--provider-settings", default="configs/provider_settings.yaml", help="Provider settings YAML.")
    parser.add_argument("--pricing-config", default="configs/model_pricing.yaml", help="Model pricing YAML.")
    parser.add_argument("--prompt-file", required=True, help="Prompt template file.")
    parser.add_argument("--eer-input-file", required=True, help="Prompt-ready EER input Markdown.")
    parser.add_argument("--output-format-file", default="docs/logical_relational_gold_template.json", help="Output format spec file.")
    parser.add_argument("--previous-output-file", default=None, help="Previous relational JSON for C4.")
    parser.add_argument("--validation-report-file", default=None, help="Validation report for C4.")
    parser.add_argument("--output-dir", default="results/llm_runs", help="Base output directory.")
    parser.add_argument("--publish-dir", default="llm_outputs", help="Base directory for published response_text outputs.")
    parser.add_argument("--run-id", default=None, help="Optional run id.")
    parser.add_argument("--dry-run", action="store_true", help="Render prompt and manifest but do not call a provider.")
    parser.add_argument("--notes", default="", help="Optional notes.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    models_config_path = Path(args.models_config)
    if not models_config_path.exists():
        raise FileNotFoundError(f"Models config not found: {models_config_path}")

    models_config = load_yaml(models_config_path)
    model_cfg = (models_config.get("models") or {}).get(args.model_key)

    if not model_cfg:
        raise KeyError(f"Model key not found in {models_config_path}: {args.model_key}")

    provider = model_cfg.get("provider")
    provider_settings_path = Path(args.provider_settings)

    provider_settings_all: Dict[str, Any] = {}
    if provider != "manual":
        if not provider_settings_path.exists():
            raise FileNotFoundError(
                f"Provider settings not found: {provider_settings_path}. "
                "Copy configs/provider_settings.example.yaml to configs/provider_settings.yaml."
            )
        provider_settings_all = load_yaml(provider_settings_path)

    provider_settings = get_provider_settings(provider_settings_all, provider)

    pricing_config_path = Path(args.pricing_config)
    pricing_config = load_pricing_config(str(pricing_config_path)) if pricing_config_path.exists() else {}

    prompt_template_path = Path(args.prompt_file)
    eer_input_path = Path(args.eer_input_file)
    output_format_path = Path(args.output_format_file)

    prompt_template = read_required_file(str(prompt_template_path), "Prompt template")
    eer_input_text = read_required_file(str(eer_input_path), "EER input")
    output_format_spec = read_required_file(str(output_format_path), "Output format")

    previous_output = read_required_file(args.previous_output_file, "Previous output")
    validation_report = read_required_file(args.validation_report_file, "Validation report")

    rendered_prompt = render_prompt(
        prompt_template=prompt_template,
        eer_input_text=eer_input_text,
        output_format_spec=output_format_spec,
        previous_relational_json=previous_output,
        validation_report=validation_report,
    )

    run_id = args.run_id or build_run_id(args.dataset, args.model_key, args.condition)
    output_dir = Path(args.output_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    rendered_prompt_path = output_dir / "rendered_prompt.txt"
    rendered_prompt_path.write_text(rendered_prompt, encoding="utf-8")

    start_time = time.time()
    error_message = None

    if args.dry_run:
        call_result = {
            "provider": provider,
            "raw_response": {
                "message": "Dry run. No provider call was made.",
                "model_key": args.model_key,
                "model": model_cfg.get("model"),
            },
            "response_text": "",
        }
        status = "dry_run"
    else:
        try:
            call_result = call_provider(rendered_prompt, model_cfg, provider_settings)
            status = "success"
        except Exception as exc:
            call_result = {
                "provider": provider,
                "raw_response": {
                    "error": str(exc),
                    "error_type": exc.__class__.__name__,
                },
                "response_text": "",
            }
            status = "error"
            error_message = str(exc)

    end_time = time.time()
    latency_seconds = end_time - start_time

    response_text = call_result.get("response_text", "")
    raw_response = call_result.get("raw_response", {})

    usage_and_cost = build_usage_and_cost(
        provider=provider,
        model_name=model_cfg.get("model"),
        raw_response=raw_response,
        latency_seconds=latency_seconds,
        pricing_config=pricing_config,
        pricing_config_path=str(pricing_config_path) if pricing_config_path.exists() else None,
    )
    response_text_path = output_dir / "response_text.txt"
    response_text_path.write_text(response_text, encoding="utf-8")

    raw_response_path = output_dir / "raw_response.json"
    write_json(raw_response_path, raw_response)

    usage_and_cost_path = output_dir / "usage_and_cost.json"
    write_json(usage_and_cost_path, usage_and_cost)

    published_output_path = None
    if response_text:
        publish_dir = Path(args.publish_dir) / args.dataset
        publish_dir.mkdir(parents=True, exist_ok=True)
        published_output_path = publish_dir / f"{run_id}_raw.txt"
        published_output_path.write_text(response_text, encoding="utf-8")

    manifest = {
        "run_id": run_id,
        "created_at_utc": now_utc_iso(),
        "script": "scripts/run_llm_experiments.py",
        "dataset": args.dataset,
        "condition": args.condition,
        "model_key": args.model_key,
        "provider": provider,
        "model": model_cfg.get("model"),
        "model_config": model_cfg,
        "status": status,
        "error_message": error_message,
        "latency_seconds": latency_seconds,
        "usage_and_cost": usage_and_cost,
        "pricing_config": str(pricing_config_path) if pricing_config_path.exists() else None,
        "pricing_config_sha256": file_sha256(pricing_config_path) if pricing_config_path.exists() else None,
        "models_config": str(models_config_path),
        "models_config_sha256": file_sha256(models_config_path),
        "provider_settings_file": str(provider_settings_path) if provider_settings_path.exists() else None,
        "prompt_file": str(prompt_template_path),
        "prompt_file_sha256": file_sha256(prompt_template_path),
        "eer_input_file": str(eer_input_path),
        "eer_input_file_sha256": file_sha256(eer_input_path),
        "output_format_file": str(output_format_path),
        "output_format_file_sha256": file_sha256(output_format_path),
        "previous_output_file": args.previous_output_file,
        "validation_report_file": args.validation_report_file,
        "output_dir": str(output_dir),
        "published_output_file": str(published_output_path) if published_output_path else None,
        "dry_run": args.dry_run,
        "notes": args.notes,
        "generated_files": [
            "rendered_prompt.txt",
            "response_text.txt",
            "raw_response.json",
            "llm_run_manifest.json",
        ],
    }

    write_json(output_dir / "llm_run_manifest.json", manifest)

    print("LLM run completed.")
    print(f"Run ID: {run_id}")
    print(f"Status: {status}")
    print(f"Provider: {provider}")
    print(f"Model: {model_cfg.get('model')}")
    print(f"Output directory: {output_dir}")
    print(f"Input tokens: {usage_and_cost.get('input_tokens')}")
    print(f"Output tokens: {usage_and_cost.get('output_tokens')}")
    print(f"Estimated cost USD: {usage_and_cost.get('estimated_cost_usd')}")
    if published_output_path:
        print(f"Published response: {published_output_path}")
    if error_message:
        print(f"Error: {error_message}")


if __name__ == "__main__":
    main()
