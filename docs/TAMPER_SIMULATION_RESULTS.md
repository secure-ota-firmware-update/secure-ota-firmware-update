# Tamper Simulation Results

**Date:** Week 3 Day 3
**Tester:** Member 1
**Purpose:** Prove the edge agent correctly detects and rejects
             firmware that has been tampered with or forged.

---

## Simulation 1 — Normal Flow (Baseline)

**Scenario:** Legitimate firmware downloaded from GitHub Release,
valid signature, correct SHA-256 hash.

**Steps:**
1. Reset version store to 0.0.0
2. Set GITHUB_RELEASE_BASE_URL
3. Run python edge_agent/agent.py

**Result:**
Hash verification PASSED

Signature verification PASSED

Outcome: INSTALLED

**Conclusion:** Normal update flow works correctly end to end.

---

## Simulation 2 — MITM Attack (Corrupted Binary)

**Scenario:** Attacker intercepts the downloaded firmware binary
and modifies bytes 100-103 from original to 0xDEADC0DE.

**Steps:**
1. Downloaded firmware corrupted at byte offset 100
2. Agent run with corrupted local file
3. Hash verification run against corrupted binary

**Result:**
[CRITICAL] Hash verification FAILED — tampering detected

[CRITICAL] Expected: <original hash>

[CRITICAL] Computed: <hash of corrupted file>

**Conclusion:** SHA-256 hash detects even 4-byte modification.
Matches THREAT_MODEL.md Threat 2 mitigation.

---

## Simulation 3 — Supply Chain Attack (Attacker Signed Firmware)

**Scenario:** Attacker generates their own ECDSA key pair and
signs the legitimate firmware with their private key. They replace
the legitimate .sig file with their own signature.

**Steps:**
1. Generated attacker ECDSA P-256 key pair
2. Signed firmware with attacker private key
3. Replaced downloaded .sig with attacker signature
4. Ran signature verification with original public_key.pem

**Result:**
[CRITICAL] Signature verification FAILED — forged or corrupted signature

[CRITICAL] This firmware was NOT signed by the legitimate private key

**Conclusion:** Public key on device rejects signature from any
key other than the legitimate private key. Matches THREAT_MODEL.md
Threat 1 mitigation.

---

## Summary

| Attack | Detected | Response |
|--------|----------|----------|
| No attack (baseline) | N/A | INSTALLED successfully |
| MITM — corrupted binary | YES | Hash mismatch logged, install refused |
| Supply chain — wrong key sig | YES | Sig invalid logged, install refused |

Both attack vectors are fully mitigated by the two-layer
verification system:
Layer 1 — SHA-256 hash (detects modification)
Layer 2 — ECDSA signature (proves authenticity)