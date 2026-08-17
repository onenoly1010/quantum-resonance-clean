"""
QPF Prototype – Verification runner.

Runs integrity checks and prints a structured report.
"""

import sys
from verifier import verify

DB = "provenance.db"


def main():
    result = verify(DB, artifact_root=".")

    print("=" * 60)
    print("QPF INTEGRITY VERIFICATION REPORT")
    print("=" * 60)
    print(f"Database:  {DB}")
    print(f"Artifacts: {result.checked}")
    print(f"Status:    {'PASS' if result.passed else 'FAIL'}")
    print()
    print("WHAT THIS ESTABLISHES:")
    print(f"  {result.ESTABLISHES}")
    print()
    print("WHAT THIS DOES NOT ESTABLISH:")
    print(f"  {result.DOES_NOT_ESTABLISH}")

    if result.failures:
        print()
        print("FAILURES:")
        for f in result.failures:
            print(f"  - {f}")
    print("=" * 60)

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
