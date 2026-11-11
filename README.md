# HEATPUMPSPECS

An evidence-based, machine-readable technical specifications database for domestic heat pumps, focused on the Irish and EU markets.

This repository is the canonical working store for HEATPUMPSPECS. It is a data and evidence repository, not the consumer-facing website.

## Governing data standard

Product records follow the **TechSpecs Canonical Data Standard — Version 2.0**:

- [Canonical V2 standard](docs/canonical-data-standard-v2.md)
- [Canonical V2 JSON Schema](schemas/product-record-v2.schema.json)

The V2 standard is applied as established. Repository structure, record format, extraction, validation and naming conventions are not to be independently redesigned.

## Repository layout

- `data/<brand>/<category>/` — canonical product records, one per distinct marketed model/variant where specifications differ.
- `sources/` — preserved source evidence and provenance sidecars.
- `schemas/` — canonical JSON schemas.
- `scripts/` — deterministic validation and source-integrity checks.
- `docs/` — governing standards and repository guidance.
- `.github/workflows/` — automated validation.

## Required working sequence

1. Inspect the existing repository structure and schema.
2. Identify the product/model scope.
3. Discover candidate sources.
4. Verify official sources and exact model/variant applicability.
5. Preserve original source material and provenance.
6. Extract source sections without silently rewriting them.
7. Create the V2 product record.
8. Add normalized specifications only where the evidence supports them.
9. Validate schema, source references, naming and factual claims.
10. Commit and retain the audit trail.

## Evidence and verification

- Preserve original source material; do not replace it with a summary.
- Keep source statements separate from normalized technical facts and derived values.
- Unknown, not stated, not applicable and unverified are distinct.
- A reachable URL is not proof that its contents have been verified.
- Never invent missing specifications, model numbers, source dates or test conditions.
- Structural validation and factual verification are separate gates.

## Source archive currently committed

The SEAI homepage supplied as the project's first source is retained at:

`sources/seai/homepage/homepage.html`

Its provenance sidecar is:

`sources/seai/homepage/homepage.html.metadata.json`

This is a source archive, **not a heat-pump product record**. It must not be forced into the product-record schema. The source archive audit checks its recorded SHA-256 against the preserved file.

## Validation

Install the dependency and run:

```bash
python -m pip install -r requirements.txt
python scripts/validate_product_records.py
python scripts/audit_source_archives.py
```

The V2 schema is checked even before the first product record exists. The validator reports an empty product collection as an initial state, not as a fabricated successful product-record validation.

## Publishing

No public data-host URL or catalogue endpoint is declared here until the HEATPUMPSPECS publishing destination and routing are configured. GitHub remains the canonical repository.
