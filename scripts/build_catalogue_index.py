#!/usr/bin/env python3
"""Build the machine-readable HEATPUMPSPECS catalogue from V2 product records."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
OUTPUT = DATA_ROOT / "catalogue.json"
DEFAULT_BASE_URL = "https://raw.githubusercontent.com/heatpumpspecs-pixel/HEATPUMPSPECS/main"
BASE_URL = os.environ.get("HEATPUMPSPECS_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
NON_PRODUCT_FILENAMES = {
    "catalogue.json",
    "api-manifest.json",
    "generation-report.json",
    "source-inventory.json",
}


def text_value(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def raw_url(relative_path: str) -> str:
    return f"{BASE_URL}/{relative_path}"


def build_entry(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict) or record.get("schema_version") != "2.0":
        raise ValueError("record must be a TechSpecs V2 object")

    product = record.get("product") if isinstance(record.get("product"), dict) else {}
    source = record.get("source") if isinstance(record.get("source"), dict) else {}
    relative_path = path.relative_to(DATA_ROOT).as_posix()
    record_id = relative_path.removesuffix(".json")

    section_sources = []
    seen = set()
    for section in record.get("sections", []):
        if not isinstance(section, dict):
            continue
        source_url = text_value(section.get("source_url"))
        source_file = text_value(section.get("source_file"))
        key = (source_url, source_file)
        if key == (None, None) or key in seen:
            continue
        seen.add(key)
        section_sources.append({
            "source_url": source_url,
            "source_file": source_file,
            "source_file_url": raw_url(source_file) if source_file else None,
        })

    return {
        "record_id": record_id,
        "path": relative_path,
        "record_url": raw_url(f"data/{relative_path}"),
        "schema_version": "2.0",
        "brand": text_value(product.get("brand")),
        "category": text_value(product.get("category")),
        "family": text_value(product.get("family")),
        "model": text_value(product.get("model")),
        "model_slug": text_value(product.get("model_slug")),
        "model_year": product.get("model_year") if isinstance(product.get("model_year"), int) else None,
        "variant": text_value(product.get("variant")),
        "source": {
            "source_type": text_value(source.get("source_type")),
            "publisher": text_value(source.get("publisher")),
            "source_url": text_value(source.get("source_url")),
            "source_file": text_value(source.get("source_file")),
            "source_file_url": raw_url(source["source_file"]) if text_value(source.get("source_file")) else None,
            "verification_status": text_value(source.get("verification_status")),
            "checked_at": text_value(source.get("checked_at")),
        },
        "section_sources": section_sources,
    }


def main() -> int:
    if not DATA_ROOT.is_dir():
        print("ERROR: data/ directory not found", file=sys.stderr)
        return 1

    files = sorted(
        path for path in DATA_ROOT.rglob("*.json")
        if path != OUTPUT
        and path.name not in NON_PRODUCT_FILENAMES
        and "schemas" not in path.relative_to(DATA_ROOT).parts
    )
    entries = []
    for path in files:
        try:
            entries.append(build_entry(path))
        except Exception as exc:
            print(f"ERROR: cannot index {path.relative_to(ROOT)}: {exc}", file=sys.stderr)
            return 1

    if not entries:
        print("ERROR: no V2 product records found under data/", file=sys.stderr)
        return 1

    ids = [entry["record_id"] for entry in entries]
    urls = [entry["record_url"] for entry in entries]
    if len(ids) != len(set(ids)) or len(urls) != len(set(urls)):
        print("ERROR: duplicate catalogue record IDs or URLs", file=sys.stderr)
        return 1

    entries.sort(key=lambda item: item["path"])
    catalogue = {
        "catalogue_version": "1.0",
        "title": "HEATPUMPSPECS Machine-Readable Product Catalogue",
        "description": "Machine-readable index of domestic heat-pump product records following the TechSpecs Canonical Data Standard v2.0. Source evidence and verification status are exposed for each record.",
        "purpose": "machine_reading",
        "canonical_host": BASE_URL,
        "record_count": len(entries),
        "records": entries,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {OUTPUT.relative_to(ROOT)} with {len(entries)} V2 product records.")
    print(f"Catalogue base URL: {BASE_URL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
