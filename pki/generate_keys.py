"""
generate_keys.py

Generates an ECDSA P-256 asymmetric key pair for firmware signing.

The private key is used by the CI/CD pipeline to sign firmware binaries.
The public key is stored on every IoT edge device to verify signatures.

SECURITY RULES:
- Private key must NEVER be committed to the repository
- Private key must be stored as a GitHub Secret (Week 2)
- Only public_key.pem is safe to commit

Usage:
    python pki/generate_keys.py
    python pki/generate_keys.py --output-dir pki/
"""

import argparse
import os
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


def generate_ecdsa_keypair():
    """
    Generate an ECDSA P-256 key pair.

    P-256 (secp256r1) is chosen because:
    - Provides 128-bit security level
    - Much smaller keys than RSA with equivalent security
    - Natively supported by Python cryptography library
    - Industry standard for IoT firmware signing

    Returns:
        tuple: (private_key, public_key) as cryptography library objects
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key


def save_private_key(private_key, output_dir: str) -> str:
    """
    Save private key to disk in PEM format.

    WARNING: This file must NEVER be committed to git.
    It should be stored as a GitHub Secret for CI/CD use.

    Args:
        private_key: ECDSA private key object
        output_dir: Directory to save the key

    Returns:
        str: Path where private key was saved
    """
    private_key_path = os.path.join(output_dir, "private_key.pem")

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    with open(private_key_path, "wb") as f:
        f.write(private_key_pem)

    return private_key_path


def save_public_key(public_key, output_dir: str) -> str:
    """
    Save public key to disk in PEM format.

    This file is safe to commit to the repository.
    It is embedded in every IoT edge device at manufacture time.

    Args:
        public_key: ECDSA public key object
        output_dir: Directory to save the key

    Returns:
        str: Path where public key was saved
    """
    public_key_path = os.path.join(output_dir, "public_key.pem")

    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open(public_key_path, "wb") as f:
        f.write(public_key_pem)

    return public_key_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate ECDSA P-256 key pair for firmware signing"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="pki",
        help="Directory to save keys (default: pki/)"
    )

    args = parser.parse_args()

    print("[*] Generating ECDSA P-256 key pair...")
    private_key, public_key = generate_ecdsa_keypair()

    private_path = save_private_key(private_key, args.output_dir)
    public_path = save_public_key(public_key, args.output_dir)

    print(f"[+] Private key saved: {private_path}")
    print(f"[+] Public key saved:  {public_path}")
    print()
    print("[!] SECURITY WARNING:")
    print(f"[!] DO NOT commit {private_path} to git")
    print(f"[!] Add private_key.pem to .gitignore")
    print(f"[!] Store private key as GitHub Secret for CI/CD use")
    print()
    print(f"[+] Safe to commit: {public_path}")
    print("[*] Key generation complete")


if __name__ == "__main__":
    main()