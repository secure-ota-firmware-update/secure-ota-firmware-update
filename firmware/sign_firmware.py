"""
sign_firmware.py

Signs a firmware binary using ECDSA P-256 private key.

This script is the core of the signing pipeline. It:
1. Validates the firmware file exists and has reasonable size
2. Reads the private key from an environment variable or argument
3. Computes SHA-256 hash of the firmware binary
4. Signs the hash using ECDSA P-256
5. Saves the signature to a .sig file

SECURITY RULES:
- Private key is NEVER hardcoded
- Private key path comes from environment variable or --key argument
- No secrets are printed to stdout or stderr
- The .sig file is a gitignored generated artifact

Usage:
    export FIRMWARE_PRIVATE_KEY_PATH=pki/private_key.pem
    python firmware/sign_firmware.py --firmware firmware/dummy_firmware_v1.0.0.bin

    python firmware/sign_firmware.py \
        --firmware firmware/dummy_firmware_v1.0.0.bin \
        --key pki/private_key.pem \
        --output firmware/dummy_firmware_v1.0.0.sig
"""

import argparse
import hashlib
import os
import sys

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.exceptions import InvalidSignature


# Maximum allowed firmware file size — 100MB
# Anything larger is likely an error or a suspicious input
MAX_FIRMWARE_SIZE_BYTES = 100 * 1024 * 1024

# Minimum firmware file size — 16 bytes
# An empty or near-empty file is not valid firmware
MIN_FIRMWARE_SIZE_BYTES = 16


def validate_firmware_file(firmware_path: str) -> None:
    """
    Validate the firmware file before signing.

    Checks:
    - File exists
    - File is not empty
    - File is not unreasonably large
    - File has .bin extension

    Args:
        firmware_path: path to firmware binary

    Raises:
        SystemExit: if any validation check fails
    """
    if not os.path.exists(firmware_path):
        print(f"[ERROR] Firmware file not found: {firmware_path}")
        sys.exit(1)

    if not firmware_path.endswith(".bin"):
        print(f"[WARNING] Firmware file does not have .bin extension: {firmware_path}")
        print("[WARNING] Proceeding, but verify this is the correct file")

    size = os.path.getsize(firmware_path)

    if size < MIN_FIRMWARE_SIZE_BYTES:
        print(f"[ERROR] Firmware file is too small: {size} bytes")
        print(f"[ERROR] Minimum allowed size: {MIN_FIRMWARE_SIZE_BYTES} bytes")
        sys.exit(1)

    if size > MAX_FIRMWARE_SIZE_BYTES:
        print(f"[ERROR] Firmware file is too large: {size / (1024*1024):.1f} MB")
        print(f"[ERROR] Maximum allowed size: {MAX_FIRMWARE_SIZE_BYTES / (1024*1024):.0f} MB")
        sys.exit(1)

    print(f"[+] Firmware validated: {firmware_path} ({size} bytes)")


def validate_key_file(key_path: str) -> None:
    """
    Validate the private key file before loading.

    Checks:
    - File exists
    - File has .pem extension
    - File contains PEM header (basic format check)

    SECURITY: Does NOT print key contents.

    Args:
        key_path: path to private key PEM file

    Raises:
        SystemExit: if validation fails
    """
    if not os.path.exists(key_path):
        print(f"[ERROR] Private key file not found: {key_path}")
        print("[ERROR] Generate key pair first: python pki/generate_keys.py")
        sys.exit(1)

    if not key_path.endswith(".pem"):
        print(f"[WARNING] Key file does not have .pem extension: {key_path}")

    # Read just the first line to check PEM format — never print contents
    with open(key_path, "r") as f:
        first_line = f.readline().strip()

    if "BEGIN" not in first_line:
        print(f"[ERROR] File does not appear to be in PEM format: {key_path}")
        print("[ERROR] Expected file starting with '-----BEGIN ...'")
        sys.exit(1)

    if "PRIVATE" not in first_line:
        print(f"[ERROR] File does not appear to be a private key: {key_path}")
        print("[ERROR] Do not use the public key for signing")
        sys.exit(1)

    print(f"[+] Private key validated: {key_path} (PEM format confirmed)")


def load_private_key(key_path: str):
    """
    Load ECDSA private key from PEM file.

    Args:
        key_path: path to private key PEM file

    Returns:
        private key object
    """
    with open(key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None
        )
    print(f"[+] Private key loaded")
    return private_key


def compute_sha256(firmware_path: str) -> bytes:
    """
    Compute SHA-256 hash of firmware binary.

    Reads in 8KB chunks to handle large files without
    loading entire binary into memory at once.

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
    hex_digest = sha256.hexdigest()
    print(f"[+] SHA-256 computed: {hex_digest}")
    return digest


def sign_firmware(private_key, firmware_hash: bytes) -> bytes:
    """
    Sign firmware hash using ECDSA P-256.

    Uses Prehashed because the hash was already computed
    by compute_sha256(). Both sides (sign and verify) must
    use the same approach — Prehashed with SHA-256.

    Args:
        private_key: loaded ECDSA private key
        firmware_hash: raw SHA-256 digest bytes (32 bytes)

    Returns:
        bytes: DER-encoded ECDSA signature
    """
    signature = private_key.sign(
        firmware_hash,
        ec.ECDSA(utils.Prehashed(hashes.SHA256()))
    )

    print(f"[+] Firmware signed — signature length: {len(signature)} bytes")
    return signature


def validate_signature(private_key, firmware_hash: bytes, signature: bytes) -> bool:
    """
    Self-verify the signature immediately after creation.

    This catches any issue with the signing process before
    the .sig file is saved and distributed. If verification
    fails immediately after signing, something is seriously wrong.

    Args:
        private_key: the key that was used to sign
        firmware_hash: raw hash that was signed
        signature: signature to verify

    Returns:
        bool: True if self-verification passes
    """
    public_key = private_key.public_key()

    try:
        public_key.verify(
            signature,
            firmware_hash,
            ec.ECDSA(utils.Prehashed(hashes.SHA256()))
        )
        print("[+] Self-verification PASSED — signature is valid")
        return True
    except InvalidSignature:
        print("[ERROR] Self-verification FAILED — signing produced invalid signature")
        return False


def save_signature(signature: bytes, output_path: str) -> None:
    """
    Save ECDSA signature to .sig file.

    Args:
        signature: raw signature bytes
        output_path: path to save the .sig file
    """
    with open(output_path, "wb") as f:
        f.write(signature)

    print(f"[+] Signature saved: {output_path}")


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
        help="Path to save .sig file (default: firmware path with .sig extension)"
    )
    parser.add_argument(
        "--key",
        type=str,
        default=None,
        help="Path to private key PEM (default: FIRMWARE_PRIVATE_KEY_PATH env var)"
    )

    args = parser.parse_args()

    # Resolve private key path from argument or environment variable
    key_path = args.key or os.environ.get("FIRMWARE_PRIVATE_KEY_PATH")
    if not key_path:
        print("[ERROR] Private key path not specified")
        print("[ERROR] Use --key argument or set FIRMWARE_PRIVATE_KEY_PATH env var")
        sys.exit(1)

    # Resolve output path
    output_path = args.output or args.firmware.replace(".bin", ".sig")

    print()
    print("[*] Secure OTA Firmware Signing")
    print(f"[*] Firmware: {args.firmware}")
    print(f"[*] Output:   {output_path}")
    print()

    # Step 1 — Validate inputs
    validate_firmware_file(args.firmware)
    validate_key_file(key_path)
    print()

    # Step 2 — Load key and compute hash
    private_key = load_private_key(key_path)
    firmware_hash = compute_sha256(args.firmware)
    print()

    # Step 3 — Sign
    signature = sign_firmware(private_key, firmware_hash)
    print()

    # Step 4 — Self-verify immediately after signing
    if not validate_signature(private_key, firmware_hash, signature):
        print("[ERROR] Aborting — signature self-verification failed")
        sys.exit(1)
    print()

    # Step 5 — Save
    save_signature(signature, output_path)

    print()
    print("[+] Signing complete")
    print(f"[+] Firmware: {args.firmware}")
    print(f"[+] Signature: {output_path}")
    print("[*] Upload both files to distribution server in CI/CD pipeline")
    print()


if __name__ == "__main__":
    main()