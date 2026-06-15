# Architecture Decisions

This document records significant architectural decisions made
during the project and the reasoning behind them.

---

## Decision 1 — Firmware Distribution: GitHub Releases instead of AWS S3

### Context

The project specification states firmware must be uploaded to a
"secure distribution server or AWS S3 bucket" after signing.

### Decision

Firmware artifacts (.bin, .sig, manifest.json) are distributed via
GitHub Releases instead of AWS S3.

### Reasoning

**No external account required**
AWS account creation requires a credit/debit card for verification.
GitHub Releases requires nothing beyond the existing repository.

**Fewer secrets to manage**
S3 approach required 4 secrets: FIRMWARE_PRIVATE_KEY,
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME.
GitHub Releases approach requires only 1: FIRMWARE_PRIVATE_KEY.
GITHUB_TOKEN is automatically provided by GitHub Actions —
no manual creation, no rotation needed, scoped to this repo only.

**Simpler edge agent**
S3 required either public bucket policies (security risk) or
signed URLs (added complexity). GitHub Release assets on a public
repository are directly downloadable via a predictable URL pattern
with zero authentication:

https://github.com/<owner>/<repo>/releases/download/<tag>/<filename>

**Still satisfies the specification**
GitHub Releases is a "secure distribution server" — it is served
over HTTPS, access-controlled by GitHub's infrastructure, and
provides versioned, immutable artifact storage with built-in
release notes and changelogs.

**Reduced attack surface**
No AWS IAM policies to misconfigure, no S3 bucket permission
mistakes (a common real-world breach cause), no AWS credentials
that could leak.

### What Changed

| Component | Before (S3) | After (GitHub Releases) |
|-----------|-------------|--------------------------|
| Upload script | firmware/upload_to_s3.py | firmware/prepare_release_assets.py |
| Workflow step | AWS S3 upload via boto3 | softprops/action-gh-release@v2 |
| Secrets needed | 4 | 1 |
| Agent env var | S3_BASE_URL | GITHUB_RELEASE_BASE_URL |
| Dependency | boto3 | none (uses GITHUB_TOKEN, auto-provided) |

### Trade-offs Acknowledged

- GitHub Releases has a 2GB per-file limit — not a concern for
  firmware binaries in this project (256KB test firmware)
- Less "enterprise cloud" feel than S3, but functionally equivalent
  for the security properties this project demonstrates
  (signing, hashing, verification)
- In a real production fleet with millions of devices, a CDN-backed
  S3 setup would scale better — this is noted as a "production
  improvement" alongside HSM and TUF in CRYPTOGRAPHY_DECISIONS.md