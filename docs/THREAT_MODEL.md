# Threat Model — Secure OTA Firmware Update System

## 1. System Overview

This system distributes firmware updates Over-The-Air (OTA) to a fleet
of simulated IoT edge devices. The pipeline cryptographically signs every
firmware binary before distribution. The edge device agent verifies the
signature and hash before installing any update.

---

## 2. Assets Being Protected

- Firmware binary — must not be tampered with in transit
- Private signing key — must never leave the secure signing environment
- Device update mechanism — must only install legitimate firmware
- Version state on device — must not be rolled back to vulnerable versions

---

## 3. Trust Boundaries

- TRUSTED: The GitHub Actions pipeline with access to GitHub Secrets
- TRUSTED: The device's local public key storage (baked in at manufacture)
- UNTRUSTED: The network between S3 and the edge device
- UNTRUSTED: The S3 bucket itself (treat as a public distribution channel)
- UNTRUSTED: Any firmware file before verification is complete

---

## 4. Threat 1 — Supply Chain Attack

### Description

An attacker intercepts the firmware delivery process and replaces the
legitimate firmware binary with a malicious one.
Supply chain attacks are among the most significant threats to modern software distribution systems because they target the update process itself. By enforcing signature verification at the device level, trust is established through cryptographic proof rather than through the delivery channel.

### Attack Scenario

Attacker gains access to the S3 bucket or network path between S3 and
the device. They replace firmware_v1.2.0.bin with their own malicious
binary that has the same filename.

### Mitigation

Every firmware binary is signed with the developer's ECDSA private key.
The device verifies this signature using the public key baked in at
manufacture. A replaced binary will not have a valid signature and will
be rejected before installation.


### Real World References
- SolarWinds SUNBURST (2020) — attackers compromised the build pipeline
  and inserted malicious code into legitimate software updates distributed
  to 18,000 organizations including US government agencies.
- CVE-2021-44228 (Log4Shell) — malicious payloads delivered through
  legitimate-looking update mechanisms.

---

## 5. Threat 2 — Man-in-the-Middle (MITM) Attack

### Description

An attacker intercepts the firmware file in transit and modifies even
a single byte of the binary.

### Attack Scenario

Attacker sits between the device and S3, intercepts the firmware download,
and injects malicious code into the binary before it reaches the device.

### Mitigation

The device recomputes the SHA-256 hash of the downloaded binary and
compares it against the hash stored in the signed manifest. Any
modification — even one byte — produces a completely different hash
and the device rejects the payload immediately.
### Real World References
- CVE-2019-9483 — Wemo smart plugs accepted unsigned firmware updates
  allowing any attacker on the same network to push malicious firmware.
- CVE-2018-19968 — Multiple IoT devices from various manufacturers
  accepted unverified OTA updates over HTTP without any integrity check.

---

## 6. Threat 3 — Rollback Attack

### Description

An attacker forces the device to install an older firmware version that
contains known, unpatched vulnerabilities.

### Attack Scenario

A vulnerability was present in firmware v1.0.0 and patched in v1.1.0.
The attacker re-serves the legitimately signed v1.0.0 firmware to a
device currently running v1.1.0, exploiting the fact that v1.0.0 has
a valid signature.

### Mitigation

The device maintains a minimum allowed version in version_store.json.
Any incoming firmware version lower than this minimum is rejected
before installation, even if its signature is valid.

---


- CVE-2019-15126 (Kr00k) — affecting Broadcom WiFi chips. A rollback
  to vulnerable firmware version would re-expose patched devices.
- Tesla Model S (2016) — researchers demonstrated rollback attacks on
  automotive ECU firmware allowing re-exploitation of patched bugs.
### Real World References
- Uber GitHub breach (2022) — attackers found AWS credentials in a
  private GitHub repository and accessed 57 million user records.
- Twitch source code leak (2021) — internal credentials exposed through
  misconfigured repository access.
- GitHub Token Exposure — GitHub reports over 1 million secrets
  accidentally committed to public repos every year.





- CVE-2019-15126 (Kr00k) — affecting Broadcom WiFi chips. A rollback
  to vulnerable firmware version would re-expose patched devices.
- Tesla Model S (2016) — researchers demonstrated rollback attacks on
  automotive ECU firmware allowing re-exploitation of patched bugs.
### Real World References
- Uber GitHub breach (2022) — attackers found AWS credentials in a
  private GitHub repository and accessed 57 million user records.
- Twitch source code leak (2021) — internal credentials exposed through
  misconfigured repository access.
- GitHub Token Exposure — GitHub reports over 1 million secrets
  accidentally committed to public repos every year.




## 7. Threat 4 — Key Compromise

### Description

An attacker obtains the private signing key and uses it to sign
malicious firmware that will pass all device verification checks.

### Attack Scenario

A developer accidentally commits private_key.pem to the GitHub repository.
The attacker finds it in the git history, signs their own malicious
firmware, and distributes it to devices.

### Mitigation

The private key is stored exclusively as a GitHub Secret (never in any
file in the repository). The .gitignore explicitly excludes all .pem and
.key files. The signing script reads the key only from an environment
variable injected at runtime, never from a hardcoded path in code.

---

## 8. Assumptions

- The device manufacturer controls the private signing key
- The public key is embedded in the device at manufacture time and
  cannot be changed over the air
- The GitHub Actions environment with Secrets access is trusted
- The device's local storage for version_store.json is not tampered with

---

## 9. Out of Scope

- Physical device tampering by someone with hardware access
- Compromise of the GitHub Actions runner environment itself
- Side-channel attacks on the edge device
- Attacks on the device after a successful legitimate firmware install

---

## 10. Mitigations Implemented

| Threat | Mitigation | Implemented In |
|--------|-----------|----------------|
| Supply Chain Attack | ECDSA signature verification | Week 1 & 3 |
| MITM Attack | SHA-256 hash check | Week 1 & 3 |
| Rollback Attack | Anti-rollback version check | Week 4 |
| Key Compromise | Private key in GitHub Secrets only | Week 2 |

The implemented controls provide layered security across the OTA update process. By combining cryptographic signing, integrity verification, version enforcement, and secure key management, the system reduces the likelihood of successful firmware-based attacks and improves overall device security.
 Status |The implemented controls provide layered security across the OTA update process. By combining cryptographic signing, integrity verification, version enforcement, and secure key management, the system reduces the likelihood of successful firmware-based attacks and improves overall device security. Status | |--------|-----------|----------------|--------| | Supply Chain Attack | ECDSA signature verification | edge_agent/agent.py verify_signature() | ✅ COMPLETE (Week 3) | | MITM Attack | SHA-256 hash integrity check | edge_agent/agent.py verify_hash() | ✅ COMPLETE (Week 1) | | Rollback Attack | Anti-rollback version check | edge_agent/agent.py anti_rollback_check() | 🔄 Week 4 | | Key Compromise | Private key in GitHub Secrets only | .github/workflows/sign-and-release.yml | ✅ COMPLETE (Week 2) |

- OWASP IoT Top 10: https://owasp.org/www-project-internet-of-things/
- NIST SP 800-193 Platform Firmware Resilience Guidelines
- The Update Framework (TUF) specification: https://theupdateframework.io
- NIST FIPS 186-5 Digital Signature Standard (ECDSA)
- MCUboot Secure Boot documentation: https://docs.mcuboot.com
=======
The implemented controls provide layered security across the OTA update process. By combining cryptographic signing, integrity verification, version enforcement, and secure key management, the system reduces the likelihood of successful firmware-based attacks and improves overall device security.

## 11. Week 3 Verification Coverage

The following attack scenarios were tested and confirmed rejected:

| Attack Scenario | Test | Result |
|-----------------|------|--------|
| Valid firmware + valid signature | test_verify_signature_accepts_valid | PASS |
| Corrupted binary + original signature | test_verify_signature_rejects_corrupted_binary | REJECTED |
| Valid binary + completely forged signature | test_verify_signature_rejects_fake_signature | REJECTED |
| Valid binary + signature from wrong key | test_verify_signature_rejects_wrong_key | REJECTED |

See docs/SIGNATURE_VERIFICATION_TEST_RESULTS.md for full details.
See tests/test_local_pipeline.py for automated test implementation.

The system now enforces TWO independent security checks on every
firmware update — neither can be bypassed independently:

1. SHA-256 hash check — detects any byte-level modification in transit
2. ECDSA signature check — proves firmware came from the legitimate signer

An attacker would need to simultaneously:
- Possess the private key (stored only as GitHub Secret)
- Know the exact hash that was signed
to produce a firmware update that passes both checks. This is
computationally infeasible without the private key.