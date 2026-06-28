""
run_all_tests.py

Convenience script to run the complete test suite and
produce a clean summary report.

Equivalent to: python -m pytest tests/ -v
But adds a formatted summary at the end for easy reading.

Usage:
    python run_all_tests.py
    python run_all_tests.py --fail-fast
"""

import argparse
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(
        description="Run complete Secure OTA test suite"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--no-verbose",
        action="store_true",
        help="Run without verbose output"
    )

    args = parser.parse_args()

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     Secure OTA Firmware Update — Full Test Suite         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # Build pytest command
    cmd = [sys.executable, "-m", "pytest", "tests/"]

    if not args.no_verbose:
        cmd.append("-v")

    if args.fail_fast:
        cmd.append("-x")

    cmd.extend(["--tb=short"])

    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    print()

    start_time = time.time()
    result = subprocess.run(cmd)
    duration = time.time() - start_time

    print()
    print("=" * 60)
    print("  TEST SUITE COMPLETE")
    print("=" * 60)
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Exit code: {result.returncode}")
    print()

    if result.returncode == 0:
        print("  ✅ ALL TESTS PASSED")
        print()
        print("  Test files:")
        print("  - tests/test_local_pipeline.py  (14 tests)")
        print("  - tests/test_tamper_simulation.py (15 tests)")
        print()
        print("  Security layers verified:")
        print("  ✅ SHA-256 hash verification (Layer 1)")
        print("  ✅ ECDSA signature verification (Layer 2)")
        print("  ✅ Anti-rollback version check (Layer 3)")
    else:
        print("  ❌ SOME TESTS FAILED")
        print("  Run with -v for detailed output")

    print()
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()