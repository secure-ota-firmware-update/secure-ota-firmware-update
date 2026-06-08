
"""
agent.py

Simulated IoT Edge Device Verification Agent.

This script simulates the firmware update client running on an IoT device.
It is responsible for:
1. Checking if a new firmware version is available
2. Downloading the firmware binary and signature from S3
3. Verifying the SHA-256 hash to detect tampering
4. Verifying the ECDSA signature using the stored public key
5. Checking anti-rollback version requirements
6. Installing the firmware if all checks pass
7. Logging a critical alert and rejecting if any check fails

In a real system this would run as a daemon on the embedded device.
Here we simulate the entire flow in Python.

Usage:
    python edge_agent/agent.py
    python edge_agent/agent.py --manifest-url <S3_URL>
    python edge_agent/agent.py --dry-run
"""

import os
import json
import hashlib
import logging
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("edge_agent/agent.log")
    ]
)
logger = logging.getLogger(__name__)


VERSION_STORE_PATH = "edge_agent/version_store.json"
PUBLIC_KEY_PATH = "pki/public_key.pem"


def load_version_store() -> dict:
    """
    Load the version store from disk.

    The version store tracks:
    - current_version: firmware version currently installed on device
    - minimum_version: lowest version allowed (anti-rollback protection)

    Returns:
        dict: version store contents
    """
    # TODO: implement in Week 4
    pass


def save_version_store(data: dict) -> None:
    """
    Save updated version store to disk after successful firmware install.

    Args:
        data: version store dict with updated current_version
    """
    # TODO: implement in Week 4
    pass


def check_for_update(manifest: dict, version_store: dict) -> bool:
    """
    Compare manifest version against currently installed version.

    Args:
        manifest: parsed manifest.json from S3
        version_store: local version tracking data

    Returns:
        bool: True if update is available, False if already up to date
    """
    # TODO: implement in Week 3
    pass


def download_firmware(manifest: dict, download_dir: str = "edge_agent/downloads") -> tuple:
    """
    Download firmware binary and signature file from S3.

    Args:
        manifest: parsed manifest.json containing filename and URLs
        download_dir: local directory to save downloaded files

    Returns:
        tuple: (firmware_path, signature_path) paths to downloaded files
    """
    # TODO: implement in Week 3
    pass


def verify_hash(firmware_path: str, expected_hash: str) -> bool:
    """
    Recompute SHA-256 hash of downloaded firmware and compare with manifest.

    This detects any byte-level tampering that occurred during transit.
    Even a single changed byte produces a completely different hash.

    Args:
        firmware_path: path to downloaded firmware binary
        expected_hash: SHA-256 hex string from manifest.json

    Returns:
        bool: True if hash matches, False if tampered
    """
    # TODO: implement in Week 3
    pass


def verify_signature(firmware_path: str, signature_path: str, public_key_path: str) -> bool:
    """
    Verify the ECDSA signature of the firmware using the stored public key.

    This proves the firmware was signed by the legitimate developer
    who holds the private key. An attacker cannot forge this signature
    without the private key.

    Args:
        firmware_path: path to downloaded firmware binary
        signature_path: path to downloaded .sig file
        public_key_path: path to public key PEM file stored on device

    Returns:
        bool: True if signature valid, False if invalid or forged
    """
    # TODO: implement in Week 3
    pass


def anti_rollback_check(incoming_version: str, minimum_version: str) -> bool:
    """
    Check that incoming firmware version meets minimum version requirement.

    Prevents attackers from forcing installation of older vulnerable firmware
    even if that older firmware has a valid signature.

    Args:
        incoming_version: version string from manifest e.g. "1.2.0"
        minimum_version: minimum allowed version from version_store e.g. "1.0.0"

    Returns:
        bool: True if version is acceptable, False if rollback attempt detected
    """
    # TODO: implement in Week 4
    pass


def mock_install(manifest: dict) -> None:
    """
    Simulate firmware installation after all verification checks pass.

    In a real system this would flash the firmware to device storage
    and trigger a hardware reboot. Here we simulate it with log messages
    and update the version store.

    Args:
        manifest: manifest dict containing version to install
    """
    # TODO: implement in Week 3
    pass


def main():
    """
    Main entry point for the edge device agent.

    Orchestrates the full firmware update flow:
    load version store → fetch manifest → check for update →
    download → verify hash → verify signature →
    anti-rollback check → install or reject
    """
    logger.info("=" * 50)
    logger.info("Edge Device Agent started")
    logger.info("=" * 50)

    # TODO: implement full orchestration in Week 3
    logger.info("Agent skeleton initialized — implementation coming in Week 3")


if __name__ == "__main__":
    main()
