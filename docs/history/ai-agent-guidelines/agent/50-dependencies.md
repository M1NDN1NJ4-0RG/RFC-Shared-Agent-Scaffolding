# Dependency Management Policy

**Status:** Approval required before adding/updating dependencies.
**Load:** When adding dependencies or updating versions.

---

## Core Policy

**Rule:** All dependency additions and updates require explicit human approval.

**Why:**

- Dependencies increase attack surface
- Unmaintained dependencies create technical debt
- Version conflicts can break builds
- License compatibility must be verified

---

## Before Adding a Dependency

### Step 1: Justify the Need

**Ask:**

- Can this be implemented with existing dependencies or stdlib?
- Is this dependency actively maintained?
- What is the maintenance burden?
- Are there simpler alternatives?

**Document:**

- Why the dependency is needed
- What problem it solves
- Alternatives considered
- Expected maintenance burden

### Step 2: Security Scan

**MANDATORY:** Run GitHub Advisory Database check.

**Supported ecosystems:**

- npm (Node.js)
- pip (Python)
- rubygems (Ruby)
- maven (Java)
- go (Go)
- nuget (.NET)
- composer (PHP)
- cargo (Rust)

**How to scan:**

```bash
# This is done automatically by gh-advisory-database tool
# No manual commands needed - tool handles it
```

**If vulnerabilities found:**

- Document severity (critical, high, medium, low)
- Check if patched version exists
- Decide: fix first, or choose alternative dependency

### Step 3: Version Pinning

**Rule:** Always pin to specific versions in lock files.

**Examples:**

```json
// package-lock.json (npm)
{
  "lodash": "4.17.21"
}
```

```txt
# requirements.txt (pip)
requests==2.28.1
```

```
# Gemfile.lock (Ruby)
lodash (4.17.21)
```

**Why:**

- Reproducible builds
- Avoid surprise breaking changes
- Security: known-good versions

### Step 4: Request Approval

**Format:**

```markdown
**APPROVAL NEEDED: Add Dependency**

**Package:** <name>
**Version:** <version>
**Ecosystem:** <npm/pip/etc>
**Why:** <justification>
**Alternatives considered:** <list>
**Security scan:** ✅ Pass / ⚠️ Vulnerabilities found (details below)
**Maintenance:** <active/inactive, last release date>

Refs: #<issue-number>
```

**Where to post:**

- Comment on PR
- Or create new issue if not yet in PR

**Wait for:** Explicit approval (👍, "LGTM", "Approved", etc.)

---

## Dependency Categories

### Direct Dependencies

**Definition:** Dependencies directly imported/required by your code.

**Examples:**

- `import lodash` (npm)
- `import requests` (Python)
- `use JSON::PP` (Perl)

**Approval:** REQUIRED for all direct dependencies.

### Transitive Dependencies

**Definition:** Dependencies pulled in by your direct dependencies.

**Examples:**

- lodash depends on X, which depends on Y

**Approval:** Review only (no approval needed unless vulnerability found).

### Development Dependencies

**Definition:** Dependencies used only for development/testing (not in production).

**Examples:**

- Test frameworks (Pester, pytest, Jest)
- Linters (eslint, pylint, shellcheck)
- Build tools (webpack, rollup)

**Approval:** REQUIRED, but faster approval process acceptable.

---

## Updating Dependencies

### Security Updates

**Priority:** HIGH — Fix critical vulnerabilities immediately.

**Process:**

1. Identify vulnerability (GitHub Dependabot alert, advisory DB)
2. Check if patch available
3. Update to patched version
4. Run tests
5. Fast-track approval if tests pass

### Feature Updates

**Priority:** LOW — Update only when needed.

**Process:**

1. Justify why update is needed
2. Review changelog for breaking changes
3. Run tests
4. Request approval

### Major Version Updates

**Priority:** MEDIUM — Plan carefully.

**Process:**

1. Review migration guide
2. Estimate effort
3. List breaking changes
4. Create migration plan
5. Request approval BEFORE starting work

---

## Lock File Management

### When to Update Lock Files

- Adding new dependency
- Updating existing dependency
- Security patch applied

### When to Commit Lock Files

- **Always** commit lock files (`package-lock.json`, `requirements.txt`, `Gemfile.lock`, etc.)
- Lock files ensure reproducible builds
- CI and local builds use same versions

### When Lock Files Conflict

1. **STOP** — Don't attempt to resolve manually
2. Comment: `**BLOCKED — LOCK FILE CONFLICT**`
3. Request human intervention
4. Wait for instructions

---

## License Compatibility

**Check license before adding:**

- Is license compatible with project license?
- Are there restrictions (copyleft, attribution, etc.)?
- Document license in approval request

**Common licenses:**

- MIT, Apache 2.0, BSD — Generally permissive
- GPL, LGPL — Copyleft (careful with linking)
- Proprietary — May have restrictions

**When in doubt:** Request legal review.

---

## Dependency Removal

**When to remove dependencies:**

- No longer needed
- Security issues with no patch available
- Unmaintained (no updates in 2+ years)
- Replaced by better alternative

**Process:**

1. Verify dependency is truly unused
2. Remove from code
3. Remove from dependency manifest
4. Update lock files
5. Run tests
6. Request approval (lower priority than additions)

---

## Anti-patterns

❌ **Don't:** Add dependencies "just in case"
✅ **Do:** Add only when actively needed

❌ **Don't:** Use `latest` or `*` in version specs
✅ **Do:** Pin to specific versions

❌ **Don't:** Skip security scanning
✅ **Do:** Always scan before adding

❌ **Don't:** Update all dependencies at once
✅ **Do:** Update one at a time, test between

❌ **Don't:** Add dependencies without approval
✅ **Do:** Request approval first

---

## Tooling Support

### GitHub Dependabot

**Purpose:** Automated security and version updates.

**Configuration:** `.github/dependabot.yml`

**Behavior:**

- Creates PRs for security updates
- Creates PRs for version updates (if enabled)
- Automatically scans for vulnerabilities

**Human action required:** Review and approve PRs.

### GitHub Advisory Database

**Purpose:** Check dependencies for known vulnerabilities.

**Integration:** Built into approval workflow.

**Action:** Fix critical/high vulnerabilities before approval.

---

## Project-Specific Notes

### This Repository (RFC Shared Agent Scaffolding)

**Current dependencies:**

- **Bash:** `jq` (external, not managed via package manager)
- **Python 3:** Stdlib only (no external dependencies)
- **Perl:** Stdlib only (no external dependencies)
- **PowerShell:** Pester (dev dependency for tests)

**Policy:**

- Keep dependencies minimal
- Prefer stdlib over external packages
- External tools (jq, gh) documented in README

---

**Version:** 1.0
**Last Updated:** 2025-12-26
**Refs:** RFC v0.1.0 section 6.4, copilot-instructions.md
