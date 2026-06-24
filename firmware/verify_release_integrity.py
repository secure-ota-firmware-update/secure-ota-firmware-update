import argparse
import hashlib
import json
import os
import sys
import tempfile

import requests


GITHUB_API_BASE = "https://api.github.com"
DEFAULT_REPO = "secure-ota-firmware-update/secure-ota-firmware-update"


def get_release(repo: str, tag: str = None) -> dict:
    """
    Fetch a specific or latest release from GitHub API.

    Args:
        repo: GitHub repo in owner/repo format
        tag: specific tag to fetch, or None for latest

    Returns:
        dict: GitHub release object
    """
    if tag:
        url = f"{GITHUB_API_BASE}/repos/{repo}/releases/tags/{tag}"
    else:
        url = f"{GITHUB_API_BASE}/repos/{repo}/releases/latest"

    response = requests.get(
        url,
        headers={"Accept": "application/vnd.github+json"},
        timeout=10
    )

    if response.status_code == 404:
        print(f"[ERROR] Release not found: {tag or 'latest'}")
        sys.exit(1)

    response.raise_for_status()
    return response.json()


def download_to_temp(url: str, filename: str, temp_dir: str) -> str:
    """
    Download a file from URL into a temp directory.

    Args:
        url: download URL
        filename: local filename to save as
        temp_dir: temp directory path

    Returns:
        str: path to downloaded file
    """
    dest = os.path.join(temp_dir, filename)

    print(f"[*] Downloading: {filename}")
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    size_kb = os.path.getsize(dest) / 1024
    print(f"[+] Downloaded: {filename} ({size_kb:.1f} KB)")
    return dest


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hex digest of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Verify integrity of firmware release assets from GitHub"
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=DEFAULT_REPO,
        help=f"GitHub repo (default: {DEFAULT_REPO})"
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Specific release tag to verify (default: latest)"
    )

    args = parser.parse_args()

    print("=" * 55)
    print("  Firmware Release Integrity Verification Tool")
    print("=" * 55)
    print()

    # Fetch release
    release = get_release(args.repo, args.tag)
    tag_name = release["tag_name"]
    print(f"[+] Verifying release: {tag_name}")
    print(f"[+] Published: {release['published_at']}")
    print()

    # Map asset names to download URLs
    assets = {
        asset["name"]: asset["browser_download_url"]
        for asset in release.get("assets", [])
    }

    required_files = ["manifest.json"]
    for name in required_files:
        if name not in assets:
            print(f"[ERROR] Required asset missing from release: {name}")
            sys.exit(1)

    # Work in a temp directory — clean up automatically
    with tempfile.TemporaryDirectory() as temp_dir:

        # Download manifest first
        manifest_path = download_to_temp(
            assets["manifest.json"], "manifest.json", temp_dir
        )

        with open(manifest_path) as f:
            manifest = json.load(f)

        firmware_filename = manifest["filename"]
        sig_filename = manifest["signature_filename"]

        print()
        print(f"[+] Manifest version: {manifest['version']}")
        print(f"[+] Expected SHA-256: {manifest['sha256']}")
        print()

        # Check firmware and sig are in release
        if firmware_filename not in assets:
            print(f"[ERROR] Firmware not in release assets: {firmware_filename}")
            sys.exit(1)
        if sig_filename not in assets:
            print(f"[ERROR] Signature not in release assets: {sig_filename}")
            sys.exit(1)

        # Download firmware and signature
        firmware_path = download_to_temp(
            assets[firmware_filename], firmware_filename, temp_dir
        )
        sig_path = download_to_temp(
            assets[sig_filename], sig_filename, temp_dir
        )

        print()
        print("[*] Running integrity checks...")
        print()

        all_passed = True

        # Check 1 — firmware non-empty
        fw_size = os.path.getsize(firmware_path)
        if fw_size > 0:
            print(f"[PASS] Firmware binary exists and non-empty ({fw_size} bytes)")
        else:
            print("[FAIL] Firmware binary is empty")
            all_passed = False

        # Check 2 — signature non-empty
        sig_size = os.path.getsize(sig_path)
        if sig_size > 0:
            print(f"[PASS] Signature file exists and non-empty ({sig_size} bytes)")
        else:
            print("[FAIL] Signature file is empty")
            all_passed = False

        # Check 3 — SHA-256 hash match
        actual_hash = compute_sha256(firmware_path)
        if actual_hash == manifest["sha256"]:
            print(f"[PASS] SHA-256 hash matches manifest")
            print(f"       {actual_hash}")
        else:
            print(f"[FAIL] SHA-256 hash MISMATCH — tampering detected")
            print(f"       Expected: {manifest['sha256']}")
            print(f"       Actual:   {actual_hash}")
            all_passed = False

        print()
        if all_passed:
            print("=" * 55)
            print(f"  ALL CHECKS PASSED — Release {tag_name} is VALID")
            print("=" * 55)
        else:
            print("=" * 55)
            print(f"  CHECKS FAILED — Release {tag_name} is INVALID")
            print("=" * 55)
            sys.exit(1)


if __name__ == "__main__":
    main()