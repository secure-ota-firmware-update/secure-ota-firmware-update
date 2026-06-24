"""
sign_firmware.py

Signs a firmware binary using ECDSA P-256 private key.

This script is called by the GitHub Actions CI/CD pipeline in Week 2.
The private key is NEVER hardcoded — it is read from an environment
variable that is injected from GitHub Secrets at runtime.

Steps:
1. Read private key from environment variable
2. Read firmware binary from disk
3. Compute SHA-256 hash of firmware binary
4. Sign the hash using ECDSA P-256 private key
5. Save signature to .sig file

Usage:
    export FIRMWARE_PRIVATE_KEY_PATH=/tmp/private_key.pem
    python firmware/sign_firmware.py --firmware firmware/dummy_firmware_v1.0.0.bin
    python firmware/sign_firmware.py --firmware firmware/dummy_firmware_v1.0.0.bin --output firmware/dummy_firmware_v1.0.0.sig
"""

import argparse
import hashlib
import os
import sys
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec , utils


def load_private_key(key_path: str):
    """
    Load ECDSA private key from PEM file.

    The key path is passed as an argument — never hardcoded.
    In CI/CD pipeline, the key is written from GitHub Secrets
    to a temporary file and this path is passed in.

    Args:
        key_path: path to private key PEM file

    Returns:
        private key object
    """
    if not os.path.exists(key_path):
        print(f"[ERROR] Private key not found at: {key_path}")
        print("[ERROR] Set FIRMWARE_PRIVATE_KEY_PATH environment variable")
        sys.exit(1)

    with open(key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )

    print(f"[+] Private key loaded from: {key_path}")
    return private_key


def compute_sha256(firmware_path: str) -> bytes:
    """
    Compute SHA-256 hash of firmware binary.

    Reads file in chunks to handle large firmware files
    without loading entire file into memory at once.

    Args:
        firmware_path: path to firmware binary

    Returns:
        bytes: raw SHA-256 digest (32 bytes)
    """
    sha256 = hashlib.sha256()

    with open(firmware_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    digest = sha256.digest()
    print(f"[+] SHA-256 hash computed: {digest.hex()}")
    return digest


def sign_firmware(private_key, firmware_hash: bytes) -> bytes:
    """
    Sign firmware hash using ECDSA P-256 private key.

    Signs the SHA-256 hash of the firmware, not the firmware itself.
    This is the standard approach — hash first then sign.

    Args:
        private_key: loaded ECDSA private key object
        firmware_hash: raw SHA-256 digest bytes

    Returns:
        bytes: ECDSA signature bytes
    """
    signature = private_key.sign(
        firmware_hash,
        ec.ECDSA(utils.Prehashed(hashes.SHA256()))
    )

    print(f"[+] Firmware signed successfully")
    print(f"[+] Signature length: {len(signature)} bytes")
    return signature


def save_signature(signature: bytes, output_path: str) -> None:
    """
    Save ECDSA signature to .sig file.

    Args:
        signature: raw signature bytes
        output_path: path to save the .sig file
    """
    with open(output_path, "wb") as f:
        f.write(signature)

    print(f"[+] Signature saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Sign firmware binary using ECDSA P-256 private key"
    )
    parser.add_argument(
        "--firmware",
        type=str,
        required=True,
        help="Path to firmware binary to sign"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save signature file (default: firmware path with .sig extension)"
    )
    parser.add_argument(
        "--key",
        type=str,
        default=None,
        help="Path to private key PEM file (default: reads FIRMWARE_PRIVATE_KEY_PATH env var)"
    )

    args = parser.parse_args()

    # Resolve private key path
    key_path = args.key or os.environ.get("FIRMWARE_PRIVATE_KEY_PATH")
    if not key_path:
        print("[ERROR] Private key path not provided")
        print("[ERROR] Use --key argument or set FIRMWARE_PRIVATE_KEY_PATH env var")
        sys.exit(1)

    # Resolve output path
    output_path = args.output or args.firmware.replace(".bin", ".sig")

    print(f"[*] Signing firmware: {args.firmware}")
    print(f"[*] Using key: {key_path}")
    print(f"[*] Output: {output_path}")
    print()

    # Execute signing pipeline
    private_key = load_private_key(key_path)
    firmware_hash = compute_sha256(args.firmware)
    signature = sign_firmware(private_key, firmware_hash)
    save_signature(signature, output_path)

    print()
    print("[+] Signing complete")
    print(f"[+] Firmware: {args.firmware}")
    print(f"[+] Signature: {output_path}")
    print("[*] Both files must be uploaded to S3 together in Week 2")


if __name__ == "__main__":
    main()