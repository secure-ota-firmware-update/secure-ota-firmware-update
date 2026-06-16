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
