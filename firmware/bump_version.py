"""
bump_version.py

Convenience script for creating a new firmware release.

Handles the full release process:
1. Reads current version from distribution/manifest.json
2. Bumps major, minor, or patch version
3. Generates new dummy firmware binary with new version
4. Signs the firmware locally for testing
5. Updates manifest.json with new version and hash
6. Creates a git tag
7. Pushes the tag to trigger the CI/CD pipeline

This script is for development use — the CI/CD pipeline handles
the actual signing with the secure private key from GitHub Secrets.

Usage:
    python firmware/bump_version.py --bump patch
    python firmware/bump_version.py --bump minor
    python firmware/bump_version.py --bump major
    python firmware/bump_version.py --bump patch --dry-run
"""

import argparse
import json
import os
import subprocess
import sys


def read_current_version() -> str:
    """Read current version from manifest.json."""
    manifest_path = "distribution/manifest.json"
    if not os.path.exists(manifest_path):
        print("[ERROR] distribution/manifest.json not found")
        print("[ERROR] Run generate_manifest.py first")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    return manifest["version"]


def bump_version(version: str, bump_type: str) -> str:
    """
    Bump a semantic version string.

    Args:
        version: current version e.g. "1.2.3"
        bump_type: "major", "minor", or "patch"

    Returns:
        str: new version string
    """
    parts = [int(x) for x in version.split(".")]
    major, minor, patch = parts[0], parts[1], parts[2]

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        print(f"[ERROR] Invalid bump type: {bump_type}")
        print("[ERROR] Use: major, minor, or patch")
        sys.exit(1)

    return f"{major}.{minor}.{patch}"


def run_command(args: list, description: str, dry_run: bool = False) -> bool:
    """
    Run a shell command with status output.

    Args:
        args: command arguments
        description: human readable description
        dry_run: if True, print command but do not execute

    Returns:
        bool: True if successful
    """
    print(f"  → {description}")

    if dry_run:
        print(f"    [DRY RUN] Would run: {' '.join(args)}")
        return True

    result = subprocess.run(args, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    [ERROR] {result.stderr.strip()}")
        return False

    if result.stdout.strip():
        for line in result.stdout.strip().split("\n"):
            print(f"    {line}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Bump firmware version and create GitHub Release"
    )
    parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Version component to bump (default: patch)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without executing"
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Create tag locally but do not push to GitHub"
    )

    args = parser.parse_args()

    print()
    print("=" * 55)
    print("  Firmware Version Bump and Release Creator")
    print("=" * 55)
    print()

    # Step 1 — Read current version
    current = read_current_version()
    new_version = bump_version(current, args.bump)
    tag = f"v{new_version}"

    print(f"  Current version: {current}")
    print(f"  New version:     {new_version} ({args.bump} bump)")
    print(f"  Git tag:         {tag}")

    if args.dry_run:
        print()
        print("  [DRY RUN MODE — no changes will be made]")

    print()

    # Step 2 — Generate new firmware binary
    firmware_path = f"firmware/dummy_firmware_v{new_version}.bin"
    ok = run_command(
        [sys.executable, "firmware/create_dummy_firmware.py",
         "--version", new_version, "--size", "256"],
        f"Generate firmware binary v{new_version}",
        args.dry_run
    )
    if not ok:
        sys.exit(1)

    # Step 3 — Sign locally for testing (pipeline will re-sign)
    private_key_path = "pki/private_key.pem"
    if os.path.exists(private_key_path):
        run_command(
            [sys.executable, "firmware/sign_firmware.py",
             "--firmware", firmware_path,
             "--key", private_key_path],
            "Sign firmware locally for testing",
            args.dry_run
        )
    else:
        print("  → Skipping local signing — private_key.pem not found")
        print("    (Pipeline will sign using GitHub Secrets)")

    # Step 4 — Update manifest
    ok = run_command(
        [sys.executable, "firmware/generate_manifest.py",
         "--version", new_version,
         "--firmware", firmware_path,
         "--output", "distribution/manifest.json",
         "--description", f"Firmware release v{new_version}"],
        "Update distribution/manifest.json",
        args.dry_run
    )
    if not ok:
        sys.exit(1)

    # Step 5 — Stage and commit
    ok = run_command(
        ["git", "add",
         firmware_path,
         "distribution/manifest.json"],
        "Stage firmware and manifest",
        args.dry_run
    )
    if not ok:
        sys.exit(1)

    ok = run_command(
        ["git", "commit", "-m",
         f"chore: bump firmware version to v{new_version}"],
        f"Commit version bump to v{new_version}",
        args.dry_run
    )
    if not ok:
        sys.exit(1)

    # Step 6 — Create tag
    ok = run_command(
        ["git", "tag", tag],
        f"Create git tag {tag}",
        args.dry_run
    )
    if not ok:
        sys.exit(1)

    # Step 7 — Push to trigger pipeline
    if not args.skip_push:
        print()
        ok = run_command(
            ["git", "push", "origin", "HEAD"],
            "Push commit to remote",
            args.dry_run
        )
        if not ok:
            sys.exit(1)

        ok = run_command(
            ["git", "push", "origin", tag],
            f"Push tag {tag} → triggers GitHub Actions pipeline",
            args.dry_run
        )
        if not ok:
            sys.exit(1)

    print()
    print("=" * 55)
    if args.dry_run:
        print(f"  [DRY RUN COMPLETE] Would create release v{new_version}")
    elif args.skip_push:
        print(f"  Tag {tag} created locally — push manually to trigger pipeline:")
        print(f"  git push origin {tag}")
    else:
        print(f"  Release v{new_version} triggered!")
        print(f"  Watch pipeline: https://github.com/secure-ota-firmware-update")
        print(f"  /secure-ota-firmware-update/actions")
    print("=" * 55)
    print()


if __name__ == "__main__":
    main()