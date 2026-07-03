
"""
test_tamper_simulation.py

Five comprehensive attack simulation tests for the Secure OTA
Firmware Update pipeline.

These tests simulate real-world attack scenarios described in
docs/THREAT_MODEL.md and prove that the edge agent correctly
detects and rejects all of them.

Test mapping to threats:
    Test 1 — Valid firmware           → Baseline (no attack)
    Test 2 — Corrupted binary         → Threat 2 (MITM Attack)
    Test 3 — Wrong key signature      → Threat 1 (Supply Chain Attack)
    Test 4 — Rollback attempt         → Threat 3 (Rollback Attack)
    Test 5 — Completely fake .sig     → Threat 1 (Key Compromise / Forged Sig)

Usage:
    python -m pytest tests/test_tamper_simulation.py -v
    python -m pytest tests/ -v  (runs all 19 tests)
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from edge_agent.agent import (
    verify_hash,
    verify_signature,
    anti_rollback_check,
)


# ─────────────────────────────────────────────
# Shared test fixtures
# ─────────────────────────────────────────────

@pytest.fixture(scope="module")
def signed_firmware():
    """
    Generate a real signed firmware set for use across all 5 tests.

    Creates:
    - A fresh dummy firmware binary (version 8.8.8 to avoid collisions)
    - A valid ECDSA signature from the project's private key
    - A valid manifest.json with correct sha256

    Yields a dict with paths to all generated artifacts.
    Cleans up all generated files after the module finishes.
    """
    import subprocess

    version = "8.8.8"
    firmware_path = os.path.join(PROJECT_ROOT, "firmware", f"dummy_firmware_v{version}.bin")
    sig_path = os.path.join(PROJECT_ROOT, "firmware", f"dummy_firmware_v{version}.sig")
    manifest_path = os.path.join(PROJECT_ROOT, "distribution", f"manifest_attack_test_{version}.json")
    private_key_path = os.path.join(PROJECT_ROOT, "pki", "private_key.pem")
    public_key_path = os.path.join(PROJECT_ROOT, "pki", "public_key.pem")

    # Step 1 — Generate dummy firmware binary
    result = subprocess.run(
        [sys.executable, "firmware/create_dummy_firmware.py",
         "--version", version, "--size", "16"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"create_dummy_firmware.py failed: {result.stderr}"
    assert os.path.exists(firmware_path), "Firmware binary not created"

    # Step 2 — Sign the firmware
    result = subprocess.run(
        [sys.executable, "firmware/sign_firmware.py",
         "--firmware", f"firmware/dummy_firmware_v{version}.bin",
         "--key", "pki/private_key.pem"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"sign_firmware.py failed: {result.stderr}"
    assert os.path.exists(sig_path), "Signature file not created"

    # Step 3 — Generate manifest
    result = subprocess.run(
        [sys.executable, "firmware/generate_manifest.py",
         "--version", version,
         "--firmware", f"firmware/dummy_firmware_v{version}.bin",
         "--output", f"distribution/manifest_attack_test_{version}.json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"generate_manifest.py failed: {result.stderr}"
    assert os.path.exists(manifest_path), "Manifest not created"

    with open(manifest_path) as f:
        manifest = json.load(f)

    yield {
        "firmware_path": firmware_path,
        "sig_path": sig_path,
        "manifest_path": manifest_path,
        "manifest": manifest,
        "public_key_path": public_key_path,
        "private_key_path": private_key_path,
        "version": version,
    }

    # Cleanup
    for path in [firmware_path, sig_path, manifest_path]:
        if os.path.exists(path):
            os.remove(path)


# ─────────────────────────────────────────────
# Test 1 — Valid Firmware (Baseline)
# ─────────────────────────────────────────────

class TestValidFirmware:
    """
    Test 1 — Normal operation baseline.

    Scenario: Legitimate firmware signed with the correct private key.
    All three verification checks must PASS.
    This confirms the system works correctly before testing attacks.
    """

    def test_hash_verification_passes(self, signed_firmware):
        """SHA-256 hash of valid firmware matches manifest."""
        result = verify_hash(
            signed_firmware["firmware_path"],
            signed_firmware["manifest"]["sha256"]
        )
        assert result is True, "Valid firmware hash should pass"

    def test_signature_verification_passes(self, signed_firmware):
        """ECDSA signature of valid firmware verifies against public key."""
        result = verify_signature(
            signed_firmware["firmware_path"],
            signed_firmware["sig_path"],
            signed_firmware["public_key_path"]
        )
        assert result is True, "Valid firmware signature should pass"

    def test_anti_rollback_passes(self, signed_firmware):
        """Version 8.8.8 satisfies minimum version 1.0.0."""
        result = anti_rollback_check(
            signed_firmware["version"],
            "1.0.0"
        )
        assert result is True, "Valid version should pass anti-rollback"

    def test_all_three_checks_pass(self, signed_firmware):
        """All three security checks pass for valid firmware."""
        hash_ok = verify_hash(
            signed_firmware["firmware_path"],
            signed_firmware["manifest"]["sha256"]
        )
        sig_ok = verify_signature(
            signed_firmware["firmware_path"],
            signed_firmware["sig_path"],
            signed_firmware["public_key_path"]
        )
        rollback_ok = anti_rollback_check(
            signed_firmware["version"],
            "1.0.0"
        )
        assert hash_ok and sig_ok and rollback_ok, (
            f"All checks should pass: hash={hash_ok}, sig={sig_ok}, rollback={rollback_ok}"
        )


# ─────────────────────────────────────────────
# Test 2 — MITM Attack (Corrupted Binary)
# ─────────────────────────────────────────────

class TestMITMAttack:
    """
    Test 2 — Man-in-the-Middle attack simulation.

    Scenario: Attacker intercepts the firmware download and modifies
    the binary. The signature file is unchanged (attacker cannot
    forge it without the private key).

    Expected: Hash check FAILS. Agent rejects firmware.
    Maps to: Threat 2 in THREAT_MODEL.md
    """

    def test_corrupted_binary_fails_hash_check(self, signed_firmware):
        """Even a 1-byte corruption in the binary is caught by SHA-256."""
        with tempfile.NamedTemporaryFile(
            suffix=".bin", delete=False
        ) as tmp:
            corrupted_path = tmp.name

        try:
            shutil.copy2(signed_firmware["firmware_path"], corrupted_path)

            # Flip a single byte at position 50
            with open(corrupted_path, "r+b") as f:
                f.seek(50)
                original_byte = f.read(1)
                f.seek(50)
                f.write(bytes([(original_byte[0] + 1) % 256]))

            result = verify_hash(
                corrupted_path,
                signed_firmware["manifest"]["sha256"]
            )
            assert result is False, (
                "Corrupted binary should fail hash verification"
            )
        finally:
            if os.path.exists(corrupted_path):
                os.remove(corrupted_path)

    def test_corrupted_binary_fails_signature_check(self, signed_firmware):
        """A corrupted binary also fails signature verification."""
        with tempfile.NamedTemporaryFile(
            suffix=".bin", delete=False
        ) as tmp:
            corrupted_path = tmp.name

        try:
            shutil.copy2(signed_firmware["firmware_path"], corrupted_path)

            with open(corrupted_path, "r+b") as f:
                f.seek(100)
                f.write(bytes([0xDE, 0xAD, 0xC0, 0xDE]))

            result = verify_signature(
                corrupted_path,
                signed_firmware["sig_path"],
                signed_firmware["public_key_path"]
            )
            assert result is False, (
                "Corrupted binary should fail signature verification"
            )
        finally:
            if os.path.exists(corrupted_path):
                os.remove(corrupted_path)


# ─────────────────────────────────────────────
# Test 3 — Supply Chain Attack (Wrong Key)
# ─────────────────────────────────────────────

class TestSupplyChainAttack:
    """
    Test 3 — Supply Chain Attack simulation.

    Scenario: Attacker generates their own ECDSA key pair and signs
    the firmware with their private key. They replace the legitimate
    .sig file with their own. The firmware binary is unchanged.

    Expected: Hash check PASSES (binary is unmodified).
              Signature check FAILS (wrong key used).
    Maps to: Threat 1 in THREAT_MODEL.md
    """

    def test_wrong_key_signature_fails_verification(self, signed_firmware):
        """Signature from attacker key fails verification against embedded public key."""
        from cryptography.hazmat.primitives.asymmetric import ec, utils
        from cryptography.hazmat.primitives import hashes, serialization

        # Generate attacker key pair
        attacker_key = ec.generate_private_key(ec.SECP256R1())

        # Sign the firmware with attacker's key
        sha256 = hashlib.sha256()
        with open(signed_firmware["firmware_path"], "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        firmware_hash = sha256.digest()

        attacker_sig = attacker_key.sign(
            firmware_hash,
            ec.ECDSA(utils.Prehashed(hashes.SHA256()))
        )

        with tempfile.NamedTemporaryFile(
            suffix=".sig", delete=False
        ) as tmp:
            attacker_sig_path = tmp.name
            tmp.write(attacker_sig)

        try:
            # Hash check should PASS (binary unchanged)
            hash_result = verify_hash(
                signed_firmware["firmware_path"],
                signed_firmware["manifest"]["sha256"]
            )
            assert hash_result is True, "Hash should pass — binary unchanged"

            # Signature check should FAIL (wrong key)
            sig_result = verify_signature(
                signed_firmware["firmware_path"],
                attacker_sig_path,
                signed_firmware["public_key_path"]
            )
            assert sig_result is False, (
                "Attacker signature should be rejected by embedded public key"
            )
        finally:
            if os.path.exists(attacker_sig_path):
                os.remove(attacker_sig_path)


# ─────────────────────────────────────────────
# Test 4 — Rollback Attack
# ─────────────────────────────────────────────

class TestRollbackAttack:
    """
    Test 4 — Rollback Attack simulation.

    Scenario: Attacker attempts to install an older firmware version
    that contains known vulnerabilities. The older firmware has a
    valid signature (it was legitimately signed in the past).

    Expected: Hash check PASSES. Signature check PASSES.
              Anti-rollback check FAILS.
    Maps to: Threat 3 in THREAT_MODEL.md
    """

    def test_rollback_to_older_major_rejected(self, signed_firmware):
        """Attempt to install v0.1.0 when minimum is v1.0.0 is rejected."""
        result = anti_rollback_check("0.1.0", "1.0.0")
        assert result is False, (
            "Rollback to older major version should be rejected"
        )

    def test_rollback_to_older_minor_rejected(self, signed_firmware):
        """Attempt to install v1.0.0 when minimum is v1.1.0 is rejected."""
        result = anti_rollback_check("1.0.0", "1.1.0")
        assert result is False, (
            "Rollback to older minor version should be rejected"
        )

    def test_rollback_to_older_patch_rejected(self, signed_firmware):
        """Attempt to install v1.1.0 when minimum is v1.1.1 is rejected."""
        result = anti_rollback_check("1.1.0", "1.1.1")
        assert result is False, (
            "Rollback to older patch version should be rejected"
        )

    def test_valid_sig_does_not_bypass_rollback(self, signed_firmware):
        """
        A legitimate signature does NOT bypass anti-rollback.
        Even if hash and sig PASS, rollback check must still FAIL.
        This is the key property that makes anti-rollback meaningful.
        """
        # Hash and sig both pass for legitimate old firmware
        hash_ok = verify_hash(
            signed_firmware["firmware_path"],
            signed_firmware["manifest"]["sha256"]
        )
        sig_ok = verify_signature(
            signed_firmware["firmware_path"],
            signed_firmware["sig_path"],
            signed_firmware["public_key_path"]
        )

        # But rollback check fails because version is too old
        # Simulate: current minimum is 99.0.0, incoming is 8.8.8
        rollback_ok = anti_rollback_check("8.8.8", "99.0.0")

        assert hash_ok is True, "Hash should pass"
        assert sig_ok is True, "Signature should pass"
        assert rollback_ok is False, (
            "Rollback should fail independently of hash and sig"
        )


# ─────────────────────────────────────────────
# Test 5 — Completely Fake Signature
# ─────────────────────────────────────────────

class TestFakeSignature:
    """
    Test 5 — Completely forged signature simulation.

    Scenario: Attacker has no private key at all. They attempt to
    create a signature file by generating random bytes, hoping the
    verification will fail gracefully rather than crash.

    Expected: Agent handles gracefully — returns False, no crash.
    Maps to: Threat 1 (Key Compromise) and Threat 4 in THREAT_MODEL.md
    """

    def test_random_bytes_signature_rejected(self, signed_firmware):
        """70 bytes of 0xAA is rejected without crashing."""
        with tempfile.NamedTemporaryFile(
            suffix=".sig", delete=False
        ) as tmp:
            fake_sig_path = tmp.name
            tmp.write(bytes([0xAA] * 70))

        try:
            result = verify_signature(
                signed_firmware["firmware_path"],
                fake_sig_path,
                signed_firmware["public_key_path"]
            )
            assert result is False, "Random bytes should be rejected"
        finally:
            if os.path.exists(fake_sig_path):
                os.remove(fake_sig_path)

    def test_zero_bytes_signature_rejected(self, signed_firmware):
        """All-zero bytes signature is rejected without crashing."""
        with tempfile.NamedTemporaryFile(
            suffix=".sig", delete=False
        ) as tmp:
            fake_sig_path = tmp.name
            tmp.write(bytes(70))

        try:
            result = verify_signature(
                signed_firmware["firmware_path"],
                fake_sig_path,
                signed_firmware["public_key_path"]
            )
            assert result is False, "Zero bytes should be rejected"
        finally:
            if os.path.exists(fake_sig_path):
                os.remove(fake_sig_path)

    def test_empty_signature_file_rejected(self, signed_firmware):
        """Empty .sig file is rejected without crashing."""
        with tempfile.NamedTemporaryFile(
            suffix=".sig", delete=False
        ) as tmp:
            fake_sig_path = tmp.name
            # Write nothing — empty file

        try:
            result = verify_signature(
                signed_firmware["firmware_path"],
                fake_sig_path,
                signed_firmware["public_key_path"]
            )
            assert result is False, "Empty signature file should be rejected"
        finally:
            if os.path.exists(fake_sig_path):
                os.remove(fake_sig_path)

    def test_truncated_signature_rejected(self, signed_firmware):
        """Truncated real signature (first 10 bytes only) is rejected."""
        with open(signed_firmware["sig_path"], "rb") as f:
            full_sig = f.read()

        truncated_sig = full_sig[:10]

        with tempfile.NamedTemporaryFile(
            suffix=".sig", delete=False
        ) as tmp:
            fake_sig_path = tmp.name
            tmp.write(truncated_sig)

        try:
            result = verify_signature(
                signed_firmware["firmware_path"],
                fake_sig_path,
                signed_firmware["public_key_path"]
            )
            assert result is False, "Truncated signature should be rejected"
        finally:
            if os.path.exists(fake_sig_path):

                os.remove(fake_sig_path)


                os.remove(fake_sig_path)

                


