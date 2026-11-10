"""Offline tests for the team's new tool; no model/API credits needed."""
from copy import deepcopy

import pytest

from tools import TOOL_FUNCTIONS

compare_sources = TOOL_FUNCTIONS["compare_sources"]


def test_duplicates_keep_first_item_count_domains_and_do_not_mutate_input():
    items = [
        {"title": "First", "url": " https://EXAMPLE.com:443/report#intro ", "summary": "Original"},
        {"title": "Repeated", "url": "https://example.com/report#results"},
        {"title": "Other", "url": "https://other.org/post"},
    ]
    original = deepcopy(items)
    result = compare_sources(items)
    assert result["tool"] == "compare_sources"
    assert (result["input_count"], result["unique_count"], result["duplicate_count"]) == (3, 2, 1)
    assert result["returned_count"] == 2
    assert result["truncated"] is False
    assert result["items"][0] == {
        **items[0], "canonical_url": "https://example.com/report", "source_domain": "example.com"
    }
    assert result["duplicate_groups"] == [
        {"canonical_url": "https://example.com/report", "input_indexes": [0, 1]}
    ]
    assert result["source_counts"] == [
        {"domain": "example.com", "unique_url_count": 1},
        {"domain": "other.org", "unique_url_count": 1},
    ]
    assert items == original


def test_limit_caps_items_but_counts_cover_all_inputs():
    result = compare_sources([
        {"url": "https://example.com/a"}, {"url": "https://example.com/b"},
        {"url": "https://other.org/c"}, {"url": "https://other.org/c#fragment"},
    ], max_items=1)
    assert len(result["items"]) == result["returned_count"] == 1
    assert result["unique_count"] == 3
    assert result["duplicate_count"] == 1
    assert result["truncated"] is True
    assert result["source_counts"] == [
        {"domain": "example.com", "unique_url_count": 2},
        {"domain": "other.org", "unique_url_count": 1},
    ]
    assert result["duplicate_groups"][0]["input_indexes"] == [2, 3]


def test_distinct_queries_paths_schemes_ports_and_subdomains_are_not_merged():
    urls = [
        "https://example.com/a?x=1", "https://example.com/a?x=2",
        "https://example.com/A?x=1", "http://example.com/a?x=1",
        "https://example.com:8443/a?x=1", "https://www.example.com/a?x=1",
        "https://example.com/a/?x=1",
    ]
    result = compare_sources([{"url": url} for url in urls])
    assert result["unique_count"] == len(urls)
    assert result["duplicate_count"] == 0


def test_root_urls_and_default_http_ports_are_normalized():
    result = compare_sources([{"url": "http://EXAMPLE.com:80"}, {"url": "http://example.com/#top"}])
    assert result["unique_count"] == 1
    assert result["items"][0]["canonical_url"] == "http://example.com/"


def test_empty_list_returns_empty_success():
    assert compare_sources([]) == {
        "tool": "compare_sources", "items": [], "input_count": 0,
        "unique_count": 0, "duplicate_count": 0, "returned_count": 0,
        "truncated": False, "duplicate_groups": [], "source_counts": [],
    }


@pytest.mark.parametrize("items", [
    None, "", {}, [None], [{"url": ""}], [{}], [{"url": 123}],
    [{"url": "https://example.com", "summary": None}],
])
def test_bad_model_input_returns_error_dict(items):
    result = compare_sources(items)
    assert result["tool"] == "compare_sources"
    assert result["error"] in {"TypeError", "ValueError"}
    assert result["message"]
    assert "items" not in result


@pytest.mark.parametrize("limit", [0, -1, 101, "5", True, 1.5, None])
def test_invalid_limit_returns_error_instead_of_silent_coercion(limit):
    result = compare_sources([], max_items=limit)
    assert result["error"] in {"TypeError", "ValueError"}
    assert "max_items" in result["message"]


@pytest.mark.parametrize("url", [
    "not-a-url", "ftp://example.com/file", "https:///missing-host",
    "https://example.com:bad/path", "https://example.com:99999/path",
    "https://[broken", "https://user:secret@example.com/",
    "https://example.com/a b", "https://example.com/\npath",
])
def test_url_parsing_failures_return_error_without_partial_results(url):
    result = compare_sources([{"url": "https://valid.org/"}, {"url": url}])
    assert result["tool"] == "compare_sources"
    assert result["error"] == "ValueError"
    assert result["message"]
    assert "items" not in result


def test_ipv6_urls_support_default_port_normalization():
    result = compare_sources([{"url": "https://[::1]:443/a"}, {"url": "https://[::1]/a#top"}])
    assert result["unique_count"] == 1
    assert result["items"][0]["canonical_url"] == "https://[::1]/a"


def test_omitted_items_returns_error_dict():
    assert compare_sources()["error"] == "TypeError"
