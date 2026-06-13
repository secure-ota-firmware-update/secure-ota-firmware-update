# Edge Agent

This folder contains the simulated IoT Edge Device Verification Agent.
It represents the firmware update client that would run on a real
IoT tracking device in the field.

---

## Files

### agent.py
The main agent script. Orchestrates the full firmware update flow.

### version_store.json
Tracks the device's current firmware version and the minimum
allowed version (anti-rollback protection).

### downloads/
Directory where downloaded firmware and signature files are saved
during the update process.

### agent.log
Log file generated when the agent runs. Contains timestamped
INFO, WARNING, and CRITICAL messages.

---

## How the Agent Works
1.Load version_store.json
2.Load manifest.json (from S3 in Week 3, local file for now)
3.Check if manifest version > current version
4.If update available:
a. Download firmware binary and signature
b. Verify SHA-256 hash matches manifest
c. Verify ECDSA signature matches public key (Week 3)
d. Check anti-rollback version requirement (Week 4)
e. If all checks pass — install and update version_store
f. If any check fails — log CRITICAL alert and reject

---

## Running the Agent

```bash
python edge_agent/agent.py
```

---

## Expected Output — Update Available (PASS scenario)
2026-06-09 10:00:00 [INFO] Edge Device Agent started
2026-06-09 10:00:00 [INFO] Version store loaded — current version: 0.0.0
2026-06-09 10:00:00 [INFO] Manifest loaded — firmware version: 1.0.0
2026-06-09 10:00:00 [INFO] Update available: 0.0.0 → 1.0.0
2026-06-09 10:00:00 [INFO] Firmware downloaded: edge_agent/downloads/dummy_firmware_v1.0.0.bin
2026-06-09 10:00:00 [INFO] Signature downloaded: edge_agent/downloads/dummy_firmware_v1.0.0.sig
2026-06-09 10:00:00 [INFO] Verifying SHA-256 hash of: edge_agent/downloads/dummy_firmware_v1.0.0.bin
2026-06-09 10:00:00 [INFO] Hash verification PASSED — firmware integrity confirmed
2026-06-09 10:00:00 [INFO] All checks passed so far — signature verification coming in Week 3

---

## Expected Output — No Update Needed
2026-06-09 10:00:00 [INFO] Edge Device Agent started
2026-06-09 10:00:00 [INFO] Version store loaded — current version: 1.0.0
2026-06-09 10:00:00 [INFO] Manifest loaded — firmware version: 1.0.0
2026-06-09 10:00:00 [INFO] Already up to date: current=1.0.0, manifest=1.0.0
2026-06-09 10:00:00 [INFO] No update needed. Agent exiting.

---

## Expected Output — Hash Mismatch (FAIL scenario)

If the downloaded firmware is tampered with:
2026-06-09 10:00:00 [INFO] Verifying SHA-256 hash of: edge_agent/downloads/dummy_firmware_v1.0.0.bin
2026-06-09 10:00:00 [INFO] Expected hash: a3f1c9e2b847d6f0...
2026-06-09 10:00:00 [INFO] Computed hash: ff00ff00ff00ff00...
2026-06-09 10:00:00 [CRITICAL] Hash verification FAILED — tampering detected
2026-06-09 10:00:00 [CRITICAL] Expected: a3f1c9e2b847d6f0...
2026-06-09 10:00:00 [CRITICAL] Computed: ff00ff00ff00ff00...
2026-06-09 10:00:00 [CRITICAL] Dropping firmware payload — refusing installation
2026-06-09 10:00:00 [CRITICAL] SECURITY ALERT — Hash verification failed. Aborting.

---

## Coming in Week 3 and Week 4

- `verify_signature()` — ECDSA signature verification using public key
- `anti_rollback_check()` — prevents downgrade to vulnerable firmware versions
- Download from real S3 URL instead of local file copy
Commit and push:
bash
git add edge_agent/README.md
git commit -m "docs: write edge_agent/README.md with agent design and pass/fail output examples (fixes #26)"
git push origin <your-branch>
Open PR from your branch → main
PR Title:
docs: write edge_agent/README.md with agent design and output examples
PR Description:
## What does this PR implement?

Adds edge_agent/README.md documenting:
- Purpose of each file (agent.py, version_store.json, downloads/, agent.log)
- Full agent workflow diagram
- How to run the agent
- Expected output for PASS scenario (update available)
- Expected output for already up to date scenario
- Expected output for FAIL scenario (hash mismatch)
- Preview of Week 3 and Week 4 additions

## Closes issue
Closes #26

## Week
- [x] Week 1 — PKI & Hashing

## Security checklist
- [x] No real hash values from actual keys exposed
- [x] No credentials in documentation

## How was this tested?
Ran agent.py and compared actual log output against documented examples.
Manually corrupted firmware to verify FAIL scenario output matches.