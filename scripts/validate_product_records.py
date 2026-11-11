#!/usr/bin/env python3
"""Validate HEATPUMPSPECS product records against the canonical TechSpecs V2 schema."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
SCHEMA_PATH = ROOT / "schemas" / "product-record-v2.schema.json"
NON_PRODUCT_FILENAMES = {"catalogue.json", "api-manifest.json", "generation-report.json", "source-inventory.json"}


def repo_file(value: str) -> Path | None:
    candidate = (ROOT / value).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-v2", action="store_true", help="require every product JSON record to declare and satisfy schema v2")
    args = parser.parse_args()

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("ERROR: missing dependency; run python -m pip install -r requirements.txt")
        return 2

    if not SCHEMA_PATH.is_file():
        print("ERROR: canonical V2 schema is missing")
        return 2

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    except Exception as exc:
        print(f"ERROR: canonical V2 schema is invalid: {exc}")
        return 2

    files = sorted(
        p for p in DATA_ROOT.rglob("*.json")
        if p.name not in NON_PRODUCT_FILENAMES and "schemas" not in p.relative_to(DATA_ROOT).parts
    ) if DATA_ROOT.exists() else []

    if not files:
        print("Canonical V2 schema: valid")
        print("Product records found: 0")
        print("STATUS: repository scaffold is valid; no product records have been created yet.")
        return 0

    errors: list[str] = []
    warnings: list[str] = []
    validated = 0

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{rel}: invalid JSON: {exc}")
            continue
        if not isinstance(record, dict):
            errors.append(f"{rel}: top-level JSON value must be an object")
            continue

        version = record.get("schema_version")
        if version != "2.0":
            message = f"{rel}: schema_version is {version!r}, not '2.0'"
            if args.strict_v2:
                errors.append(message)
            else:
                warnings.append(message)
        else:
            validated += 1
            for issue in sorted(validator.iter_errors(record), key=lambda e: list(map(str, e.absolute_path))):
                location = ".".join(str(part) for part in issue.absolute_path) or "$"
                errors.append(f"{rel}: {location}: {issue.message}")

        product = record.get("product") if isinstance(record.get("product"), dict) else {}
        slug = product.get("model_slug")
        if slug and str(slug) != path.stem:
            errors.append(f"{rel}: product.model_slug {slug!r} does not match filename {path.stem!r}")

        source = record.get("source") if isinstance(record.get("source"), dict) else {}
        source_file = source.get("source_file")
        if source_file:
            resolved = repo_file(str(source_file))
            if resolved is None:
                errors.append(f"{rel}: source.source_file escapes repository: {source_file!r}")
            elif not resolved.is_file():
                errors.append(f"{rel}: source.source_file does not exist: {source_file!r}")

        sections = record.get("sections")
        if isinstance(sections, list):
            for index, section in enumerate(sections):
                if not isinstance(section, dict) or not section.get("source_file"):
                    continue
                resolved = repo_file(str(section["source_file"]))
                if resolved is None:
                    errors.append(f"{rel}: sections[{index}].source_file escapes repository")
                elif not resolved.is_file():
                    errors.append(f"{rel}: sections[{index}].source_file does not exist: {section['source_file']!r}")

    print(f"Product records scanned: {len(files)}")
    print(f"Records validated against V2 schema: {validated}")
    print(f"Errors: {len(errors)} | Warnings: {len(warnings)}")
    for item in errors:
        print("ERROR: " + item)
    for item in warnings:
        print("WARNING: " + item)
    if errors:
        print("STATUS: FAILED")
        return 1
    print("STATUS: PASSED (structural validation only; factual verification remains separate)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
