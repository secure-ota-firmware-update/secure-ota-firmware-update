# Security Audit Report

**Date:** Week 2 Day 6
**Auditor:** Member 1 (Team Lead)
**Scope:** Full git history and current repository state

---

## Audit Checks

| Check | Command | Result |
|-------|---------|--------|
| Private key in git history | `git log --all -p \| grep "BEGIN EC PRIVATE KEY"` | PASS — no results |
| .pem files in repo | `git ls-tree -r --name-only HEAD \| grep .pem` | PASS — only public_key.pem |
| AWS credentials in history | `git log --all -p \| grep -E "AKIA[0-9A-Z]{16}"` | PASS — no results |
| .env files committed | `git ls-tree -r --name-only HEAD \| grep .env` | PASS — no results |
| .sig files committed | `git ls-tree -r --name-only HEAD \| grep .sig` | PASS — no results |
| .gitignore covers private key | `cat .gitignore \| grep private_key` | PASS — excluded |

---

## GitHub Secrets Configured

| Secret Name | Status |
|-------------|--------|
| FIRMWARE_PRIVATE_KEY | Configured |
| GITHUB_TOKEN | Auto-provided by GitHub |

---

## Findings

No security issues found. Repository is clean.

All sensitive material (private key) is stored exclusively
as a GitHub Secret and is never committed to the repository.

---

## Recommendations for Week 3 and 4

- Continue to verify .gitignore before any git add . operations
- Never use git add . without checking git status first
- If a secret is ever accidentally committed — rotate it immediately
  and force-push to remove from history