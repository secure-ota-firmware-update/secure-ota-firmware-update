# Member 2 Independent Test Verification

**Date:** Week 3 Day 5
**Tests verified:** tests/test_tamper_simulation.py

---

## Environment

- OS: Windows 11 (Git Bash)
- Python: 3.13
- cryptography library: 42.0.8

---

## Results

```bash
python -m pytest tests/test_tamper_simulation.py -v
```
tests/test_tamper_simulation.py::TestValidFirmware::test_hash_verification_passes PASSED                                                                          [  6%]
tests/test_tamper_simulation.py::TestValidFirmware::test_signature_verification_passes PASSED                                                                     [ 13%]
tests/test_tamper_simulation.py::TestValidFirmware::test_anti_rollback_passes PASSED                                                                              [ 20%]
tests/test_tamper_simulation.py::TestValidFirmware::test_all_three_checks_pass PASSED                                                                             [ 26%]
tests/test_tamper_simulation.py::TestMITMAttack::test_corrupted_binary_fails_hash_check PASSED                                                                    [ 33%]
tests/test_tamper_simulation.py::TestMITMAttack::test_corrupted_binary_fails_signature_check PASSED                                                               [ 40%]
tests/test_tamper_simulation.py::TestSupplyChainAttack::test_wrong_key_signature_fails_verification PASSED                                                        [ 46%]
tests/test_tamper_simulation.py::TestRollbackAttack::test_rollback_to_older_major_rejected PASSED                                                                 [ 53%]
tests/test_tamper_simulation.py::TestRollbackAttack::test_rollback_to_older_minor_rejected PASSED                                                                 [ 60%]
tests/test_tamper_simulation.py::TestRollbackAttack::test_rollback_to_older_patch_rejected PASSED                                                                 [ 66%]
tests/test_tamper_simulation.py::TestRollbackAttack::test_valid_sig_does_not_bypass_rollback PASSED                                                               [ 73%]
tests/test_tamper_simulation.py::TestFakeSignature::test_random_bytes_signature_rejected PASSED                                                                   [ 80%]
tests/test_tamper_simulation.py::TestFakeSignature::test_zero_bytes_signature_rejected PASSED                                                                     [ 86%]
tests/test_tamper_simulation.py::TestFakeSignature::test_empty_signature_file_rejected PASSED                                                                     [ 93%]
tests/test_tamper_simulation.py::TestFakeSignature::test_truncated_signature_rejected PASSED                                                                      [100%]

========================================================================== 15 passed in 0.75s ==========================================================================

15 passed, 0 failed

```bash
python -m pytest tests/ -v
```
tests/test_local_pipeline.py::test_firmware_binary_exists PASSED                                                                                                  [  3%]
tests/test_local_pipeline.py::test_signature_file_exists_and_nonempty PASSED                                                                                      [  6%]
tests/test_local_pipeline.py::test_manifest_has_all_required_fields PASSED                                                                                        [ 10%]
tests/test_local_pipeline.py::test_manifest_sha256_matches_binary PASSED                                                                                          [ 13%]
tests/test_local_pipeline.py::test_public_key_exists PASSED                                                                                                       [ 17%]
tests/test_local_pipeline.py::test_verify_signature_accepts_valid PASSED                                                                                          [ 20%]
tests/test_local_pipeline.py::test_verify_signature_rejects_corrupted_binary PASSED                                                                               [ 24%]
tests/test_local_pipeline.py::test_verify_signature_rejects_fake_signature PASSED                                                                                 [ 27%]
tests/test_local_pipeline.py::test_verify_signature_rejects_wrong_key PASSED                                                                                      [ 31%]
tests/test_local_pipeline.py::test_anti_rollback_accepts_newer_version PASSED                                                                                     [ 34%]
tests/test_local_pipeline.py::test_anti_rollback_accepts_equal_version PASSED                                                                                     [ 37%]
tests/test_local_pipeline.py::test_anti_rollback_rejects_older_major PASSED                                                                                       [ 41%]
tests/test_local_pipeline.py::test_anti_rollback_rejects_older_patch PASSED                                                                                       [ 44%]
tests/test_local_pipeline.py::test_anti_rollback_integer_comparison_correctness PASSED                                                                            [ 48%]
tests/test_tamper_simulation.py::TestValidFirmware::test_hash_verification_passes PASSED                                                                          [ 51%]
tests/test_tamper_simulation.py::TestValidFirmware::test_signature_verification_passes PASSED                                                                     [ 55%]
tests/test_tamper_simulation.py::TestValidFirmware::test_anti_rollback_passes PASSED                                                                              [ 58%]
tests/test_tamper_simulation.py::TestValidFirmware::test_all_three_checks_pass PASSED                                                                             [ 62%]
tests/test_tamper_simulation.py::TestMITMAttack::test_corrupted_binary_fails_hash_check PASSED                                                                    [ 65%]
tests/test_tamper_simulation.py::TestMITMAttack::test_corrupted_binary_fails_signature_check PASSED                                                               [ 68%]
tests/test_tamper_simulation.py::TestSupplyChainAttack::test_wrong_key_signature_fails_verification PASSED                                                        [ 72%]
tests/test_tamper_simulation.py::TestRollbackAttack::test_rollback_to_older_major_rejected PASSED                                                                 [ 75%]
tests/test_tamper_simulation.py::TestRollbackAttack::test_rollback_to_older_minor_rejected PASSED                                                                 [ 79%]
tests/test_tamper_simulation.py::TestRollbackAttack::test_rollback_to_older_patch_rejected PASSED                                                                 [ 82%]
tests/test_tamper_simulation.py::TestRollbackAttack::test_valid_sig_does_not_bypass_rollback PASSED                                                               [ 86%]
tests/test_tamper_simulation.py::TestFakeSignature::test_random_bytes_signature_rejected PASSED                                                                   [ 89%]
tests/test_tamper_simulation.py::TestFakeSignature::test_zero_bytes_signature_rejected PASSED                                                                     [ 93%]
tests/test_tamper_simulation.py::TestFakeSignature::test_empty_signature_file_rejected PASSED                                                                     [ 96%]
tests/test_tamper_simulation.py::TestFakeSignature::test_truncated_signature_rejected PASSED                                                                      [100%]

========================================================================== 29 passed in 1.58s ==========================================================================


29 passed, 0 failed

---

## Notes

All 15 attack simulation tests passed independently on
Member 2's local machine confirming the tests are not
environment-specific and the security controls work
consistently across different environments.
Commit and push:
