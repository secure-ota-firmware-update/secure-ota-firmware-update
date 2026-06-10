# Threat Model — Secure OTA Firmware Update System

## 1. System Overview

This system distributes firmware updates Over-The-Air (OTA) to a fleet
of simulated IoT edge devices. The pipeline cryptographically signs every
firmware binary before distribution. The edge device agent verifies the
signature and hash before installing any update.


The OTA workflow is designed around a zero-trust distribution model, where firmware authenticity is never assumed based on its source alone. Every update must successfully pass cryptographic validation checks before the installation process can begin, ensuring that only verified firmware reaches production devices.
## 2. Assets Being Protected

- Firmware binary — must not be tampered with in transit
- Private signing key — must never leave the secure signing environment
- Device update mechanism — must only install legitimate firmware
- Version state on device — must not be rolled back to vulnerable versions

Protecting these assets is critical because compromise of any single component can undermine the security of the entire update ecosystem. The signing key protects firmware authenticity, while version tracking and verification mechanisms ensure devices remain secure throughout their operational lifecycle.

## 3. Trust Boundaries

- TRUSTED: The GitHub Actions pipeline with access to GitHub Secrets
- TRUSTED: The device's local public key storage (baked in at manufacture)
- UNTRUSTED: The network between S3 and the edge device
- UNTRUSTED: The S3 bucket itself (treat as a public distribution channel)
- UNTRUSTED: Any firmware file before verification is complete

Clearly defining trust boundaries helps identify where security controls must be enforced. All data crossing from an untrusted environment into a trusted one must undergo verification to prevent unauthorized modifications, malicious payload delivery, or misuse of system resources.

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

---
Hash verification provides integrity assurance by allowing the device to independently validate the downloaded content. Even if attackers gain full visibility into network traffic, they cannot alter firmware without causing the integrity validation process to fail.
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

Rollback protection ensures that security improvements delivered in newer firmware releases cannot be bypassed by reintroducing older vulnerable versions. This control is particularly important in long-lived IoT deployments where devices may operate unattended for extended periods.

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

Protecting the signing key is the most critical security requirement in the entire update pipeline. If the private key remains secure, attackers cannot generate firmware that devices will trust, making key management a foundational defense mechanism

## 8. Assumptions

- The device manufacturer controls the private signing key
- The public key is embedded in the device at manufacture time and
  cannot be changed over the air
- The GitHub Actions environment with Secrets access is trusted
- The device's local storage for version_store.json is not tampered with

These assumptions define the security model under which the threat analysis was conducted. If any assumption becomes invalid in a real-world deployment, additional controls and compensating safeguards would be required to maintain the same security guarantees.

## 9. Out of Scope

- Physical device tampering by someone with hardware access
- Compromise of the GitHub Actions runner environment itself
- Side-channel attacks on the edge device
- Attacks on the device after a successful legitimate firmware install

While these scenarios are excluded from the current implementation, they remain important considerations for enterprise-scale deployments. Future enhancements may address some of these risks through hardware security modules, secure boot mechanisms, or advanced runtime protections.

## 10. Mitigations Implemented

| Threat | Mitigation | Implemented In |
|--------|-----------|----------------|
| Supply Chain Attack | ECDSA signature verification | Week 1 & 3 |
| MITM Attack | SHA-256 hash check | Week 1 & 3 |
| Rollback Attack | Anti-rollback version check | Week 4 |
| Key Compromise | Private key in GitHub Secrets only | Week 2 |
The implemented controls provide layered security across the OTA update process. By combining cryptographic signing, integrity verification, version enforcement, and secure key management, the system reduces the likelihood of successful firmware-based attacks and improves overall device security.