# Documentation Index

Complete documentation for the Secure OTA Firmware Update project.
All documents are in the `docs/` folder.

---

## Start Here

New to the project? Read in this order:

1. [../README.md](../README.md) — project overview, architecture, quick start
2. [THREAT_MODEL.md](THREAT_MODEL.md) — what attacks this solves
3. [FINAL_SECURITY_LAYERS.md](FINAL_SECURITY_LAYERS.md) — how the three layers work together
4. [CRYPTOGRAPHY_DECISIONS.md](CRYPTOGRAPHY_DECISIONS.md) — why these algorithms
5. [CICD_PIPELINE.md](CICD_PIPELINE.md) — how the pipeline works
6. [LOCAL_TESTING.md](LOCAL_TESTING.md) — run it yourself

---

## Security Documentation

| Document | Description | Related |
|----------|-------------|---------|
| [THREAT_MODEL.md](THREAT_MODEL.md) | 4 threats with CVE references, attack scenarios, mitigations | FINAL_SECURITY_LAYERS.md |
| [CRYPTOGRAPHY_DECISIONS.md](CRYPTOGRAPHY_DECISIONS.md) | ECDSA vs RSA, SHA-256 vs MD5, key storage reasoning | GLOSSARY.md |
| [FINAL_SECURITY_LAYERS.md](FINAL_SECURITY_LAYERS.md) | Three-layer defense architecture with diagram | THREAT_MODEL.md, ANTI_ROLLBACK.md |
| [ANTI_ROLLBACK.md](ANTI_ROLLBACK.md) | Anti-rollback design, version store, ratchet mechanism | FINAL_SECURITY_LAYERS.md |
| [SECURITY_AUDIT.md](SECURITY_AUDIT.md) | Git history credential audit results | SECRETS_SETUP.md |
| [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) | ADR-001 GitHub Releases, ADR-002 ECDSA, ADR-003 SHA-256 | CRYPTOGRAPHY_DECISIONS.md |

---

## Operational Documentation

| Document | Description | Related |
|----------|-------------|---------|
| [LOCAL_TESTING.md](LOCAL_TESTING.md) | Step-by-step local pipeline with expected output | ../CONTRIBUTING.md |
| [SECRETS_SETUP.md](SECRETS_SETUP.md) | GitHub Secrets configuration guide | CICD_PIPELINE.md |
| [CICD_PIPELINE.md](CICD_PIPELINE.md) | Full pipeline architecture and troubleshooting | SECRETS_SETUP.md |

<<<<<<< HEAD
---

## Test and Review Documentation

| Document | Description | Related |
|----------|-------------|---------|
| [TEST_RESULTS.md](TEST_RESULTS.md) | Full 29-test suite results with threat coverage table | TAMPER_SIMULATION_RESULTS.md |
| [TAMPER_SIMULATION_RESULTS.md](TAMPER_SIMULATION_RESULTS.md) | Manual attack simulation results | THREAT_MODEL.md |
| [SIGNATURE_VERIFICATION_TEST_RESULTS.md](SIGNATURE_VERIFICATION_TEST_RESULTS.md) | verify_signature() test results | ANTI_ROLLBACK.md |
| [MEMBER2_TEST_VERIFICATION.md](MEMBER2_TEST_VERIFICATION.md) | Independent test verification | TEST_RESULTS.md |
| [PRE_REVIEW_SIGNOFF.md](PRE_REVIEW_SIGNOFF.md) | Final pre-review validation results | FINAL_REVIEW_PREP.md |

---

## Project Management Documentation

| Document | Description | Related |
|----------|-------------|---------|
| [WORK_DISTRIBUTION.md](WORK_DISTRIBUTION.md) | Official task distribution (submit to Infotact) | — |
| [MID_REVIEW_PREP.md](MID_REVIEW_PREP.md) | Mid Review demo script and Q&A | FINAL_REVIEW_PREP.md |
| [FINAL_REVIEW_PREP.md](FINAL_REVIEW_PREP.md) | Final Review demo script and Q&A | PRE_REVIEW_SIGNOFF.md |
| [WEEK2_COMPLETION_REPORT.md](WEEK2_COMPLETION_REPORT.md) | Week 2 final status | FINAL_WEEK2_TEST.md |
| [FINAL_WEEK2_TEST.md](FINAL_WEEK2_TEST.md) | Final Week 2 end-to-end test | WEEK2_COMPLETION_REPORT.md |
| [WEEK3_PROGRESS.md](WEEK3_PROGRESS.md) | Week 3 implementation summary | FINAL_SECURITY_LAYERS.md |
| [PROJECT_COMPLETION_REPORT.md](PROJECT_COMPLETION_REPORT.md) | Full 3-week project summary (submit to Infotact) | — |

---

=======
---

## Test and Review Documentation

| Document | Description | Related |
|----------|-------------|---------|
| [TEST_RESULTS.md](TEST_RESULTS.md) | Full 29-test suite results with threat coverage table | TAMPER_SIMULATION_RESULTS.md |
| [TAMPER_SIMULATION_RESULTS.md](TAMPER_SIMULATION_RESULTS.md) | Manual attack simulation results | THREAT_MODEL.md |
| [SIGNATURE_VERIFICATION_TEST_RESULTS.md](SIGNATURE_VERIFICATION_TEST_RESULTS.md) | verify_signature() test results | ANTI_ROLLBACK.md |
| [MEMBER2_TEST_VERIFICATION.md](MEMBER2_TEST_VERIFICATION.md) | Independent test verification | TEST_RESULTS.md |
| [PRE_REVIEW_SIGNOFF.md](PRE_REVIEW_SIGNOFF.md) | Final pre-review validation results | FINAL_REVIEW_PREP.md |


=======
| [FINAL_SECURITY_LAYERS.md](FINAL_SECURITY_LAYERS.md) | Complete three-layer defense architecture summary |
| [ANTI_ROLLBACK.md](ANTI_ROLLBACK.md) | Anti-rollback design and version store |
| [TAMPER_SIMULATION_RESULTS.md](TAMPER_SIMULATION_RESULTS.md) | Manual attack simulation results |
| [SIGNATURE_VERIFICATION_TEST_RESULTS.md](SIGNATURE_VERIFICATION_TEST_RESULTS.md) | Signature verification test results |
| [WEEK3_PROGRESS.md](WEEK3_PROGRESS.md) | Week 3 implementation summary |
| [MEMBER2_TEST_VERIFICATION.md](MEMBER2_TEST_VERIFICATION.md) | Independent test verification |
| [TEST_RESULTS.md](TEST_RESULTS.md) | Full 29-test suite results |


| [ANTI_ROLLBACK.md](ANTI_ROLLBACK.md) | Anti-rollback design, version store, three security layers |
| [TAMPER_SIMULATION_RESULTS.md](TAMPER_SIMULATION_RESULTS.md) | Manual attack simulation results |
| [SIGNATURE_VERIFICATION_TEST_RESULTS.md](SIGNATURE_VERIFICATION_TEST_RESULTS.md) | verify_signature() test results |
| [WEEK3_PROGRESS.md](WEEK3_PROGRESS.md) | Week 3 implementation summary |
| [MEMBER2_TEST_VERIFICATION.md](MEMBER2_TEST_VERIFICATION.md) | Independent test verification |

---

## Project Management Documentation

| Document | Description | Related |
|----------|-------------|---------|
| [WORK_DISTRIBUTION.md](WORK_DISTRIBUTION.md) | Official task distribution (submit to Infotact) | — |
| [MID_REVIEW_PREP.md](MID_REVIEW_PREP.md) | Mid Review demo script and Q&A | FINAL_REVIEW_PREP.md |
| [FINAL_REVIEW_PREP.md](FINAL_REVIEW_PREP.md) | Final Review demo script and Q&A | PRE_REVIEW_SIGNOFF.md |
| [WEEK2_COMPLETION_REPORT.md](WEEK2_COMPLETION_REPORT.md) | Week 2 final status | FINAL_WEEK2_TEST.md |
| [FINAL_WEEK2_TEST.md](FINAL_WEEK2_TEST.md) | Final Week 2 end-to-end test | WEEK2_COMPLETION_REPORT.md |
| [WEEK3_PROGRESS.md](WEEK3_PROGRESS.md) | Week 3 implementation summary | FINAL_SECURITY_LAYERS.md |
| [PROJECT_COMPLETION_REPORT.md](PROJECT_COMPLETION_REPORT.md) | Full 3-week project summary (submit to Infotact) | — |

---

>>>>>>> origin
## Learning Documentation

| Document | Description | Related |
|----------|-------------|---------|
| [LESSONS_LEARNED.md](LESSONS_LEARNED.md) | Technical insights, bugs caught, production comparison | ARCHITECTURE_DECISIONS.md |
| [GLOSSARY.md](GLOSSARY.md) | All cryptographic and security terms defined | CRYPTOGRAPHY_DECISIONS.md |

---

## Quick Reference

**Running the project:**
```bash
python verify_setup.py          # check environment
python run_all_tests.py         # run all tests
python demo_attack.py           # live attack demo
python edge_agent/agent.py      # run edge agent
```

**Creating a new firmware release:**
```bash
python firmware/bump_version.py --bump patch
```

**Checking pipeline:**
```bash
python firmware/pipeline_status.py
python firmware/verify_release_integrity.py
```

**Security audit:**
```bash
git log --all -p | grep -c "BEGIN EC PRIVATE KEY"
git ls-tree -r --name-only HEAD | grep "\.sig$"
```