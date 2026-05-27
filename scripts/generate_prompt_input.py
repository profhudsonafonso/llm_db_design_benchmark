#!/usr/bin/env python3
"""
Generate prompt-ready textual EER input from conceptual_eer.yaml.

This script converts an expert-defined EER-YAML file into a Markdown text
input that can be inserted into the LLM prompt templates.

Main outputs:
- eer_input_text.md
- source_conceptual_eer.yaml
- prompt_input_manifest.json

Optional:
- publish a copy to datasets/<dataset>/prompt_inputs/eer_input_text.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import unicodedata
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: PyYAML. Install it with: pip install pyyaml"
    ) from exc


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


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def scalar(value: Any, default: str = "not_specified") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value if value.strip() else default
    return json.dumps(value, ensure_ascii=False)


def load_yaml(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a dictionary: {path}")
    return data


def md_list(items: List[Any], empty: str = "- none") -> str:
    clean = [scalar(item) for item in items if scalar(item) != "not_specified"]
    if not clean:
        return empty
    return "\n".join(f"- {item}" for item in clean)


def render_metadata(schema: Dict[str, Any]) -> str:
    meta = schema.get("schema_metadata", {}) or {}
    scope = schema.get("model_scope", {}) or {}
    complexity = schema.get("complexity_metadata", {}) or {}

    lines = []
    lines.append("# Textual EER Input")
    lines.append("")
    lines.append("This file was generated from an expert-defined EER-YAML file.")
    lines.append("It is used as controlled input for LLM conceptual-to-logical schema generation.")
    lines.append("")
    lines.append("## Schema Metadata")
    lines.append("")
    lines.append(f"- Schema ID: {scalar(meta.get('schema_id'))}")
    lines.append(f"- Dataset name: {scalar(meta.get('dataset_name'))}")
    lines.append(f"- Dataset complexity: {scalar(meta.get('dataset_complexity'))}")
    lines.append(f"- Version: {scalar(meta.get('version'))}")
    lines.append(f"- Source description: {scalar(meta.get('source_description'))}")
    lines.append(f"- Notes: {scalar(meta.get('notes'), default='none')}")
    lines.append("")
    lines.append("## Model Scope")
    lines.append("")
    lines.append("Included entities:")
    lines.append(md_list(as_list(scope.get("included_entities"))))
    lines.append("")
    lines.append("Excluded entities:")
    lines.append(md_list(as_list(scope.get("excluded_entities"))))
    lines.append("")
    lines.append(f"Inclusion criteria: {scalar(scope.get('inclusion_criteria'), default='none')}")
    lines.append(f"Exclusion criteria: {scalar(scope.get('exclusion_criteria'), default='none')}")
    lines.append("")
    lines.append("## Complexity Metadata")
    lines.append("")
    lines.append(f"- Number of entities: {scalar(complexity.get('number_of_entities'))}")
    lines.append(f"- Number of relationships: {scalar(complexity.get('number_of_relationships'))}")
    lines.append(f"- Number of attributes: {scalar(complexity.get('number_of_attributes'))}")
    lines.append(f"- Number of specializations: {scalar(complexity.get('number_of_specializations'))}")
    lines.append(f"- Number of weak entities: {scalar(complexity.get('number_of_weak_entities'))}")
    lines.append(f"- Number of multivalued attributes: {scalar(complexity.get('number_of_multivalued_attributes'))}")
    lines.append(f"- Number of relationship attributes: {scalar(complexity.get('number_of_relationship_attributes'))}")
    lines.append("")
    return "\n".join(lines)


def render_entities(schema: Dict[str, Any]) -> str:
    entities = as_list(schema.get("entities"))

    lines = []
    lines.append("## Entities")
    lines.append("")

    if not entities:
        lines.append("No entities specified.")
        lines.append("")
        return "\n".join(lines)

    for entity in entities:
        if not isinstance(entity, dict):
            continue

        name = scalar(entity.get("name"))
        lines.append(f"### Entity: {name}")
        lines.append("")
        lines.append(f"- ID: {scalar(entity.get('id'))}")
        lines.append(f"- Type: {scalar(entity.get('entity_type'))}")
        lines.append(f"- Description: {scalar(entity.get('description'), default='none')}")
        aliases = as_list(entity.get("aliases"))
        if aliases:
            lines.append(f"- Aliases: {', '.join(scalar(a) for a in aliases)}")
        else:
            lines.append("- Aliases: none")

        identifiers = entity.get("identifiers", {}) or {}
        primary = identifiers.get("primary", {}) or {}

        lines.append("")
        lines.append("Identifier:")
        lines.append(f"- Primary identifier name: {scalar(primary.get('name'))}")
        lines.append(f"- Primary identifier attributes: {', '.join(scalar(a) for a in as_list(primary.get('attributes'))) or 'none'}")
        lines.append(f"- Identifier type: {scalar(primary.get('identifier_type'))}")

        candidates = as_list(identifiers.get("candidates"))
        alternate_keys = as_list(identifiers.get("alternate_keys"))

        if candidates:
            lines.append("- Candidate identifiers:")
            for candidate in candidates:
                lines.append(f"  - {scalar(candidate)}")
        else:
            lines.append("- Candidate identifiers: none")

        if alternate_keys:
            lines.append("- Alternate keys:")
            for key in alternate_keys:
                if isinstance(key, dict):
                    attrs = ", ".join(scalar(a) for a in as_list(key.get("attributes")))
                    lines.append(f"  - {scalar(key.get('name'))}: {attrs}")
                else:
                    lines.append(f"  - {scalar(key)}")
        else:
            lines.append("- Alternate keys: none")

        lines.append("")
        lines.append("Attributes:")

        attributes = as_list(entity.get("attributes"))
        if not attributes:
            lines.append("- none")
        else:
            for attr in attributes:
                if not isinstance(attr, dict):
                    continue

                attr_name = scalar(attr.get("name"))
                attr_type = scalar(attr.get("data_type"))
                required = scalar(attr.get("required"))
                nullable = scalar(attr.get("nullable"))
                kind = scalar(attr.get("attribute_kind"))
                is_identifier = scalar(attr.get("is_identifier_attribute"))
                description = scalar(attr.get("description"), default="none")
                cardinality = attr.get("cardinality", {}) or {}
                min_card = scalar(cardinality.get("min"))
                max_card = scalar(cardinality.get("max"))

                lines.append(f"- {attr_name}")
                lines.append(f"  - Description: {description}")
                lines.append(f"  - Data type: {attr_type}")
                lines.append(f"  - Required: {required}")
                lines.append(f"  - Nullable: {nullable}")
                lines.append(f"  - Attribute kind: {kind}")
                lines.append(f"  - Cardinality: min {min_card}, max {max_card}")
                lines.append(f"  - Identifier attribute: {is_identifier}")
                components = as_list(attr.get("components"))
                if components:
                    lines.append(f"  - Components: {', '.join(scalar(c) for c in components)}")
                notes = scalar(attr.get("notes"), default="none")
                lines.append(f"  - Notes: {notes}")

        weak = entity.get("weak_entity", {}) or {}
        if weak.get("is_weak"):
            lines.append("")
            lines.append("Weak entity information:")
            lines.append(f"- Owner entities: {', '.join(scalar(e) for e in as_list(weak.get('owner_entities'))) or 'none'}")
            lines.append(f"- Identifying relationship: {scalar(weak.get('identifying_relationship'))}")
            lines.append(f"- Partial key: {', '.join(scalar(k) for k in as_list(weak.get('partial_key'))) or 'none'}")
            lines.append(f"- Notes: {scalar(weak.get('notes'), default='none')}")

        lines.append("")

    return "\n".join(lines)


def render_relationships(schema: Dict[str, Any]) -> str:
    relationships = as_list(schema.get("relationships"))

    lines = []
    lines.append("## Relationships")
    lines.append("")

    if not relationships:
        lines.append("No relationships specified.")
        lines.append("")
        return "\n".join(lines)

    for rel in relationships:
        if not isinstance(rel, dict):
            continue

        name = scalar(rel.get("name"))
        lines.append(f"### Relationship: {name}")
        lines.append("")
        lines.append(f"- ID: {scalar(rel.get('id'))}")
        lines.append(f"- Type: {scalar(rel.get('relationship_type'))}")
        lines.append(f"- Arity: {scalar(rel.get('arity'))}")
        lines.append(f"- Description: {scalar(rel.get('description'), default='none')}")

        aliases = as_list(rel.get("aliases"))
        if aliases:
            lines.append(f"- Aliases: {', '.join(scalar(a) for a in aliases)}")
        else:
            lines.append("- Aliases: none")

        lines.append("")
        lines.append("Participants:")

        participants = as_list(rel.get("participants"))
        if not participants:
            lines.append("- none")
        else:
            for participant in participants:
                if not isinstance(participant, dict):
                    continue

                card = participant.get("cardinality", {}) or {}
                lines.append(f"- Entity: {scalar(participant.get('entity'))}")
                lines.append(f"  - Role: {scalar(participant.get('role'))}")
                lines.append(f"  - Cardinality: min {scalar(card.get('min'))}, max {scalar(card.get('max'))}")
                lines.append(f"  - Participation: {scalar(participant.get('participation'))}")
                lines.append(f"  - Identifying: {scalar(participant.get('identifying'))}")
                lines.append(f"  - Notes: {scalar(participant.get('notes'), default='none')}")

        rel_attrs = as_list(rel.get("relationship_attributes"))
        lines.append("")
        lines.append("Relationship attributes:")

        if not rel_attrs:
            lines.append("- none")
        else:
            for attr in rel_attrs:
                if not isinstance(attr, dict):
                    continue
                lines.append(f"- {scalar(attr.get('name'))}")
                lines.append(f"  - Data type: {scalar(attr.get('data_type'))}")
                lines.append(f"  - Required: {scalar(attr.get('required'))}")
                lines.append(f"  - Nullable: {scalar(attr.get('nullable'))}")
                lines.append(f"  - Attribute kind: {scalar(attr.get('attribute_kind'))}")
                lines.append(f"  - Notes: {scalar(attr.get('notes'), default='none')}")

        constraints = rel.get("constraints", {}) or {}
        lines.append("")
        lines.append("Relationship constraints:")
        lines.append(f"- Cardinality class: {scalar(constraints.get('cardinality_class'))}")
        lines.append(f"- Is functional: {scalar(constraints.get('is_functional'))}")
        lines.append(f"- Functional from: {scalar(constraints.get('functional_from'))}")
        lines.append(f"- Functional to: {scalar(constraints.get('functional_to'))}")
        lines.append(f"- Requires relationship table: {scalar(constraints.get('requires_relationship_table'))}")
        lines.append(f"- Notes: {scalar(constraints.get('notes'), default='none')}")
        lines.append("")

    return "\n".join(lines)


def render_specializations(schema: Dict[str, Any]) -> str:
    specializations = as_list(schema.get("specializations"))

    lines = []
    lines.append("## Specialization and Generalization")
    lines.append("")

    if not specializations:
        lines.append("No specialization/generalization structures specified.")
        lines.append("")
        return "\n".join(lines)

    for sp in specializations:
        if not isinstance(sp, dict):
            continue

        lines.append(f"### Specialization: {scalar(sp.get('name'))}")
        lines.append("")
        lines.append(f"- ID: {scalar(sp.get('id'))}")
        lines.append(f"- Supertype: {scalar(sp.get('supertype'))}")
        lines.append(f"- Completeness: {scalar(sp.get('completeness'))}")
        lines.append(f"- Disjointness: {scalar(sp.get('disjointness'))}")
        lines.append(f"- Inheritance type: {scalar(sp.get('inheritance_type'))}")
        lines.append(f"- Supertype abstract: {scalar(sp.get('is_supertype_abstract'))}")
        lines.append("- Subtypes:")

        subtypes = as_list(sp.get("subtypes"))
        if not subtypes:
            lines.append("  - none")
        else:
            for subtype in subtypes:
                if isinstance(subtype, dict):
                    lines.append(f"  - {scalar(subtype.get('entity'))}")
                    lines.append(f"    - Predicate: {scalar(subtype.get('predicate'))}")
                    lines.append(f"    - Notes: {scalar(subtype.get('notes'), default='none')}")
                else:
                    lines.append(f"  - {scalar(subtype)}")

        lines.append(f"- Notes: {scalar(sp.get('notes'), default='none')}")
        lines.append("")

    return "\n".join(lines)


def render_global_constraints(schema: Dict[str, Any]) -> str:
    constraints = schema.get("global_constraints", {}) or {}

    lines = []
    lines.append("## Global Constraints")
    lines.append("")

    groups = [
        ("Key constraints", "key_constraints"),
        ("Participation constraints", "participation_constraints"),
        ("Cardinality constraints", "cardinality_constraints"),
        ("Inclusion constraints", "inclusion_constraints"),
        ("Exclusion constraints", "exclusion_constraints"),
        ("Business rules", "business_rules"),
    ]

    for title, key in groups:
        lines.append(f"### {title}")
        items = as_list(constraints.get(key))
        if not items:
            lines.append("- none")
        else:
            for item in items:
                if isinstance(item, dict):
                    item_id = scalar(item.get("id"))
                    description = scalar(item.get("description"), default="")
                    notes = scalar(item.get("notes"), default="none")
                    compact = {k: v for k, v in item.items() if k not in {"id", "description", "notes"}}
                    lines.append(f"- ID: {item_id}")
                    if description:
                        lines.append(f"  - Description: {description}")
                    if compact:
                        lines.append(f"  - Details: {json.dumps(compact, ensure_ascii=False)}")
                    lines.append(f"  - Notes: {notes}")
                else:
                    lines.append(f"- {scalar(item)}")
        lines.append("")

    return "\n".join(lines)


def render_expert_notes(schema: Dict[str, Any]) -> str:
    notes = schema.get("expert_notes", {}) or {}

    lines = []
    lines.append("## Expert Notes")
    lines.append("")

    for title, key in [
        ("Assumptions", "assumptions"),
        ("Ambiguities", "ambiguities"),
        ("Mapping-relevant observations", "mapping_relevant_observations"),
        ("Excluded details", "excluded_details"),
    ]:
        lines.append(f"### {title}")
        lines.append(md_list(as_list(notes.get(key))))
        lines.append("")

    return "\n".join(lines)


def render_task_instruction() -> str:
    lines = []
    lines.append("## Task")
    lines.append("")
    lines.append("Generate a logical relational schema in the benchmark JSON format.")
    lines.append("")
    lines.append("Important requirements:")
    lines.append("- Use only the information supported by this EER input.")
    lines.append("- Do not invent unsupported entities, attributes, keys, relationships, or constraints.")
    lines.append("- Preserve identifiers, cardinalities, participation constraints, relationship attributes, and specialization/generalization semantics.")
    lines.append("- If more than one mapping is possible, choose the most justified mapping and document the decision in the output notes.")
    lines.append("- Return only the relational JSON when answering the prompt.")
    lines.append("")
    return "\n".join(lines)


def render_prompt_input(schema: Dict[str, Any]) -> str:
    sections = [
        render_metadata(schema),
        render_entities(schema),
        render_relationships(schema),
        render_specializations(schema),
        render_global_constraints(schema),
        render_expert_notes(schema),
        render_task_instruction(),
    ]
    return "\n".join(section.strip() for section in sections if section.strip()) + "\n"


def count_schema_items(schema: Dict[str, Any]) -> Dict[str, int]:
    num_entities = len(as_list(schema.get("entities")))
    num_relationships = len(as_list(schema.get("relationships")))
    num_specializations = len(as_list(schema.get("specializations")))
    num_attributes = 0
    num_relationship_attributes = 0

    for entity in as_list(schema.get("entities")):
        if isinstance(entity, dict):
            num_attributes += len(as_list(entity.get("attributes")))

    for rel in as_list(schema.get("relationships")):
        if isinstance(rel, dict):
            num_relationship_attributes += len(as_list(rel.get("relationship_attributes")))

    return {
        "num_entities": num_entities,
        "num_relationships": num_relationships,
        "num_specializations": num_specializations,
        "num_entity_attributes": num_attributes,
        "num_relationship_attributes": num_relationship_attributes,
    }


def build_run_id(dataset: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{normalize_name(dataset)}_prompt_input_{timestamp}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate prompt-ready textual EER input from conceptual_eer.yaml."
    )

    parser.add_argument("--conceptual-yaml", required=True, help="Path to conceptual_eer.yaml.")
    parser.add_argument("--dataset", required=True, help="Dataset name.")
    parser.add_argument("--output-dir", default="results/prompt_input_runs", help="Base output directory.")
    parser.add_argument("--run-id", default=None, help="Optional run id.")
    parser.add_argument("--publish-to", default=None, help="Optional path to publish/copy eer_input_text.md.")
    parser.add_argument("--notes", default="", help="Optional execution notes.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    conceptual_path = Path(args.conceptual_yaml)
    if not conceptual_path.exists():
        raise FileNotFoundError(f"Conceptual YAML not found: {conceptual_path}")

    schema = load_yaml(conceptual_path)
    prompt_text = render_prompt_input(schema)

    run_id = args.run_id or build_run_id(args.dataset)
    output_dir = Path(args.output_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_output_path = output_dir / "eer_input_text.md"
    prompt_output_path.write_text(prompt_text, encoding="utf-8")

    source_snapshot_path = output_dir / "source_conceptual_eer.yaml"
    shutil.copy2(conceptual_path, source_snapshot_path)

    published_path = None
    if args.publish_to:
        published_path = Path(args.publish_to)
        published_path.parent.mkdir(parents=True, exist_ok=True)
        published_path.write_text(prompt_text, encoding="utf-8")

    manifest = {
        "run_id": run_id,
        "created_at_utc": now_utc_iso(),
        "script": "scripts/generate_prompt_input.py",
        "dataset": args.dataset,
        "conceptual_yaml": str(conceptual_path),
        "conceptual_yaml_sha256": file_sha256(conceptual_path),
        "output_dir": str(output_dir),
        "prompt_input_file": str(prompt_output_path),
        "published_prompt_input_file": str(published_path) if published_path else None,
        "notes": args.notes,
        "schema_counts": count_schema_items(schema),
        "generated_files": [
            "eer_input_text.md",
            "source_conceptual_eer.yaml",
            "prompt_input_manifest.json",
        ],
    }

    manifest_path = output_dir / "prompt_input_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Prompt input generation completed.")
    print(f"Run ID: {run_id}")
    print(f"Output directory: {output_dir}")
    print(f"Prompt input: {prompt_output_path}")
    if published_path:
        print(f"Published copy: {published_path}")


if __name__ == "__main__":
    main()
