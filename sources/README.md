# Source evidence

Preserve original source files as evidence snapshots. Do not silently overwrite the only copy.

For each captured source, retain a provenance sidecar where practical. The sidecar should identify the source URL, source-declared title and publisher when known, acquisition method, original filename, repository-relative archive path, checksum, and verification limitations.

The original source and its metadata are not product records. Do not validate an HTML or PDF source archive against the product-record V2 schema.

When a product record is later created:
- reference the preserved source with `source.source_file`;
- retain relevant source sections in the product record as required by the V2 standard;
- keep the original wording distinct from normalized technical values;
- mark verification status according to the checks actually completed.

Never infer that an official-looking page, a source URL in supplied HTML, or a preserved file has been independently verified merely because it has been archived.
