"""
agent.py

Simulated IoT Edge Device Verification Agent.

This script simulates the firmware update client running on an IoT device.
It is responsible for:
1. Checking if a new firmware version is available
2. Downloading the firmware binary and signature from GitHub Releases
3. Verifying the SHA-256 hash to detect tampering           (Layer 1)
4. Verifying the ECDSA signature using the stored public key (Layer 2)
5. Checking anti-rollback version requirements               (Layer 3)
6. Installing the firmware if all checks pass
7. Logging a CRITICAL alert and rejecting if any check fails

In a real system this would run as a daemon on the embedded device.
Here we simulate the entire flow in Python.

Usage:
    python edge_agent/agent.py
    python edge_agent/agent.py --manifest-url <URL>
"""

import hashlib
import json
import logging
import logging.handlers
import os
import shutil
import uuid
from datetime import datetime

import requests

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils


# ─────────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────────

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

    # Prevent duplicate handlers if setup_logging is called multiple times
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
        maxBytes=1024 * 1024,
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


# ─────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────

VERSION_STORE_PATH = "edge_agent/version_store.json"
PUBLIC_KEY_PATH = "pki/public_key.pem"
GITHUB_REPO = "secure-ota-firmware-update/secure-ota-firmware-update"
GITHUB_API_BASE = "https://api.github.com"


# ─────────────────────────────────────────────────────────
# Version store helpers
# ─────────────────────────────────────────────────────────

def load_version_store() -> dict:
    """
    Load the version store from disk.

    The version store tracks:
    - current_version: firmware version currently installed on device
    - minimum_version: lowest version allowed (anti-rollback protection)
    - install_history: log of all previous installs

    Returns:
        dict: version store contents

    Raises:
        FileNotFoundError: if version_store.json does not exist
    """
    if not os.path.exists(VERSION_STORE_PATH):
        logger.error(f"Version store not found: {VERSION_STORE_PATH}")
        raise FileNotFoundError(f"Version store not found: {VERSION_STORE_PATH}")

    with open(VERSION_STORE_PATH, "r") as f:
        data = json.load(f)

    logger.info(f"Version store loaded — current version: {data.get('current_version')}")
    return data


def save_version_store(data: dict) -> None:
    """
    Save updated version store to disk after successful firmware install.

    Args:
        data: version store dict with updated current_version
    """
    data["last_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(VERSION_STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Version store saved — current version: {data.get('current_version')}")


# ─────────────────────────────────────────────────────────
# Update check
# ─────────────────────────────────────────────────────────

def check_for_update(manifest: dict, version_store: dict) -> bool:
    """
    Compare manifest version against currently installed version.

    Uses integer tuple comparison — NOT string comparison.
    String comparison gives wrong results:
        "1.10.0" < "1.9.0" as strings — WRONG
        (1,10,0) > (1,9,0) as integers — CORRECT

    Args:
        manifest: parsed manifest.json
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


# ─────────────────────────────────────────────────────────
# Download
# ─────────────────────────────────────────────────────────

def _download_from_url(url: str, dest_path: str, max_retries: int = 3) -> None:
    """
    Download a file from a URL and save to disk with retry logic.

    Retries up to max_retries times with exponential backoff
    to handle transient network failures common in IoT deployments.

    Args:
        url: source URL
        dest_path: local path to save file
        max_retries: number of attempts before giving up
    """
    import time

    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Download succeeded on attempt {attempt}/{max_retries}")
            return

        except requests.RequestException as e:
            last_exception = e
            wait_time = 2 ** attempt
            logger.warning(f"Download attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    logger.critical(f"All {max_retries} download attempts failed for: {url}")
    raise last_exception


def download_firmware(
    manifest: dict,
    download_dir: str = "edge_agent/downloads"
) -> tuple:
    """
    Download firmware binary and signature file.

    If GITHUB_RELEASE_BASE_URL env var is set, downloads from GitHub
    Releases via HTTPS. Otherwise falls back to local file copy for
    development and testing without a published release.

    Args:
        manifest: parsed manifest.json containing filename and version
        download_dir: local directory to save downloaded files

    Returns:
        tuple: (firmware_path, signature_path)
    """
    os.makedirs(download_dir, exist_ok=True)

    filename = manifest["filename"]
    sig_filename = manifest["signature_filename"]
    version = manifest["version"]

    dest_firmware = os.path.join(download_dir, filename)
    dest_sig = os.path.join(download_dir, sig_filename)

    release_base_url = os.environ.get("GITHUB_RELEASE_BASE_URL")

    if release_base_url:
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
            raise FileNotFoundError(f"Firmware not found: {source_firmware}")

        if not os.path.exists(source_sig):
            raise FileNotFoundError(f"Signature not found: {source_sig}")

        shutil.copy2(source_firmware, dest_firmware)
        shutil.copy2(source_sig, dest_sig)

    logger.info(f"Firmware downloaded: {dest_firmware}")
    logger.info(f"Signature downloaded: {dest_sig}")

    return dest_firmware, dest_sig


# ─────────────────────────────────────────────────────────
# Layer 1 — SHA-256 hash verification
# ─────────────────────────────────────────────────────────

def verify_hash(firmware_path: str, expected_hash: str) -> bool:
    """
    Recompute SHA-256 hash of downloaded firmware and compare with manifest.

    Detects any byte-level tampering during transit — even a single
    changed bit produces a completely different hash output.

    Args:
        firmware_path: path to downloaded firmware binary
        expected_hash: SHA-256 hex string from manifest.json

    Returns:
        bool: True if hash matches (integrity confirmed)
              False if mismatch, missing file, or empty firmware
    """
    logger.info(f"Verifying SHA-256 hash of: {firmware_path}")
    logger.info(f"Expected hash: {expected_hash}")

    # Check file exists before attempting to read
    if not os.path.exists(firmware_path):
        logger.critical(f"Firmware file not found: {firmware_path}")
        return False

    # Reject empty firmware explicitly — fail closed
    if os.path.getsize(firmware_path) == 0:
        logger.critical("Firmware file is empty — refusing installation")
        return False

    # Read the firmware binary in 8KB chunks rather than all at once.
    # A real IoT device may have limited RAM — chunked reading
    # prevents out-of-memory errors on large firmware files.
    sha256 = hashlib.sha256()
    with open(firmware_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    computed_hash = sha256.hexdigest()
    logger.info(f"Computed hash: {computed_hash}")

    # String comparison of hex digests is safe here —
    # SHA-256 digests are always 64 chars, so == is constant-time.
    if computed_hash == expected_hash:
        logger.info("Hash verification PASSED — firmware integrity confirmed")
        return True
    else:
        # Log both hashes so a security engineer can investigate
        # the discrepancy when reviewing the audit log.
        logger.critical("Hash verification FAILED — tampering detected")
        logger.critical(f"Expected: {expected_hash}")
        logger.critical(f"Computed: {computed_hash}")
        logger.critical("Dropping firmware payload — refusing installation")
        return False


# ─────────────────────────────────────────────────────────
# Layer 2 — ECDSA signature verification
# ─────────────────────────────────────────────────────────

def verify_signature(
    firmware_path: str,
    signature_path: str,
    public_key_path: str
) -> bool:
    """
    Verify the ECDSA signature of the firmware using the stored public key.

    Proves the firmware was signed by the legitimate developer who holds
    the private key. An attacker cannot forge this signature without the
    private key, even if they replace the firmware and recompute a
    matching SHA-256 hash.

    Args:
        firmware_path: path to downloaded firmware binary
        signature_path: path to downloaded .sig file
        public_key_path: path to public key PEM stored on device

    Returns:
        bool: True if signature valid, False if invalid, forged, or files missing
    """
    logger.info(f"Verifying ECDSA signature of: {firmware_path}")

    # Load the public key baked into the device at manufacture.
    # In a real device this would be in ROM or a secure enclave.
    # Here we read it from pki/public_key.pem which simulates that.
    if not os.path.exists(public_key_path):
        logger.critical(f"Public key not found: {public_key_path}")
        return False

    try:
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
    except Exception as e:
        logger.critical(f"Error loading public key: {type(e).__name__}: {e}")
        return False

    # Load the .sig file downloaded alongside the firmware.
    # Contains the DER-encoded ECDSA signature from sign_firmware.py.
    if not os.path.exists(signature_path):
        logger.critical(f"Signature file not found: {signature_path}")
        return False

    try:
        with open(signature_path, "rb") as f:
            signature = f.read()
    except Exception as e:
        logger.critical(f"Error loading signature: {type(e).__name__}: {e}")
        return False

    # Check firmware exists before hashing
    if not os.path.exists(firmware_path):
        logger.critical(f"Firmware file not found: {firmware_path}")
        return False

    # Reject empty firmware — fail closed
    if os.path.getsize(firmware_path) == 0:
        logger.critical("Firmware file is empty — refusing verification")
        return False

    # Recompute SHA-256 hash of the firmware.
    # We use Prehashed because sign_firmware.py signed a pre-computed hash.
    # Both sides must use the same approach for verification to succeed.
    sha256 = hashlib.sha256()
    with open(firmware_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    firmware_hash = sha256.digest()  # raw bytes, not hex string

    try:
        # Core cryptographic operation.
        # The ECDSA math proves that only the private key holder
        # could have produced this signature for this exact hash.
        # An invalid signature raises InvalidSignature immediately.
        public_key.verify(
            signature,
            firmware_hash,
            ec.ECDSA(utils.Prehashed(hashes.SHA256()))
        )
        logger.info("Signature verification PASSED — firmware authenticity confirmed")
        return True

    except InvalidSignature:
        # Catches both:
        # 1. Corrupted binary (hash doesn't match what was signed)
        # 2. Wrong private key (signature mathematically invalid)
        logger.critical("Signature verification FAILED — forged or corrupted signature")
        logger.critical("This firmware was NOT signed by the legitimate private key")
        logger.critical("Dropping firmware payload — refusing installation")
        return False

    except Exception as e:
        # Catches malformed .sig files that fail before ECDSA math —
        # e.g. truncated files, random bytes, wrong DER encoding.
        logger.critical(f"Signature verification error: {type(e).__name__}: {e}")
        return False


# ─────────────────────────────────────────────────────────
# Layer 3 — Anti-rollback version check
# ─────────────────────────────────────────────────────────

def anti_rollback_check(incoming_version: str, minimum_version: str) -> bool:
    """
    Check that incoming firmware version meets minimum version requirement.

    Prevents attackers from forcing installation of older vulnerable firmware
    even if that older firmware has a perfectly valid ECDSA signature.

    Uses integer tuple comparison — NOT string comparison.
    String comparison gives WRONG results:
        "1.10.0" < "1.9.0" as strings — WRONG (lexicographic)
        (1,10,0) > (1,9,0) as integers — CORRECT

    Args:
        incoming_version: version string from manifest e.g. "1.2.0"
        minimum_version: minimum allowed version from version_store e.g. "1.0.0"

    Returns:
        bool: True if incoming >= minimum (safe to install)
              False if incoming < minimum (rollback attempt detected)
    """
    logger.info(
        f"Anti-rollback check: incoming={incoming_version}, "
        f"minimum={minimum_version}"
    )

    def parse_version(version_str: str) -> tuple:
        """Parse semantic version string into tuple of integers."""
        parts = version_str.strip().split(".")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid version format: '{version_str}'. "
                f"Expected X.Y.Z (e.g. 1.2.3)"
            )
        return tuple(int(p) for p in parts)

    try:
        incoming = parse_version(incoming_version)
        minimum = parse_version(minimum_version)
    except ValueError as e:
        logger.critical(f"Anti-rollback check failed — invalid version format: {e}")
        # When in doubt, fail closed — reject the update rather than
        # allowing installation with an uncertain version check.
        return False

    if incoming >= minimum:
        logger.info(
            f"Anti-rollback check PASSED — "
            f"v{incoming_version} >= minimum v{minimum_version}"
        )
        return True
    else:
        logger.critical(
            f"Anti-rollback check FAILED — "
            f"v{incoming_version} < minimum v{minimum_version}"
        )
        logger.critical(
            "Rollback attack detected — refusing to install older vulnerable firmware"
        )
        return False


# ─────────────────────────────────────────────────────────
# Rejection report
# ─────────────────────────────────────────────────────────

def write_rejection_report(
    reason: str,
    manifest: dict,
    firmware_path: str = None,
    details: str = None
) -> None:
    """
    Write a structured JSON rejection report to disk when verification fails.

    Creates a timestamped report file in edge_agent/rejections/ that a
    Security Architect can query for audit purposes.

    In a real IoT system this would be forwarded to a SIEM
    (Security Information and Event Management) system.

    Args:
        reason: short reason code e.g. HASH_MISMATCH, INVALID_SIGNATURE
        manifest: the manifest being processed
        firmware_path: path to the rejected firmware file (optional)
        details: additional context for the rejection (optional)
    """
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

    # Include computed hash if firmware file is available
    if firmware_path and os.path.exists(firmware_path):
        sha256 = hashlib.sha256()
        with open(firmware_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        report["firmware_sha256_computed"] = sha256.hexdigest()
        report["hash_match"] = (
            report["firmware_sha256_computed"] ==
            report["firmware_sha256_in_manifest"]
        )

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"rejection_{timestamp}_{reason}.json"
    filepath = os.path.join(rejections_dir, filename)

    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)

    logger.critical(f"Rejection report written: {filepath}")


# ─────────────────────────────────────────────────────────
# Mock install
# ─────────────────────────────────────────────────────────

def mock_install(manifest: dict, version_store: dict) -> None:
    """
    Simulate firmware installation after all verification checks pass.

    Updates version_store.json with:
    - current_version: the newly installed version
    - minimum_version: raised to installed version (anti-rollback ratchet)
    - install_history: new entry added

    Raising minimum_version to current ensures that once a device installs
    v1.2.0, it can never be downgraded to v1.1.0 or below — even if v1.1.0
    has a valid signature. The minimum only moves forward, never backward.

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

    old_version = version_store["current_version"]
    old_minimum = version_store.get("minimum_version", "0.0.0")

    version_store["current_version"] = version

    # Raise minimum_version to match newly installed version.
    # This is the anti-rollback ratchet — the minimum only moves forward.
    version_store["minimum_version"] = version

    version_store.setdefault("install_history", []).append({
        "version": version,
        "installed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "previous_version": old_version,
        "minimum_version_raised_to": version,
        "status": "success"
    })

    save_version_store(version_store)

    logger.info(f"current_version: {old_version} -> {version}")
    logger.info(f"minimum_version: {old_minimum} -> {version}")
    logger.info(f"Install complete — device now running v{version}")
    logger.info("Initiating mock reboot...")
    logger.info("=" * 50)


# ─────────────────────────────────────────────────────────
# GitHub Releases manifest fetcher
# ─────────────────────────────────────────────────────────

def fetch_manifest_from_release() -> dict:
    """
    Fetch the latest firmware manifest from GitHub Releases.

    Uses GitHub's public API to find the latest release, then
    downloads the manifest.json asset from that release.

    No authentication required for public repositories.

    Returns:
        dict: parsed manifest contents, or None if unavailable
    """
    repo = os.environ.get("GITHUB_REPO", GITHUB_REPO)
    api_url = f"{GITHUB_API_BASE}/repos/{repo}/releases/latest"

    logger.info(f"Fetching latest release from GitHub API: {api_url}")

    try:
        response = requests.get(
            api_url,
            headers={"Accept": "application/vnd.github+json"},
            timeout=10
        )
    except requests.RequestException as e:
        logger.error(f"GitHub API request failed: {e}")
        return None

    if response.status_code == 404:
        logger.error("No releases found on GitHub — falling back to local manifest")
        return None

    response.raise_for_status()
    release = response.json()

    logger.info(f"Found release: {release['tag_name']}")

    manifest_url = None
    for asset in release.get("assets", []):
        if asset["name"] == "manifest.json":
            manifest_url = asset["browser_download_url"]
            break

    if not manifest_url:
        logger.error("manifest.json not found in release assets")
        return None

    logger.info(f"Downloading manifest from: {manifest_url}")
    try:
        manifest_response = requests.get(manifest_url, timeout=10)
        manifest_response.raise_for_status()
        manifest = manifest_response.json()
        logger.info(f"Manifest fetched — firmware version: {manifest['version']}")
        return manifest
    except Exception as e:
        logger.error(f"Failed to download manifest: {e}")
        return None


# ─────────────────────────────────────────────────────────
# Run summary tracker
# ─────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────
# Main flow
# ─────────────────────────────────────────────────────────

def _run_update_check(summary: AgentRunSummary) -> None:
    """
    Internal update check logic with summary tracking.

    Full verification sequence:
    1. Load version store
    2. Fetch manifest (GitHub Releases or local fallback)
    3. Check if update is available
    4. Download firmware and signature
    5. Layer 1: SHA-256 hash verification
    6. Layer 2: ECDSA signature verification
    7. Layer 3: Anti-rollback version check
    8. Install
    """
    # Step 1 — Load version store
    version_store = load_version_store()
    summary.record_pass("Version store loaded")

    # Step 2 — Fetch manifest
    manifest = None
    github_release_base = os.environ.get("GITHUB_RELEASE_BASE_URL")

    if github_release_base:
        logger.info("GITHUB_RELEASE_BASE_URL set — fetching manifest from GitHub Releases")
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
        logger.info(f"Using local manifest — firmware version: {manifest['version']}")

    summary.set_version(manifest["version"])

    # Step 3 — Check for update
    if not check_for_update(manifest, version_store):
        summary.set_outcome("NO UPDATE NEEDED")
        logger.info("No update needed. Agent exiting.")
        return

    summary.record_pass("Update check — update available")

    # Step 4 — Download firmware
    firmware_path, sig_path = download_firmware(manifest)
    summary.record_pass("Firmware and signature downloaded")

    # Step 5 — Layer 1: SHA-256 hash verification
    if not verify_hash(firmware_path, manifest["sha256"]):
        summary.record_fail("SHA-256 hash verification")
        summary.set_outcome("REJECTED — hash mismatch")
        write_rejection_report(
            reason="HASH_MISMATCH",
            manifest=manifest,
            firmware_path=firmware_path,
            details="Downloaded binary hash does not match manifest value"
        )
        logger.critical("SECURITY ALERT — Hash verification failed. Aborting.")
        for path in [firmware_path, sig_path]:
            if os.path.exists(path):
                os.remove(path)
        return

    summary.record_pass("SHA-256 hash verification (Layer 1)")

    # Step 6 — Layer 2: ECDSA signature verification
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
        for path in [firmware_path, sig_path]:
            if os.path.exists(path):
                os.remove(path)
        return

    summary.record_pass("ECDSA signature verification (Layer 2)")
    logger.info("Both hash and signature verified — firmware is authentic")

    # Step 7 — Layer 3: Anti-rollback version check
    minimum_version = version_store.get("minimum_version", "0.0.0")
    incoming_version = manifest["version"]

    if not anti_rollback_check(incoming_version, minimum_version):
        summary.record_fail("Anti-rollback version check")
        summary.set_outcome("REJECTED — rollback attempt detected")
        write_rejection_report(
            reason="ROLLBACK_ATTEMPT",
            manifest=manifest,
            details=(
                f"Incoming version v{incoming_version} is below "
                f"minimum allowed version v{minimum_version}. "
                f"Rollback attack suspected."
            )
        )
        logger.critical("=" * 50)
        logger.critical("SECURITY ALERT")
        logger.critical("Rollback attack detected")
        logger.critical(f"Incoming: v{incoming_version}")
        logger.critical(f"Minimum:  v{minimum_version}")
        logger.critical("Installation refused")
        logger.critical("=" * 50)
        for path in [firmware_path, sig_path]:
            if os.path.exists(path):
                os.remove(path)
        return

    summary.record_pass("Anti-rollback version check (Layer 3)")

    # Step 8 — Install
    summary.set_outcome("INSTALLED")
    mock_install(manifest, version_store)


def main():
    """
    Main entry point for the edge device agent.
    """
    summary = AgentRunSummary()

    logger.info("=" * 55)
    logger.info("Edge Device Agent started")

    # Load configuration
    config = load_config()
    logger.info(
        f"Agent version: {config['agent']['version']}"
    )
    logger.info(
        f"GitHub repo: {config['distribution']['github_repo']}"
    )
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

    # Step 4 — Anti-rollback check
    minimum_version = version_store.get("minimum_version", "0.0.0")
    incoming_version = manifest["version"]

    if not anti_rollback_check(incoming_version, minimum_version):
        summary.record_fail("Anti-rollback version check")
        summary.set_outcome("REJECTED — rollback attempt detected")
        write_rejection_report(
            reason="ROLLBACK_ATTEMPT",
            manifest=manifest,
            details=(
                f"Incoming version v{incoming_version} is below "
                f"minimum allowed version v{minimum_version}. "
                f"Rollback attack suspected."
            )
        )
        logger.critical("=" * 50)
        logger.critical("SECURITY ALERT")
        logger.critical(f"Rollback attack detected")
        logger.critical(f"Incoming: v{incoming_version}")
        logger.critical(f"Minimum:  v{minimum_version}")
        logger.critical("Installation refused")
        logger.critical("=" * 50)
        for path in [firmware_path, sig_path]:
            if os.path.exists(path):
                os.remove(path)
        return

    summary.record_pass("Anti-rollback version check")

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
    
def anti_rollback_check(current_version: str, minimum_version: str) -> bool:
    """
    Compares the incoming firmware version against the allowed minimum version.
    Uses integer-based semantic version comparison to prevent string sorting bugs.
    
    Returns:
        True if current_version >= minimum_version
        False otherwise
    """
    try:
        # Split version strings and convert components to integers
        current_parts = [int(x) for x in current_version.split('.')]
        minimum_parts = [int(x) for x in minimum_version.split('.')]
        
        # Pad with zeros if version strings have mismatching lengths (e.g., '1.0' vs '1.0.0')
        max_len = max(len(current_parts), len(minimum_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        minimum_parts.extend([0] * (max_len - len(minimum_parts)))
        
        # Compare tuple of integers directly
        return current_parts >= minimum_parts
    except (ValueError, AttributeError):
        # If versions are malformed or invalid, reject them safely
        return False

def load_config(config_path: str = "edge_agent/config.json") -> dict:
    """
    Load agent configuration from config.json.

    Falls back to hardcoded defaults if config file is missing.
    This allows the agent to run without a config file in
    development environments.

    Args:
        config_path: path to config.json

    Returns:
        dict: configuration values
    """
    defaults = {
        "agent": {
            "version": "1.0.0",
            "log_level": "INFO"
        },
        "firmware": {
            "public_key_path": "pki/public_key.pem",
            "version_store_path": "edge_agent/version_store.json",
            "downloads_dir": "edge_agent/downloads",
            "rejections_dir": "edge_agent/rejections"
        },
        "distribution": {
            "github_repo": "secure-ota-firmware-update/secure-ota-firmware-update",
            "manifest_filename": "manifest.json",
            "local_manifest_path": "distribution/manifest.json",
            "download_timeout_seconds": 30,
            "max_download_retries": 3
        },
        "security": {
            "delete_on_verification_failure": True,
            "write_rejection_reports": True
        }
    }

    if not os.path.exists(config_path):
        logger.warning(
            f"Config file not found: {config_path} — using defaults"
        )
        return defaults

    with open(config_path, "r") as f:
        config = json.load(f)

    logger.info(f"Configuration loaded from: {config_path}")
    return config




if __name__ == "__main__":
    main()