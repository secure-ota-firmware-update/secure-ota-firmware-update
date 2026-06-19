# Local Testing Guide

This document explains how to run the full OTA signing pipeline locally
for development and testing purposes.

## Prerequisites

Install dependencies:
```bash
pip install -r requirements.txt
```

## Step 1 — Generate ECDSA Key Pair

```bash
python pki/generate_keys.py
```

Expected output:
- pki/private_key.pem  (DO NOT commit this)
- pki/public_key.pem   (safe to commit)

## Step 2 — Generate Dummy Firmware Binary

```bash
python firmware/create_dummy_firmware.py --version 1.0.0
```

Expected output:
- firmware/dummy_firmware_v1.0.0.bin

## Step 3 — Sign the Firmware

```bash
export FIRMWARE_PRIVATE_KEY_PATH=pki/private_key.pem

python firmware/sign_firmware.py \
    --firmware firmware/dummy_firmware_v1.0.0.bin
```

Expected output:
- firmware/dummy_firmware_v1.0.0.sig

## Step 4 — Generate Manifest

```bash
python firmware/generate_manifest.py \
    --version 1.0.0 \
    --firmware firmware/dummy_firmware_v1.0.0.bin \
    --output distribution/manifest.json
```

Expected output:
- distribution/manifest.json

## Step 5 — Verify Everything Exists

```bash
ls firmware/
ls distribution/
```

You should see:
- firmware/dummy_firmware_v1.0.0.bin
- firmware/dummy_firmware_v1.0.0.sig
- distribution/manifest.json

## Security Reminders

- NEVER commit private_key.pem
- NEVER commit dummy_firmware_v1.0.0.sig (generated artifact)
- NEVER hardcode the private key path in any script
- Always use environment variables for key paths

## Verification Results — Day 6 Integration Test

All 5 steps completed successfully on Day 6.

SHA-256 hash verified — manifest hash matches direct binary hash.
Edge agent initializes without errors.
All output files confirmed present:
- pki/public_key.pem
- firmware/dummy_firmware_v1.0.0.bin
- firmware/dummy_firmware_v1.0.0.sig
- distribution/manifest.json

## CI/CD Pipeline Status

Pipeline tested and confirmed green on tag v0.1.0.


GitHub Release created automatically with all 3 firmware assets attached.

## End-to-End Test — Week 2 Day 5

Ran edge agent against real GitHub Release v0.1.0:

```bash
export GITHUB_RELEASE_BASE_URL=https://github.com/secure-ota-firmware-update/secure-ota-firmware-update
python edge_agent/agent.py
```

Results:
- Manifest fetched from GitHub Releases API successfully
- Firmware binary downloaded from release assets
- Signature downloaded from release assets
- SHA-256 hash verification PASSED
- Version check: 0.0.0 → 1.0.0 (update available)
- Agent completed without errors

Full end-to-end flow confirmed working:

Developer push tag → Pipeline sign → GitHub Release → Agent download → Hash verify
=======
Developer push tag → Pipeline sign → GitHub Release → Agent download → Hash verify

GitHub Release created automatically with all 3 firmware assets attached.
