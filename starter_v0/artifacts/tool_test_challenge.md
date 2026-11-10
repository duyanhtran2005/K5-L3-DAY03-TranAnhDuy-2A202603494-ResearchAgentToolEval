# Tool unit-test challenge evidence

Client date: 2026-11-10 (Asia/Bangkok)
Branch: tranduongtrungtinh_2A202603488

## Scope and outcome

Completed all 17 original pytest.skip(TODO) stubs in tests/test_tools_todo.py.
Two parametrized original tests cover both None/[] and Top/Latest, yielding 19
cases. Added 16 regression/compatibility cases in the same file: 35 cases total.
All 31 previously delivered compare_sources cases remain passing.

Read and followed tests/test_tools_examples.py and tests/conftest.py:
- HTTP tools use fake_http with FakeResponse and assert requests and results.
- Credentials are synthetic test-key / test-token / test-channel set by monkeypatch.
- clean_env removes tool credentials and block_network rejects real requests.
- No .env loading, model calls, real API keys, HTTP calls or Telegram posts.
- Policy tests use the repository's local policy markdown files.

Before fixes, the completed TODO file produced:
12 failed, 23 passed in 0.33s (exit code 1).
The 12 failures are the regression tests described below; no skips remained.

## Bugs reproduced and fixed

### 1. Telegram confirmation accepted truthy values of the wrong type

Location: tools/send/tool.py, send_telegram.
Before: if not confirmed treated "false", "true", 1 and a non-empty object as
confirmation and issued a mocked POST when synthetic credentials were available.
Fix: if confirmed is not True returns needs_confirmation without making HTTP.
Only literal boolean True enters the sending branch.

Regression:
test_send_non_boolean_confirmation_never_posts (4 cases).
The original confirmed=True success case and confirmed=False guardrail test
remain passing. This protects execution even if a model supplies malformed args.

### 2. Four result-count arguments silently accepted nonpositive counts

Locations:
- tools/timeline/tool.py: limit=0 became 5; negative values used Python negative slicing.
- tools/social_search/tool.py: the same limit fallback/negative-slice behavior.
- tools/lookup/tool.py: max_results=0 became 5; negative values were sent to Tavily.
- tools/policy/tool.py: top_k=0 became 3; negative values were clamped to 1.

Chosen boundary: counts must be positive. Zero and negative values are invalid,
not a request to use the default. Defaults still apply when the argument is omitted.
Fix: convert to int, validate >0 before HTTP/local search, and return the existing
error dictionary containing ValueError and the argument name on invalid counts.
Slice/send only the validated count. Existing numeric strings such as "1" remain
supported; normal positive limits and defaults are unchanged.

Regressions:
- test_nonpositive_result_count_returns_error_without_http (8 cases)
- test_numeric_string_result_count_remains_supported (4 compatibility cases)

Updated the five relevant TOOL.md files to document the enforced boundaries.
Shared artifacts/tools.yaml remains untouched for the coordinator to manage.

## Final verification

Working directory: starter_v0

Command:
```powershell
.\.venv\Scripts\python.exe -B -m pytest -q --capture=sys -p no:cacheprovider
```

Observed output (exit code 0):
```text
........................................................................ [ 56%]
........................................................                 [100%]
128 passed in 0.40s
```

Result: 128 passed, 0 failed, 0 skipped.
The repository contract suite and worked examples were included in this run.
A separate git diff --check found no whitespace errors.

## Suggested REPORT B5 handoff

Completed 17 TODO stubs and retained regression tests for two bug families across
five existing tools. The full offline suite passes 128 cases with no skips.
Tool-routing eval alone does not verify Telegram's execution-time confirmation
guard or reject invalid counts before HTTP; these unit tests check both behaviors.
Evidence: artifacts/tool_test_challenge.md.

No edits to shared REPORT.md, eval_base.json, eval_group.json, system_prompt.md,
tools.yaml or version_log.csv were needed for this challenge.
