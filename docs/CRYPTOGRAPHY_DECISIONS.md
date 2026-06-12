# Cryptographic Algorithm Decisions

This document explains every cryptographic choice made in this project
and the reasoning behind each decision.

---

## 1. Digital Signature Algorithm — ECDSA P-256

### Why not RSA?

RSA requires much larger key sizes to achieve equivalent security.
RSA-3072 is needed to match the security level of ECDSA P-256.
On constrained IoT devices with limited flash storage and processing
power, smaller keys and faster operations matter significantly:

| Algorithm   | Key Size | Signature Size | Security Level |
|-------------|----------|----------------|----------------|
| RSA-2048    | 2048 bit | 256 bytes      | ~112 bit       |
| RSA-3072    | 3072 bit | 384 bytes      | ~128 bit       |
| ECDSA P-256 | 256 bit  | 64 bytes       | ~128 bit       |

ECDSA P-256 achieves the same 128-bit security level as RSA-3072 but
with a 6x smaller signature and 12x smaller key. For a fleet of 10,000
IoT devices each storing a public key, this difference is significant.

### Why ECDSA P-256 specifically?

P-256 (also called secp256r1 or prime256v1) is the NIST-recommended
elliptic curve standard. It is:

- Supported natively by the Python cryptography library
- Supported by AWS Key Management Service (KMS)
- Used in TLS 1.3 by default
- The standard curve in most IoT firmware verification frameworks
  including MCUboot and RAUC

ECDSA is particularly well-suited for OTA firmware updates because it provides strong authentication with minimal bandwidth and storage overhead. Since firmware signatures are distributed to every device, smaller signature sizes reduce network usage and improve update efficiency across large IoT deployments.
---

## 2. Hash Algorithm — SHA-256

### Why not MD5?

MD5 is cryptographically broken. Collision attacks have been
demonstrated practically — two different inputs can be engineered
to produce the same MD5 hash. This means an attacker could craft
malicious firmware that has the same MD5 hash as legitimate firmware,
bypassing integrity checks entirely.

### Why not SHA-1?

SHA-1 is also considered broken. In 2017, Google's Project Zero team
demonstrated SHAttered — the first practical SHA-1 collision attack.
SHA-1 is officially deprecated by NIST and must not be used for
any security-critical integrity verification.

### Why SHA-256?

SHA-256 is part of the SHA-2 family standardized by NIST. It:

- Has no known practical attacks as of 2026
- Produces a 256-bit (32-byte) digest
- Is computationally infeasible to reverse or forge
- Is the standard for firmware integrity in RAUC, SWUpdate, MCUboot
- Is natively available in Python's hashlib (no external dependency)
SHA-256 is widely adopted across security-critical systems, including TLS certificates, software package verification, blockchain technologies, and secure boot mechanisms. Its extensive industry adoption and long-term cryptographic reliability make it a safe choice for firmware integrity verification.
---

## 3. Why Both Hash Check AND Signature Verification?

The ECDSA signature mathematically covers the hash of the firmware.
So a valid signature already implies the hash is correct. Why check both?

**Reason 1 — Performance (fail fast)**

SHA-256 verification is extremely fast (microseconds).
ECDSA verification involves elliptic curve math and is slower.
By doing the hash check first, we reject obviously corrupted files
immediately without burning CPU cycles on ECDSA math.

**Reason 2 — Defense in depth**

If a bug existed in the ECDSA verification code, the hash check
provides a second independent layer of protection.

**Reason 3 — Industry standard pattern**

Real firmware update stacks (MCUboot, RAUC, SWUpdate) all implement
both checks in sequence for the same reasons.

Verification order in our agent:

1. Download .bin and .sig
2. Recompute SHA-256 of .bin → compare with manifest hash [fast check]
3. Verify ECDSA signature of hash using public key [crypto check]
4. Check version >= minimum_version [rollback check]
5. Install
Separating integrity verification from authenticity verification also improves troubleshooting and monitoring. If a hash mismatch occurs, the system can immediately identify transmission or storage corruption, while a signature failure typically indicates an authentication or key-management issue. This distinction simplifies incident response and debugging.

---

## 4. Key Storage — Why GitHub Secrets

### Why not a config file or .env file?

Storing the private key in any file in the repository — even encrypted —
creates a permanent record in git history. Even if the file is deleted
in a later commit, git history preserves it forever. Anyone who clones
the repository can recover it with:

```
git log --all -p | grep -A 30 "BEGIN EC PRIVATE KEY"
```

This is one of the most common real-world security incidents.
Thousands of private keys are exposed on GitHub every year this way.

### Why GitHub Secrets?

GitHub Secrets are:

- Stored encrypted at rest using libsodium sealed boxes
- Never printed in workflow logs (automatically masked)
- Injected only into the runtime environment of authorized workflows
- Not accessible to pull requests from forks
- Scoped to specific repositories or environments

The private key exists in memory only for the exact seconds the
signing step runs, then the /tmp file is deleted in the cleanup step.

Using GitHub Secrets aligns with the principle of least exposure by ensuring sensitive cryptographic material is never committed to source control. This reduces the attack surface and helps enforce secure key-management practices throughout the development and deployment lifecycle.

---

## 5. Production Improvements

This project uses GitHub Secrets as a practical internship-level
approach. A production system would use:

**Hardware Security Module (HSM)**

The private key would be stored in an HSM (AWS CloudHSM, YubiKey HSM,
or Thales Luna). The key physically never leaves the HSM — the signing
operation happens inside the hardware and only the signature is returned.
Even if the build server is compromised, the private key cannot be stolen.

**The Update Framework (TUF)**

TUF adds threshold signatures (multiple keys must sign), key rotation
without device updates, delegation (different keys for different device
types), and a transparent audit log.

**Sigstore / Cosign**

An emerging standard for software supply chain security. Provides
keyless signing using short-lived certificates, a transparency log
(Rekor), and integration with GitHub OIDC.

**Secure Enclave on Device**

Rather than storing the public key in a regular file, production devices
use a secure enclave (ARM TrustZone, ATECC608A crypto chip) where the
public key is fused at manufacture and cannot be overwritten over the air.
Production-grade OTA systems typically combine multiple security controls rather than relying on a single mechanism. Secure key storage, signed metadata, audit logging, hardware-backed trust anchors, and automated key rotation work together to create a resilient firmware update ecosystem that remains secure even if one layer is compromised.