"""
verify_setup.py

Verifies that the development environment is correctly configured
for the Secure OTA Firmware Update project.

Checks:
1. Python version >= 3.10
2. All required packages installed
3. Required project files present
4. .gitignore correctly excludes sensitive files
5. private_key.pem is NOT committed to git

Usage:
    python verify_setup.py
"""

import importlib
import os
import subprocess
import sys


def check(description: str, passed: bool, detail: str = "") -> bool:
    """Print a check result."""
    icon = "✅" if passed else "❌"
    print(f"  {icon} {description}")
    if not passed and detail:
        print(f"     → {detail}")
    return passed


def main():
    print()
    print("=" * 55)
    print("  Secure OTA Firmware Update — Setup Verification")
    print("=" * 55)
    print()

    all_passed = True

    # ─────────────────────────────────────────
    # Section 1 — Python version
    # ─────────────────────────────────────────
    print("Python version:")

    major = sys.version_info.major
    minor = sys.version_info.minor
    version_ok = (major == 3 and minor >= 10)
    result = check(
        f"Python {major}.{minor} (need 3.10+)",
        version_ok,
        "Install Python 3.10 or higher from python.org"
    )
    all_passed = all_passed and result
    print()

    # ─────────────────────────────────────────
    # Section 2 — Required packages
    # ─────────────────────────────────────────
    print("Required packages:")

    packages = [
        ("cryptography", "ECDSA signing and verification"),
        ("requests", "HTTP downloads in edge agent"),
        ("boto3", "AWS S3 upload (optional)"),
        ("pytest", "Test suite runner"),
    ]

    for package, purpose in packages:
        try:
            mod = importlib.import_module(package)
            version = getattr(mod, "__version__", "unknown")
            result = check(f"{package} ({version}) — {purpose}", True)
        except ImportError:
            result = check(
                f"{package} — {purpose}",
                False,
                f"Run: pip install {package}"
            )
            all_passed = all_passed and result

    print()

    # ─────────────────────────────────────────
    # Section 3 — Required files
    # ─────────────────────────────────────────
    print("Required project files:")

    required_files = [
        ("pki/generate_keys.py", "Key generation script"),
        ("pki/public_key.pem", "Public key (committed to repo)"),
        ("firmware/create_dummy_firmware.py", "Firmware simulator"),
        ("firmware/sign_firmware.py", "Signing script"),
        ("firmware/generate_manifest.py", "Manifest generator"),
        ("edge_agent/agent.py", "IoT edge agent"),
        ("edge_agent/version_store.json", "Version tracking"),
        ("distribution/manifest.json", "Sample manifest"),
        ("tests/test_local_pipeline.py", "Pipeline tests"),
        ("tests/test_tamper_simulation.py", "Attack simulation tests"),
        (".github/workflows/sign-and-release.yml", "CI/CD pipeline"),
        (".gitignore", "Git ignore rules"),
        ("requirements.txt", "Python dependencies"),
    ]

    for filepath, description in required_files:
        exists = os.path.exists(filepath)
        result = check(
            f"{filepath} — {description}",
            exists,
            f"File missing — check git pull and branch sync"
        )
        all_passed = all_passed and result

    print()

    # ─────────────────────────────────────────
    # Section 4 — Security checks
    # ─────────────────────────────────────────
    print("Security checks:")

    # Check private_key.pem is NOT committed
    try:
        git_result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD"],
            capture_output=True, text=True
        )
        committed_files = git_result.stdout.splitlines()
        private_key_committed = any(
            "private_key.pem" in f for f in committed_files
        )
        result = check(
            "private_key.pem NOT committed to git",
            not private_key_committed,
            "CRITICAL: private_key.pem is in the repo — remove immediately"
        )
        all_passed = all_passed and result
    except Exception:
        check("Git check", False, "Git not available or not in a git repo")

    # Check .sig files not committed
    try:
        sig_committed = any(
            f.endswith(".sig") for f in committed_files
        )
        result = check(
            "No .sig files committed",
            not sig_committed,
            ".sig files found in repo — check .gitignore"
        )
        all_passed = all_passed and result
    except Exception:
        pass

    # Check .gitignore covers private_key.pem
    if os.path.exists(".gitignore"):
        with open(".gitignore") as f:
            gitignore_content = f.read()
        covers_private_key = "private_key.pem" in gitignore_content
        result = check(
            ".gitignore covers private_key.pem",
            covers_private_key,
            "Add 'private_key.pem' to .gitignore"
        )
        all_passed = all_passed and result

    print()

    # ─────────────────────────────────────────
    # Section 5 — Optional checks
    # ─────────────────────────────────────────
    print("Optional checks:")

    # Check private key exists locally (needed to sign)
    private_key_exists = os.path.exists("pki/private_key.pem")
    check(
        "pki/private_key.pem exists locally (needed for local signing)",
        private_key_exists,
        "Run: python pki/generate_keys.py to generate key pair"
    )

    # Check firmware binary exists
    firmware_exists = os.path.exists("firmware/dummy_firmware_v1.0.0.bin")
    check(
        "firmware/dummy_firmware_v1.0.0.bin exists",
        firmware_exists,
        "Run: python firmware/create_dummy_firmware.py --version 1.0.0"
    )

    print()

    # ─────────────────────────────────────────
    # Final result
    # ─────────────────────────────────────────
    print("=" * 55)
    if all_passed:
        print("  ✅ ALL CHECKS PASSED — Environment is ready")
        print()
        print("  Next steps:")
        print("  1. python pki/generate_keys.py")
        print("  2. python run_all_tests.py")
        print("  3. python demo_attack.py")
    else:
        print("  ❌ SOME CHECKS FAILED — Fix issues above before proceeding")
    print("=" * 55)
    print()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()