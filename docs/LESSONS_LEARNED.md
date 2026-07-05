# Lessons Learned

This document captures technical insights, challenges encountered,
and reflections from building the Secure OTA Firmware Update system
across three weeks of the internship.

---

## 1. The Prehashed Bug — Test End-to-End, Not Just Units

### What happened
During Week 3 Day 1, when implementing `verify_signature()`, we
discovered that `sign_firmware.py` from Week 1 had a latent bug.
`Prehashed` was being imported from `cryptography.hazmat.primitives.hashes`
but it actually lives in `cryptography.hazmat.primitives.asymmetric.utils`.
Additionally, `Prehashed()` was called without specifying the hash
algorithm — `Prehashed(hashes.SHA256())` is required.

The bug caused this error:
AttributeError: module 'cryptography.hazmat.primitives.hashes'
has no attribute 'Prehashed'

### Why it wasn't caught earlier
The signing script produced a `.sig` file without error because
the bug was in how the ECDSA algorithm was configured, not in
the signing call itself. The signing operation appeared to succeed.
It only failed when we tried to verify the signature on the other end.

### Lesson
Always test the full round-trip — sign AND verify — not just the
signing step in isolation. A signing script that produces output
without crashing does not mean the output is cryptographically
valid. This is a general principle: security controls must be
tested against the operations they are designed to enable.

### Fix applied
Corrected both `sign_firmware.py` and `verify_signature()`:
```python
# Before (wrong)
ec.ECDSA(hashes.Prehashed())

# After (correct)
from cryptography.hazmat.primitives.asymmetric import utils
ec.ECDSA(utils.Prehashed(hashes.SHA256()))
```

---

## 2. String vs Integer Version Comparison

### What happened
When designing `anti_rollback_check()`, the initial approach
was to compare version strings directly:
```python
incoming_version >= minimum_version  # string comparison — WRONG
```

### Why this is dangerous
Python's string comparison is lexicographic (dictionary order):
```python
"1.10.0" < "1.9.0"  # True — WRONG
"1.2.0"  > "1.10.0" # True — WRONG
```

This means a device on minimum version `1.9.0` would accept
firmware version `1.10.0` correctly, but would also incorrectly
reject it if the string comparison evaluated to less-than first.
Worse, an attacker could potentially craft version strings that
exploit this ordering.

### Lesson
Version numbers look like strings but must be treated as
structured integers. The correct approach is always:
```python
tuple(int(x) for x in version.split("."))
```

This is a well-documented pitfall in software version handling.
Always use semver-aware comparison logic, not raw string comparison.

### Fix applied
`anti_rollback_check()` converts all version strings to integer
tuples before comparison. Test `test_anti_rollback_integer_comparison_correctness`
was added specifically to catch any regression to string comparison.

---

## 3. Defense in Depth Is Not Redundancy

### The insight
Before building the anti-rollback check, there was a discussion
about whether it was necessary. The reasoning was: if ECDSA
signature verification already proves the firmware is legitimate,
why do we need to check the version too?

The answer is demonstrated by Demo 3 in `demo_attack.py`:

A legitimately signed old firmware (v0.9.0) passes:
- SHA-256 hash check: PASS (binary unchanged)
- ECDSA signature check: PASS (was signed with real private key)
- Anti-rollback check: FAIL (v0.9.0 < v1.0.0 minimum)

Without Layer 3, an attacker who possesses any old legitimately
signed firmware can downgrade devices to vulnerable versions.
The ECDSA signature check does not protect against this at all.

### Lesson
Each security layer protects against a different threat vector.
Removing any one layer does not just reduce security proportionally
— it completely removes protection against the specific attack
that layer was designed to catch. Defense in depth means independent
layers, each covering threats the others cannot.

---

## 4. The S3 to GitHub Releases Pivot

### What happened
The original pipeline design used AWS S3 as the firmware distribution
server. This required creating an AWS account, IAM user, bucket policy,
and 3 additional GitHub Secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
S3_BUCKET_NAME).

When it became clear that AWS requires a credit card for account
verification, we pivoted to GitHub Releases as the distribution server.

### Why GitHub Releases works
The project specification says "a secure distribution server or AWS
S3 bucket." GitHub Releases qualifies as a secure distribution server:
- Files are served over HTTPS
- Only authorized pipelines can publish releases
- Public repositories mean release assets are downloadable without auth
- No additional accounts or credentials required

### Lesson
Constraints drive good architecture decisions. The pivot to GitHub
Releases reduced the number of secrets from 4 to 1, eliminated an
external service dependency, and simplified the pipeline while still
satisfying the security requirements. This is a useful principle:
when facing a constraint, look for solutions that simplify rather
than work around.

The decision was documented in `docs/ARCHITECTURE_DECISIONS.md` ADR-001
so future contributors understand why GitHub Releases was chosen over S3.

---

## 5. Commit Discipline as an Engineering Practice

### The challenge
Maintaining daily commits with meaningful messages across 21 days,
across 4 team members, while also building real functionality, is
harder than it sounds. Several challenges emerged:

- Commit messages like "update", "fix stuff", "changes" are useless
- Committing too much at once loses the granular history
- Team members forgetting to commit on a given day creates gaps
- Merge commits without proper message formatting muddy the history

### What worked
The approach of creating GitHub Issues before writing code — then
referencing issues in commit messages — created a natural workflow:
1. Create issue describing the task
2. Write the code
3. Commit with `(fixes #N)` — which automatically closes the issue

This made commit messages meaningful without extra effort, because
the issue number links to a description of what was being built.

### Lesson
Treat the commit history as a deliverable, not a side effect.
The Infotact evaluation explicitly grades GitHub Commit Discipline
at 30% of the score — the same weight as Implementation Completion.
This reflects real engineering reality: a codebase with a clean,
traceable history is significantly more maintainable than one without.

---

## 6. The Value of Documenting Architecture Decisions

### Observation
The project generated several important decisions:
- ECDSA over RSA
- SHA-256 over MD5/SHA-1
- GitHub Releases over S3
- Integer comparison for version numbers
- Prehashed approach for ECDSA signing

Without documenting these, a future contributor (or evaluator)
would see the result but not understand the reasoning. They might
change ECDSA to RSA thinking it's equivalent, or use string
comparison for versions thinking it's simpler.

### Lesson
Architecture decisions should be documented at the time they are
made, not reconstructed afterward. The Architecture Decision Record
(ADR) format used in `docs/ARCHITECTURE_DECISIONS.md` captures:
- Context (what was the situation)
- Decision (what was chosen)
- Reasons (why)
- Consequences (what changed as a result)

This format was adapted from Michael Nygard's ADR template, widely
used in enterprise engineering teams.

---

## 7. What We Would Do Differently in Production

**Replace GitHub Secrets with an HSM**
The private key in GitHub Secrets is protected by GitHub's
infrastructure, but it's still a software secret. A hardware
security module would make the key physically non-extractable.

**Use TUF (The Update Framework)**
TUF provides key rotation, threshold signatures (multiple people
must sign), delegation, and a transparency log. Building on TUF
from the start rather than a custom signing pipeline would give
these properties without reinventing them.

**Hardware-enforced anti-rollback**
The version_store.json can theoretically be modified by someone
with physical device access. Real devices use OTP (One-Time
Programmable) registers that store the minimum version in hardware
that cannot be overwritten by software.

**SIEM integration for rejection reports**
The JSON rejection reports currently go to a local directory.
In production, these would be forwarded to a SIEM (Security
Information and Event Management) system for real-time alerting
and fleet-wide threat visibility.

**Ed25519 as an alternative to ECDSA P-256**
Ed25519 is increasingly preferred over ECDSA P-256 because it
has no parameter choices that could be misconfigured, faster
signature operations, and deterministic (not randomized) signing
which eliminates the risk of nonce reuse vulnerabilities.

---

## Summary

| Lesson | Key Takeaway |
|--------|-------------|
| Prehashed bug | Test the full round-trip, not just signing |
| Version comparison | Numbers that look like strings must be parsed as integers |
| Defense in depth | Each layer covers threats the others cannot |
| S3 pivot | Constraints drive good architecture decisions |
| Commit discipline | Commit history is a first-class deliverable |
| ADRs | Document decisions at the time they are made |
| Production gap | Software solutions exist for hardware-level problems |