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
import logging.handlers
import shutil
import requests
from datetime import datetime


def setup_logging() -> logging.Logger:
    """
    Configure structured logging with console output and
    rotating file handler.

    Log rotation keeps the last 5 log files, each max 1MB.
    This prevents the log file growing indefinitely on a
    real IoT device with limited storage.

    Returns:
        logging.Logger: configured logger instance
    """
    log_dir = "edge_agent"
    log_file = os.path.join(log_dir, "agent.log")

    logger = logging.getLogger("edge_agent")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if setup_logging called multiple times
    if logger.handlers:
        return logger

    # Console handler — INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)

    # Rotating file handler — DEBUG and above
    # Keeps 5 backup files, each max 1MB
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ"
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()


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
        logger.info(f"Update available: {current} -> {incoming}")
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
    without the private key, even if they replace the firmware and
    recompute a matching SHA-256 hash.

    Args:
        firmware_path: path to downloaded firmware binary
        signature_path: path to downloaded .sig file
        public_key_path: path to public key PEM file stored on device

    Returns:
        bool: True if signature is valid, False if invalid or forged
    """
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec, utils
    from cryptography.exceptions import InvalidSignature

    logger.info(f"Verifying ECDSA signature of: {firmware_path}")

    # Load public key
    if not os.path.exists(public_key_path):
        logger.critical(f"Public key not found: {public_key_path}")
        return False

    with open(public_key_path, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    # Load signature
    if not os.path.exists(signature_path):
        logger.critical(f"Signature file not found: {signature_path}")
        return False

    with open(signature_path, "rb") as f:
        signature = f.read()

    # Recompute SHA-256 hash of firmware (same as verify_hash does)
    sha256 = hashlib.sha256()
    with open(firmware_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    firmware_hash = sha256.digest()

    # Verify signature against the hash using the public key
    try:
        public_key.verify(
            signature,
            firmware_hash,
            ec.ECDSA(utils.Prehashed(hashes.SHA256()))
        )
        logger.info("Signature verification PASSED — firmware authenticity confirmed")
        return True

    except InvalidSignature:
        logger.critical("Signature verification FAILED — forged or corrupted signature")
        logger.critical("This firmware was NOT signed by the legitimate private key")
        logger.critical("Dropping firmware payload — refusing installation")
        return False

    except Exception as e:
        logger.critical(f"Signature verification error: {type(e).__name__}: {e}")
        return False


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


class AgentRunSummary:
    """
    Tracks and reports the outcome of a single agent run.

    Provides a clean summary log entry at the end of each run
    for easy audit trail review by a Security Architect.
    """

    def __init__(self):
        self.start_time = datetime.utcnow()
        self.steps_passed = []
        self.steps_failed = []
        self.firmware_version = None
        self.outcome = "UNKNOWN"

    def record_pass(self, step: str):
        self.steps_passed.append(step)

    def record_fail(self, step: str):
        self.steps_failed.append(step)

    def set_version(self, version: str):
        self.firmware_version = version

    def set_outcome(self, outcome: str):
        self.outcome = outcome

    def log_summary(self):
        duration = (datetime.utcnow() - self.start_time).total_seconds()

        logger.info("=" * 55)
        logger.info("AGENT RUN SUMMARY")
        logger.info("=" * 55)
        logger.info(f"Outcome:          {self.outcome}")
        logger.info(f"Firmware version: {self.firmware_version or 'N/A'}")
        logger.info(f"Duration:         {duration:.2f} seconds")
        logger.info(f"Steps passed:     {len(self.steps_passed)}")

        for step in self.steps_passed:
            logger.info(f"  [PASS] {step}")

        if self.steps_failed:
            logger.warning(f"Steps failed:     {len(self.steps_failed)}")
            for step in self.steps_failed:
                logger.warning(f"  [FAIL] {step}")

        logger.info("=" * 55)


def main():
    """
    Main entry point for the edge device agent.
    """
    summary = AgentRunSummary()

    logger.info("=" * 55)
    logger.info("Edge Device Agent started")
    logger.info("=" * 55)

    try:
        _run_update_check(summary)
    except FileNotFoundError as e:
        summary.record_fail("File system check")
        summary.set_outcome("HALTED — missing file")
        logger.critical(f"Required file missing: {e}")
    except Exception as e:
        summary.record_fail("Unexpected error")
        summary.set_outcome("HALTED — unexpected error")
        logger.critical(f"Unexpected error: {type(e).__name__}: {e}")
    finally:
        summary.log_summary()



def _run_update_check(summary: AgentRunSummary):
    """
    Internal update check logic with summary tracking.
    """
    # Load version store
    version_store = load_version_store()
    summary.record_pass("Version store loaded")

    # Load manifest
    manifest = None
    github_release_base = os.environ.get("GITHUB_RELEASE_BASE_URL")

    if github_release_base:
        manifest = fetch_manifest_from_release()
        if manifest:
            summary.record_pass("Manifest fetched from GitHub Releases")

    if manifest is None:
        manifest_path = "distribution/manifest.json"
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        summary.record_pass("Manifest loaded from local file")

    summary.set_version(manifest["version"])

    # Check for update
    if not check_for_update(manifest, version_store):
        summary.set_outcome("NO UPDATE NEEDED")
        logger.info("No update needed. Agent exiting.")
        return

    summary.record_pass("Update check — update available")

    # Download firmware
    firmware_path, sig_path = download_firmware(manifest)
    summary.record_pass("Firmware downloaded")

    # Verify hash
    if not verify_hash(firmware_path, manifest["sha256"]):
        summary.record_fail("SHA-256 hash verification")
        summary.set_outcome("REJECTED — hash mismatch")
        write_rejection_report(
            reason="HASH_MISMATCH",
            manifest=manifest,
            firmware_path=firmware_path,
            details=f"Downloaded binary hash does not match manifest value"
        )
        logger.critical("SECURITY ALERT — Hash verification failed. Aborting.")
        for path in [firmware_path, sig_path]:
            if os.path.exists(path):
                os.remove(path)
        return

    # Step 3 — Verify ECDSA signature
    if not verify_signature(firmware_path, sig_path, PUBLIC_KEY_PATH):
        summary.record_fail("ECDSA signature verification")
        summary.set_outcome("REJECTED — invalid or forged signature")
        write_rejection_report(
            reason="INVALID_SIGNATURE",
            manifest=manifest,
            firmware_path=firmware_path,
            details="ECDSA signature does not match public key stored on device"
        )
        logger.critical("=" * 50)
        logger.critical("SECURITY ALERT")
        logger.critical("Signature verification FAILED")
        logger.critical("Firmware was NOT signed by the legitimate key")
        logger.critical("Payload dropped — installation refused")
        logger.critical("=" * 50)

        # Clean up downloaded files
        for path in [firmware_path, sig_path]:
            if os.path.exists(path):
                os.remove(path)
        return

    summary.record_pass("ECDSA signature verification")
    logger.info("Both hash and signature verified — firmware is authentic")

    # Step 4 — Anti-rollback check (Week 4)
    # Placeholder until Week 4 implementation
    logger.info("Anti-rollback check — coming in Week 4")

    # Step 5 — Install
    summary.set_outcome("INSTALLED")
    mock_install(manifest, version_store)
    

def write_rejection_report(
    reason: str,
    manifest: dict,
    firmware_path: str = None,
    details: str = None
) -> None:
    """
    Write a structured JSON rejection report to disk when
    firmware verification fails.
 
    Creates a timestamped report file in edge_agent/rejections/
    that a Security Architect can query for audit purposes.
 
    In a real IoT system this would be sent to a central SIEM
    (Security Information and Event Management) system.
 
    Args:
        reason: short reason code e.g. HASH_MISMATCH, INVALID_SIGNATURE
        manifest: the manifest that was being processed
        firmware_path: path to the rejected firmware file
        details: additional context for the rejection
    """
    import uuid
 
    rejections_dir = "edge_agent/rejections"
    os.makedirs(rejections_dir, exist_ok=True)
 
    report = {
        "report_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "severity": "CRITICAL",
        "reason": reason,
        "firmware_version": manifest.get("version", "unknown"),
        "firmware_filename": manifest.get("filename", "unknown"),
        "firmware_sha256_in_manifest": manifest.get("sha256", "unknown"),
        "details": details or "No additional details",
        "action_taken": "Firmware payload dropped. Installation refused.",
        "device_info": {
            "public_key_path": PUBLIC_KEY_PATH,
            "version_store_path": VERSION_STORE_PATH,
            "agent_version": "1.0.0"
        }
    }
 
    # Include computed hash if firmware path is available
    if firmware_path and os.path.exists(firmware_path):
        sha256 = hashlib.sha256()
        with open(firmware_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        report["firmware_sha256_computed"] = sha256.hexdigest()
        report["hash_match"] = (
            report["firmware_sha256_computed"] == report["firmware_sha256_in_manifest"]
        )
 
    # Save with timestamped filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"rejection_{timestamp}_{reason}.json"
    filepath = os.path.join(rejections_dir, filename)
 
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)
 
    logger.critical(f"Rejection report written: {filepath}")

if __name__ == "__main__":
    main()
