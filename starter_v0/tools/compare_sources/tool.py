"""Compare already-collected URLs locally; no network or fact verification."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit

from tools._shared import err


def _canonical_url(url: str) -> tuple[str, str]:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Each item needs a non-empty string url.")
    url = url.strip()
    if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url):
        raise ValueError("URLs must not contain whitespace or control characters.")
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Each url must be an absolute HTTP(S) URL with a hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URLs must not contain credentials.")
    hostname = parsed.hostname.lower()
    port = parsed.port
    authority = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None and (parsed.scheme.lower(), port) not in {("http", 80), ("https", 443)}:
        authority += f":{port}"
    return urlunsplit((parsed.scheme.lower(), authority, parsed.path or "/", parsed.query, "")), hostname


def compare_sources(items: list[dict[str, Any]] | None = None, max_items: int = 10) -> dict[str, Any]:
    """Deduplicate URLs and count unique URLs per hostname; keep first occurrence."""
    try:
        if not isinstance(items, list):
            raise TypeError("items must be a list of objects; use [] for an empty collection.")
        if isinstance(max_items, bool) or not isinstance(max_items, int):
            raise TypeError("max_items must be an integer.")
        if not 1 <= max_items <= 100:
            raise ValueError("max_items must be between 1 and 100.")
        unique: dict[str, dict[str, Any]] = {}
        indexes: dict[str, list[int]] = {}
        counts: dict[str, int] = {}
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise TypeError(f"items[{index}] must be an object.")
            for field in ("title", "source", "summary"):
                if field in item and not isinstance(item[field], str):
                    raise TypeError(f"items[{index}].{field} must be a string.")
            canonical, host = _canonical_url(item.get("url"))
            indexes.setdefault(canonical, []).append(index)
            if canonical not in unique:
                unique[canonical] = {**item, "canonical_url": canonical, "source_domain": host}
                counts[host] = counts.get(host, 0) + 1
        kept = list(unique.values())[:max_items]
        return {
            "tool": "compare_sources", "items": kept,
            "input_count": len(items), "unique_count": len(unique),
            "duplicate_count": len(items) - len(unique), "returned_count": len(kept),
            "truncated": len(unique) > len(kept),
            "duplicate_groups": [
                {"canonical_url": url, "input_indexes": positions}
                for url, positions in indexes.items() if len(positions) > 1
            ],
            "source_counts": [
                {"domain": host, "unique_url_count": count} for host, count in sorted(counts.items())
            ],
        }
    except Exception as exc:
        return err("compare_sources", exc)
