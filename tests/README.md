# Tests

This folder will contain end-to-end tamper simulation tests for the
OTA firmware update pipeline.

---

## Coming in Week 4
### Week 4 — Final Polish and Documentation ✅ COMPLETE

- [x] Comprehensive README.md as project showcase
- [x] CONTRIBUTING.md with developer onboarding
- [x] verify_setup.py environment verification script
- [x] bump_version.py one-command release creator
- [x] demo_attack.py live attack demonstration
- [x] run_all_tests.py one-command test runner
- [x] GLOSSARY.md with 40+ security terms defined
- [x] LESSONS_LEARNED.md with 7 technical insights
- [x] SUBMISSION_CHECKLIST.md mapping spec to implementation
- [x] Full repo audit — fixed agent.py, stray files, .gitignore
- [x] Final release v1.1.0 published and verified
### test_tamper_simulation.py

This test file will contain 5 critical security tests:

1. **test_valid_firmware()**
   Signs a real binary, runs the agent, asserts PASS and
   version_store.json is updated correctly.

2. **test_corrupted_binary()**
   Flips one byte in the firmware after signing.
   Asserts the agent detects the hash mismatch and rejects.

3. **test_wrong_signature()**
   Signs firmware with a different key.
   Asserts the agent rejects with signature verification error.

4. **test_rollback_attack()**
   Attempts to install an older signed version when minimum
   version is higher. Asserts the agent rejects with rollback error.

5. **test_completely_fake_sig()**
   Creates random bytes as a .sig file.
   Asserts the agent handles invalid signature format gracefully
   without crashing.

---

## Why These Tests Matter

Each test simulates a real attack scenario described in
docs/THREAT_MODEL.md:

| Test                     | Threat Simulated                             |
| ------------------------ | -------------------------------------------- |
| test_valid_firmware      | Baseline — confirms normal operation works   |
| test_corrupted_binary    | MITM Attack (Threat 2)                       |
| test_wrong_signature     | Supply Chain Attack (Threat 1)               |
| test_rollback_attack     | Rollback Attack (Threat 3)                   |
| test_completely_fake_sig | Key Compromise / Forged Signature (Threat 4) |

---

## Running Tests (Week 4)

```bash
python -m pytest tests/test_tamper_simulation.py -v
```
## Latest Release

```bash
python firmware/pipeline_status.py    # check pipeline status
python firmware/verify_release_integrity.py  # verify release artifacts
```

Latest release: v1.1.0
Assets: dummy_firmware_v1.0.0.bin + dummy_firmware_v1.0.0.sig + manifest.json