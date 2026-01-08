# Markdown Contracts

**Status:** Canonical source of truth for Markdown formatting requirements
**Last Updated:** 2026-01-08
**Enforcement:** Enforced via `markdownlint-cli2` in `repo-lint check --ci`

## Overview

This document defines the mandatory Markdown formatting and style requirements for the RFC-Shared-Agent-Scaffolding repository. These standards ensure consistency, readability, and maintainability across all Markdown documentation.

**Key Principle:** All Markdown files must follow a consistent, deterministic style that is machine-checkable and auto-fixable where possible.

---

## Scope

### Files Enforced

**Default:** All `*.md` files in the repository are subject to Markdown linting.

**Included directories:**

- `docs/**/*.md` (all documentation)
- `*.md` (root-level files: README.md, CONTRIBUTING.md, etc.)
- `wrappers/**/*.md` (wrapper documentation)
- `conformance/**/*.md` (conformance test documentation)
- `rust/**/*.md` (Rust project documentation)
- `tools/**/*.md` (tooling documentation)

### Exclusions

The following files/directories are **explicitly excluded** from Markdown linting:

1. **CI failure reports:** `repo-lint-failure-reports/**/*.md`
   - **Reason:** Generated artifacts, not human-authored documentation
   - **Format:** Machine-generated summaries with intentional violations for readability

2. **Vendored/third-party content:** (none currently)
   - **Future:** If external Markdown is vendored, add exclusions here

3. **Temporary/scratch files:** Any `*.md` files in `/tmp/` or build artifacts

**Important:** Exclusions MUST be documented with a clear reason. Avoid broad exclusions.

---

## Ruleset

### Rule Philosophy

This ruleset follows **Markdown Best Practices** from authoritative sources:

- [Markdown Guide](https://www.markdownguide.org/basic-syntax/) - Industry-standard Markdown reference
- [CommonMark Specification](https://commonmark.org/) - Standardized Markdown syntax
- [Google Developer Documentation Style Guide](https://developers.google.com/style/markdown)
- [GitHub Flavored Markdown](https://github.github.com/gfm/) - GitHub's Markdown extensions

**Core Principles:**

- **Prefer machine-fixable rules** to reduce manual effort
- **No vague rules:** Every rule must be deterministic and checkable
- **Compatibility first:** Rules must work with common Markdown renderers (GitHub, GitLab, CommonMark)
- **Accessibility:** Support screen readers and assistive technologies
- **Consistency:** Use one style throughout the repository

### Core Rules (MANDATORY)

#### 1. Heading Structure

**Best Practice Rationale:** Proper heading hierarchy improves document structure, SEO, accessibility (screen readers), and navigation.

**MD001/heading-increment** - Headings MUST increment by one level at a time (Markdown Guide: Heading Best Practices)

```markdown
# ✅ Correct - proper hierarchy
## Section
### Subsection
#### Detail

# ❌ Wrong - skipped level
### Subsection (no H2 before this)
```

**MD003/heading-style** - Use ATX-style headings (`#`) consistently (CommonMark best practice)

**Rationale:** ATX headings (`#`) are more widely supported and easier to parse than Setext headings (underlines).

```markdown
# ✅ Correct - ATX style
## Section

❌ Wrong - Setext style (underlines)
Section
-------
```

**MD018/no-missing-space-atx** - MUST include space after `#` in headings (Markdown Guide requirement)

```markdown
# ✅ Correct
## Section

#❌ Wrong (no space)
##Wrong (no space)
```

**MD019/no-multiple-space-atx** - No multiple spaces after `#` (consistency best practice)

```markdown
# ✅ Correct
## Section

#  ❌ Wrong (two spaces)
##   ❌ Wrong (three spaces)
```

**MD020/no-missing-space-closed-atx** - Space required before closing `#` in ATX closed headings

```markdown
# ✅ Correct #
## Section ##

#❌ Wrong# (no spaces)
```

**MD021/no-multiple-space-closed-atx** - No multiple spaces in ATX closed headings

```markdown
# ✅ Correct #
## Section ##

#  ❌ Wrong  # (multiple spaces)
```

**MD022/blanks-around-headings** - Headings MUST be surrounded by blank lines (Markdown Guide: Compatibility Best Practice)

**Rationale:** Ensures consistent rendering across different Markdown processors.

```markdown
# ✅ Correct

Text before heading.

## Section

Text after heading.

# ❌ Wrong
## No blank line above
Text immediately after.
```

**MD023/heading-start-left** - Headings MUST start at the beginning of the line (CommonMark requirement)

```markdown
# ✅ Correct
## Section

  # ❌ Wrong (indented)
```

**MD024/no-duplicate-heading** - Avoid duplicate headings (RELAXED: allowed in different sections)

**Best Practice:** Use unique headings when possible for better navigation and linking. When duplicates are necessary (e.g., "Overview" in multiple sections), ensure they're in different hierarchical contexts.

**MD025/single-title/single-h1** - Each document SHOULD have exactly one H1 (`#`) title at the top (Markdown Guide: Document Structure)

**Rationale:** Improves document structure, SEO, and screen reader navigation.

**MD026/no-trailing-punctuation** - Headings SHOULD NOT end with punctuation (`.` `!` `,` `:` `;`)

**Rationale:** Markdown Guide best practice - headings are titles, not sentences.

```markdown
# ✅ Correct
## Installation

# ❌ Wrong
## Installation.
## What is this?
```

**MD041/first-line-heading/first-line-h1** - Files SHOULD start with a top-level heading (H1) (Document Structure Best Practice)

**Rationale:** Provides immediate context and improves document navigation.

**MD043/required-headings** - DISABLED (too restrictive for general-purpose docs)

#### 2. Line Length

**MD013/line-length** - Line length limit

**Best Practice Source:** Google Developer Style Guide recommends 80-120 characters for readability.

**Policy:**

- **Maximum:** 120 characters (balanced between readability and practicality)
- **Rationale:**
  - 80 chars (markdownlint default) is too restrictive for technical documentation
  - 120 chars is widely accepted (matches Python's PEP 8 recommendation)
  - Accommodates code examples, long URLs, and technical terms
- **Exceptions (automatically excluded):**
  - Code blocks (fenced or indented)
  - Tables
  - Headings (only when unavoidable)
  - URLs/links (breaking would break functionality)

**Configuration:**

```json
{
  "MD013": {
    "line_length": 120,
    "code_blocks": false,
    "tables": false,
    "headings": true
  }
}
```

#### 3. Code Blocks

**Best Practice Rationale:** Proper code block formatting enables syntax highlighting, improves readability, and ensures consistent rendering.

**MD040/fenced-code-language** - Code blocks MUST specify a language (Markdown Guide: Code Block Best Practices)

**Rationale:** Enables syntax highlighting and clarifies the code's purpose.

```markdown
# ✅ Correct - language specified
```bash
echo "Hello"
```

# ❌ Wrong - no language

```
echo "Hello"
```

```

**Allowed language identifiers:**

- **Shell/CLI:** `bash`, `sh`, `shell`, `console`, `powershell`, `cmd`
- **Programming:** `python`, `rust`, `perl`, `javascript`, `typescript`, `java`, `c`, `cpp`, `csharp`, `go`, `ruby`, `php`
- **Data/Config:** `yaml`, `toml`, `json`, `xml`, `ini`, `conf`
- **Markup/Other:** `markdown`, `html`, `css`, `sql`, `diff`, `plaintext`, `text`
- **No highlighting needed:** Use `text` or `plaintext`

**MD046/code-block-style** - Use fenced code blocks (```) consistently (CommonMark Best Practice)

**Rationale:** Fenced blocks are more versatile (support language tags, work in lists) and widely supported.

```markdown
# ✅ Correct - fenced
```bash
echo "test"
```

# ❌ Wrong - indented (less flexible)

    echo "test"

```

**MD048/code-fence-style** - Use backticks (```) for code fences, NOT tildes (`~~~`) (Consistency Best Practice)

**Rationale:** Backticks are more common and widely recognized.

```markdown
# ✅ Correct - backticks
```bash
code
```

# ❌ Wrong - tildes (less common)

~~~bash
code
~~~

```

#### 4. Whitespace

**Best Practice Rationale:** Clean whitespace improves diff clarity, prevents rendering issues, and ensures consistency.

**MD009/no-trailing-spaces** - NO trailing spaces at end of lines (Markdown Guide: Best Practices)

**Rationale:** Trailing spaces are invisible, cause noisy diffs, and can create unintended line breaks.

**Exception:** Two trailing spaces for explicit line breaks are DISCOURAGED - use `<br>` tag instead for clarity.

**MD010/no-hard-tabs** - Use spaces, NOT tabs (Universal Best Practice)

**Rationale:** Tabs render inconsistently across editors and platforms.

**MD012/no-multiple-blanks** - Maximum one consecutive blank line (Markdown Guide: Compatibility)

**Rationale:** Excessive blank lines don't affect rendering but add noise to source.

```markdown
# ✅ Correct - single blank line
Text

Another paragraph

# ❌ Wrong - three blank lines
Text



Another paragraph
```

**MD047/single-trailing-newline** - Files MUST end with a single newline (POSIX Standard)

**Rationale:** POSIX standard for text files; prevents issues with version control and text processing tools.

#### 5. Lists

**Best Practice Rationale:** Consistent list formatting improves readability and ensures proper rendering across Markdown processors.

**MD004/ul-style** - Unordered lists MUST use `-` (dash) consistently (Markdown Guide: List Best Practices)

**Rationale:** Dashes are most readable and widely used. Mixing styles reduces consistency.

```markdown
# ✅ Correct - consistent dashes
- Item one
- Item two
  - Nested item

# ❌ Wrong - mixed styles
* Item one
+ Item two
- Item three
```

**MD005/list-indent** - Consistent indentation for nested lists (2 spaces per level) (CommonMark Specification)

```markdown
# ✅ Correct - 2 spaces
- Parent
  - Child
    - Grandchild

# ❌ Wrong - 4 spaces
- Parent
    - Child (too much indent)
```

**MD006/ul-start-left** - Unordered lists MUST start at the beginning of the line

**MD007/ul-indent** - Unordered list indentation: 2 spaces per level (Markdown Guide Standard)

**MD027/no-multiple-space-blockquote** - No multiple spaces after blockquote marker

**MD029/ol-prefix** - Ordered lists SHOULD use sequential numbers (Markdown Guide: Ordered List Best Practice)

**Rationale:** Makes source readable and matches rendered output. Some tools auto-number, but explicit numbering is clearer.

```markdown
# ✅ Correct - sequential
1. First
2. Second
3. Third

# ⚠️ Acceptable but discouraged - all 1s (auto-numbered)
1. First
1. Second
1. Third

# ❌ Wrong - random numbers
1. First
5. Second
2. Third
```

**Configuration:** Prefer `ordered` style

```json
{
  "MD029": { "style": "ordered" }
}
```

**MD030/list-marker-space** - Exactly 1 space after list markers (Markdown Guide Standard)

```markdown
# ✅ Correct
- Item
1. Item

# ❌ Wrong
-  Item (two spaces)
1.Item (no space)
```

**MD032/blanks-around-lists** - Lists MUST be surrounded by blank lines (Markdown Guide: Compatibility Best Practice)

**Rationale:** Ensures lists are recognized correctly by all Markdown processors.

```markdown
# ✅ Correct

Text before list.

- Item
- Item

Text after list.

# ❌ Wrong
Text before list.
- Item (no blank line above)
- Item
Text after list. (no blank line below)
```

#### 6. Links and Images

**Best Practice Rationale:** Proper link formatting ensures functionality, accessibility, and maintainability.

**MD011/no-reversed-links** - Link syntax MUST be `[text](url)`, NOT `(url)[text]` (Markdown Syntax Requirement)

```markdown
# ✅ Correct
[Link text](https://example.com)

# ❌ Wrong (reversed)
(https://example.com)[Link text]
```

**MD034/no-bare-urls** - URLs MUST be wrapped (Markdown Guide: Link Best Practices)

**Rationale:** Bare URLs may not be clickable in all renderers; wrapping ensures they're recognized as links.

```markdown
# ✅ Correct - wrapped
<https://example.com>
[Example](https://example.com)
Visit our site: <https://example.com>

# ❌ Wrong - bare URL
Visit https://example.com for more info.
```

**MD039/no-space-in-links** - No spaces in link URLs

```markdown
# ✅ Correct
[Link](https://example.com/path)

# ❌ Wrong
[Link](https://example.com /path)
```

**MD042/no-empty-links** - Links MUST have descriptive text (Accessibility Best Practice)

**Rationale:** Screen readers need descriptive link text; empty links are not accessible.

```markdown
# ✅ Correct - descriptive text
[User Guide](docs/guide.md)
[Download](https://example.com/file.zip)

# ❌ Wrong - empty text
[](https://example.com)
```

**MD044/proper-names** - DISABLED (too opinionated for technical docs)

**MD045/no-alt-text** - Images SHOULD have alt text (Accessibility Best Practice - WCAG 2.1)

**Rationale:** Alt text is essential for screen readers and when images fail to load.

```markdown
# ✅ Correct - descriptive alt text
![Diagram showing the request flow](architecture.png)
![GitHub logo](github-logo.svg)

# ❌ Wrong - no alt text (accessibility issue)
![](screenshot.png)

# ⚠️ Acceptable for decorative images only
![](decorative-line.png)
```

**Configuration:** Warning level (not error) to allow decorative images

```json
{
  "MD045": { "severity": "warning" }
}
```

#### 7. HTML in Markdown

**MD033/no-inline-html** - Inline HTML is **allowed but minimized** (Markdown Guide: Keep it Simple)

**Best Practice:** Prefer pure Markdown for portability and simplicity. Use HTML only when Markdown cannot express the desired formatting.

**Allowed HTML tags (when necessary):**

- `<details>`, `<summary>` - Collapsible sections (no Markdown equivalent)
- `<kbd>` - Keyboard shortcuts (semantic meaning)
- `<br>` - Explicit line breaks (prefer over trailing spaces for clarity)
- `<sub>`, `<sup>` - Subscript/superscript (no Markdown equivalent)
- `<dl>`, `<dt>`, `<dd>` - Definition lists (no Markdown equivalent)

**Prohibited HTML (security/maintenance):**

- `<script>`, `<style>` - Security risk, not portable
- `<iframe>`, `<embed>`, `<object>` - Security risk
- Complex HTML structures - Defeats the purpose of Markdown

**Configuration:**

```json
{
  "MD033": {
    "allowed_elements": [
      "details", "summary", "kbd", "br", "sub", "sup",
      "dl", "dt", "dd"
    ]
  }
}
```

#### 8. Emphasis and Inline Formatting

**Best Practice Rationale:** Consistent inline formatting improves readability and source maintainability.

**MD036/no-emphasis-as-heading** - Do NOT use emphasis (bold/italic) as heading substitute (Markdown Guide: Headings)

**Rationale:** Use proper heading syntax for structure and accessibility.

```markdown
# ✅ Correct - proper heading
## Section Title

# ❌ Wrong - fake heading
**Section Title**
```

**MD037/no-space-in-emphasis** - No spaces inside emphasis markers (Markdown Syntax)

**Rationale:** Spaces break the emphasis syntax in many processors.

```markdown
# ✅ Correct
This is **bold** and *italic* text.

# ❌ Wrong
This is ** bold ** and * italic * text.
```

**MD049/emphasis-style** - Use asterisks (`*`) for emphasis, NOT underscores (Markdown Guide: Best Practice)

**Rationale:** Asterisks work in more contexts (e.g., mid-word emphasis) and are more common.

```markdown
# ✅ Correct - asterisks
*italic* and **bold**

# ❌ Wrong - underscores (less versatile)
_italic_ and __bold__
```

**MD050/strong-style** - Use `**` for strong emphasis, NOT `__` (Consistency)

```markdown
# ✅ Correct
**bold text**

# ❌ Wrong
__bold text__
```

**MD051/link-fragments** - Link fragments SHOULD exist (link validation)

**Configuration:** Warning level (enforcing requires full link checking infrastructure)

#### 9. Blockquotes

**MD027/no-multiple-space-blockquote** - Single space after `>` in blockquotes

```markdown
# ✅ Correct
> This is a quote.
> Second line.

# ❌ Wrong
>  This has two spaces.
>   This has three.
```

**MD028/no-blanks-blockquote** - No blank lines inside a single blockquote

```markdown
# ✅ Correct - continuous blockquote
> Line one.
> Line two.

# ✅ Correct - separate blockquotes
> First quote.

> Second quote.

# ❌ Wrong - blank line inside single blockquote
> Line one.
>
> Line two (should be continuous or separate).
```

---

## Configuration Mapping

The following `.markdownlint-cli2.jsonc` configuration implements this contract:

```jsonc
{
  "config": {
    // Heading rules
    "MD001": true,  // heading-increment
    "MD003": { "style": "atx" },  // heading-style
    "MD018": true,  // no-missing-space-atx
    "MD019": true,  // no-multiple-space-atx
    "MD022": true,  // blanks-around-headings
    "MD023": true,  // heading-start-left
    "MD024": false, // no-duplicate-heading (allow in different sections)
    "MD025": true,  // single-h1
    "MD041": true,  // first-line-h1

    // Line length
    "MD013": {
      "line_length": 120,
      "code_blocks": false,
      "tables": false,
      "headings": true
    },

    // Code blocks
    "MD040": true,  // fenced-code-language
    "MD046": { "style": "fenced" },  // code-block-style
    "MD048": { "style": "backtick" },  // code-fence-style

    // Whitespace
    "MD009": true,  // no-trailing-spaces
    "MD010": true,  // no-hard-tabs
    "MD012": true,  // no-multiple-blanks
    "MD030": { "ul_single": 1, "ul_multi": 1, "ol_single": 1, "ol_multi": 1 },  // list-marker-space

    // Lists
    "MD004": { "style": "dash" },  // ul-style
    "MD005": true,  // list-indent
    "MD007": { "indent": 2 },  // ul-indent
    "MD029": { "style": "ordered" },  // ol-prefix
    "MD032": true,  // blanks-around-lists

    // Links
    "MD011": true,  // no-reversed-links
    "MD034": true,  // no-bare-urls
    "MD042": true,  // no-empty-links
    "MD045": false, // no-alt-text (warning only, not error)

    // HTML
    "MD033": {
      "allowed_elements": ["details", "summary", "kbd", "br", "sub", "sup"]
    },

    // Emphasis
    "MD036": true,  // no-emphasis-as-heading
    "MD037": true,  // no-space-in-emphasis
    "MD049": { "style": "asterisk" },  // emphasis-style
    "MD050": { "style": "asterisk" }   // strong-style
  },
  "globs": [
    "**/*.md"
  ],
  "ignores": [
    "repo-lint-failure-reports/**/*.md",
    "node_modules/**",
    ".venv/**"
  ]
}
```

---

## Enforcement

### Tools

- **Primary tool:** `markdownlint-cli2` (Node.js package)
- **Configuration:** `.markdownlint-cli2.jsonc` at repository root
- **Integration:** `repo-lint check --ci` runs Markdown linting via a Markdown runner

### CI Integration

Markdown linting runs as part of `repo-lint check --ci`:

```bash
# Check all Markdown files
repo-lint check --ci

# Fix auto-fixable issues (if supported)
repo-lint fix
```

### Exit Codes

- **0** - All Markdown files pass
- **1** - Violations found (CI failure)
- **2** - Tool missing or configuration error (blocker)

---

## Auto-Fix Support

**Supported:** markdownlint-cli2 supports automatic fixing for many rules.

**Auto-fixable rules include:**

- MD009 (trailing spaces)
- MD010 (hard tabs → spaces)
- MD012 (multiple blanks → single blank)
- MD018, MD019 (heading spacing)
- MD022 (blanks around headings)
- MD030 (list marker spacing)
- MD037 (spaces in emphasis)
- MD047 (single final newline)

**Not auto-fixable (manual intervention required):**

- MD013 (line length - requires content rewording)
- MD040 (code language - requires human to determine correct language)
- MD041 (first line heading - requires structural change)

**Safe auto-fix policy:**

- Auto-fix MAY be enabled in `repo-lint fix` for deterministic, low-risk rules
- High-risk fixes (structural changes, content rewording) MUST remain check-only initially

---

## Special Cases and Edge Cases

### Long URLs

**Allowed exception:** Line length violations are acceptable when breaking a URL would break functionality.

```markdown
<!-- ✅ Acceptable even if > 120 chars -->
[Very Long Link Text](https://example.com/very/long/path/to/resource?with=many&query=parameters&that=exceed&line=length)
```

### Code Blocks with Long Lines

**Allowed exception:** Code blocks are excluded from line length checks (via `code_blocks: false` in MD013 config).

### Tables

**Allowed exception:** Tables are excluded from line length checks (via `tables: false` in MD013 config).

### Collapsible Sections

**Allowed HTML:** `<details>` and `<summary>` tags for collapsible content.

```markdown
<!-- ✅ Allowed -->
<details>
<summary>Click to expand</summary>

Content here.

</details>
```

### Migration Notes

When migrating existing Markdown files to this contract:

1. **Run linting first** to identify all violations
2. **Auto-fix safe issues** using `markdownlint-cli2 --fix`
3. **Manually fix remaining issues** (language tags, line length)
4. **Document intentional exceptions** in comments if needed

---

## References

- [markdownlint rules documentation](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)
- [markdownlint-cli2 documentation](https://github.com/DavidAnson/markdownlint-cli2)
- [CommonMark specification](https://commonmark.org/)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)

---

## Change Log

- **2026-01-08:** Initial creation (Issue #278, Phase 3.5.1)
  - Defined core ruleset
  - Set line length to 120 chars (extended from default 80)
  - Documented exclusions (failure reports)
  - Mapped rules to configuration
