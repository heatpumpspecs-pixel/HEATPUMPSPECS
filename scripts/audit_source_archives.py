#!/usr/bin/env python3
"""Check source metadata sidecars against the original archived files."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "sources"


def main() -> int:
    sidecars = sorted(SOURCE_ROOT.rglob("*.metadata.json")) if SOURCE_ROOT.exists() else []
    errors: list[str] = []
    checked = 0

    for sidecar in sidecars:
        rel = sidecar.relative_to(ROOT).as_posix()
        try:
            metadata = json.loads(sidecar.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{rel}: invalid JSON: {exc}")
            continue
        if not isinstance(metadata, dict):
            errors.append(f"{rel}: metadata must be a JSON object")
            continue

        archive_path = metadata.get("archive_path")
        expected_hash = metadata.get("sha256")
        if not isinstance(archive_path, str) or not archive_path.strip():
            errors.append(f"{rel}: archive_path is missing")
            continue
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            errors.append(f"{rel}: sha256 is missing or malformed")
            continue

        archive = (ROOT / archive_path).resolve()
        try:
            archive.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{rel}: archive_path escapes repository: {archive_path!r}")
            continue
        if not archive.is_file():
            errors.append(f"{rel}: archived source is missing: {archive_path!r}")
            continue

        actual_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
        checked += 1
        if actual_hash.lower() != expected_hash.lower():
            errors.append(
                f"{rel}: SHA-256 mismatch for {archive_path!r}; "
                f"metadata={expected_hash}, actual={actual_hash}"
            )

    print(f"Source metadata sidecars found: {len(sidecars)}")
    print(f"Archived source files checksum-verified: {checked}")
    for item in errors:
        print("ERROR: " + item)
    if errors:
        print(f"STATUS: FAILED ({len(errors)} errors)")
        return 1
    print("STATUS: PASSED (archive integrity only; this does not verify source authenticity or factual claims)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
