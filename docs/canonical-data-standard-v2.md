# TechSpecs Canonical Data Standard — Version 2.0

**Status:** Initial standard for new and migrated records  
**Schema:** `schemas/product-record-v2.schema.json`  
**Applies to:** Product records in `data/<brand>/<category>/`  
**Principle:** Preserve source material, make provenance explicit, and never invent missing specifications.

## 1. Goals

Every product record must be:
- identifiable as one specific product/model/variant;
- traceable to the source material used;
- explicit about whether the source and its claims have been checked;
- structurally valid and consistently named;
- safe to compare only where values, units and definitions are compatible.

A record can be a valid archival record without being ready for comparisons. **JSON validity is not factual verification.**

## 2. Canonical record layout

New canonical records use `schema_version: "2.0"` and the structure defined in `schemas/product-record-v2.schema.json`.

Required top-level properties:
- `schema_version`
- `product`
- `source`
- `extraction`
- `sections`

Optional:
- `normalized_specifications`
- `record_notes`

The `sections` array preserves the supplied source text. Normalized values are added separately; do not replace or silently rewrite the source text during normalization.

## 3. Product identity rules

Required product fields:
- `brand`: manufacturer/brand name.
- `category`: broad product category, e.g. `smartphone`.
- `family`: product family, e.g. `iPhone`.
- `model`: user-facing model name, including size or tier where applicable.
- `model_slug`: stable lowercase kebab-case identifier used in filenames and links.

Use one record per distinct marketed model/variant where the specifications differ. Do not combine standard, Plus, Pro, Pro Max, mini, SE generations, or other distinct variants into a single record.

Use `model_year` for the model's year of introduction. `year_introduced` is accepted for transition compatibility; for new records prefer `model_year`. Do not use the year a document was created as the product year.

## 4. Source and verification rules

Required source fields:
- `source_type`
- `source_url` (use JSON `null` if no verified URL is available)
- `verification_status`
- `checked_at` (use `null` until a human or automated review has checked the source)

Allowed `source_type` values:
- `manufacturer`
- `regulatory`
- `retailer`
- `user_supplied_document`
- `third_party_reference`
- `other`

Allowed `verification_status` values:
- `not_checked`: source or its claims have not been checked.
- `url_checked`: the URL was opened and confirmed to resolve to the intended source, but the specifications have not all been checked.
- `content_verified`: the record's claims were checked against the cited source within a documented scope.
- `partially_verified`: only some claims/sections were checked; explain scope in `verification_notes`.
- `conflicting_sources`: credible sources disagree; document the conflict.
- `unavailable`: the original source could not be accessed or located.

Important:
- A URL copied from a user document, inferred from a link, guessed from a pattern, or merely plausible is **not** a verified source URL. Leave `source_url` null until checked.
- Do not mark a record `content_verified` merely because its source is an official manufacturer page. The claims themselves must have been compared.
- `checked_at` is the date the source was last checked, in ISO `YYYY-MM-DD` format.
- Preserve user-supplied source files and identify them using `source_file` as a repository-relative path.
- Record source title, publisher and publication date when known. Use null when unknown; do not infer them.
- If sources conflict, retain the conflict and its provenance. Do not silently choose one value.

## 5. Extraction and normalization rules

Required extraction fields:
- `method`
- `normalization_status`
- `note`

Allowed `method` values:
- `manual`
- `section_preserving`
- `structured_extraction`
- `transcribed`
- `mixed`

Allowed `normalization_status` values:
- `archival_first_pass`: source sections retained; not normalized field by field.
- `partially_normalized`: some fields normalized; remaining gaps are explicit.
- `normalized`: all in-scope fields follow the agreed field and unit conventions.
- `not_applicable`: no normalization is intended for this record.

The note must explain what was done and any important limitations. Dates such as `extracted_at` and `reviewed_at` use ISO `YYYY-MM-DD`.

## 6. Normalized specification values

The optional `normalized_specifications` object contains groups (for example `display`, `dimensions`, `performance`, `camera`, `battery`, `connectivity`, `durability`, `software`, `in_box`). Each field is an object with:

- `value`: string, number, integer, boolean, array, or null.
- `unit`: unit string or null.
- `source_section`: exact heading in `sections` or null.
- `verification_status`: one of `not_checked`, `source_transcribed`, `content_verified`, `partially_verified`, `not_applicable`.
- `notes`: optional explanation or qualification.

Rules:
1. Use stable field names across all products in the same category.
2. Store numeric measurements as numbers, not numeric strings, when practical.
3. Always include units for dimensional, mass, capacity, frequency, power, and rate values.
4. Do not convert units unless the original value is retained or the conversion is documented and reproducible.
5. Distinguish a missing value from zero, false, and not applicable. Use `null` for unknown/unavailable values; use `not_applicable` only when the field genuinely does not apply.
6. Preserve qualifiers such as “up to”, “typical”, “minimum”, “maximum”, regional limitations, and test conditions in `notes` or a dedicated field agreed for the category.
7. Do not combine different measurement methods or test conditions in a direct comparison without clearly flagging the difference.
8. Every normalized value must point to its source section where possible.
9. Use `source_transcribed` when faithfully copied from the source but not independently checked. Reserve `content_verified` for values checked against the cited source.
10. Never fill a missing field using assumptions, another model's specifications, or marketing convention.

A normalized record does not have to contain every imaginable field. It must clearly represent what is known, unknown, not applicable, and out of scope.

## 7. Source preservation

- Keep original supplied Markdown in `sources/`.
- Treat source files as immutable evidence snapshots. If a correction is required, add a dated/revisioned source or document the change; do not silently overwrite the only copy.
- Preserve headings, footnotes, caveats, tables, and embedded links as faithfully as possible.
- Do not assume the JSON sections are complete transcriptions until checked against the Markdown.
- Keep the original source wording separate from normalized interpretations.

## 8. File naming and location

Use:
- `data/<brand>/<category>/<model-slug>.json`
- `sources/<brand>/<category>/<generation-or-family>/<model-slug>-source.md`

For Apple smartphones, retain the established paths under `data/apple/iphone/` and `sources/apple/iphone/`.

The model slug in the JSON, data filename, and source filename must match (source filename adds `-source`).

## 9. Validation checklist

A record passes structural validation only when:
- [ ] It parses as JSON.
- [ ] It validates against the v2 JSON Schema.
- [ ] Required product identity fields are present and non-empty.
- [ ] `model_slug` matches the data filename.
- [ ] A source file exists and is referenced correctly, or the reason for no source file is documented.
- [ ] Source URL is null or an actually checked URL; no guessed URL is presented as verified.
- [ ] Verification status accurately reflects the work performed.
- [ ] Every section has a heading and source text.
- [ ] Every normalized field has a value, unit, source section, and field-level verification status.
- [ ] Units, qualifiers and test conditions are retained.
- [ ] Unknown values are not represented as zero or false.
- [ ] No unsupported or inferred specifications have been added.

Structural validation and editorial/factual review are separate gates. Passing the schema does not mean the product data is factually correct.

## 10. Migration policy for existing records

The existing iPhone collection is a mixed legacy archive. Do not mass-edit it in place.

Migration should happen in controlled batches:
1. Keep the current records and source Markdown intact.
2. Map existing metadata and sections to v2 fields without inventing missing values.
3. Retain legacy field-level data (such as the iPhone 6 Plus `specifications`) while mapping it into the new normalized structure.
4. Record every unmappable or ambiguous field for review.
5. Validate migrated records against the schema.
6. Compare migrated sections against the source Markdown.
7. Commit a small batch and verify it before proceeding.

For older records, use `not_checked` unless the source has actually been checked. Do not backdate verification.

## 11. Versioning and change control

- Increment `schema_version` when a record format change is incompatible.
- Document schema changes and migration notes in the repository.
- Do not rename established fields casually; update the schema, documentation, and validators together.
- Keep validation deterministic and repeatable.
- Record the audit/migration commit or report that introduced major changes.

## 12. Current collection status

The current 48 iPhone JSON records are **not yet certified as v2 compliant**. They use legacy top-level structures and inconsistent metadata. The v2 schema is the target standard for new records and controlled migration, not a claim that all current records have already been converted.

The current repository audit is available at `reports/iphone-catalogue-audit.md`.
