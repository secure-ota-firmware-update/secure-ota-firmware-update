 **Update:** As of Week 2, this project uses GitHub Releases instead
> of AWS S3 for firmware distribution. Only `FIRMWARE_PRIVATE_KEY`
> is required. The AWS secrets documented below are no longer needed.
> See `docs/ARCHITECTURE_DECISIONS.md` ADR-001 for full reasoning.

# GitHub Secrets Setup Guide

This document explains the GitHub Secret required for the
CI/CD signing and release pipeline.

---

## Why GitHub Secrets

GitHub Secrets are encrypted environment variables that are:
- Stored encrypted at rest
- Never printed in workflow logs (automatically masked)
- Injected only into authorized workflow runs
- Not accessible to pull requests from forks

See `docs/CRYPTOGRAPHY_DECISIONS.md` section 4 for full reasoning
on why secrets are used instead of committing keys to files.

---

## How to Add a Secret

1. Go to the repository on GitHub
2. Click **Settings**
3. In the left sidebar, click **Secrets and variables** -> **Actions**
4. Click **New repository secret**
5. Enter the **Name** exactly as specified below
6. Enter the **Value**
7. Click **Add secret**

---

## Required Secret

### FIRMWARE_PRIVATE_KEY

**What it contains:**
The full contents of `pki/private_key.pem` — the ECDSA P-256
private key used to sign firmware binaries.

**How to get the value:**
```bash
cat pki/private_key.pem
```

Copy the entire output including the `-----BEGIN EC PRIVATE KEY-----`
and `-----END EC PRIVATE KEY-----` lines.

**Used by:**
The "Write private key from GitHub Secret" step in
`.github/workflows/sign-and-release.yml`.

**Security note:**
After adding this secret, keep a secure offline backup of the
private key in case key rotation is needed later. Never re-upload
it through any other channel.

---

## About GITHUB_TOKEN

The workflow also uses `secrets.GITHUB_TOKEN` to create GitHub
Releases. This token:

- Is automatically created by GitHub for every workflow run
- Requires NO setup — you do not create or add this secret
- Is automatically scoped to this repository only
- Expires automatically when the workflow run completes

The only requirement is that the workflow has
`permissions: contents: write` set at the job level (already
configured in sign-and-release.yml).

---

## Verification Checklist

After adding the secret, verify in
Settings -> Secrets and variables -> Actions:

- [ ] FIRMWARE_PRIVATE_KEY shows as configured

That's it — only one secret needed.

---

## What Happens If the Secret Is Missing

If `FIRMWARE_PRIVATE_KEY` is missing, the "Write private key" step
will write an empty file, and `sign_firmware.py` will fail with: