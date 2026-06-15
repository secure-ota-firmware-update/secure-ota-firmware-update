import hashlib
import json
import os
import subprocess
import sys

import pytest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_VERSION = "9.9.9"  # Use a clearly fake version so it never collides with real releases


def run_command(args: list) -> subprocess.CompletedProcess:
    """
    Run a Python script as a subprocess and return the result.

    Args:
        args: list of command arguments e.g. ["python", "pki/generate_keys.py"]

    Returns:
        subprocess.CompletedProcess with returncode, stdout, stderr
    """
    return subprocess.run(
        args,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )


@pytest.fixture(scope="module")
def pipeline_artifacts():
    """
    Run the full local pipeline once and return paths to all
    generated artifacts. Shared across all tests in this module.
    """
    # Step 1 — Generate keys (only if not already present)
    private_key_path = os.path.join(PROJECT_ROOT, "pki", "private_key.pem")
    public_key_path = os.path.join(PROJECT_ROOT, "pki", "public_key.pem")

    if not os.path.exists(private_key_path):
        result = run_command([sys.executable, "pki/generate_keys.py"])
        assert result.returncode == 0, f"generate_keys.py failed: {result.stderr}"

    # Step 2 — Generate dummy firmware with test version
    result = run_command([
        sys.executable, "firmware/create_dummy_firmware.py",
        "--version", TEST_VERSION,
        "--size", "16"  # small size for fast tests
    ])
    assert result.returncode == 0, f"create_dummy_firmware.py failed: {result.stderr}"

    firmware_path = os.path.join(PROJECT_ROOT, "firmware", f"dummy_firmware_v{TEST_VERSION}.bin")
    assert os.path.exists(firmware_path), "Firmware binary was not created"

    # Step 3 — Sign the firmware
    result = run_command([
        sys.executable, "firmware/sign_firmware.py",
        "--firmware", f"firmware/dummy_firmware_v{TEST_VERSION}.bin",
        "--key", "pki/private_key.pem"
    ])
    assert result.returncode == 0, f"sign_firmware.py failed: {result.stderr}"

    sig_path = os.path.join(PROJECT_ROOT, "firmware", f"dummy_firmware_v{TEST_VERSION}.sig")
    assert os.path.exists(sig_path), "Signature file was not created"

    # Step 4 — Generate manifest
    manifest_path = os.path.join(PROJECT_ROOT, "distribution", f"manifest_test_{TEST_VERSION}.json")
    result = run_command([
        sys.executable, "firmware/generate_manifest.py",
        "--version", TEST_VERSION,
        "--firmware", f"firmware/dummy_firmware_v{TEST_VERSION}.bin",
        "--output", f"distribution/manifest_test_{TEST_VERSION}.json"
    ])
    assert result.returncode == 0, f"generate_manifest.py failed: {result.stderr}"
    assert os.path.exists(manifest_path), "Manifest was not created"

    yield {
        "firmware_path": firmware_path,
        "sig_path": sig_path,
        "manifest_path": manifest_path,
        "public_key_path": public_key_path,
    }

    # Cleanup test artifacts after all tests in this module finish
    for path in [firmware_path, sig_path, manifest_path]:
        if os.path.exists(path):
            os.remove(path)


def test_firmware_binary_exists(pipeline_artifacts):
    """Dummy firmware binary was created on disk."""
    assert os.path.exists(pipeline_artifacts["firmware_path"])
    assert os.path.getsize(pipeline_artifacts["firmware_path"]) > 0


def test_signature_file_exists_and_nonempty(pipeline_artifacts):
    """Signature file was created and is not empty."""
    sig_path = pipeline_artifacts["sig_path"]
    assert os.path.exists(sig_path)
    assert os.path.getsize(sig_path) > 0


def test_manifest_has_all_required_fields(pipeline_artifacts):
    """Manifest contains every field defined in manifest_schema.json."""
    with open(pipeline_artifacts["manifest_path"]) as f:
        manifest = json.load(f)

    required_fields = [
        "version", "filename", "sha256",
        "signature_filename", "released_at",
        "minimum_version", "description"
    ]

    for field in required_fields:
        assert field in manifest, f"Manifest missing required field: {field}"


def test_manifest_sha256_matches_binary(pipeline_artifacts):
    """
    The sha256 field in manifest.json must exactly match the
    actual SHA-256 hash of the firmware binary on disk.

    This is the most important test — if this fails, the edge
    agent's hash verification will always fail for legitimate firmware.
    """
    with open(pipeline_artifacts["manifest_path"]) as f:
        manifest = json.load(f)

    sha256 = hashlib.sha256()
    with open(pipeline_artifacts["firmware_path"], "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    actual_hash = sha256.hexdigest()
    manifest_hash = manifest["sha256"]

    assert actual_hash == manifest_hash, (
        f"Hash mismatch!\n"
        f"Manifest hash: {manifest_hash}\n"
        f"Actual hash:   {actual_hash}"
    )


def test_public_key_exists(pipeline_artifacts):
    """Public key exists and will be available for verification."""
    assert os.path.exists(pipeline_artifacts["public_key_path"])