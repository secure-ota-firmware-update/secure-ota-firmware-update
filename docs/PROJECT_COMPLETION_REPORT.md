 Project Completion Report

**Project:** Secure OTA Firmware Update & Code Signing Infrastructure
**Organization:** Infotact Solutions
**Duration:** 3 weeks (Month 1 of 2-month internship)
**Team size:** 4 members

---

## Executive Summary

This project successfully designed and implemented a production-inspired
Secure Over-The-Air (OTA) Firmware Update framework for IoT devices.

The system addresses the real-world problem of supply chain security
in logistics IoT deployments — where an attacker intercepting an
unprotected firmware update can commandeer an entire fleet of devices.

The completed system provides three independent layers of security
verification that prevent firmware tampering, forgery, and rollback
attacks, with full automated testing and CI/CD pipeline integration.

---

## Problem Statement

Supply chain and logistics companies rely on fleets of IoT tracking
devices. Updating firmware on remote devices over the air presents
significant security risks:

- MITM attacks can intercept and modify firmware in transit
- Supply chain attacks can replace firmware with malicious versions
- Rollback attacks can force devices back to vulnerable old versions

This project built the infrastructure to prevent all three.

---

## Technical Architecture

### Signing Pipeline (Developer Side)
Developer pushes git tag → GitHub Actions triggered →

Private key from GitHub Secrets → SHA-256 hash computed →

ECDSA P-256 signature generated → GitHub Release published →

.bin + .sig + manifest.json distributed

### Verification Agent (Device Side)
Agent polls manifest → Update detected → Download .bin + .sig →

Layer 1: SHA-256 hash check → Layer 2: ECDSA signature check →

Layer 3: Anti-rollback version check → Install or REJECT

---

## Deliverables Completed

### Week 1 — PKI Setup and Cryptographic Hashing

| Deliverable | File | Status |
|-------------|------|--------|
| ECDSA P-256 key generation | pki/generate_keys.py | COMPLETE |
| Firmware binary simulation | firmware/create_dummy_firmware.py | COMPLETE |
| SHA-256 + ECDSA signing | firmware/sign_firmware.py | COMPLETE |
| Manifest generation | firmware/generate_manifest.py | COMPLETE |
| Edge agent skeleton | edge_agent/agent.py | COMPLETE |
| Threat model | docs/THREAT_MODEL.md | COMPLETE |
| Cryptographic decisions | docs/CRYPTOGRAPHY_DECISIONS.md | COMPLETE |

### Week 2 — CI/CD Automated Code Signing

| Deliverable | File | Status |
|-------------|------|--------|
| GitHub Actions pipeline | .github/workflows/sign-and-release.yml | COMPLETE |
| GitHub Secrets integration | Repo settings | COMPLETE |
| Secure distribution server | GitHub Releases | COMPLETE |
| Agent GitHub API integration | edge_agent/agent.py | COMPLETE |
| Pipeline architecture docs | docs/CICD_PIPELINE.md | COMPLETE |

### Week 3 — Edge Device Verification Logic

| Deliverable | File | Status |
|-------------|------|--------|
| ECDSA signature verification | edge_agent/agent.py | COMPLETE |
| Anti-rollback enforcement | edge_agent/agent.py | COMPLETE |
| JSON rejection reports | edge_agent/rejections/ | COMPLETE |
| 29-test automated suite | tests/ | COMPLETE |
| 5-class attack simulation | tests/test_tamper_simulation.py | COMPLETE |
| Live attack demo | demo_attack.py | COMPLETE |

---

## Security Properties Achieved

**Integrity**
SHA-256 verification detects any byte-level modification in transit.
Tested against: MITM attack (corrupted binary).
Result: 100% detection rate in automated tests.

**Authenticity**
ECDSA P-256 signature verification proves firmware came from the
legitimate developer. Cannot be bypassed without the private key.
Tested against: supply chain attack (attacker key pair), forged
signatures (random bytes, zero bytes, empty file, truncated).
Result: 100% detection rate in automated tests.

**Freshness / Anti-rollback**
Minimum version enforcement prevents installation of older firmware
even when legitimately signed. Minimum version auto-raises after
each install.
Tested against: rollback to older major, minor, and patch versions.
Result: 100% detection rate in automated tests.

**Auditability**
Every rejection produces a structured JSON report with UUID,
timestamp, reason code, version info, and hash comparison.
Provides a machine-readable audit trail.

---

## Test Results

| Test File | Tests | Passed | Failed |
|-----------|-------|--------|--------|
| test_local_pipeline.py | 14 | 14 | 0 |
| test_tamper_simulation.py | 15 | 15 | 0 |
| **Total** | **29** | **29** | **0** |

Attack coverage:
- Threat 1 (Supply Chain): 5 tests
- Threat 2 (MITM): 2 tests
- Threat 3 (Rollback): 4 tests
- Threat 4 (Key Compromise): 4 tests
- Baseline (valid firmware): 4 tests

---

## Cryptographic Algorithm Choices

| Purpose | Algorithm | Justification |
|---------|-----------|---------------|
| Digital signature | ECDSA P-256 | 128-bit security, 6x smaller than RSA-3072 |
| Integrity hash | SHA-256 | No known attacks, industry standard |
| Key storage | GitHub Secrets | Encrypted at rest, never logged, auto-deleted |

See docs/CRYPTOGRAPHY_DECISIONS.md for full technical reasoning.

---

## Architectural Decision: GitHub Releases vs AWS S3

Originally planned to use AWS S3 for firmware distribution.
Pivoted to GitHub Releases because:
- Satisfies "secure distribution server" per project spec
- No AWS account or credit card required
- Only 1 GitHub Secret needed instead of 4
- HTTPS enforced, authenticated publishing
- Public repo = public release assets (no auth needed for agent)

See docs/ARCHITECTURE_DECISIONS.md ADR-001 for full analysis.

---

## Comparison to Production Systems

| Feature | This Project | Production System |
|---------|-------------|-------------------|
| Key storage | GitHub Secrets | Hardware Security Module (HSM) |
| Distribution | GitHub Releases | Dedicated CDN/S3 with signed URLs |
| Anti-rollback | Software (version_store.json) | Hardware OTP registers |
| Update framework | Custom | TUF (The Update Framework) |
| Signature scheme | ECDSA P-256 | ECDSA P-256 or Ed25519 |
| Audit trail | Local JSON files | SIEM integration |

The project makes pragmatic choices appropriate for an internship
scope while demonstrating the same fundamental security principles
used in production systems like MCUboot, RAUC, and SWUpdate.

---

## Lessons Learned

**Cryptography library APIs require careful reading**
The `Prehashed` class is in `asymmetric.utils`, not in `hashes`.
This caused a bug that was only caught during end-to-end testing,
not during unit-level development. Lesson: always test the full
verification path, not just signing in isolation.

**Defense in depth requires independent layers**
The rollback attack demo proved this clearly: hash and signature
both PASS for legitimately signed old firmware — only anti-rollback
catches it. Each layer must be independent to provide real protection.

**Commit discipline reflects engineering discipline**
Maintaining daily commits with semantic messages and issue references
across 21 days mirrors real engineering workflows. Version control
history is a first-class artifact.

**Architecture decisions have real consequences**
The S3 to GitHub Releases pivot eliminated 3 secrets, simplified
the workflow, and removed an external dependency. Documenting the
reasoning in an ADR means future contributors understand why.

---

## Repository Statistics

- Total commits on main: [fill from git log --oneline main | wc -l]
- Unique commit days: [fill from git log --date=short | sort -u | wc -l]
- GitHub Issues created: [fill from GitHub]
- GitHub Issues closed: [fill from GitHub]
- Total Python files: [fill from find . -name "*.py" | wc -l]
- Total documentation files: [fill from ls docs/ | wc -l]
- Total test count: 29
- Test pass rate: 100%