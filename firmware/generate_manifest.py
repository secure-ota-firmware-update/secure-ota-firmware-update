import argparse
import hashlib
import json
import os
import sys
from datetime import datetime


def compute_sha256(filepath: str) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        filepath: path to file

    Returns:
        str: hex string of SHA-256 digest
    """
    sha256 = hashlib.sha256()

    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def generate_manifest(
    version: str,
    firmware_path: str,
    minimum_version: str = "1.0.0",
    description: str = ""
) -> dict:
    """
    Generate the firmware manifest dictionary.

    Args:
        version: semantic version of this firmware e.g. "1.2.0"
        firmware_path: path to firmware binary to compute hash from
        minimum_version: minimum device version to accept update
        description: human readable release notes

    Returns:
        dict: complete manifest matching manifest_schema.json
    """
    if not os.path.exists(firmware_path):
        print(f"[ERROR] Firmware file not found: {firmware_path}")
        sys.exit(1)

    filename = os.path.basename(firmware_path)
    sig_filename = filename.replace(".bin", ".sig")
    sha256_hash = compute_sha256(firmware_path)
    released_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest = {
        "version": version,
        "filename": filename,
        "sha256": sha256_hash,
        "signature_filename": sig_filename,
        "released_at": released_at,
        "minimum_version": minimum_version,
        "description": description or f"Firmware release v{version}"
    }

    return manifest


def save_manifest(manifest: dict, output_path: str) -> None:
    """
    Save manifest dictionary to JSON file.

    Args:
        manifest: manifest dictionary
        output_path: path to save manifest.json
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[+] Manifest saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate OTA firmware update manifest JSON"
    )
    parser.add_argument(
        "--version",
        type=str,
        required=True,
        help="Firmware version e.g. 1.0.0"
    )
    parser.add_argument(
        "--firmware",
        type=str,
        required=True,
        help="Path to firmware binary"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="distribution/manifest.json",
        help="Output path for manifest.json (default: distribution/manifest.json)"
    )
    parser.add_argument(
        "--minimum-version",
        type=str,
        default="1.0.0",
        help="Minimum device version to accept this update (default: 1.0.0)"
    )
    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Release notes for this firmware version"
    )

    args = parser.parse_args()

    print(f"[*] Generating manifest for firmware v{args.version}")
    print(f"[*] Firmware file: {args.firmware}")

    manifest = generate_manifest(
        version=args.version,
        firmware_path=args.firmware,
        minimum_version=args.minimum_version,
        description=args.description
    )

    save_manifest(manifest, args.output)

    print()
    print("[+] Manifest contents:")
    for key, value in manifest.items():
        print(f"    {key}: {value}")
    print()
    print("[+] Manifest generation complete")
    print(f"[*] Upload {args.output} to S3 alongside firmware in Week 2")


if __name__ == "__main__":
    main()