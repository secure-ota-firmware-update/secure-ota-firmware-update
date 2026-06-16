# Firmware

This folder contains all scripts related to firmware creation,
signing, and manifest generation.

---

## Files

### create_dummy_firmware.py
Generates a dummy firmware binary for testing the OTA pipeline.
Since we have no real IoT hardware, this simulates a compiled
firmware binary with a structured header and random payload bytes.

Usage:
```bash
python firmware/create_dummy_firmware.py --version 1.0.0
python firmware/create_dummy_firmware.py --version 1.1.0 --size 512
```

Output: firmware/dummy_firmware_vX.X.X.bin

---

### sign_firmware.py
Signs a firmware binary using the ECDSA P-256 private key.
Computes SHA-256 hash of the binary then signs the hash.
Private key is NEVER hardcoded — read from environment variable.

Usage:
```bash
export FIRMWARE_PRIVATE_KEY_PATH=pki/private_key.pem
python firmware/sign_firmware.py --firmware firmware/dummy_firmware_v1.0.0.bin
```

Output: firmware/dummy_firmware_vX.X.X.sig

Security rule: Never commit the .sig file or private_key.pem

---

### generate_manifest.py
Generates the manifest.json file that the edge agent reads to
check for updates and verify firmware integrity.

Usage:
```bash
python firmware/generate_manifest.py \
    --version 1.0.0 \
    --firmware firmware/dummy_firmware_v1.0.0.bin \
    --output distribution/manifest.json
```

Output: distribution/manifest.json

---

## Correct Order of Operations

Always run scripts in this order:
1.python pki/generate_keys.py
2.python firmware/create_dummy_firmware.py --version X.X.X
3.python firmware/sign_firmware.py --firmware firmware/dummy_firmware_vX.X.X.bin
4.python firmware/generate_manifest.py --version X.X.X --firmware firmware/dummy_firmware_vX.X.X.bin

---

## Security Rules

- NEVER commit private_key.pem
- NEVER commit .sig files
- ALWAYS use environment variables for private key path
- public_key.pem is the ONLY key file safe to commit