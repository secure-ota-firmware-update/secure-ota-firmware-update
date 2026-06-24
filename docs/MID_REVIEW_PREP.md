# Mid Review Preparation Guide

Mid Review window: 20th to 27th of Month 1
Covers: Week 1 + Week 2 implementations

---

## GitHub Requirements Check

Before the Mid Review, confirm:

- [ ] Team repository has commits on at least 10 different days
      in the last 14 days
- [ ] Each member has commits in their own branch
- [ ] All commits follow format: type: description (fixes #N)
- [ ] All GitHub Issues #1 through #48 are created
- [ ] Work Distribution Document submitted to Infotact

---

## What Was Built — Summary for Evaluator

### Week 1 — PKI Setup and Cryptographic Hashing

The team established a Public Key Infrastructure using ECDSA P-256.
A dummy firmware binary was created to simulate real IoT firmware.
A signing script computes SHA-256 hash and signs with the private key.
An edge device agent skeleton was built with hash verification.
A threat model documenting 4 attack vectors was written.

Key files to show:
- pki/generate_keys.py
- firmware/sign_firmware.py
- edge_agent/agent.py
- docs/THREAT_MODEL.md
- docs/CRYPTOGRAPHY_DECISIONS.md

### Week 2 — CI/CD Automated Code Signing

A GitHub Actions pipeline was built that triggers on a release tag push.
The private key is stored as a GitHub Secret and injected at runtime.
The pipeline signs firmware, generates a manifest, and publishes a
GitHub Release with all 3 artifacts attached.
The edge agent was updated to fetch the manifest from GitHub Releases
API and download firmware from release assets.
End-to-end flow was tested and confirmed working.

Key files to show:
- .github/workflows/sign-and-release.yml
- firmware/prepare_release_assets.py
- firmware/get_latest_release.py
- docs/CICD_PIPELINE.md
- docs/ARCHITECTURE_DECISIONS.md

---

## Demo Script — What to Run in the Review

### Demo 1 — Show the Pipeline (2 minutes)

Go to:
https://github.com/secure-ota-firmware-update/secure-ota-firmware-update/releases

Show the release with 3 artifacts attached:
- dummy_firmware_v1.0.0.bin
- dummy_firmware_v1.0.0.sig
- manifest.json

Click manifest.json and show its contents.

### Demo 3 — Run the Edge Agent Live (2 minutes)

```bash
export GITHUB_RELEASE_BASE_URL=https://github.com/secure-ota-firmware-update/secure-ota-firmware-update
python edge_agent/agent.py
```

Walk through the output:
- Manifest fetched from GitHub API
- Update available detected
- Firmware downloaded
- Hash verification PASSED
- Summary report printed

### Demo 4 — Show Commit History (1 minute)

```bash
git log --oneline main | head -20
```

Show that every commit has:
- Semantic prefix (feat/fix/docs/test/chore)
- Descriptive message
- Issue reference (fixes #N)

### Demo 5 — Show Security Audit (1 minute)

Open docs/SECURITY_AUDIT.md and walk through the 6 checks.
Show that no credentials were found anywhere in git history.

---

## Answers to Common Evaluator Questions

**Q: Why ECDSA over RSA?**
A: Same 128-bit security level with 6x smaller signatures.
   Critical for IoT devices with limited storage.
   See docs/CRYPTOGRAPHY_DECISIONS.md section 1.

**Q: Why GitHub Releases instead of S3?**
A: GitHub Releases satisfies "secure distribution server" from the spec.
   No AWS account needed. Only 1 secret required instead of 4.
   See docs/ARCHITECTURE_DECISIONS.md ADR-001.

**Q: How is the private key protected?**
A: Stored as GitHub Secret. Written to /tmp only during signing step.
   Deleted immediately after by cleanup step with if: always().
   Never committed to repository — confirmed by security audit.

**Q: What happens if the firmware is tampered?**
A: SHA-256 hash mismatch is detected. Agent logs CRITICAL alert
   and refuses to install. ECDSA signature verification added Week 3.

**Q: What is coming in Week 3?**
A: ECDSA signature verification in the edge agent.
   Agent will verify the .sig file using the public key stored on device.
   Any firmware not signed by the private key will be rejected.

---

## File Structure for Evaluator Reference
.github/workflows/sign-and-release.yml  ← pipeline

pki/generate_keys.py                    ← PKI setup

pki/public_key.pem                      ← public key on device

firmware/sign_firmware.py               ← signing script

firmware/generate_manifest.py           ← manifest generator

firmware/prepare_release_assets.py      ← pre-release verification

firmware/get_latest_release.py          ← GitHub API helper

firmware/verify_release_integrity.py    ← audit tool

edge_agent/agent.py                     ← IoT device simulation

edge_agent/version_store.json           ← version tracking

distribution/manifest.json              ← sample manifest

docs/THREAT_MODEL.md                    ← 4 threats + CVE refs

docs/CRYPTOGRAPHY_DECISIONS.md          ← algorithm reasoning

docs/CICD_PIPELINE.md                   ← pipeline architecture

docs/ARCHITECTURE_DECISIONS.md          ← ADR-001 GitHub Releases

docs/SECURITY_AUDIT.md                  ← credential audit results

docs/LOCAL_TESTING.md                   ← how to run locally

docs/MID_REVIEW_PREP.md                 ← this file

