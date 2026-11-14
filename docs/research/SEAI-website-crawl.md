# SEAI website crawl

The SEAI site crawler is a source-archiving utility. It is separate from the TechSpecs V2 product-record pipeline.

## Scope

- Starts at https://www.seai.ie/ and discovers additional public pages using the site's sitemap and internal links.
- Restricts page crawling to www.seai.ie and seai.ie.
- Reads robots.txt and skips URLs disallowed for its declared user agent.
- Archives original HTML, extracted plain text, ordered text blocks (including headings, paragraphs, lists and tables), and a provenance sidecar.
- Tracks its queue, visited URLs, captures and failures so a crawl can be resumed.
- Can optionally download linked PDF and office documents.

It does not create product records, interpret SEAI policy, access HARP, or claim that archived claims have been fact-checked.

## Install

From the repository root:

```bash
python -m pip install -r requirements.txt
python -m pip install requests beautifulsoup4
```

## Run

### Use a saved sitemap file

If SEAI's sitemap has already been saved locally, place the XML file in the repository root (beside `README.md`). Then run:

```bash
python scripts/crawl_seai_website.py --sitemap-file sitemap.xml --max-pages 10 --delay 2
```

The local sitemap is parsed before capture attempts. Its URL entries and source-declared `lastmod` values are retained in `url-inventory.json`, including URLs that are pending, blocked by `robots.txt`, or fail to download. The crawler still checks the live `robots.txt` file and does not bypass access restrictions.

Start a small test batch first:

```bash
python scripts/crawl_seai_website.py --max-pages 10 --delay 2
```

Run without a page-count cap:

```bash
python scripts/crawl_seai_website.py --delay 2
```

Resume an interrupted run:

```bash
python scripts/crawl_seai_website.py --resume --delay 2
```

Include linked PDFs and office documents:

```bash
python scripts/crawl_seai_website.py --resume --include-documents --delay 2
```

Use `--max-pages N` to constrain each run. The same crawl state can be resumed later with `--resume`.

## Output

All crawler output is written under `sources/seai/site-crawl/`:

- `pages/` — original HTML, text extraction, blocks JSON and provenance sidecars.
- `documents/` — optional linked document downloads and sidecars.
- `state.json` — crawl queue, visited URLs, successes and failures.
- `url-inventory.json` — URL-level inventory, sitemap `lastmod` values when supplied, capture statuses and completion counts.

A page is marked `url_and_content_archived_not_fact_checked`. This describes capture only; it is not a factual verification status.

## Operational notes

- The tool makes requests sequentially and waits between them. Do not reduce the delay to evade site limits.
- The crawler respects robots.txt. If robots.txt cannot be retrieved, it stops rather than crawling blindly.
- Sitemap discovery and internal-link traversal are complementary; the final inventory reports what was actually found and attempted.
- Some pages may require JavaScript, block automated access, redirect outside the SEAI domain, or exist only in linked systems. Such cases are not silently represented as successfully archived.
- Check SEAI's current website terms and contact SEAI for permission or guidance before running a high-volume crawl or redistributing archived content.
- The script does not overwrite the repository's existing homepage archive or any existing V2/product data.
