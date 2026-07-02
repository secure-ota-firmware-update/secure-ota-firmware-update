# Week 3 Progress Report

**Week:** 3 — Edge Device Verification Logic
**Status:** IN PROGRESS (Days 1-3 complete)

---

## What Was Built

### Day 1 — verify_signature() Implementation

Implemented the core ECDSA signature verification function in
`edge_agent/agent.py`. Fixed a critical bug in `sign_firmware.py`
where `Prehashed` was imported from the wrong module and called
without the hash algorithm argument.

Key technical details:
- Loads `pki/public_key.pem` (the public key baked into the device)
- Reads the `.sig` file downloaded alongside the firmware binary
- Recomputes SHA-256 hash of the firmware
- Calls `public_key.verify()` with `ec.ECDSA(utils.Prehashed(hashes.SHA256()))`
- Returns True on valid signature, False on any failure
- Logs CRITICAL for every rejection path

Files changed: `edge_agent/agent.py`, `firmware/sign_firmware.py`

---

### Day 2 — Test Coverage and Full Flow Integration

Added 4 automated pytest tests for verify_signature():
- Valid signature → PASS
- Corrupted binary → REJECTED
- Forged signature → REJECTED
- Wrong key pair signature → REJECTED

Wired verify_signature() into the main agent flow:

Download → Hash check → Signature check → Anti-rollback → Install

Files changed: `tests/test_local_pipeline.py`, `edge_agent/agent.py`

---

### Day 3 — Tamper Simulation, Rejection Reports, Test Suite

Ran full tamper simulation against real GitHub Release:
- MITM attack (corrupted binary) → detected and rejected
- Supply chain attack (attacker-signed firmware) → detected and rejected

Added structured JSON rejection reports to `edge_agent/rejections/`
with UUID, timestamp, reason code, hash comparison, and action taken.

Ran complete pytest suite — 9 passed, 0 failed.

Files changed: `edge_agent/agent.py`, `docs/TAMPER_SIMULATION_RESULTS.md`,
`docs/TEST_RESULTS.md`, `docs/SIGNATURE_VERIFICATION_TEST_RESULTS.md`

---

## Security Properties Now Guaranteed

After Week 3, the edge agent guarantees these properties on every update:

**Integrity** (SHA-256)
Any modification to the firmware binary in transit is detected.
Even a single byte change produces a completely different hash.
The agent rejects and never installs tampered firmware.

**Authenticity** (ECDSA P-256)
Firmware must have been signed by the holder of the private key.
An attacker cannot produce a valid signature without the private key.
Even if an attacker signs their own malicious firmware with their own
key, the device's embedded public key rejects it.

**Non-repudiation**
Every rejection is logged with a CRITICAL alert and a structured
JSON report. The audit trail proves which firmware was rejected,
why it was rejected, and when.

---

## What is Coming in Week 4

### Anti-rollback version enforcement
Implement `anti_rollback_check()` — compare incoming firmware
version against `minimum_version` in `version_store.json`.
Reject any firmware where version < minimum, even if signature
is valid. This prevents attackers from forcing devices back to
versions with known vulnerabilities.

### Final test suite (5 attack tests)
Add `tests/test_tamper_simulation.py` with 5 comprehensive tests:
1. Valid firmware — INSTALLED
2. Corrupted binary — REJECTED (hash)
3. Wrong key signature — REJECTED (signature)
4. Rollback attempt — REJECTED (version)
5. Completely fake signature — REJECTED (signature)

### Final documentation
Complete threat model with all mitigations implemented.
Final README polish. Cryptographic algorithm final review.

---

## Current Test Coverage

| Component | Tests | Status |
|-----------|-------|--------|
| create_dummy_firmware.py | test_firmware_binary_exists | PASSING |
| sign_firmware.py | test_signature_file_exists_and_nonempty | PASSING |
| generate_manifest.py | test_manifest_has_all_required_fields, test_manifest_sha256_matches_binary | PASSING |
| generate_keys.py | test_public_key_exists | PASSING |
| verify_signature() | 4 tests covering valid + 3 attack scenarios | PASSING |
| anti_rollback_check() | Not yet tested | Week 4 |

---

## Commit Activity — Week 3 Days 1-3

All 4 members committed on each of the 3 days.
No gaps in commit graph.
All commits follow semantic format with issue references.