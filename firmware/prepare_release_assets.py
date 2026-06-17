import argparse
import hashlib
import json
import os
import sys


REQUIRED_MANIFEST_FIELDS = [
    "version", "filename", "sha256",
    "signature_filename", "released_at",
    "minimum_version", "description"
]


def verify_file_exists(path: str, description: str) -> bool:
    """
    Verify a file exists and is non-empty.

    Args:
        path: path to the file
        description: human readable name for error messages

    Returns:
        bool: True if file exists and is non-empty
    """
    if not os.path.exists(path):
        print(f"[ERROR] {description} not found: {path}")
        return False

    size = os.path.getsize(path)
    if size == 0:
        print(f"[ERROR] {description} is empty: {path}")
        return False

    print(f"[+] {description}: {path} ({size} bytes)")
    return True


def verify_manifest(manifest_path: str, firmware_path: str) -> bool:
    """
    Verify manifest.json is valid JSON, contains all required fields,
    and that its sha256 field matches the actual firmware binary hash.

    Args:
        manifest_path: path to manifest.json
        firmware_path: path to firmware binary to verify hash against

    Returns:
        bool: True if manifest is valid and hash matches
    """
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Manifest is not valid JSON: {e}")
        return False

    missing_fields = [f for f in REQUIRED_MANIFEST_FIELDS if f not in manifest]
    if missing_fields:
        print(f"[ERROR] Manifest missing required fields: {missing_fields}")
        return False

    print(f"[+] Manifest contains all {len(REQUIRED_MANIFEST_FIELDS)} required fields")

    # Verify sha256 matches actual binary
    sha256 = hashlib.sha256()
    with open(firmware_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    actual_hash = sha256.hexdigest()
    manifest_hash = manifest["sha256"]

    if actual_hash != manifest_hash:
        print(f"[ERROR] SHA-256 mismatch!")
        print(f"[ERROR] Manifest hash: {manifest_hash}")
        print(f"[ERROR] Actual hash:   {actual_hash}")
        return False

    print(f"[+] SHA-256 hash verified: {actual_hash}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Verify firmware release assets before GitHub Release creation"
    )
    parser.add_argument("--firmware", required=True, help="Path to firmware binary")
    parser.add_argument("--signature", required=True, help="Path to signature file")
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")

    args = parser.parse_args()

    print("[*] Verifying release assets before publishing...")
    print()

    checks = [
        verify_file_exists(args.firmware, "Firmware binary"),
        verify_file_exists(args.signature, "Signature file"),
        verify_file_exists(args.manifest, "Manifest"),
    ]

    if all(checks):
        checks.append(verify_manifest(args.manifest, args.firmware))

    print()

    if all(checks):
        print("[+] All release assets verified — ready for GitHub Release")
    else:
        print("[ERROR] One or more checks failed — aborting release")
        sys.exit(1)


if __name__ == "__main__":
    main()