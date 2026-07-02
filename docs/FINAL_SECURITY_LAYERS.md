# Final Security Architecture — Three Layer Defense

This document summarizes the complete security architecture of the
Secure OTA Firmware Update system after all three weeks of
implementation are complete.

---

## The Three Security Layers
┌─────────────────────────────────────────────────────┐
│ Firmware Downloaded │
└─────────────────────────┬───────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────┐
│ LAYER 1 — SHA-256 Hash Verification │
│ │
│ Recomputes SHA-256 of downloaded binary │
│ Compares against hash in signed manifest │
│ Detects: any byte-level modification in transit │
│ Blocks: MITM attacks (Threat 2) │
│ │
│ FAIL → CRITICAL alert, files deleted, halt │
└─────────────────────────┬───────────────────────────┘
│ PASS
▼
┌─────────────────────────────────────────────────────┐
│ LAYER 2 — ECDSA P-256 Signature Verification │
│ │
│ Verifies .sig file using public_key.pem │
│ Proves firmware was signed by legitimate dev key │
│ Detects: forged signatures, wrong key pair │
│ Blocks: Supply chain attacks (Threat 1) │
│ Key compromise (Threat 4) │
│ │
│ FAIL → CRITICAL alert, files deleted, halt │
└─────────────────────────┬───────────────────────────┘
│ PASS
▼
┌─────────────────────────────────────────────────────┐
│ LAYER 3 — Anti-Rollback Version Check │
│ │
│ Compares incoming version >= minimum_version │
│ minimum_version auto-raised after each install │
│ Detects: attempts to install older versions │
│ Blocks: Rollback attacks (Threat 3) │
│ │
│ FAIL → CRITICAL alert, rejection report, halt │
└─────────────────────────┬───────────────────────────┘
│ PASS
▼
┌─────────────────────────────────────────────────────┐
│ Firmware INSTALLED │
│ minimum_version raised to current version │
│ Install history updated in version_store.json │
└─────────────────────────────────────────────────────┘

---

## What Each Layer Protects Against

### Layer 1 — SHA-256 Hash

**Protects against:** Any modification to the firmware binary
after it was signed. Works because SHA-256 is a one-way function —
you cannot find an input that produces a given hash without
brute force, which is computationally infeasible for a 256-bit digest.

**Limitation:** Does NOT prove who created the firmware.
An attacker could create their own firmware, compute its hash,
and present it as legitimate. This is why Layer 2 is needed.

**Implementation:** `edge_agent/agent.py → verify_hash()`

---

### Layer 2 — ECDSA Signature

**Protects against:** Firmware not signed by the legitimate
developer's private key. Works because:
- The private key is stored as a GitHub Secret — never committed
- The public key is embedded in every device at manufacture
- Without the private key, no valid signature can be produced
- With a different key pair, the device's public key rejects it

**Limitation:** Does NOT prevent replay of old signed firmware.
An attacker could re-serve legitimately signed v1.0.0 to a
device that should be on v1.1.0+. This is why Layer 3 is needed.

**Implementation:** `edge_agent/agent.py → verify_signature()`

---

### Layer 3 — Anti-Rollback

**Protects against:** Installation of older firmware versions
that may contain known vulnerabilities. Works because:
- minimum_version is stored on the device
- minimum_version only moves forward, never backward
- Even legitimately signed old firmware is rejected

**Limitation:** Does NOT protect against a compromised private key.
If the private key is stolen, an attacker could sign and distribute
any firmware at any version. Key rotation (out of scope for this
project) would be needed to recover from key compromise.

**Implementation:** `edge_agent/agent.py → anti_rollback_check()`

---

## What An Attacker Would Need To Bypass All Three Layers

To successfully install malicious firmware an attacker must
simultaneously:

1. Possess the ECDSA private key (stored only as GitHub Secret,
   never committed, deleted from /tmp after each pipeline run)

2. Know the exact version number that is >= the device's
   minimum_version (or compromise the device's version_store.json
   through physical access)

3. Produce a correctly signed firmware binary with a valid
   SHA-256 hash that matches the manifest

This combination requires:
- Compromising GitHub Secrets (infrastructure-level breach)
- AND physical access to the device to modify version store
- OR key compromise + knowing the device's minimum version

For a logistics IoT fleet, this attack surface is extremely narrow
compared to an unsigned OTA system where any network attacker
can push arbitrary firmware.

---

## Security Properties Formally Stated

**Integrity**
∀ firmware f: if verify_hash(f) = TRUE then f was not modified
since it was signed, with probability 1 - 2^(-256)

**Authenticity**
∀ firmware f: if verify_signature(f) = TRUE then f was signed
by the holder of the private key corresponding to public_key.pem

**Freshness / Anti-rollback**
∀ firmware f with version v: if anti_rollback_check(v) = TRUE
then v ≥ minimum_version, ensuring no older vulnerable version
can be installed

---

## Test Coverage Summary

All three layers are independently tested:

| Layer | Function | Tests | File |
|-------|----------|-------|------|
| Hash | verify_hash() | 3 tests | test_local_pipeline.py |
| Signature | verify_signature() | 5 tests | test_local_pipeline.py |
| Anti-rollback | anti_rollback_check() | 5 tests | test_local_pipeline.py |
| Combined attacks | All three | 15 tests | test_tamper_simulation.py |

**Total: 29 tests, 0 failures**

---

## Files Implementing These Layers
Signing pipeline (CI/CD):
firmware/sign_firmware.py ← computes hash + signs with private key
firmware/generate_manifest.py ← records hash in manifest
.github/workflows/sign-and-release.yml ← automates pipeline on tag push
Edge agent (device-side):
edge_agent/agent.py
├── verify_hash() ← Layer 1
├── verify_signature() ← Layer 2
├── anti_rollback_check() ← Layer 3
├── write_rejection_report() ← audit trail
└── mock_install() ← raises minimum_version after install
Key material:
pki/public_key.pem ← embedded in device (safe to commit)
GitHub Secret: FIRMWARE_PRIVATE_KEY ← never committed, deleted after use