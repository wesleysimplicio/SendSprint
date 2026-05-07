# ADR-005: Security findings are flag-only — never auto-fixed

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-04-05 |
| Deciders | wesley@beyondlabs |
| Supersedes | — |

---

## Context

Step 6 of the SendSprint flow runs `SecurityReviewer.scan()`, which detects:

- **Secret patterns** (12 regexes: AWS keys, GCP keys, JWT, private RSA, GitHub PAT, Stripe live key, …)
- **Dependency audits** (`npm audit`, `pip-audit`, `cargo audit`, `dotnet list package --vulnerable`).
- **Permission misconfigs** (`chmod 0777`, `S3 PublicAccessBlock=false` in IaC).
- **Insecure crypto patterns** (`md5`, `sha1` for password hashing, `random.random()` for tokens).

A naïve "auto-fix" temptation exists: replace `md5` → `sha256`, redact secrets, pin vulnerable deps to safe versions. But these "fixes" are **dangerous in practice**.

---

## Decision

`SecurityReviewer` is a **read-only step**. When a finding is detected:

1. **Halt the run** for that repo (do NOT proceed to step 7 fix loop, push, or PR).
2. **Report the finding** in `RunReport.steps[5]` with file path, line number, pattern matched, and remediation hint.
3. **Mark `RunReport.failed = true`** for the repo.
4. **Never modify any file** as part of remediation.
5. **Do NOT generate** a "fix it" PR or comment — the user must address it manually.

```python
class SecurityReviewer:
    def scan(self, repo: Path) -> list[SecurityFinding]:
        findings: list[SecurityFinding] = []
        findings.extend(self._scan_secrets(repo))
        findings.extend(self._scan_dependencies(repo))
        findings.extend(self._scan_permissions(repo))
        findings.extend(self._scan_crypto(repo))
        # Never modify files. Never auto-pin. Never auto-redact.
        return findings
```

---

## Consequences

### Positive
- **No accidental shipping** of fake-fixed secrets (e.g., redacted token committed to git history is still leaked in the previous commit — irreversible).
- **No false-confidence**: a `md5 → sha256` change without rotating existing hashes is worse than the original (creates the illusion of a fix).
- **Human in the loop**: security findings always reach a person who can decide rotate-vs-revoke-vs-accept.
- **Clean audit trail**: `RunReport` shows exactly what was found and that nothing was changed.

### Negative
- **Slower remediation**: user must manually fix and re-run. Cannot batch-resolve trivial findings.
- **Visible failure**: a single secret finding fails the entire repo's run. Acceptable: secrets ARE always blocking.
- **No "ignore" mechanism in v0.2.x**: future ADR may add `.sendsprint-allowlist` for accepted false positives.

---

## Real incidents this prevents

| Incident pattern | What flag-only avoids |
|------------------|----------------------|
| Auto-redacted secret committed | The original commit still leaks; redaction creates false comfort |
| Auto-pinned vulnerable dep | Pinned version may break unrelated functionality with no test coverage |
| Auto-rewrote `md5` to `sha256` for password hash | Existing hashed passwords now invalid; users locked out |
| Auto-removed `chmod 0777` | The reason for permissive mode is sometimes deployment-correct (rare); silent fix breaks deploy |
| Auto-replaced `random.random()` with `secrets.token_hex` | Token format changed without migration; downstream parsers break |

In every case, the "fix" looked correct in isolation but caused a worse downstream incident than the original finding.

---

## Alternatives considered

| Approach | Rejected because |
|----------|------------------|
| Auto-fix with PR-only output (no merge) | Users will merge without review; same risk as direct push |
| Auto-fix gated by allowlist | Allowlist becomes stale; defeats the purpose |
| Auto-fix only "trivial" findings | "Trivial" is subjective — every example above looked trivial in isolation |
| Skip security entirely | Defeats the value of a delivery pipeline |

---

## See also

- [DESIGN.md](DESIGN.md) — failure model
- [/.specs/product/DOMAIN.md](../product/DOMAIN.md) — invariant 5
- [/AGENTS.md](../../AGENTS.md)
