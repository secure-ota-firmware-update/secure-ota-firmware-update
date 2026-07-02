"""
test_edge_cases.py

Edge case tests for the Secure OTA Firmware Update agent.
"""

import os, sys, tempfile, pytest, hashlib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from edge_agent.agent import verify_hash, verify_signature, anti_rollback_check

# ─────────────────────────────────────────────
# Missing File Tests
# ─────────────────────────────────────────────
class TestMissingFiles:
    def test_verify_hash_missing_firmware(self):
        result = verify_hash("/nonexistent/path/firmware.bin", "a" * 64)
        assert result is False

    def test_verify_signature_missing_firmware(self):
        with tempfile.NamedTemporaryFile(suffix=".sig", delete=False) as tmp:
            tmp.write(b"fake")
            sig_path = tmp.name
        try:
            result = verify_signature("/nonexistent/firmware.bin", sig_path, "pki/public_key.pem")
            assert result is False
        finally:
            os.remove(sig_path)

    def test_verify_signature_missing_signature(self):
        fw_path = os.path.join(PROJECT_ROOT, "firmware", "dummy_firmware_v1.0.0.bin")
        if not os.path.exists(fw_path):
            pytest.skip("firmware binary not present")
        result = verify_signature(fw_path, "/nonexistent/path/firmware.sig", "pki/public_key.pem")
        assert result is False

    def test_verify_signature_missing_public_key(self):
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as fw, \
             tempfile.NamedTemporaryFile(suffix=".sig", delete=False) as sig:
            fw.write(b"x" * 1024)
            fw_path, sig_path = fw.name, sig.name
        try:
            result = verify_signature(fw_path, sig_path, "/nonexistent/public_key.pem")
            assert result is False
        finally:
            os.remove(fw_path); os.remove(sig_path)

# ─────────────────────────────────────────────
# Malformed Version Tests
# ─────────────────────────────────────────────
class TestMalformedVersions:
    def test_missing_patch_version(self): assert anti_rollback_check("1.0", "1.0.0") is False
    def test_empty_version_string(self): assert anti_rollback_check("", "1.0.0") is False
    def test_non_numeric_version(self): assert anti_rollback_check("1.a.0", "1.0.0") is False
    def test_extra_version_parts(self): assert anti_rollback_check("1.0.0.0", "1.0.0") is False
    def test_valid_zero_version(self): assert anti_rollback_check("0.0.0", "1.0.0") is False
    def test_large_version_numbers(self): assert anti_rollback_check("999.999.999", "1.0.0") is True

# ─────────────────────────────────────────────
# Hash Edge Cases
# ─────────────────────────────────────────────
class TestHashEdgeCases:
    def test_empty_firmware_file(self):
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
            empty_path = tmp.name
        try:
            result = verify_hash(empty_path, "a" * 64)
            assert result is False
            empty_sha256 = hashlib.sha256(b"").hexdigest()
            assert verify_hash(empty_path, empty_sha256) is False
        finally:
            os.remove(empty_path)

    def test_wrong_hash_length(self):
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
            tmp.write(b"test firmware content")
            fw_path = tmp.name
        try:
            assert verify_hash(fw_path, "tooshort") is False
            assert verify_hash(fw_path, "a" * 128) is False
        finally:
            os.remove(fw_path)

    def test_correct_hash_of_known_content(self):
        content = b"test firmware content for hash verification"
        expected_hash = hashlib.sha256(content).hexdigest()
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
            tmp.write(content)
            fw_path = tmp.name
        try:
            assert verify_hash(fw_path, expected_hash) is True
        finally:
            os.remove(fw_path)
