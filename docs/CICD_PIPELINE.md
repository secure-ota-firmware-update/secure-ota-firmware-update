# CI/CD Pipeline Architecture

This document explains how the GitHub Actions pipeline in
`.github/workflows/sign-and-release.yml` works end to end.

---

## What Triggers the Pipeline

The pipeline runs automatically whenever a git tag matching
`v*.*.*` is pushed to the repository:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Tags like `v1.0.0`, `v1.2.3`, `v2.0.0` all trigger the pipeline.
Regular commits and branch pushes do NOT trigger it.

---

## Pipeline Steps — Detailed Walkthrough

### Step 1 — Checkout repository
Standard GitHub Actions step. Clones the repository code into
the runner so subsequent steps can access all files.

### Step 2 — Set up Python
Installs Python 3.11 on the Ubuntu runner.

### Step 3 — Install dependencies
Runs `pip install -r requirements.txt` to install cryptography,
boto3, requests, and pytest.

### Step 4 — Write private key from GitHub Secret
```yaml
env:
  FIRMWARE_PRIVATE_KEY: ${{ secrets.FIRMWARE_PRIVATE_KEY }}
run: |
  echo "$FIRMWARE_PRIVATE_KEY" > /tmp/private_key.pem
  chmod 600 /tmp/private_key.pem
```

This is the most security-critical step. The private key exists
ONLY as an in-memory environment variable until this step writes
it to `/tmp/private_key.pem` with restricted permissions (600 =
owner read/write only). GitHub automatically masks this value in
all logs — even if printed accidentally, it shows as `***`.

### Step 5 — Sign firmware binary
```yaml
run: |
  python firmware/sign_firmware.py \
    --firmware firmware/dummy_firmware_v1.0.0.bin \
    --key /tmp/private_key.pem
```

Calls `sign_firmware.py` which:
1. Loads the private key from `/tmp/private_key.pem`
2. Computes SHA-256 hash of the firmware binary
3. Signs the hash using ECDSA P-256
4. Writes the signature to `firmware/dummy_firmware_v1.0.0.sig`

### Step 6 — Generate manifest
```yaml
run: |
  VERSION="${{ github.ref_name }}"
  VERSION="${VERSION#v}"
  python firmware/generate_manifest.py \
    --version "$VERSION" \
    --firmware firmware/dummy_firmware_v1.0.0.bin \
    --output distribution/manifest.json
```

`${{ github.ref_name }}` is the tag that triggered the pipeline
(e.g. `v1.0.0`). The `${VERSION#v}` shell parameter expansion
strips the leading `v`, leaving `1.0.0`. This becomes the version
field in `manifest.json`.

### Step 7 — Upload to S3
```yaml
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  S3_BUCKET_NAME: ${{ secrets.S3_BUCKET_NAME }}
run: |
  python firmware/upload_to_s3.py ...
```

Uploads three files to `s3://<bucket>/releases/<version>/`:
- `dummy_firmware_v1.0.0.bin`
- `dummy_firmware_v1.0.0.sig`
- `manifest.json`

### Step 8 — Clean up private key
```yaml
- name: Clean up private key
  if: always()
  run: rm -f /tmp/private_key.pem
```

`if: always()` ensures this runs even if a previous step failed.
The private key never persists beyond this single workflow run —
each run gets a fresh, isolated runner that is destroyed afterward.

---

## Full Pipeline Diagram

Developer

|

| git tag v1.0.0 && git push origin v1.0.0

v

GitHub Actions triggered

|

v

[Checkout] -> [Setup Python] -> [Install deps]

|

v

[Write private key from Secret to /tmp]

|

v

[sign_firmware.py]

- computes SHA-256

- signs with ECDSA P-256

- outputs .sig file

|

v

[generate_manifest.py]

- builds manifest.json with version, hash, etc.

|

v

[upload_to_s3.py]

- uploads .bin, .sig, manifest.json to S3

|

v

[Clean up /tmp private key] (always runs)

|

v

S3 bucket now contains:

releases/1.0.0/dummy_firmware_v1.0.0.bin

releases/1.0.0/dummy_firmware_v1.0.0.sig

releases/1.0.0/manifest.json

|

v

Edge Agent (later) downloads from S3 and verifies

---

## How to Trigger a Release

```bash
git checkout main
git pull origin main
git tag v1.0.0
git push origin v1.0.0
```

Then check the **Actions** tab on GitHub to watch the pipeline run.
A green checkmark means all 8 steps succeeded and the firmware
is now live in S3.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Private key not found at /tmp/private_key.pem` | FIRMWARE_PRIVATE_KEY secret missing or empty | Check Settings -> Secrets, re-add the secret |
| `AWS credentials not found` | AWS secrets missing | Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set |
| `Access Denied` on S3 upload | IAM policy too restrictive | Check IAM policy allows s3:PutObject on the bucket |
| Workflow doesn't trigger at all | Tag doesn't match `v*.*.*` pattern | Use format `v1.0.0`, not `1.0.0` or `release-1` |

---

## Related Documentation

- [SECRETS_SETUP.md](SECRETS_SETUP.md) — how to configure the 4 required secrets
- [CRYPTOGRAPHY_DECISIONS.md](CRYPTOGRAPHY_DECISIONS.md) — why ECDSA and SHA-256 were chosen
- [THREAT_MODEL.md](THREAT_MODEL.md) — Threat 4 (Key Compromise) explains why secrets are used