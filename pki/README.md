# PKI — Public Key Infrastructure

This folder contains the ECDSA P-256 key generation script and the
public key used by edge devices for firmware signature verification.

---

## Files

### generate_keys.py
Generates an ECDSA P-256 asymmetric key pair.

Usage:
```bash
python pki/generate_keys.py
```

Output:
- `private_key.pem` — generated locally, NEVER committed
- `public_key.pem` — committed, embedded in every edge device

---

### public_key.pem
The public half of the ECDSA key pair. This file is:
- Safe to commit and share publicly
- Embedded in every IoT edge device at manufacture time
- Used by `edge_agent/agent.py` to verify firmware signatures

---

## private_key.pem — NEVER COMMIT THIS FILE

The private key:
- Is generated locally by `generate_keys.py`
- Must be excluded by `.gitignore`
- In Week 2, will be stored as a GitHub Secret (`FIRMWARE_PRIVATE_KEY`)
- Is used only by `firmware/sign_firmware.py` during the CI/CD signing step
- Should be deleted from local disk after being added to GitHub Secrets

If you ever see `private_key.pem` in `git status` as a tracked file —
STOP immediately and check `.gitignore`.

---

## Key Rotation

If the private key is ever compromised:

1. Run `python pki/generate_keys.py` again to generate a new pair
2. Update the `FIRMWARE_PRIVATE_KEY` GitHub Secret with the new private key
3. Commit the new `public_key.pem` to the repository
4. All edge devices must receive the new public key through a
   separate secure provisioning channel (out of scope for this project)
5. Old signatures signed with the compromised key become invalid
   for any future firmware — but previously verified firmware
   already installed remains unaffected

---

## Why ECDSA P-256

See `docs/CRYPTOGRAPHY_DECISIONS.md` for full technical reasoning.
Summary: P-256 provides 128-bit security with much smaller keys
and signatures than RSA, making it ideal for IoT devices.