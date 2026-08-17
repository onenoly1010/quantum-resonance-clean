"""
QPF Prototype – Verifier.

Checks two things only:
  1. Internal hash consistency – artifact sha256 values match recorded files.
  2. Referential integrity – every artifact references an existing event.

What it does NOT check, and cannot check:
  - Whether the event_id UUIDs are original or reconstructed.
  - Whether the creator_id is authentic.
  - Whether the recorded timestamps reflect when events actually occurred.

These are INTEGRITY checks.  They say nothing about AUTHENTICITY.
A perfectly forged chain with new UUIDs and recomputed hashes will pass.
See challenges table, challenge #1 (UUID_RECONSTRUCTION_WEAKNESS).
"""

import hashlib
import os
import sqlite3
from dataclasses import dataclass


@dataclass
class VerificationResult:
    passed: bool
    checked: int
    failures: list[str]

    # What this result establishes and does not establish
    ESTABLISHES = (
        "Each recorded artifact hash matched the file at verification time, "
        "and each artifact references an existing creation event."
    )
    DOES_NOT_ESTABLISH = (
        "Authenticity of the creation history.  A reconstructed chain with "
        "new UUIDs and valid internal hashes would also pass these checks."
    )


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(db_path: str, artifact_root: str = ".") -> VerificationResult:
    """Run integrity checks against provenance.db."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT a.artifact_id, a.filename, a.sha256, a.event_id,
               e.event_id AS event_exists
        FROM artifacts a
        LEFT JOIN creation_events e USING (event_id)
        """
    ).fetchall()
    conn.close()

    failures = []
    for row in rows:
        if row["event_exists"] is None:
            failures.append(
                f"artifact {row['artifact_id']}: orphaned (event {row['event_id']} not found)"
            )
            continue
        filepath = os.path.join(artifact_root, row["filename"])
        if not os.path.exists(filepath):
            failures.append(f"artifact {row['artifact_id']}: file not found at {filepath}")
            continue
        actual = _sha256_file(filepath)
        if actual != row["sha256"]:
            failures.append(
                f"artifact {row['artifact_id']}: hash mismatch\n"
                f"  recorded: {row['sha256']}\n"
                f"  actual:   {actual}"
            )

    return VerificationResult(
        passed=len(failures) == 0,
        checked=len(rows),
        failures=failures,
    )
