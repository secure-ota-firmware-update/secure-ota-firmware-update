# Work Distribution Document

**Project:** Secure OTA Firmware Update & Code Signing Infrastructure
**Team:** [Your Team Name]
**Submission Date:** Day 14 (before Mid Review)

---

## Team Members and Roles

| Member | Role | Primary Responsibility |
|--------|------|------------------------|
| Member 1 (Team Lead) | Repo owner, CI/CD architect | GitHub Actions pipeline, PKI setup, repo management, PR merging |
| Member 2 | Scripting & integration lead | Key/manifest generation, S3-to-GitHub-Releases scripts, integration testing |
| Member 3 | Edge agent lead | Edge device agent, hash verification, download logic, logging |
| Member 4 | Security & docs lead | Threat model, cryptographic decisions, architecture decisions, documentation |

---

## Week 1 — PKI Setup and Cryptographic Hashing

| Day | Member 1 | Member 2 | Member 3 | Member 4 |
|-----|----------|----------|----------|----------|
| 1 | Folder structure | .gitignore | requirements.txt | THREAT_MODEL skeleton |
| 2 | create_dummy_firmware.py | Commit dummy binary | manifest_schema.json | CRYPTOGRAPHY_DECISIONS skeleton |
| 3 | generate_keys.py | Commit public_key.pem | agent.py skeleton | version_store.json + helpers |
| 4 | sign_firmware.py | generate_manifest.py | check_for_update + mock_install | THREAT_MODEL sections filled |
| 5 | LOCAL_TESTING.md | Sample manifest.json | download_firmware() | CRYPTOGRAPHY_DECISIONS filled |
| 6 | Full pipeline test | sha256 verification | verify_hash() | CVE references added |
| 7 | pki/README.md | edge_agent/README.md | distribution + tests README | Root README Week 1 summary |

## Week 2 — CI/CD Automated Code Signing

| Day | Member 1 | Member 2 | Member 3 | Member 4 |
|-----|----------|----------|----------|----------|
| 1 | Workflow skeleton | upload_to_s3.py | download_firmware() S3 support | SECRETS_SETUP.md |
| 2 | GitHub Secrets + full workflow | test_local_pipeline.py | Retry logic + error handling | CICD_PIPELINE.md |
| 3 | (pivot decision) | get_latest_release.py prep | (pivot decision) | ARCHITECTURE_DECISIONS.md |
| 4 | Pushed test tag, debugged pipeline | get_latest_release.py | Agent GitHub Releases support | Documented S3 pivot |
| 5 | End-to-end agent test | verify_release_integrity.py | Full agent test + documented output | README Week 2 summary |
| 6 | Security audit | pipeline_status.py | Logging improvements + summary | MID_REVIEW_PREP.md |
| 7 | Final integration check | WORK_DISTRIBUTION.md (this file) | Final pipeline test | Documentation polish pass |

---

## Contribution Summary

All 4 members contributed code, documentation, and testing across
both weeks. Tasks were distributed so each member:
- Wrote production code (Python scripts)
- Wrote technical documentation
- Performed testing or verification
- Committed daily to maintain GitHub activity requirements

No single member carried the workload alone. Cross-review happened
naturally through the PR process — every PR required review before
merging to personal branches and then to main.

---

## GitHub Activity Verification

Each member has an individual branch with daily commits:
- Member 1: `hardik-dev`
- Member 2: `kanishk-dev`
- Member 3: `mahendra-dev`
- Member 4: `praveen-dev`

All commits follow the format: `type: description (fixes #N)`

Total issues created and closed: 52 (as of Day 14)

---

## Declaration

This document accurately reflects the actual work distribution
across the team for Week 1 and Week 2 of the internship project.