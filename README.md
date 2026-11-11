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

## Initial Grant source inventory

The first model-level source inventory is [`data/grant/heat-pump/source-inventory.json`](data/grant/heat-pump/source-inventory.json). It indexes all nine Grant Engineering (Ireland) ULC subtypes found in the Heat Pump KEYMARK database, including each subtype URL and certificate PDF URL. It is a source-discovery inventory, not a final product catalogue.

## Current SEAI research

The first SEAI evidence review is recorded in [docs/research/SEAI-domestic-heat-pump-evidence-review.md](docs/research/SEAI-domestic-heat-pump-evidence-review.md). It identifies the current DTSS v4.0 (July 2026), HARP/DEAP evidence routes and the distinction between SEAI grant eligibility and voluntary Heat Pump KEYMARK certification. This is a source review, not a product record.

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

## Machine discovery and publishing

The repository publishes an interim machine-readable catalogue at [`data/catalogue.json`](data/catalogue.json) and discovery instructions at [`llms.txt`](llms.txt). The catalogue currently uses the public GitHub raw-content endpoint, so product records and source transcriptions can be retrieved directly without a separate website. The catalogue generator accepts `HEATPUMPSPECS_BASE_URL` so a future Cloudflare Pages/custom-domain host can be configured without changing product records. GitHub remains the canonical repository; no custom publishing host is claimed to be live.
