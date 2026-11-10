# compare_sources handoff

Branch: tranduongtrungtinh_2A202603488

## Tool owner delivery

- tool.py: offline URL deduplication and hostname counts.
- TOOL.md: contract, arguments, examples and limitations.
- ../../tests/test_compare_sources.py: 31 offline test cases.
- ../__init__.py: import and TOOL_FUNCTIONS registration.

## Arguments to share with the team

compare_sources(items, max_items=10)

items: required array of objects, each with an absolute HTTP(S) url.
Optional title/source/summary must be strings.
max_items: optional integer 1..100, default 10, caps returned unique items only.

## Integration owner: tool declaration

declaration.yaml contains the proposed tool declaration under a tools list.
Copy its compare_sources entry into artifacts/tools.yaml under the existing tools
list. Do not replace the existing list or add a second top-level tools key.
The shared system prompt, tools.yaml and version_log.csv are unchanged by this
branch. Until the coordinator adds this declaration, the model cannot select the
new tool via its advertised tools.

## Group eval owner

eval_case.json contains one proposed single-turn case,
G_compare_sources_existing_items. Integrate it into data/eval_group.json as one
of the required 5 single-turn cases, alongside 5 multi-turn cases. The shared
group eval file is unchanged by this branch. Run group eval after declaration
integration; no live provider result is claimed here.

## UI/report owners: suggested report content

Tool row:
compare_sources | Remove repeated collected URLs and count unique URLs per hostname | New team tool

Sample request:
Compare these collected sources, remove repeated URLs and count unique URLs per
hostname: [{"url":"https://example.com/a#intro"},
{"url":"https://example.com/a#results"},{"url":"https://other.org/b"}].
Return at most 2 unique items.

Expected: 3 inputs, 2 unique URLs, 1 duplicate, 2 hostnames.
The tool does not fetch URLs, verify facts, or judge source credibility.
Unit-test evidence is in artifacts/compare_sources_tests.txt.
The shared REPORT.md is unchanged by this branch.
