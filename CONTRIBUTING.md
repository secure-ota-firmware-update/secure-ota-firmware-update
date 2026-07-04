# Contributing Guide

This document explains how to set up the development environment,
run the project locally, and contribute new code following the
team's standards.

---

## Prerequisites

- Python 3.10 or higher
- Git
- pip

---

## Environment Setup

### 1. Clone the repository

```bash
git clone https://github.com/secure-ota-firmware-update/secure-ota-firmware-update.git
cd secure-ota-firmware-update
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify setup

```bash
python verify_setup.py
```

This checks that all dependencies are installed and all required
files are present.

---

## Running the Local Pipeline

Follow these steps in exact order:

```bash
# Step 1 — Generate ECDSA P-256 key pair
python pki/generate_keys.py

# Step 2 — Generate dummy firmware binary
python firmware/create_dummy_firmware.py --version 1.0.0

# Step 3 — Sign firmware
export FIRMWARE_PRIVATE_KEY_PATH=pki/private_key.pem   # Linux/Mac
set FIRMWARE_PRIVATE_KEY_PATH=pki/private_key.pem      # Windows cmd
python firmware/sign_firmware.py --firmware firmware/dummy_firmware_v1.0.0.bin

# Step 4 — Generate manifest
python firmware/generate_manifest.py \
    --version 1.0.0 \
    --firmware firmware/dummy_firmware_v1.0.0.bin \
    --output distribution/manifest.json

# Step 5 — Run edge agent
python edge_agent/agent.py
```

Full guide with expected output: [docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md)

---

## Running Tests

```bash
# Run all 34 tests
python run_all_tests.py

# Run specific test file
python -m pytest tests/test_local_pipeline.py -v
python -m pytest tests/test_tamper_simulation.py -v
python -m pytest tests/test_edge_cases.py -v

# Run attack demo
python demo_attack.py
```

---

## Branching and Commit Standards

### Branch naming

Each team member works on their own personal branch:
hardik-dev    ← Member 1 (Team Lead)
kanishk-dev   ← Member 2
mahendra-dev  ← Member 3
praveen-dev   ← Member 4

Feature branches are named:
<member-branch>/<week><day>-<task>
e.g. hardik-dev/week1-day2-dummy-firmware

### Commit message format

Every commit must follow this format:
<type>: <description in present tense> (fixes #<issue-number>)

Valid types:

| Type | When to use |
|------|-------------|
| feat | Adding a new feature or script |
| fix | Fixing a bug |
| docs | Documentation only changes |
| test | Adding or updating tests |
| chore | Build process, repo setup, cleanup |
| refactor | Code restructuring without behavior change |

Examples:
feat: implement verify_signature() with ECDSA P-256 (fixes #45)
fix: correct Prehashed import from asymmetric.utils (fixes #46)
docs: write ANTI_ROLLBACK.md explaining version enforcement (fixes #47)
test: add rollback attack test to test_tamper_simulation.py (fixes #48)

### Pull Request process

1. Create a GitHub Issue describing the task
2. Work in your personal branch
3. Open a PR from your branch to main
4. Fill in the PR template (security checklist included)
5. Team Lead reviews and merges

Direct commits to main are forbidden.

---

## GitHub Secrets Required

| Secret | Purpose |
|--------|---------|
| FIRMWARE_PRIVATE_KEY | ECDSA private key for CI/CD signing |
| GITHUB_TOKEN | Auto-provided — no setup needed |

Setup guide: [docs/SECRETS_SETUP.md](docs/SECRETS_SETUP.md)

---

## Creating a New Firmware Release

```bash
# Patch version bump (1.0.0 → 1.0.1)
python firmware/bump_version.py --bump patch

# Minor version bump (1.0.0 → 1.1.0)
python firmware/bump_version.py --bump minor

# Preview without executing
python firmware/bump_version.py --bump patch --dry-run
```

This generates the binary, signs locally, updates the manifest,
commits, tags, and pushes — triggering the CI/CD pipeline automatically.

---

## Security Rules — Never Break These

These rules are enforced by .gitignore and branch protection.
Violating them can result in immediate disqualification.
❌ NEVER commit private_key.pem
❌ NEVER commit .sig files
❌ NEVER commit .env files
❌ NEVER hardcode API keys or passwords in any file
❌ NEVER push directly to main
❌ NEVER use git add . without checking git status first

To verify the repository is clean:

```bash
git ls-tree -r --name-only HEAD | grep "\.pem" | grep -v "public"
git ls-tree -r --name-only HEAD | grep "\.sig$"
git log --all -p | grep "BEGIN EC PRIVATE KEY"
```

All three commands must return empty output.

---

## Project Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview and quick start |
| [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) | Security analysis |
| [docs/CRYPTOGRAPHY_DECISIONS.md](docs/CRYPTOGRAPHY_DECISIONS.md) | Algorithm choices |
| [docs/FINAL_SECURITY_LAYERS.md](docs/FINAL_SECURITY_LAYERS.md) | Architecture summary |
| [docs/CICD_PIPELINE.md](docs/CICD_PIPELINE.md) | Pipeline walkthrough |
| [docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md) | Local setup guide |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Term definitions |