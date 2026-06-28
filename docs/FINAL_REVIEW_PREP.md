# Final Review Preparation Guide

Final Review window: 5th to 10th of Month 2
Covers: Week 3 + Week 4 implementations

---

## GitHub Requirements — Final Check

Before the Final Review confirm ALL of these:

- [ ] Team repo has commits on every single day for the last 20 days
      (no gaps allowed — even one missing day fails the requirement)
- [ ] Each member has commits in their own branch
- [ ] All commits follow format: type: description (fixes #N)
- [ ] All GitHub Issues created and closed
- [ ] main branch has all work merged

---

## What Was Built — Complete Summary

### Week 1 — PKI Setup and Cryptographic Hashing
- ECDSA P-256 key pair generation (pki/generate_keys.py)
- Dummy firmware binary with version header (firmware/create_dummy_firmware.py)
- SHA-256 hash + ECDSA signing (firmware/sign_firmware.py)
- Manifest generation (firmware/generate_manifest.py)
- Edge agent skeleton with hash verification (edge_agent/agent.py)
- Threat model with 4 threats and CVE references (docs/THREAT_MODEL.md)

### Week 2 — CI/CD Automated Code Signing
- GitHub Actions pipeline on release tag push
- Private key injected from GitHub Secrets — deleted after signing
- Manifest and signature uploaded to GitHub Releases
- Edge agent fetches manifest from GitHub API
- SHA-256 hash verification end-to-end confirmed

### Week 3 — Edge Device Verification Logic
- verify_signature() — ECDSA P-256 verification against public key
- anti_rollback_check() — semantic version comparison
- mock_install() — raises minimum_version after each install
- write_rejection_report() — structured JSON audit trail
- 29 automated tests — 0 failures
- 5-class attack simulation test suite
- demo_attack.py — live attack demo

---

## Final Review Demo — Exact Commands to Run

### Step 1 — Show test suite passing (2 minutes)

```bash
python run_all_tests.py
```

Walk through the output:
- 14 tests in test_local_pipeline.py
- 15 tests in test_tamper_simulation.py
- All 29 pass, 0 fail
- Point out the 5 attack classes

---

### Step 2 — Run live attack demo (3 minutes)

```bash
python demo_attack.py
```

Walk through each demo:

Demo 0 — Legitimate firmware installs successfully
Demo 1 — MITM attack: 4 bytes corrupted, hash mismatch caught
Demo 2 — Supply chain: attacker key rejected by embedded public key
Demo 3 — Rollback: v0.9.0 rejected when minimum is v1.0.0

Key talking point for Demo 3:
"Notice that hash and signature BOTH pass for the old firmware —
it was legitimately signed. But anti-rollback catches it independently.
This shows the three layers are independent security controls."

---

### Step 3 — Show GitHub Release and pipeline (2 minutes)

Go to:
https://github.com/secure-ota-firmware-update/secure-ota-firmware-update/releases

Show the release with 3 artifacts attached.

Go to:
https://github.com/secure-ota-firmware-update/secure-ota-firmware-update/actions

Show green pipeline run. Walk through each step briefly.

---

### Step 4 — Run edge agent live against GitHub Release (2 minutes)

Reset version store first:

```bash
python -c "
import json
data = {
    'current_version': '0.0.0',
    'minimum_version': '0.0.0',
    'last_updated': '2026-06-21T00:00:00Z',
    'install_history': []
}
with open('edge_agent/version_store.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Version store reset')
"
```

Run agent:

```bash
export GITHUB_RELEASE_BASE_URL=https://github.com/secure-ota-firmware-update/secure-ota-firmware-update
python edge_agent/agent.py
```

Walk through output:
- Manifest fetched from GitHub API
- Update detected
- Firmware downloaded
- Hash verified
- Signature verified
- Anti-rollback passed
- INSTALLED

---

### Step 5 — Show commit history (1 minute)

```bash
git log --oneline main | head -20
```

Point out:
- Every commit has semantic prefix
- Every commit references an issue number
- Commits span all days

---

### Step 6 — Show security audit (1 minute)

Open docs/SECURITY_AUDIT.md and walk through the 6 checks.
Then run live:

```bash
git ls-tree -r --name-only HEAD | grep "\.pem"
```

Should only show `pki/public_key.pem`.

```bash
git log --all -p | grep -c "BEGIN EC PRIVATE KEY"
```

Should return 0.

---

## Answers to Expected Evaluator Questions

**Q: Why ECDSA over RSA?**
Same 128-bit security with 6x smaller signature.
Critical for IoT devices with limited storage.
P-256 is NIST recommended and industry standard.
See docs/CRYPTOGRAPHY_DECISIONS.md section 1.

**Q: Why both hash check AND signature check?**
Two independent layers — defense in depth.
Hash is fast (microseconds) — fails early on corruption.
Signature is slower — proves authenticity.
If hash passes but signature fails, a sophisticated attack
is detected (valid binary, forged signature).
See docs/CRYPTOGRAPHY_DECISIONS.md section 3.

**Q: Why GitHub Releases instead of S3?**
GitHub Releases satisfies "secure distribution server" from spec.
No AWS account needed. Only 1 secret required.
HTTPS enforced. Only authorized pipeline can publish.
See docs/ARCHITECTURE_DECISIONS.md ADR-001.

**Q: How is the private key protected?**
Stored as GitHub Secret — encrypted at rest, never in logs.
Written to /tmp only during signing step with chmod 600.
Deleted in cleanup step with if: always().
Never committed to repository — confirmed by security audit.

**Q: What happens when firmware is tampered?**
SHA-256 hash mismatch detected immediately.
Agent logs CRITICAL alert with expected vs computed hash.
Writes structured JSON rejection report to edge_agent/rejections/.
Downloads deleted from device storage.
Installation refused. Version store not updated.
Run demo_attack.py Demo 1 to show this live.

**Q: What is anti-rollback protection?**
Minimum version stored in version_store.json.
Any incoming firmware version below minimum is rejected —
even if hash and signature both pass.
Minimum version automatically raised after each install
so it only moves forward, never backward.
Run demo_attack.py Demo 3 to show this live.

**Q: How many tests do you have?**
29 total tests across 2 files.
test_local_pipeline.py — 14 tests (pipeline + unit tests)
test_tamper_simulation.py — 15 tests (5 attack classes)
All 29 pass, 0 failures.
Run: python run_all_tests.py

**Q: What are the limitations of your system?**
No hardware enforcement of anti-rollback — a physical attacker
could modify version_store.json on the device.
GitHub Releases is appropriate for internship scale but production
would use a dedicated artifact store.
Key compromise requires full key rotation procedure — not
automated in this system.
See docs/FINAL_SECURITY_LAYERS.md for full analysis.

---

## File Structure for Evaluator Reference
.github/workflows/sign-and-release.yml  ← CI/CD pipeline

pki/generate_keys.py                    ← PKI setup

pki/public_key.pem                      ← device public key

firmware/create_dummy_firmware.py       ← firmware simulator

firmware/sign_firmware.py               ← signing script

firmware/generate_manifest.py           ← manifest generator

firmware/prepare_release_assets.py      ← pre-release check

firmware/get_latest_release.py          ← GitHub API helper

firmware/verify_release_integrity.py    ← audit tool

firmware/pipeline_status.py             ← pipeline status check

edge_agent/agent.py                     ← IoT device simulation

edge_agent/version_store.json           ← version tracking

edge_agent/rejections/                  ← JSON rejection reports

distribution/manifest.json              ← sample manifest

tests/test_local_pipeline.py            ← 14 unit tests

tests/test_tamper_simulation.py         ← 15 attack tests

demo_attack.py                          ← live demo script

run_all_tests.py                        ← one-command test runner

docs/THREAT_MODEL.md                    ← 4 threats + CVE refs

docs/CRYPTOGRAPHY_DECISIONS.md          ← algorithm reasoning

docs/CICD_PIPELINE.md                   ← pipeline architecture

docs/ARCHITECTURE_DECISIONS.md          ← ADR-001 GitHub Releases

docs/ANTI_ROLLBACK.md                   ← anti-rollback design

docs/FINAL_SECURITY_LAYERS.md           ← three-layer summary

docs/SECURITY_AUDIT.md                  ← credential audit

docs/FINAL_REVIEW_PREP.md               ← this file

---

## GitHub Commit Verification Commands

Run these before the review:

```bash
# Check unique commit days
git log --pretty=format:"%ad" --date=short main | sort -u | wc -l

# Check for gaps in last 20 days
git log --pretty=format:"%ad" --date=short main | sort -u | tail -20

# Check all members committed
git log --pretty=format:"%an" main | sort -u

# Confirm no credentials
git log --all -p | grep -c "BEGIN EC PRIVATE KEY"
git ls-tree -r --name-only HEAD | grep "\.sig$"
```

All commands must return clean results before the review.