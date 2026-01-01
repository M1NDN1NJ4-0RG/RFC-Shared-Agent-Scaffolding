@copilot — implement next: **populate the “File” and “Line” columns in ALL lint failure tables** emitted by the `repo-lint` package, across every execution path.

## Problem

Current failure output includes a header `File   Line   Message` but some entries are missing the File/Line columns or are not consistently formatted. Example from Python lint output shows module banners mixed with entries and the table data is incomplete.

## Required behavior (non-negotiable)

For every lint violation row shown in any report/table (console output AND any committed failure-report artifacts):

1. **File column** MUST be the filename only (basename), including extension, no directories.

   * Example: `reporter.py` not `tools/repo_lint/ui/reporter.py`
2. **Line column** MUST be the exact integer line number for the violation.

   * Example: `447`
3. **Message column** MUST contain the violation message (include rule/code like `W0611`, `E0401`, `W1309` when available).

If a tool does not provide a line number:

* Use `-` in Line, but ONLY if the tool truly has no line concept.
* Do NOT leave the File column blank; it must still be basename if any file is known.

## Implementation requirements

* Identify and fix the point(s) where violation objects are created / normalized.
* Ensure a single canonical normalization step that produces:

  * `file_basename` (string)
  * `line` (int or "-")
  * `message` (string)
  * (optional) `code` (string like `W0611`) if present, but message must still render cleanly.
* Ensure all renderers (Rich table, markdown artifact writers, consolidated report writers) consume this canonical normalized structure and NEVER re-derive file/line inconsistently.

## Output formatting requirements

* Every violation is exactly one row in the table.
* No module banners or separators should masquerade as a “row” in the File/Line/Message table.

  * If you want module sections, render them as section headers ABOVE the table, not as fake rows.

## Full test requirements (must add/extend tests)

Add/extend tests so this is enforced across all relevant `repo-lint` report paths:

1. Unit tests for the normalization function: given raw linter output, it produces correct basename + exact line.
2. Tests for reporter/table rendering: the rendered table rows always include populated File and Line columns for violations.
3. Regression test using the provided sample failures:

   * `tools/repo_lint/tests/test_phase_2_7_features.py:320:12: W0611 ...`
   * `tools/repo_lint/ui/reporter.py:447:35: W1309 ...`
     Ensure table rows contain:
   * File = `test_phase_2_7_features.py`, Line = `320`
   * File = `reporter.py`, Line = `447`

## Acceptance criteria

* Run the full repo-lint test suite locally and in CI: all tests pass.
* Generate a failure report (force a known lint failure) and verify:

  * The File column is ALWAYS basename+ext
  * The Line column is ALWAYS present with correct integer line number when available
  * No blank File/Line cells for real violations
* Update or add a fixture/example output file demonstrating correct populated table output.
