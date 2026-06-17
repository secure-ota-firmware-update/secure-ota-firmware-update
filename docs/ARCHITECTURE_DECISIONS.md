
# Architecture Decision Records

This document records significant architectural decisions made
during the project and the reasoning behind each one.

---

## ADR-001 — Distribution: GitHub Releases instead of AWS S3

### Date
Week 2 of internship

### Status
Accepted

### Context

The project specification states that firmware artifacts must be
uploaded to a "secure distribution server or AWS S3 bucket" after
being signed by the CI/CD pipeline.

The original plan was to use AWS S3 as the distribution server.
This would require:
- An AWS account with credit/debit card for verification
- IAM user creation with scoped S3 permissions
- 3 additional GitHub Secrets (AWS_ACCESS_KEY_ID,
  AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME)
- Ongoing management of AWS credentials

### Decision

We pivoted to **GitHub Releases** as the secure distribution server.

When the pipeline runs on a release tag push:
1. Firmware binary, signature, and manifest are signed and generated
2. The `softprops/action-gh-release@v2` Action creates a GitHub Release
3. All 3 artifacts are attached as downloadable release assets

The edge agent uses the GitHub public API to discover the latest
release and downloads artifacts from the public release URLs.

### Reasons

**Satisfies the spec:**
GitHub Releases is a valid "secure distribution server" — it is:
- HTTPS-enforced (encrypted in transit)
- Served by GitHub's CDN infrastructure
- Authenticated publishing (only the pipeline can create releases)
- Publicly downloadable (no credentials needed for the edge agent)

**Simpler setup:**
- No AWS account or credit card required
- Only 1 GitHub Secret needed (FIRMWARE_PRIVATE_KEY)
- Everything stays within GitHub — no external service dependency

**Fewer credentials:**
S3 approach required 4 secrets — GitHub Releases requires 1.
Fewer secrets = smaller attack surface for key compromise (Threat 4).

**Production note:**
In a real production system, a dedicated artifact store (AWS S3,
Azure Blob, or a self-hosted distribution server) would be used for
better access control, versioning, and bandwidth management. GitHub
Releases is appropriate for this internship-scale project.

### Consequences

**Positive:**
- Simpler pipeline
- No AWS costs or account setup
- Edge agent needs no credentials to download firmware

**Negative:**
- GitHub Releases has file size limits (2GB per file — not a concern
  for firmware binaries which are typically under 100MB)
- Dependent on GitHub availability (99.99% uptime SLA)
- Public repo means anyone can download the firmware (acceptable —
  security comes from signature verification, not obscurity)

### Files changed due to this decision

| Original | New | Reason |
|---|---|---|
| `firmware/upload_to_s3.py` | `firmware/prepare_release_assets.py` | Verify assets instead of uploading to S3 |
| `firmware/upload_to_s3.py` | `firmware/get_latest_release.py` | Fetch release URLs from GitHub API |
| `docs/SECRETS_SETUP.md` | Updated | Removed 3 AWS secret entries |
| `.github/workflows/sign-and-release.yml` | Updated | Replaced S3 upload with GitHub Release action |

---

## ADR-002 — Key Algorithm: ECDSA P-256 over RSA

See `docs/CRYPTOGRAPHY_DECISIONS.md` section 1 for full reasoning.

Summary: ECDSA P-256 provides equivalent security to RSA-3072 with
6x smaller signatures — critical for constrained IoT devices.

---

## ADR-003 — Hash Algorithm: SHA-256 over MD5/SHA-1

See `docs/CRYPTOGRAPHY_DECISIONS.md` section 2 for full reasoning.

Summary: MD5 and SHA-1 are cryptographically broken. SHA-256 has
no known practical attacks and is the industry standard for firmware
integrity verification.
=======
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
