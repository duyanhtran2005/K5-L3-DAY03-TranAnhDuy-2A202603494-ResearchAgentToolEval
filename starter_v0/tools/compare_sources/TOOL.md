---
name: compare_sources
track: bonus
kind: local_formatter
provider: none
requires_env: []
inputs: [items, max_items]
outputs: [items, input_count, unique_count, duplicate_count, returned_count, truncated, duplicate_groups, source_counts]
side_effect: false
requires_confirmation: false
---
# compare_sources

Compare sources already collected by lookup/fetch/papers/social tools or supplied
by the user. Detect repeated URLs and count unique URLs per hostname.
No API key, dependencies beyond the starter, network access, or file writes.

## Arguments

- items (required): list of objects with a non-empty absolute HTTP(S) url.
  Optional title, source, summary must be strings. Additional metadata is
  preserved from the first occurrence.
- max_items (optional): integer 1..100, default 10. Caps returned unique items
  only; counts and duplicate detection cover the entire input.
  Booleans and numeric strings are rejected.

## Behavior and limitations

Trim surrounding URL whitespace, lowercase scheme/hostname, remove default ports
(HTTP 80 / HTTPS 443), normalize empty path to "/", and remove fragments.
Preserve scheme, path case, non-root trailing slashes, query strings, non-default
ports and subdomains (including www). Tracking parameters are preserved because
different queries can identify different resources.

Keep the first occurrence in input order, without mutating input or merging text.
Original url stays unchanged; canonical_url shows the key used for comparison.
duplicate_groups contains zero-based input_indexes. source_counts is sorted by
hostname and counts unique URLs, including items omitted by max_items.

This tool does not search, fetch, format a digest, verify facts, rank credibility
or prove that sources are independent. Different hostnames are not evidence of
independent reporting. Page fragments are ignored for document-level comparison.

An empty list is a valid empty result. Missing items, wrong types, invalid URLs,
embedded credentials or malformed ports return an error dictionary:
{"tool": "compare_sources", "error": "<exception type>", "message": "..."}.
Reject invalid input as a whole; never return partial success.

## Example

Call:
compare_sources(items=[
    {"title": "First", "url": "https://EXAMPLE.com:443/report#intro"},
    {"title": "Repeated", "url": "https://example.com/report#results"},
    {"title": "Other", "url": "https://other.org/post"}
], max_items=10)

Expected: input_count=3, unique_count=2, duplicate_count=1, returned_count=2,
truncated=false. First title remains "First". Duplicate input_indexes: [0, 1].

## Verification

From starter_v0, run:
python -B -m pytest -q --capture=sys -p no:cacheprovider tests/test_compare_sources.py tests/test_tool_contract.py

Integration handoff: HANDOFF.md. declaration.yaml contains the proposed tools.yaml
entry for the coordinator; eval_case.json contains G_compare_sources_existing_items
for the group-eval owner. Shared tools.yaml, eval_group.json and REPORT.md are
unchanged on this branch; the coordinator must add the declaration before live use.
