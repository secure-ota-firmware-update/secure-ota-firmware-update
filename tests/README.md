# Tests

This folder will contain end-to-end tamper simulation tests for the
OTA firmware update pipeline.

---

## Coming in Week 4

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
