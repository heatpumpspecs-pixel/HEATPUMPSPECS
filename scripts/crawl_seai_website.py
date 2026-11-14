#!/usr/bin/env python3
"""Archive SEAI website pages and linked documents as source evidence.

This is a source-capture tool, not a product-data extractor. It writes only
under sources/seai/site-crawl/ and does not modify V2 product records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import mimetypes
import re
import time
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag, unquote
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT_URL = "https://www.seai.ie/"
ALLOWED_HOSTS = {"www.seai.ie", "seai.ie"}
DEFAULT_OUT = Path("sources/seai/site-crawl")
USER_AGENT = "TechSpecs-SEAI-ResearchBot/1.0 (+https://github.com/heatpumpspecs-pixel/HEATPUMPSPECS)"
SKIP_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".css", ".js", ".ico", ".woff", ".woff2", ".ttf", ".mp4", ".mp3", ".zip"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".xml"}
CONTENT_SELECTORS = ["main", "[role=main]", "article", ".content", "#content"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_url(url: str) -> str:
    url, _ = urldefrag(url)
    p = urlparse(url)
    host = (p.hostname or "").lower()
    if host == "seai.ie":
        host = "www.seai.ie"
    path = re.sub(r"/{2,}", "/", p.path or "/")
    # Keep query strings: some SEAI pages/forms may use meaningful query parameters.
    return p._replace(scheme="https", netloc=host, path=path).geturl()


def in_scope(url: str) -> bool:
    p = urlparse(url)
    return p.scheme in {"http", "https"} and (p.hostname or "").lower() in ALLOWED_HOSTS


def safe_name(url: str, content_type: str = "") -> str:
    p = urlparse(url)
    raw = unquote(p.path).strip("/")
    if not raw:
        raw = "homepage"
    raw = re.sub(r"[^A-Za-z0-9._/-]+", "-", raw)
    raw = raw.replace("/", "__")
    suffix = Path(raw).suffix.lower()
    if not suffix:
        suffix = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".html"
    stem = raw[:-len(Path(raw).suffix)] if Path(raw).suffix else raw
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
    return f"{stem[:120]}-{digest}{suffix}"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/xml,application/pdf,*/*;q=0.8"})
    retry = Retry(total=4, connect=4, read=4, backoff_factor=1.0,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET"], respect_retry_after_header=True)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_robots(session: requests.Session, base: str) -> RobotFileParser:
    robots_url = urljoin(base, "/robots.txt")
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        response = session.get(robots_url, timeout=30)
        response.raise_for_status()
        rp.parse(response.text.splitlines())
        logging.info("Loaded robots.txt from %s", robots_url)
    except requests.RequestException as exc:
        # Fail closed: do not crawl if robots.txt cannot be checked.
        raise RuntimeError(f"Could not retrieve robots.txt; refusing to crawl: {exc}") from exc
    return rp


def sitemap_candidates(session: requests.Session, base: str, robots_text: str) -> list[str]:
    urls = []
    for line in robots_text.splitlines():
        if line.lower().startswith("sitemap:"):
            urls.append(line.split(":", 1)[1].strip())
    urls.extend([urljoin(base, "/sitemap.xml")])
    seen, result = set(), []
    for u in urls:
        if u not in seen:
            result.append(u)
            seen.add(u)
    return result


def parse_sitemap_content(xml_data: bytes, source: str) -> list[dict]:
    """Parse a sitemap URL set, retaining each URL's source-declared lastmod."""
    root = ET.fromstring(xml_data)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    if root.tag.endswith("sitemapindex"):
        raise ValueError(
            f"{source} is a sitemap index. Supply the individual sitemap files locally."
        )
    entries = []
    for item in root.findall("sm:url", ns):
        loc = item.findtext("sm:loc", default="", namespaces=ns).strip()
        if not loc or not in_scope(loc):
            continue
        lastmod = item.findtext("sm:lastmod", default="", namespaces=ns).strip() or None
        entries.append({"url": canonical_url(loc), "lastmod": lastmod, "sitemap_source": source})
    return entries


def parse_sitemap(session: requests.Session, sitemap_url: str, seen: set[str], depth: int = 0) -> list[dict]:
    if depth > 5 or sitemap_url in seen:
        return []
    seen.add(sitemap_url)
    try:
        r = session.get(sitemap_url, timeout=45)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except (requests.RequestException, ET.ParseError) as exc:
        logging.warning("Sitemap unavailable %s: %s", sitemap_url, exc)
        return []
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    if root.tag.endswith("sitemapindex"):
        found = []
        for loc in root.findall(".//sm:sitemap/sm:loc", ns):
            child = (loc.text or "").strip()
            if child:
                found.extend(parse_sitemap(session, child, seen, depth + 1))
        return found
    try:
        return parse_sitemap_content(r.content, sitemap_url)
    except (ET.ParseError, ValueError) as exc:
        logging.warning("Could not parse sitemap %s: %s", sitemap_url, exc)
        return []


def merge_sitemap_entries(entries: list[dict]) -> list[dict]:
    merged = {}
    for entry in entries:
        url = entry["url"]
        if url not in merged or (not merged[url].get("lastmod") and entry.get("lastmod")):
            merged[url] = entry
    return [merged[url] for url in sorted(merged)]


def extract_page(soup: BeautifulSoup) -> tuple[str, str, list[dict], list[str]]:
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    main = None
    for selector in CONTENT_SELECTORS:
        main = soup.select_one(selector)
        if main and main.get_text(" ", strip=True):
            break
    if main is None:
        main = soup.body or soup
    # Preserve headings, paragraphs, lists and tables in document order using HTML snippet.
    for tag in main.select("script, style, noscript, nav, footer, header"):
        tag.decompose()
    html = str(main)
    text = main.get_text("\n", strip=True)
    blocks = []
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "table"]):
        value = el.get_text(" | ", strip=True)
        if value:
            blocks.append({"element": el.name, "text": value})
    links = []
    for a in soup.find_all("a", href=True):
        absolute = canonical_url(urljoin(ROOT_URL, a["href"].strip()))
        if in_scope(absolute):
            links.append(absolute)
    return title, text, blocks, sorted(set(links))


def load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logging.warning("State file unreadable; starting a new crawl state")
    return {"queue": [ROOT_URL], "queued": [canonical_url(ROOT_URL)], "visited": [], "failed": [], "captured": []}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Crawl and archive the SEAI public website as source evidence.")
    parser.add_argument("--start", default=ROOT_URL, help="Starting SEAI URL")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output folder")
    parser.add_argument("--max-pages", type=int, default=0, help="Maximum HTML pages (0 = no configured limit)")
    parser.add_argument("--delay", type=float, default=1.5, help="Seconds between requests")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--resume", action="store_true", help="Resume from existing state.json")
    parser.add_argument("--sitemap-file", type=Path, help="Read a previously saved SEAI urlset sitemap XML file instead of downloading a sitemap")
    parser.add_argument("--include-documents", action="store_true", help="Download linked office/PDF documents")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    start = canonical_url(args.start)
    if not in_scope(start):
        parser.error("--start must be on www.seai.ie or seai.ie")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "pages").mkdir(exist_ok=True)
    (args.out / "documents").mkdir(exist_ok=True)
    state_path = args.out / "state.json"
    state = load_state(state_path) if args.resume else {
        "queue": [start], "queued": [start], "visited": [], "failed": [], "captured": [], "sitemap_entries": []
    }
    state.setdefault("sitemap_entries", [])
    session = build_session()
    robots_url = urljoin(start, "/robots.txt")
    robots_response = session.get(robots_url, timeout=args.timeout)
    robots_response.raise_for_status()
    robots_text = robots_response.text
    rp = RobotFileParser()
    rp.set_url(robots_url)
    rp.parse(robots_text.splitlines())

    # Build the full discovery inventory before attempting page capture.
    sitemap_entries = []
    if args.sitemap_file:
        try:
            sitemap_entries = parse_sitemap_content(args.sitemap_file.read_bytes(), str(args.sitemap_file))
        except (OSError, ET.ParseError, ValueError) as exc:
            parser.error(f"Could not read local sitemap: {exc}")
    else:
        for sm in sitemap_candidates(session, start, robots_text):
            sitemap_entries.extend(parse_sitemap(session, sm, set()))
    sitemap_entries = merge_sitemap_entries(sitemap_entries)
    state["sitemap_entries"] = sitemap_entries
    sitemap_urls = [entry["url"] for entry in sitemap_entries]
    for u in sitemap_urls:
        if u not in state["queued"] and u not in state["visited"]:
            state["queue"].append(u)
            state["queued"].append(u)
    state["sitemaps_discovered"] = len(sitemap_entries)
    save_state(state_path, state)

    # Export the complete discovery inventory, including URLs not yet captured.
    inventory_path = args.out / "url-inventory.json"
    while state["queue"]:
        if args.max_pages and len(state["visited"]) >= args.max_pages:
            break
        url = state["queue"].pop(0)
        if url in state["visited"]:
            continue
        if not rp.can_fetch(USER_AGENT, url):
            state["failed"].append({"url": url, "status": "blocked_by_robots_txt", "checked_at": utc_now()})
            state["visited"].append(url)
            save_state(state_path, state)
            continue
        try:
            response = session.get(url, timeout=args.timeout, allow_redirects=True)
            response.raise_for_status()
            final_url = canonical_url(response.url)
            if not in_scope(final_url):
                state["failed"].append({"url": url, "status": "redirected_out_of_scope", "final_url": response.url, "checked_at": utc_now()})
                state["visited"].append(url)
                save_state(state_path, state)
                continue
            ctype = response.headers.get("Content-Type", "").lower()
            data = response.content
            if "html" not in ctype and not urlparse(final_url).path.lower().endswith((".html", ".htm", "/")):
                ext = Path(urlparse(final_url).path).suffix.lower()
                if args.include_documents and (ext in DOCUMENT_EXTENSIONS or "pdf" in ctype):
                    name = safe_name(final_url, ctype)
                    dest = args.out / "documents" / name
                    dest.write_bytes(data)
                    metadata = {
                        "source_url": url, "final_url": final_url, "content_type": ctype,
                        "http_status": response.status_code, "retrieved_at": utc_now(),
                        "sha256": sha256(data), "archive_path": str(dest.relative_to(args.out)),
                        "acquisition_method": "automated_http_get", "verification_status": "not_independently_verified"
                    }
                    dest.with_suffix(dest.suffix + ".metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
                state["visited"].append(url)
                save_state(state_path, state)
                time.sleep(args.delay)
                continue
            soup = BeautifulSoup(data, "html.parser")
            title, text, blocks, links = extract_page(soup)
            name = safe_name(final_url, "text/html")
            html_path = args.out / "pages" / name
            html_path.write_bytes(data)
            metadata = {
                "source_url": url,
                "final_url": final_url,
                "canonical_url": (soup.find("link", rel="canonical") or {}).get("href"),
                "page_title": title or None,
                "publisher": "Sustainable Energy Authority of Ireland",
                "content_type": ctype,
                "http_status": response.status_code,
                "retrieved_at": utc_now(),
                "sha256": sha256(data),
                "archive_path": str(html_path.relative_to(args.out)),
                "acquisition_method": "automated_http_get",
                "verification_status": "url_and_content_archived_not_fact_checked",
                "outbound_internal_links": links,
                "text_path": str(html_path.with_suffix(".txt").relative_to(args.out)),
            }
            html_path.with_suffix(html_path.suffix + ".metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            html_path.with_suffix(".txt").write_text(text, encoding="utf-8")
            html_path.with_suffix(".blocks.json").write_text(json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8")
            state["captured"].append({"url": final_url, "title": title, "archive_path": str(html_path.relative_to(args.out)), "sha256": metadata["sha256"]})
            for link in links:
                if link not in state["queued"] and rp.can_fetch(USER_AGENT, link):
                    state["queue"].append(link)
                    state["queued"].append(link)
            state["visited"].append(url)
            logging.info("Captured %s | %s | queue=%d", response.status_code, final_url, len(state["queue"]))
        except requests.RequestException as exc:
            state["failed"].append({"url": url, "status": "request_error", "error": str(exc), "checked_at": utc_now()})
            state["visited"].append(url)
            logging.warning("Failed %s: %s", url, exc)
        finally:
            save_state(state_path, state)
            time.sleep(args.delay)

    captured_by_url = {item["url"]: item for item in state["captured"]}
    failures_by_url = {item["url"]: item for item in state["failed"]}
    visited_set = set(state["visited"])
    sitemap_by_url = {item["url"]: item for item in state.get("sitemap_entries", [])}
    all_urls = sorted(set(state["queued"]) | set(sitemap_by_url))
    url_records = []
    for url in all_urls:
        record = {"url": url, "lastmod": sitemap_by_url.get(url, {}).get("lastmod")}
        if url in captured_by_url:
            record.update({"status": "captured", "page_title": captured_by_url[url].get("title"), "archive_path": captured_by_url[url].get("archive_path"), "sha256": captured_by_url[url].get("sha256")})
        elif url in failures_by_url:
            record.update({"status": failures_by_url[url].get("status"), "failure": failures_by_url[url]})
        elif url in visited_set:
            record["status"] = "visited_without_page_capture"
        else:
            record["status"] = "pending"
        url_records.append(record)

    inventory = {
        "site": "https://www.seai.ie/",
        "generated_at": utc_now(),
        "sitemaps_discovered": state.get("sitemaps_discovered", 0),
        "queued_urls": len(state["queued"]),
        "visited_urls": len(state["visited"]),
        "captured_pages": len(state["captured"]),
        "failed_or_excluded": len(state["failed"]),
        "remaining_queue": len(state["queue"]),
        "urls": url_records,
        "pages": state["captured"],
        "failures": state["failed"],
        "scope_note": "URL records preserve sitemap lastmod where supplied. Capture status describes this crawler's attempts only. Only public URLs on seai.ie/www.seai.ie are in scope; robots.txt is respected. A listed URL is not proof that its content was accessible, captured, or fact-checked."
    }
    inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    save_state(state_path, state)
    logging.info("Finished batch: %d captured, %d visited, %d remaining", len(state["captured"]), len(state["visited"]), len(state["queue"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
