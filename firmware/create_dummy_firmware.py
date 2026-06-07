"""
create_dummy_firmware.py

Generates a dummy firmware binary file for testing the OTA signing pipeline.
In a real system this would be the compiled embedded firmware binary.
Here we simulate it with structured random bytes that include a version header.

Usage:
    python firmware/create_dummy_firmware.py --version 1.0.0
    python firmware/create_dummy_firmware.py --version 1.1.0 --size 512
"""

import argparse
import os
import struct
import random


def create_dummy_firmware(version: str, size_kb: int = 256) -> bytes:
    """
    Generate a dummy firmware binary with a version header followed by
    random bytes simulating compiled machine code.

    Binary structure:
    - Bytes 0-3:   Magic number 0xDEADBEEF — identifies this as firmware
    - Bytes 4-7:   Major version number
    - Bytes 8-11:  Minor version number
    - Bytes 12-15: Patch version number
    - Bytes 16+:   Random bytes simulating firmware payload

    Args:
        version: Semantic version string e.g. "1.0.0"
        size_kb: Total size of binary in kilobytes

    Returns:
        bytes: The complete firmware binary content
    """
    # Split "1.0.0" into [1, 0, 0]
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Version must be X.Y.Z format, got: {version}")

    major = int(parts[0])
    minor = int(parts[1])
    patch = int(parts[2])

    # Pack the 16-byte header
    # > = big-endian, I = unsigned int (4 bytes)
    MAGIC = 0xDEADBEEF
    header = struct.pack(">IIII", MAGIC, major, minor, patch)

    # Fill the rest with random bytes to simulate compiled code
    payload_size = (size_kb * 1024) - len(header)
    payload = bytes(random.randint(0, 255) for _ in range(payload_size))

    return header + payload


def save_firmware(data: bytes, version: str, output_dir: str = "firmware") -> str:
    """
    Save firmware binary to disk with versioned filename.

    Args:
        data: Raw firmware bytes
        version: Version string used in filename
        output_dir: Directory to save the file

    Returns:
        str: Full path to saved file
    """
    filename = f"dummy_firmware_v{version}.bin"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "wb") as f:
        f.write(data)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Generate a dummy firmware binary for OTA pipeline testing"
    )
    parser.add_argument(
        "--version",
        type=str,
        default="1.0.0",
        help="Firmware version in X.Y.Z format (default: 1.0.0)"
    )
    parser.add_argument(
        "--size",
        type=int,
        default=256,
        help="Size in kilobytes (default: 256)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="firmware",
        help="Output directory (default: firmware/)"
    )

    args = parser.parse_args()

    print(f"[*] Generating dummy firmware v{args.version} ({args.size}KB)...")
    firmware_data = create_dummy_firmware(args.version, args.size)

    filepath = save_firmware(firmware_data, args.version, args.output_dir)
    size_bytes = len(firmware_data)

    print(f"[+] Firmware binary created: {filepath}")
    print(f"[+] Size: {size_bytes} bytes ({size_bytes / 1024:.1f} KB)")
    print(f"[+] Header: MAGIC=0xDEADBEEF, version={args.version}")
    print(f"[*] This binary is for testing only — not real firmware")


if __name__ == "__main__":
    main()