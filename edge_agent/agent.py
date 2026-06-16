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
import shutil
import requests
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

# constants for GitHub  Releases integration
GITHUB_REPO = "secure-ota-firmware-update/secure-ota-firmware-update"
GITHUB_API_BASE = "https://api.github.com"



def load_version_store() -> dict:
    """
    Load the version store from disk.

    The version store tracks:
    - current_version: firmware version currently installed on device
    - minimum_version: lowest version allowed (anti-rollback protection)

    Returns:
        dict: version store contents

    Raises:
        FileNotFoundError: if version_store.json does not exist
    """
    if not os.path.exists(VERSION_STORE_PATH):
        logger.error(f"Version store not found: {VERSION_STORE_PATH}")
        raise FileNotFoundError(f"Version store not found: {VERSION_STORE_PATH}")

    try:
        with open(VERSION_STORE_PATH, "r") as f:
            data = json.load(f)
        logger.info(f"Version store loaded — current version: {data.get('current_version')}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse version store: {e}")
        raise


def save_version_store(data: dict) -> None:
    """
    Save updated version store to disk after successful firmware install.

    Args:
        data: version store dict with updated current_version
    """
    try:
        with open(VERSION_STORE_PATH, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Version store saved — new version: {data.get('current_version')}")
    except IOError as e:
        logger.error(f"Failed to save version store: {e}")
        raise


def check_for_update(manifest: dict, version_store: dict) -> bool:
    """
    Compare manifest version against currently installed version.

    Splits semantic version strings into integers and compares
    major, minor, patch numerically — not as strings.
    String comparison would make "1.10.0" < "1.9.0" which is wrong.

    Args:
        manifest: parsed manifest.json from S3
        version_store: local version tracking data

    Returns:
        bool: True if update is available, False if already up to date
    """
    incoming = manifest["version"]
    current = version_store["current_version"]

    incoming_parts = [int(x) for x in incoming.split(".")]
    current_parts = [int(x) for x in current.split(".")]

    if incoming_parts > current_parts:
        logger.info(f"Update available: {current} → {incoming}")
        return True
    else:
        logger.info(f"Already up to date: current={current}, manifest={incoming}")
        return False


def download_firmware(manifest: dict, download_dir: str = "edge_agent/downloads") -> tuple:
    """
    Download firmware binary and signature file from GitHub Releases.

    GitHub Release assets are public for public repositories and
    require no authentication. URL pattern:

        https://github.com/<owner>/<repo>/releases/download/<tag>/<filename>

    Each release is tagged as vX.Y.Z matching the manifest version.

    If GITHUB_RELEASE_BASE_URL is not set, falls back to local file
    copy for development and testing without needing a published release.
    """
    os.makedirs(download_dir, exist_ok=True)

    filename = manifest["filename"]
    sig_filename = manifest["signature_filename"]
    version = manifest["version"]

    dest_firmware = os.path.join(download_dir, filename)
    dest_sig = os.path.join(download_dir, sig_filename)

    release_base_url = os.environ.get("GITHUB_RELEASE_BASE_URL")

    if release_base_url:
        # e.g. https://github.com/secure-ota-firmware-update/secure-ota-firmware-update
        tag = f"v{version}"
        firmware_url = f"{release_base_url}/releases/download/{tag}/{filename}"
        sig_url = f"{release_base_url}/releases/download/{tag}/{sig_filename}"

        logger.info(f"Downloading firmware from GitHub Release: {firmware_url}")
        _download_from_url(firmware_url, dest_firmware)

        logger.info(f"Downloading signature from GitHub Release: {sig_url}")
        _download_from_url(sig_url, dest_sig)

    else:
        # Fallback — local file copy for development/testing
        logger.info("GITHUB_RELEASE_BASE_URL not set — using local file fallback")

        source_firmware = os.path.join("firmware", filename)
        source_sig = os.path.join("firmware", sig_filename)

        if not os.path.exists(source_firmware):
            logger.error(f"Firmware source not found: {source_firmware}")
            raise FileNotFoundError(f"Firmware not found: {source_firmware}")

        if not os.path.exists(source_sig):
            logger.error(f"Signature source not found: {source_sig}")
            raise FileNotFoundError(f"Signature not found: {source_sig}")

        shutil.copy2(source_firmware, dest_firmware)
        shutil.copy2(source_sig, dest_sig)

    logger.info(f"Firmware downloaded: {dest_firmware}")
    logger.info(f"Signature downloaded: {dest_sig}")

    return dest_firmware, dest_sig


def _download_from_url(url: str, dest_path: str) -> None:
    """
    Download a file from a URL and save it to disk.

    Uses streaming to handle large firmware files without
    loading the entire response into memory at once.

    Args:
        url: source URL to download from
        dest_path: local path to save the downloaded file

    Raises:
        requests.RequestException: if the request fails or returns
                                    a non-200 status code
    """
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def verify_hash(firmware_path: str, expected_hash: str) -> bool:
    """
    Recompute SHA-256 hash of downloaded firmware and compare with manifest.

    This detects any byte-level tampering that occurred during transit.
    Even a single changed byte produces a completely different hash.

    Reads file in 8KB chunks to handle large firmware files without
    loading the entire binary into memory at once.

    Args:
        firmware_path: path to downloaded firmware binary
        expected_hash: SHA-256 hex string from manifest.json

    Returns:
        bool: True if hash matches (integrity confirmed)
              False if hash mismatch (tampering detected)
    """
    logger.info(f"Verifying SHA-256 hash of: {firmware_path}")
    logger.info(f"Expected hash: {expected_hash}")

    sha256 = hashlib.sha256()

    with open(firmware_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    computed_hash = sha256.hexdigest()
    logger.info(f"Computed hash: {computed_hash}")

    if computed_hash == expected_hash:
        logger.info("Hash verification PASSED — firmware integrity confirmed")
        return True
    else:
        logger.critical("Hash verification FAILED — tampering detected")
        logger.critical(f"Expected: {expected_hash}")
        logger.critical(f"Computed: {computed_hash}")
        logger.critical("Dropping firmware payload — refusing installation")
        return False


def verify_signature(firmware_path: str, signature_path: str, public_key_path: str) -> bool:
    """
    Verify the ECDSA signature of the firmware using the stored public key.

    This proves the firmware was signed by the legitimate developer
    who holds the private key. An attacker cannot forge this signature
    without the private key.

    Args:
        firmware_path: path to downloaded firmware binary
        signature_path: path to signature file
        public_key_path: path to stored ECDSA public key

    Returns:
        bool: True if signature is valid, False if invalid or verification fails
    """
    # TODO: implement in Week 3
    logger.info("Signature verification coming in Week 3")
    return True


def mock_install(manifest: dict, version_store: dict) -> None:
    """
    Simulate firmware installation after all verification checks pass.

    In a real system this would:
    1. Write firmware binary to flash memory
    2. Update bootloader version pointer
    3. Trigger hardware watchdog reboot

    Here we simulate it with log messages and update version_store.json.

    Args:
        manifest: manifest dict containing version to install
        version_store: current version store to update
    """
    version = manifest["version"]

    logger.info("=" * 50)
    logger.info(f"INSTALLING firmware v{version}")
    logger.info("Step 1/4 — Verifying install conditions")
    logger.info("Step 2/4 — Writing firmware to flash memory (simulated)")
    logger.info("Step 3/4 — Updating bootloader version pointer (simulated)")
    logger.info("Step 4/4 — Updating version store")

    # Update version store
    version_store["current_version"] = version
    version_store["install_history"].append({
        "version": version,
        "installed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "success"
    })
    save_version_store(version_store)

    logger.info(f"Install complete — now running v{version}")
    logger.info("Initiating mock reboot...")
    logger.info("=" * 50)


def fetch_manifest_from_release() -> dict:
    """
    Fetch the latest firmware manifest from GitHub Releases.

    Uses GitHub's public API to find the latest release, then
    downloads the manifest.json asset from that release.
    """
    import json as json_module

    repo = os.environ.get("GITHUB_REPO", GITHUB_REPO)
    api_url = f"{GITHUB_API_BASE}/repos/{repo}/releases/latest"

    logger.info(f"Fetching latest release from GitHub API: {api_url}")

    response = requests.get(
        api_url,
        headers={"Accept": "application/vnd.github+json"},
        timeout=10
    )

    if response.status_code == 404:
        logger.error("No releases found on GitHub — falling back to local manifest")
        return None

    response.raise_for_status()
    release = response.json()

    logger.info(f"Found release: {release['tag_name']}")

    # Find manifest.json in release assets
    manifest_url = None
    for asset in release.get("assets", []):
        if asset["name"] == "manifest.json":
            manifest_url = asset["browser_download_url"]
            break

    if not manifest_url:
        logger.error("manifest.json not found in release assets")
        return None

    logger.info(f"Downloading manifest from: {manifest_url}")
    manifest_response = requests.get(manifest_url, timeout=10)
    manifest_response.raise_for_status()

    manifest = manifest_response.json()
    logger.info(f"Manifest fetched — firmware version: {manifest['version']}")

    return manifest


def main():
    """
    Main entry point for the edge device agent.

    Orchestrates the full firmware update flow:
    load version store -> fetch manifest -> check for update ->
    download -> verify hash -> verify signature (Week 3) ->
    anti-rollback check (Week 4) -> install or reject

    All exceptions are caught here so the agent never crashes
    with an unhandled traceback — every failure path logs a
    clean CRITICAL message and exits gracefully, simulating
    a real embedded device that must never hard-crash.
    """
    logger.info("=" * 50)
    logger.info("Edge Device Agent started")
    logger.info("=" * 50)

    try:
        _run_update_check()
    except FileNotFoundError as e:
        logger.critical(f"Required file missing: {e}")
        logger.critical("Agent halted — manual intervention required")
    except Exception as e:
        logger.critical(f"Unexpected error: {type(e).__name__}: {e}")
        logger.critical("Agent halted to prevent unsafe state")
    finally:
        logger.info("Agent run finished")
        logger.info("=" * 50)


def _run_update_check():
    """
    Internal function containing the actual update check logic.

    Tries to fetch manifest from GitHub Releases first.
    Falls back to local manifest.json if GitHub API unavailable.
    """
    # Load version store
    version_store = load_version_store()

    # Try GitHub Releases first, fall back to local manifest
    manifest = None

    github_release_base = os.environ.get("GITHUB_RELEASE_BASE_URL")
    if github_release_base:
        logger.info("GITHUB_RELEASE_BASE_URL set — fetching manifest from GitHub Releases")
        manifest = fetch_manifest_from_release()

    if manifest is None:
        # Fallback to local manifest
        manifest_path = "distribution/manifest.json"
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        logger.info(f"Using local manifest — firmware version: {manifest['version']}")

    # Check for update
    if not check_for_update(manifest, version_store):
        logger.info("No update needed. Agent exiting.")
        return

    # Download firmware
    firmware_path, sig_path = download_firmware(manifest)

    # Verify hash
    if not verify_hash(firmware_path, manifest["sha256"]):
        logger.critical("SECURITY ALERT — Hash verification failed. Aborting.")
        return

    logger.info("Hash verification passed")
    logger.info("Signature verification coming in Week 3")



if __name__ == "__main__":
    main()
