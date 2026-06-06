# Cryptographic Algorithm Decisions

This document explains every cryptographic choice made in this project
and the reasoning behind each decision.

## 1. Digital Signature Algorithm — ECDSA P-256

### Why not RSA?
RSA is a well-established algorithm but requires much larger key sizes
to achieve equivalent security. RSA-3072 is needed to match the security
level of ECDSA P-256. On constrained IoT devices with limited flash
storage and processing power, smaller keys and faster operations matter.
ECDSA P-256 produces a 64-byte signature vs RSA-3072's 384-byte signature.

### Why ECDSA P-256 specifically?
P-256 (also called secp256r1 or prime256v1) is the NIST-recommended
elliptic curve. It is supported natively by the Python cryptography
library, AWS, and most IoT firmware verification frameworks. It provides
128-bit security level which is the current industry standard for
firmware signing as of 2026.

## 2. Hash Algorithm — SHA-256

### Why not MD5 or SHA-1?
MD5 is cryptographically broken — collision attacks have been demonstrated
and it must never be used for security purposes. SHA-1 is also considered
weak — Google demonstrated a practical collision attack (SHAttered) in 2017.
Both are unsuitable for integrity verification of security-critical files.

### Why SHA-256?
SHA-256 is part of the SHA-2 family and has no known practical attacks.
It produces a 256-bit digest that is computationally infeasible to reverse
or forge. It is the standard choice for firmware integrity verification
used in real-world systems like RAUC, SWUpdate, and MCUboot.

## 3. Why Both Hash Check AND Signature Verification?

The ECDSA signature already mathematically covers the hash — so a valid
signature implicitly means the hash is correct. However we perform the
SHA-256 check first as a fast, cheap pre-flight check before the more
computationally expensive ECDSA verification. This is the defense-in-depth
pattern and matches real firmware update stacks.

If the hash check fails: we reject immediately without touching ECDSA math.
If the hash check passes but signature fails: we catch a sophisticated
attack where an attacker computed a matching hash but could not forge
the private key signature.

## 4. Key Storage Decision

### Why GitHub Secrets and not a config file?
Storing the private key in any file — even encrypted — in the repository
creates a permanent record in git history. Even if the file is later
deleted, git history preserves it forever and anyone who clones the repo
can recover it.

GitHub Secrets are stored encrypted at rest, never appear in logs, are
injected only into the runtime environment of authorized workflows, and
are not accessible to pull requests from forks. This matches the principle
of least privilege — the private key exists in memory only for the exact
duration of the signing step.

## 5. Production Improvements

In a production system beyond this internship scope:
- Private key would be stored in an HSM (Hardware Security Module)
  such as AWS CloudHSM or a YubiKey, where the key never leaves the device
- The update framework would implement TUF (The Update Framework)
  which adds threshold signatures, key rotation, and delegation
- Sigstore (Cosign) could replace manual ECDSA scripting with a
  transparent, auditable signing infrastructure
- The device would use a secure enclave to store the public key
  preventing physical tampering attacks
