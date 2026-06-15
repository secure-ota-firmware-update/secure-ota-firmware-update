# GitHub Secrets Setup Guide


This document explains the GitHub Secret required for the
CI/CD signing and release pipeline.
=======
This document explains every GitHub Secret required for the
CI/CD signing and distribution pipeline, what each one contains,
and how to add them to the repository.


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

3. In the left sidebar, click **Secrets and variables** → **Actions**

4. Click **New repository secret**
5. Enter the **Name** exactly as specified below
6. Enter the **Value**
7. Click **Add secret**

---


## Required Secret

### FIRMWARE_PRIVATE_KEY

## Required Secrets

### 1. FIRMWARE_PRIVATE_KEY

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
=======
The "Write private key from secret" step in
`.github/workflows/sign-and-release.yml` (added Day 2).

**Security note:**
After adding this secret, the private key should not be needed
locally anymore for CI/CD purposes. Keep a secure offline backup
in case key rotation is needed later.

---

### 2. AWS_ACCESS_KEY_ID

**What it contains:**
AWS IAM access key ID for a user with `s3:PutObject` permission
on the firmware distribution bucket.

**How to get the value:**
Create an IAM user in AWS Console with a policy scoped to only
the specific S3 bucket — never use root account credentials.

**Used by:**
`firmware/upload_to_s3.py` via the "Upload to S3" step
in the workflow (added Day 3).

---

### 3. AWS_SECRET_ACCESS_KEY

**What it contains:**
The corresponding secret access key for the IAM user above.

**Security note:**
This value is shown only once when the IAM access key is created.
If lost, you must generate a new access key pair.

---

### 4. S3_BUCKET_NAME

**What it contains:**
The name of the S3 bucket used for firmware distribution
(e.g. `secure-ota-firmware-bucket`).

**Note:**
This could also be a repository Variable instead of a Secret
since it's not sensitive — but kept as a Secret here for
configuration consistency.

---

## Recommended IAM Policy for AWS_ACCESS_KEY_ID

When creating the IAM user, attach a policy scoped to only this bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```

This follows the principle of least privilege — the credentials
can only read/write to this specific bucket, nothing else in AWS.

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

After adding all 4 secrets, verify in Settings → Secrets and variables → Actions:

- [ ] FIRMWARE_PRIVATE_KEY
- [ ] AWS_ACCESS_KEY_ID
- [ ] AWS_SECRET_ACCESS_KEY
- [ ] S3_BUCKET_NAME

All 4 should show as configured (values are hidden, only names visible).

---

## What Happens If a Secret Is Missing

If `FIRMWARE_PRIVATE_KEY` is missing, the "Write private key" step
in the workflow will write an empty file, and `sign_firmware.py`
