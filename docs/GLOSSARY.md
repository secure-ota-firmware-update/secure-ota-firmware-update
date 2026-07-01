# Glossary of Terms

All cryptographic and security terms used in this project,
explained in plain English.

---

## A

**Anti-rollback protection**
A mechanism that prevents a device from installing an older firmware
version even if that older version has a valid cryptographic signature.
Implemented via a minimum_version field in version_store.json that
only moves forward, never backward.

**Asymmetric cryptography**
A cryptographic system using two mathematically linked keys — a public
key (safe to share) and a private key (kept secret). What is signed with
the private key can be verified with the public key, but the private key
cannot be derived from the public key. Used in this project for ECDSA
firmware signing.

**Attack surface**
The set of different points where an attacker could try to enter or
extract data from a system. This project reduces the attack surface by
minimizing the number of secrets (1 GitHub Secret vs 4 for S3) and
ensuring the private key only exists in memory during signing.

---

## B

**Binary**
A file containing raw machine code bytes — the compiled firmware that
runs on an IoT device. In this project, `dummy_firmware_v1.0.0.bin`
simulates a real firmware binary.

---

## C

**CI/CD**
Continuous Integration / Continuous Deployment. An automated software
delivery pipeline. In this project, GitHub Actions automatically signs
firmware and publishes it whenever a release tag is pushed — no manual
steps required.

**CRITICAL (log level)**
The highest severity log level in the agent. Used exclusively for
security events — hash mismatches, signature failures, and rollback
attempts. Every CRITICAL log in this project indicates a potential
attack was detected and blocked.

**Cryptographic hash**
A one-way mathematical function that maps any input to a fixed-size
output (digest). The same input always produces the same output, but
you cannot reverse the process to find the input from the output.
A single changed bit in the input produces a completely different hash.

---

## D

**Defense in depth**
A security strategy using multiple independent layers of protection.
If one layer fails, others still provide protection. This project uses
three independent layers: SHA-256 hash, ECDSA signature, anti-rollback.

**DER (Distinguished Encoding Rules)**
A binary encoding format for cryptographic data. ECDSA signatures in
this project are DER-encoded byte sequences.

**Digest**
The output of a hash function. The SHA-256 digest of a file is a
64-character hexadecimal string that uniquely identifies the file
contents (with extremely high probability).

---

## E

**ECDSA (Elliptic Curve Digital Signature Algorithm)**
A digital signature algorithm based on elliptic curve mathematics.
Provides the same security as RSA but with much smaller keys and
signatures. This project uses the P-256 curve (SECP256R1).

**Edge device**
A computing device at the physical edge of a network — close to where
data is generated. IoT tracking devices on cargo trucks are edge devices.
The edge_agent in this project simulates a firmware update client on
such a device.

**Elliptic curve**
A mathematical structure defined by an equation of the form
y² = x³ + ax + b. Points on this curve form a group under a geometric
addition operation. The difficulty of the elliptic curve discrete
logarithm problem is the security basis of ECDSA.

---

## F

**Firmware**
Low-level software embedded in a hardware device that controls its
basic functions. Unlike regular software, firmware is tightly coupled
to the hardware it runs on. Updating it remotely (OTA) introduces the
security risks this project addresses.

**Forged signature**
A signature file created without access to the legitimate private key.
An attacker cannot produce a valid ECDSA signature without the private
key — any attempt at forgery is detected by verify_signature().

---

## G

**GitHub Actions**
GitHub's built-in CI/CD platform. Workflows are defined in YAML files
and triggered by events like tag pushes. The sign-and-release.yml
workflow in this project triggers on tags matching v*.*.*.

**GitHub Releases**
A GitHub feature that attaches downloadable files (assets) to tagged
repository versions. Used in this project as the secure firmware
distribution server. Assets are served over HTTPS and can only be
published by authorized workflow runs.

**GitHub Secrets**
Encrypted environment variables stored in GitHub repository settings.
They are never visible in logs and are only injected into authorized
workflow runs. The FIRMWARE_PRIVATE_KEY secret is stored here — the
single most security-critical value in the entire system.

---

## H

**Hash collision**
Two different inputs that produce the same hash output. SHA-256 was
chosen because no practical collision attacks exist against it.
MD5 and SHA-1 were rejected because collisions have been demonstrated.

**HSM (Hardware Security Module)**
A dedicated hardware device for securely storing cryptographic keys.
The key physically never leaves the HSM — signing operations happen
inside the hardware. A production version of this project would use
an HSM instead of GitHub Secrets.

---

## I

**Integrity**
The property that data has not been modified. SHA-256 verification
provides integrity assurance — if the hash matches, the firmware was
not altered since it was signed.

**IoT (Internet of Things)**
A network of physical objects (things) embedded with sensors,
software, and connectivity. Logistics tracking devices, smart meters,
and industrial sensors are all IoT devices.

---

## K

**Key compromise**
When a private key is obtained by an unauthorized party. This is
Threat 4 in the threat model. Mitigated by storing the private key
exclusively as a GitHub Secret and never committing it to git.

**Key pair**
The combination of a private key and its mathematically linked public
key in asymmetric cryptography. In this project, generated by
pki/generate_keys.py using the cryptography Python library.

---

## M

**Manifest**
A metadata file (manifest.json) distributed alongside firmware that
contains the version number, filename, SHA-256 hash, and minimum
version. The edge agent reads this to decide whether to update and
to verify the download's integrity.

**MITM (Man-in-the-Middle)**
An attack where an adversary secretly intercepts and potentially
modifies communications between two parties. In OTA firmware updates,
a MITM attacker could intercept the download and inject malicious code.
Mitigated by SHA-256 integrity verification (Layer 1).

---

## N

**Non-repudiation**
The property that the signer of a message cannot deny having signed it.
ECDSA provides non-repudiation — if a signature verifies against a
public key, it was definitely made by the corresponding private key holder.

**NIST (National Institute of Standards and Technology)**
A US government agency that produces cryptographic standards. ECDSA
P-256, SHA-256, and the recommendations used in this project are all
NIST-standardized.

---

## O

**OTA (Over-The-Air)**
Wireless delivery of software updates to remote devices, without
physical access. The entire problem this project solves — making OTA
firmware updates secure.

---

## P

**P-256 (also secp256r1, prime256v1)**
A specific elliptic curve standardized by NIST. The numbers 256 refer
to the key size in bits. P-256 provides 128-bit security — meaning an
attacker would need to perform approximately 2^128 operations to break
it, which is computationally infeasible.

**PEM (Privacy Enhanced Mail)**
A Base64 encoded format for cryptographic keys and certificates. The
public_key.pem file in this project is in PEM format. Private keys in
PEM format start with "-----BEGIN EC PRIVATE KEY-----".

**PKI (Public Key Infrastructure)**
The set of roles, policies, and procedures needed to create, manage,
and use digital certificates and public-key encryption. In this project,
PKI setup (Week 1) means generating the ECDSA key pair.

**Prehashed**
In ECDSA, signing can be done on raw data (the library hashes it
internally) or on a pre-computed hash. This project uses Prehashed
because sign_firmware.py computes the SHA-256 first (for including
in the manifest), then passes that digest directly to the signer.

---

## R

**Rejection report**
A structured JSON document written to edge_agent/rejections/ when
firmware verification fails. Contains a UUID, timestamp, reason code,
firmware details, and the action taken. Provides an audit trail.

**Replay attack**
Reusing a previously captured valid message or artifact in a new
context. In OTA updates, serving an old legitimately signed firmware
to a device is a form of replay/rollback attack.

**RSA**
An older asymmetric cryptographic algorithm. Requires much larger key
sizes than ECDSA for equivalent security. RSA-3072 provides 128-bit
security, the same as ECDSA P-256, but with 12x larger keys.

---

## S

**Semantic versioning (SemVer)**
A versioning system using MAJOR.MINOR.PATCH format. MAJOR changes
are breaking changes, MINOR adds features, PATCH fixes bugs. This
project uses SemVer for firmware versions.

**SHA-256**
Secure Hash Algorithm 256-bit, part of the SHA-2 family. Produces
a 256-bit (64 hex character) digest. No known practical attacks.
Used in this project to verify firmware binary integrity.

**Signature**
A mathematical proof created with a private key that can be verified
with the corresponding public key. If the signature verifies, the
message was signed by the private key holder and has not been modified.

**Supply chain attack**
An attack targeting the software or hardware supply chain rather than
the end system directly. In OTA firmware, compromising the firmware
distribution pipeline to push malicious firmware is a supply chain
attack. Mitigated by ECDSA signature verification (Layer 2).

---

## T

**TUF (The Update Framework)**
An industry-standard framework for securing software update systems.
Provides key rotation, threshold signatures, delegation, and a
transparency log. A production version of this project would implement
TUF on top of the cryptographic foundation built here.

**Tamper-evident**
A property of a system where any unauthorized modification can be
detected. The SHA-256 + ECDSA combination makes firmware delivery
tamper-evident — any change to the binary is detectable.

**Threat model**
A structured analysis of potential attacks against a system. This
project's THREAT_MODEL.md documents 4 threats, their attack scenarios,
real-world CVE references, and the mitigations implemented.

---

## V

**Version store**
The local file (edge_agent/version_store.json) on the IoT device that
tracks the current firmware version and the minimum allowed version.
Updated after every successful install. Central to anti-rollback protection.

---

## Z

**Zero-trust**
A security model that assumes no implicit trust — every request must
be verified regardless of where it originates. This project implements
zero-trust device management: every firmware update is verified
cryptographically before installation, regardless of the source.