# Secure OTA Firmware Update & Code Signing Infrastructure

A secure Over-The-Air (OTA) firmware update system for IoT devices.
Firmware is cryptographically signed in a CI/CD pipeline and verified
on the edge device before installation.

## Problem Statement
IoT devices in logistics fleets need remote firmware updates. Without
security, an attacker can intercept the update and push malicious
firmware to the entire fleet. This system prevents that by cryptographically
signing every firmware release and verifying the signature on the device
before any installation happens.

## Tech Stack
- Python 3.11
- ECDSA P-256 — digital signatures
- SHA-256 — integrity hashing
- GitHub Actions — automated CI/CD signing pipeline
- AWS S3 — secure firmware distribution

## Project Structure
- `pki/` — key generation scripts and public key
- `firmware/` — dummy binary, signing script, manifest generator
- `edge_agent/` — simulated IoT device verification agent
- `distribution/` — S3 manifest schema
- `tests/` — tamper simulation and end-to-end tests
- `docs/` — threat model and cryptographic decisions

## Setup
pip install -r requirements.txt

## Setup

```bash
pip install -r requirements.txt
```

---

## Quick Start — Local Pipeline Test

```bash
# 1. Generate ECDSA key pair
python pki/generate_keys.py

# 2. Generate dummy firmware
python firmware/create_dummy_firmware.py --version 1.0.0

# 3. Sign the firmware
export FIRMWARE_PRIVATE_KEY_PATH=pki/private_key.pem
python firmware/sign_firmware.py --firmware firmware/dummy_firmware_v1.0.0.bin

# 4. Generate manifest
python firmware/generate_manifest.py \
    --version 1.0.0 \
    --firmware firmware/dummy_firmware_v1.0.0.bin \
    --output distribution/manifest.json

# 5. Run the edge agent
python edge_agent/agent.py
```

See `docs/LOCAL_TESTING.md` for detailed step-by-step instructions.

---

## Progress

### Week 1 — PKI Setup and Cryptographic Hashing ✅ COMPLETE

- [x] ECDSA P-256 key pair generation (pki/generate_keys.py)
- [x] Dummy firmware binary generator (firmware/create_dummy_firmware.py)
- [x] SHA-256 hashing and ECDSA signing (firmware/sign_firmware.py)
- [x] Manifest generation (firmware/generate_manifest.py)
- [x] Edge agent skeleton with hash verification (edge_agent/agent.py)
- [x] Version store for anti-rollback (edge_agent/version_store.json)
- [x] Full threat model with CVE references (docs/THREAT_MODEL.md)
- [x] Cryptographic algorithm decisions (docs/CRYPTOGRAPHY_DECISIONS.md)

### Week 2 — CI/CD Automated Code Signing ✅ COMPLETE

- [x] GitHub Actions workflow triggered on release tag push
- [x] Private key injected from GitHub Secrets at runtime
- [x] Automated firmware signing in CI/CD pipeline
- [x] Manifest generation in pipeline
- [x] GitHub Releases used as secure distribution server
- [x] Edge agent fetches manifest from GitHub Releases API
- [x] Edge agent downloads firmware from release assets
- [x] SHA-256 hash verification passing end-to-end
- [x] Full pipeline tested — v0.1.0 release confirmed green

### Week 3 — Edge Device Verification Logic — UPCOMING

- [ ] ECDSA signature verification in agent
- [ ] Download firmware from S3 URL
- [ ] Rejection logging on verification failure
- [ ] End-to-end tamper simulation tests

### Week 4 — Version Control and Rollback Mechanisms — UPCOMING

- [ ] Anti-rollback version enforcement
- [ ] Full test suite (5 tamper tests)
- [ ] Final documentation polish
- [ ] Live attack demo


## End-to-End Flow

```
Developer
    |
    | git tag v1.0.0 && git push origin v1.0.0
    v
GitHub Actions triggered automatically
    |
    | 1. Checkout repository
    | 2. Set up Python 3.11
    | 3. Install dependencies
    | 4. Write private key from GitHub Secret to /tmp (chmod 600)
    | 5. sign_firmware.py — SHA-256 hash + ECDSA sign → .sig file
    | 6. generate_manifest.py — version + hash → manifest.json
    | 7. GitHub Release created with .bin + .sig + manifest.json
    | 8. /tmp private key deleted
    v
GitHub Releases (secure distribution server)
    |
    | Edge agent polls for updates
    v
Edge Device Agent
    |
    | 1. Fetch manifest from GitHub Releases API
    | 2. Compare version — update available?
    | 3. Download .bin and .sig from release assets
    | 4. Verify SHA-256 hash ← detects any tampering
    | 5. Verify ECDSA signature ← Week 3
    | 6. Anti-rollback version check ← Week 4
    | 7. Install or REJECT with CRITICAL alert
    v
Firmware installed securely (or rejected with full audit trail)
```
---

## Security Documentation

- [Threat Model](docs/THREAT_MODEL.md)
- [Cryptographic Decisions](docs/CRYPTOGRAPHY_DECISIONS.md)
- [Local Testing Guide](docs/LOCAL_TESTING.md)

---

## Team

Infotact Internship — Cybersecurity Project 1
Secure OTA Firmware Update & Code Signing Infrastructure



## Test Status
python -m pytest tests/ -v

29 passed, 0 failed

- test_local_pipeline.py — 14 tests (pipeline + unit tests)
- test_tamper_simulation.py — 15 tests (5 attack classes)