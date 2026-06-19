# Documentation Index

This folder contains all technical and process documentation
for the Secure OTA Firmware Update project.

---

## Security Documentation

| File | Description |
|------|-------------|
| [THREAT_MODEL.md](THREAT_MODEL.md) | Four core threats, attack scenarios, mitigations, CVE references |
| [CRYPTOGRAPHY_DECISIONS.md](CRYPTOGRAPHY_DECISIONS.md) | Why ECDSA P-256, why SHA-256, key storage reasoning |
| [SECURITY_AUDIT.md](SECURITY_AUDIT.md) | Git history audit confirming no leaked credentials |
| [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) | ADRs including the GitHub Releases pivot from AWS S3 |

## Operational Documentation

| File | Description |
|------|-------------|
| [LOCAL_TESTING.md](LOCAL_TESTING.md) | Step by step guide to run the pipeline locally |
| [SECRETS_SETUP.md](SECRETS_SETUP.md) | How to configure GitHub Secrets |
| [CICD_PIPELINE.md](CICD_PIPELINE.md) | Full pipeline architecture walkthrough |

## Review Documentation

| File | Description |
|------|-------------|
| [WORK_DISTRIBUTION.md](WORK_DISTRIBUTION.md) | Official work distribution document |
| [MID_REVIEW_PREP.md](MID_REVIEW_PREP.md) | Demo script and Q&A prep for Mid Review |
| [WEEK2_COMPLETION_REPORT.md](WEEK2_COMPLETION_REPORT.md) | Week 2 final status report |
| [FINAL_WEEK2_TEST.md](FINAL_WEEK2_TEST.md) | Final end-to-end test results |

---

## Reading Order for New Reviewers

If you are evaluating this project for the first time, read in this order:

1. Root [README.md](../README.md) — project overview and quick start
2. [THREAT_MODEL.md](THREAT_MODEL.md) — what problems this solves
3. [CRYPTOGRAPHY_DECISIONS.md](CRYPTOGRAPHY_DECISIONS.md) — why these algorithms
4. [CICD_PIPELINE.md](CICD_PIPELINE.md) — how the pipeline works
5. [FINAL_WEEK2_TEST.md](FINAL_WEEK2_TEST.md) — proof it all works together