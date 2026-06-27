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

1. Load version_store.json
2. Load manifest.json (from GitHub Releases if available, otherwise local file)
3. Check if manifest version > current version
4. If update available:  
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

## Test 1 — Real GitHub Release (PASS)

export GITHUB_RELEASE_BASE_URL=https://github.com/secure-ota-firmware-update/secure-ota-firmware-update
python edge_agent/agent.py

# Result

2026-06-17 21:00:44,019 [INFO] ==================================================
2026-06-17 21:00:44,020 [INFO] Edge Device Agent started
2026-06-17 21:00:45,446 [INFO] Found release: v0.1.1
2026-06-17 21:00:48,392 [INFO] Manifest fetched — firmware version: 0.1.1
2026-06-17 21:00:53,935 [INFO] Hash verification PASSED — firmware integrity confirmed
2026-06-17 21:00:53,936 [INFO] Signature verification coming in Week 3
2026-06-17 21:00:53,936 [INFO] Agent run finished

## Test 2 — Tampered Manifest Hash (FAIL)

unset GITHUB_RELEASE_BASE_URL
python edge_agent/agent.py

# Result

2026-06-17 21:03:36,198 [CRITICAL] Hash verification FAILED — tampering detected
2026-06-17 21:03:36,199 [CRITICAL] SECURITY ALERT — Hash verification failed. Aborting.
2026-06-17 21:03:36,200 [INFO] Agent run finished

## Test 3 — No Update Available

python edge_agent/agent.py

# Result

2026-06-17 21:40:21,497 [INFO] Version store loaded — current version: 1.0.0
2026-06-17 21:40:21,498 [INFO] Using local manifest — firmware version: 1.0.0
2026-06-17 21:40:21,498 [INFO] Already up to date: current=1.0.0 -> manifest=1.0.0
2026-06-17 21:40:21,498 [INFO] No update needed. Agent exiting.

---

## Coming in Week 3 and Week 4

- `verify_signature()` — ECDSA signature verification using public key
- `anti_rollback_check()` — prevents downgrade to vulnerable firmware versions
- Download from real S3 URL instead of local file copy
