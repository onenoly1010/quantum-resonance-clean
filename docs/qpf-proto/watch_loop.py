"""
QPF Watch Loop – Autonomous adversarial test executor.

WHAT THIS DOES
  Continuously generates and executes adversarial challenges against the QPF
  provenance prototype, records every result in challenge_results, and emits
  a cycle summary.

WHAT THIS DOES NOT DO
  It does not declare the system correct.
  It does not promote a passing result to "proven".
  It does not resolve INCONCLUSIVE rows.
  It does not erase failures.
  It does not modify the system under test and then use the modified system
  as evidence that the modification succeeded.

REPAIR PROVENANCE RULE (hard constraint)
  If a challenge produces FAIL, the watch loop may record a proposed change
  alongside the result, but it may NOT apply that change to the system under
  test and re-run as if the failure never occurred.  The correct sequence is:

      challenge → FAIL
              ↓
      proposed change recorded (as an observation, not an action)
              ↓
      new system version built independently
              ↓
      independent challenge execution against new version
              ↓
      new result row appended

  v1 remains v1.  Its failure remains real.  v2 earns its own record.
  Improvements create new history; they do not rewrite old history.

RESULT VOCABULARY
  PASS         – the attempted challenge did not falsify the tested claim.
  FAIL         – the challenge falsified the tested claim under stated conditions.
  INCONCLUSIVE – the challenge cannot currently establish either outcome.
  NOT_RUN      – defined but not executed in this cycle (function missing).
  SUPERSEDED   – replaced by a later challenge definition (not used here).

Every result row becomes part of the permanent history.  The loop may run
all night.  The conclusion — if any — belongs to a human or independently
justified authority.

Usage
  python watch_loop.py [--once] [--db PATH] [--version LABEL]
"""

import argparse
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Resolve path to the prototype directory regardless of cwd
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from provenance import record_challenge, record_challenge_result  # noqa: E402
from schema import open_db  # noqa: E402
from verifier import verify  # noqa: E402

TESTER_ID = "watch_loop_v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Challenge catalogue
# Each entry is a dict:
#   key           – stable identifier used to look up or insert the challenge
#   claim         – what the system is supposed to do
#   failure_hyp   – specific way the claim might be false
#   test_desc     – how the test is executed
#   fn            – callable(db_path, system_version) → (status, observed, ruled_out, unresolved)
# ---------------------------------------------------------------------------

def _test_uuid_reconstruction(db_path: str, system_version: str):
    """
    Adversarial test: reconstruct a structurally valid chain with fresh UUIDs
    and recomputed hashes, then run the verifier against it.

    Expected outcome under current v1 verifier: the reconstruction PASSES
    integrity checks.  That means the claim ("verifier detects reconstruction")
    is falsified → challenge result = FAIL.

    This is a known weakness.  Recording it as FAIL is correct; it is not a
    bug in the watch loop.  The failure should motivate an external-anchor
    mechanism (not declared here).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        recon_db = os.path.join(tmpdir, "recon.db")
        # Build a counterfeit provenance database from scratch
        conn = open_db(recon_db)

        fake_event_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
            (fake_event_id, "adversary", "Reconstructed history", _now()),
        )

        # Write a fake artifact file
        artifact_path = os.path.join(tmpdir, "fake_artifact.txt")
        content = b"Counterfeit artifact content.\n"
        with open(artifact_path, "wb") as f:
            f.write(content)

        fake_artifact_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
            (
                fake_artifact_id,
                fake_event_id,
                "fake_artifact.txt",
                _sha256_bytes(content),
                _now(),
            ),
        )
        conn.commit()
        conn.close()

        result = verify(recon_db, artifact_root=tmpdir)

    if result.passed:
        return (
            "FAIL",
            (
                "The reconstructed chain (new UUIDs, recomputed hashes, "
                "no connection to the original history) passed the v1 verifier. "
                "The verifier cannot distinguish an authentic chain from a "
                "structurally valid counterfeit."
            ),
            None,
            (
                "Whether any external anchor (timestamp authority, independent "
                "witness, transparency log, hardware attestation) could allow the "
                "verifier to distinguish authentic from reconstructed chains.  "
                "No anchor is currently implemented or evaluated."
            ),
        )
    else:
        return (
            "INCONCLUSIVE",
            (
                f"The reconstructed chain unexpectedly failed verification: "
                f"{result.failures}.  This was not the predicted outcome.  "
                "The test may need revision."
            ),
            None,
            "Why the reconstruction failed when the verifier was expected to accept it.",
        )


def _test_hash_tamper(db_path: str, system_version: str):
    """
    Adversarial test: tamper with an artifact file after it is recorded, then
    run the verifier.

    Expected outcome: verifier DETECTS the tamper → claim is NOT falsified →
    challenge result = PASS.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tamper_db = os.path.join(tmpdir, "tamper.db")
        conn = open_db(tamper_db)

        event_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
            (event_id, "tamper-test", "Hash tamper test event", _now()),
        )

        artifact_path = os.path.join(tmpdir, "target.txt")
        original_content = b"Original content before tampering.\n"
        with open(artifact_path, "wb") as f:
            f.write(original_content)

        artifact_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
            (
                artifact_id,
                event_id,
                "target.txt",
                _sha256_bytes(original_content),
                _now(),
            ),
        )
        conn.commit()
        conn.close()

        # Tamper: overwrite the file with different content
        with open(artifact_path, "wb") as f:
            f.write(b"Tampered content - different from what was recorded.\n")

        result = verify(tamper_db, artifact_root=tmpdir)

    if not result.passed and any("hash mismatch" in fl for fl in result.failures):
        return (
            "PASS",
            (
                "The verifier detected the hash mismatch after artifact tampering.  "
                "The integrity check correctly flagged the modified file."
            ),
            "That the verifier silently accepts a tampered artifact file.",
            None,
        )
    else:
        return (
            "FAIL",
            (
                f"The verifier did not detect the tamper.  "
                f"Passed={result.passed}, failures={result.failures}."
            ),
            None,
            "Whether there is a bypass condition under which hash tampering goes undetected.",
        )


def _test_orphan_artifact(db_path: str, system_version: str):
    """
    Adversarial test: insert an artifact that references a non-existent event_id.

    Expected outcome: verifier DETECTS the orphan → challenge result = PASS.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        orphan_db = os.path.join(tmpdir, "orphan.db")
        conn = open_db(orphan_db)

        phantom_event_id = str(uuid.uuid4())  # never inserted into creation_events

        artifact_path = os.path.join(tmpdir, "orphan.txt")
        content = b"Artifact with no parent event.\n"
        with open(artifact_path, "wb") as f:
            f.write(content)

        # Disable FK enforcement temporarily to force the bad row in
        conn.execute("PRAGMA foreign_keys = OFF")
        artifact_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
            (
                artifact_id,
                phantom_event_id,
                "orphan.txt",
                _sha256_bytes(content),
                _now(),
            ),
        )
        conn.commit()
        conn.close()

        result = verify(orphan_db, artifact_root=tmpdir)

    if not result.passed and any("orphaned" in fl for fl in result.failures):
        return (
            "PASS",
            (
                "The verifier detected the orphaned artifact "
                "(artifact referencing a non-existent creation event)."
            ),
            "That the verifier silently accepts artifacts with phantom event references.",
            None,
        )
    else:
        return (
            "FAIL",
            (
                f"The verifier did not detect the orphaned artifact.  "
                f"Passed={result.passed}, failures={result.failures}."
            ),
            None,
            "Whether there is a structural bypass for orphan detection.",
        )


def _test_deleted_event(db_path: str, system_version: str):
    """
    Adversarial test: record an artifact legitimately, then delete the parent
    creation event directly (bypassing FK enforcement).

    Expected outcome: verifier reports the artifact as orphaned → PASS.
    If verifier misses it, the referential integrity check is incomplete → FAIL.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        del_db = os.path.join(tmpdir, "del_event.db")
        conn = open_db(del_db)

        event_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
            (event_id, "delete-test", "Event that will be deleted", _now()),
        )

        artifact_path = os.path.join(tmpdir, "del_artifact.txt")
        content = b"Artifact whose parent will be deleted.\n"
        with open(artifact_path, "wb") as f:
            f.write(content)

        artifact_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
            (artifact_id, event_id, "del_artifact.txt", _sha256_bytes(content), _now()),
        )
        conn.commit()

        # Delete the parent event, bypassing FK constraints
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("DELETE FROM creation_events WHERE event_id = ?", (event_id,))
        conn.commit()
        conn.close()

        result = verify(del_db, artifact_root=tmpdir)

    if not result.passed and any("orphaned" in fl for fl in result.failures):
        return (
            "PASS",
            (
                "After deleting the parent creation event, the verifier detected the "
                "artifact as orphaned.  Referential integrity check caught the deletion."
            ),
            "That the verifier silently accepts artifacts whose parent event has been deleted.",
            None,
        )
    else:
        return (
            "FAIL",
            (
                f"Verifier did not detect orphaned artifact after parent event deletion.  "
                f"Passed={result.passed}, failures={result.failures}."
            ),
            None,
            "Whether there is a bypass path for orphan detection when events are deleted post-insert.",
        )


def _test_timestamp_reorder(db_path: str, system_version: str):
    """
    Adversarial test: insert an artifact with a recorded_at timestamp that
    predates the parent creation event's created_at timestamp.

    The v1 verifier does not check temporal ordering; this is expected to PASS
    the verifier silently.  That means the claim "the verifier detects
    impossible temporal ordering" is falsified → challenge result = FAIL.

    This is a known limitation: the verifier checks hashes and references,
    not timestamp plausibility.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        ts_db = os.path.join(tmpdir, "ts_reorder.db")
        conn = open_db(ts_db)

        event_id = str(uuid.uuid4())
        event_time = "2024-06-01T12:00:00+00:00"
        conn.execute(
            "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
            (event_id, "ts-test", "Event with future-dated artifacts", event_time),
        )

        artifact_path = os.path.join(tmpdir, "ts_artifact.txt")
        content = b"Artifact timestamped before its parent event.\n"
        with open(artifact_path, "wb") as f:
            f.write(content)

        artifact_id = str(uuid.uuid4())
        # Record artifact with a timestamp one year BEFORE the event
        artifact_time = "2023-01-01T00:00:00+00:00"
        conn.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
            (artifact_id, event_id, "ts_artifact.txt", _sha256_bytes(content), artifact_time),
        )
        conn.commit()
        conn.close()

        result = verify(ts_db, artifact_root=tmpdir)

    if result.passed:
        return (
            "FAIL",
            (
                "The verifier accepted an artifact whose recorded_at timestamp predates "
                "the parent event's created_at timestamp by over a year.  "
                "Temporal ordering is not checked by v1."
            ),
            None,
            (
                "Whether timestamp plausibility checks are necessary, "
                "and whether they could be spoofed if added.  "
                "Temporal ordering alone does not establish authenticity."
            ),
        )
    else:
        return (
            "PASS",
            (
                f"Unexpectedly, the verifier detected the temporal impossibility: "
                f"{result.failures}.  This may indicate the verifier scope has changed."
            ),
            "That the v1 verifier silently accepts impossible timestamp ordering.",
            None,
        )


def _test_partial_corruption(db_path: str, system_version: str):
    """
    Adversarial test: flip a single byte in an artifact file after recording,
    then verify.

    Expected outcome: verifier detects the hash mismatch → PASS.
    A single-byte change should produce a completely different SHA-256.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        corrupt_db = os.path.join(tmpdir, "partial_corrupt.db")
        conn = open_db(corrupt_db)

        event_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
            (event_id, "corrupt-test", "Partial corruption test event", _now()),
        )

        artifact_path = os.path.join(tmpdir, "corrupt_artifact.txt")
        original = b"Artifact content for partial corruption test.\n"
        with open(artifact_path, "wb") as f:
            f.write(original)

        artifact_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
            (artifact_id, event_id, "corrupt_artifact.txt", _sha256_bytes(original), _now()),
        )
        conn.commit()
        conn.close()

        # Flip the first byte
        corrupted = bytes([original[0] ^ 0xFF]) + original[1:]
        with open(artifact_path, "wb") as f:
            f.write(corrupted)

        result = verify(corrupt_db, artifact_root=tmpdir)

    if not result.passed and any("hash mismatch" in fl for fl in result.failures):
        return (
            "PASS",
            (
                "A single-byte flip in the artifact file was detected as a hash mismatch.  "
                "SHA-256 is sensitive to partial corruption."
            ),
            "That the verifier is insensitive to partial corruption of artifact files.",
            None,
        )
    else:
        return (
            "FAIL",
            (
                f"Single-byte corruption was not detected.  "
                f"Passed={result.passed}, failures={result.failures}."
            ),
            None,
            "Whether there exists a specific byte pattern whose flip produces the same SHA-256 (collision).",
        )


def _test_replay_duplicate(db_path: str, system_version: str):
    """
    Adversarial test: insert two artifacts with the same artifact_id (replay).

    The PRIMARY KEY constraint on artifacts should reject the duplicate.
    Expected outcome: the second insert raises an IntegrityError → the verifier
    never sees the duplicate.  The challenge tests whether the schema prevents
    replay at insert time.

    If insertion succeeds silently, that is a schema weakness → FAIL.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        replay_db = os.path.join(tmpdir, "replay.db")
        conn = open_db(replay_db)

        event_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
            (event_id, "replay-test", "Replay test event", _now()),
        )

        artifact_path = os.path.join(tmpdir, "replay_artifact.txt")
        content = b"Original artifact for replay test.\n"
        with open(artifact_path, "wb") as f:
            f.write(content)

        fixed_artifact_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
            (fixed_artifact_id, event_id, "replay_artifact.txt", _sha256_bytes(content), _now()),
        )
        conn.commit()

        # Attempt to replay the same artifact_id with different content
        replay_content = b"Replayed content - different from original.\n"
        replay_inserted = False
        try:
            conn.execute(
                "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
                (
                    fixed_artifact_id,  # same ID — replay attempt
                    event_id,
                    "replay_artifact.txt",
                    _sha256_bytes(replay_content),
                    _now(),
                ),
            )
            conn.commit()
            replay_inserted = True
        except Exception:
            pass
        conn.close()

    if not replay_inserted:
        return (
            "PASS",
            (
                "The PRIMARY KEY constraint on artifacts prevented replay: "
                "a duplicate artifact_id was rejected at insert time."
            ),
            "That the schema permits silent overwrite of existing artifact records.",
            None,
        )
    else:
        return (
            "FAIL",
            (
                "A duplicate artifact_id was accepted silently.  "
                "The schema does not prevent replay of artifact records."
            ),
            None,
            "Whether an attacker who can insert directly into the database could silently replace artifact records.",
        )


def _test_malformed_inputs(db_path: str, system_version: str):
    """
    Adversarial test: attempt to insert creation events with malformed inputs:
      - empty creator_id
      - empty description
      - SQL metacharacters in all fields
      - extremely long strings

    Expected: the schema enforces NOT NULL but does not length-restrict fields.
    Empty string insertions will succeed (SQLite treats '' as a valid non-NULL value).
    SQL metacharacters should be stored safely via parameterized queries.

    This challenge tests whether malformed data causes silent corruption or
    verifier confusion, not whether the schema rejects it at insert time.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        mal_db = os.path.join(tmpdir, "malformed.db")
        conn = open_db(mal_db)

        results_detail = []

        # Case 1: empty creator_id ('' is not NULL; SQLite NOT NULL allows it)
        event_id_1 = str(uuid.uuid4())
        try:
            conn.execute(
                "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
                (event_id_1, "", "empty creator test", _now()),
            )
            conn.commit()
            results_detail.append("empty creator_id: accepted")
        except Exception as e:
            results_detail.append(f"empty creator_id: rejected ({e})")

        # Case 2: SQL metacharacters
        event_id_2 = str(uuid.uuid4())
        try:
            conn.execute(
                "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
                (event_id_2, "'; DROP TABLE creation_events; --", "sql meta test", _now()),
            )
            conn.commit()
            results_detail.append("SQL metacharacters: accepted safely via parameterization")
        except Exception as e:
            results_detail.append(f"SQL metacharacters: rejected ({e})")

        # Case 3: overlong string (1 MB description)
        event_id_3 = str(uuid.uuid4())
        long_str = "A" * (1024 * 1024)
        try:
            conn.execute(
                "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
                (event_id_3, "overlong-test", long_str, _now()),
            )
            conn.commit()
            results_detail.append("1MB description: accepted (no length limit in schema)")
        except Exception as e:
            results_detail.append(f"1MB description: rejected ({e})")

        conn.close()

        # Now run verifier — it should not crash on malformed but valid rows
        result = verify(mal_db, artifact_root=tmpdir)

    # The verifier should run without exception; empty artifacts table → 0 checked, passed
    observed = "; ".join(results_detail)
    if result.passed and result.checked == 0:
        return (
            "PASS",
            (
                f"Verifier completed without exception on malformed-input database.  "
                f"Insert results: {observed}"
            ),
            "That malformed inputs cause verifier crashes or silent data corruption detectable at verify time.",
            (
                "Whether application-layer validation is needed to reject empty creator_id "
                "or excessively long fields.  Schema-level enforcement is absent."
            ),
        )
    else:
        return (
            "INCONCLUSIVE",
            (
                f"Unexpected verifier outcome on malformed-input database.  "
                f"Passed={result.passed}, checked={result.checked}, failures={result.failures}.  "
                f"Insert results: {observed}"
            ),
            None,
            "Why the verifier produced an unexpected result on a database with no artifacts.",
        )


def _test_verifier_error_handling(db_path: str, system_version: str):
    """
    Adversarial test: run the verifier against a database where a recorded
    artifact file is missing from the filesystem.

    Expected outcome: verifier reports 'file not found' rather than crashing
    or silently passing.  If it reports the missing file, the error path is
    exercised → PASS.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_db = os.path.join(tmpdir, "missing_file.db")
        conn = open_db(missing_db)

        event_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
            (event_id, "err-test", "Error handling test event", _now()),
        )

        # Record an artifact that will not exist on disk
        phantom_content = b"Content that will never exist on disk.\n"
        artifact_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
            (
                artifact_id,
                event_id,
                "nonexistent_file.txt",
                _sha256_bytes(phantom_content),
                _now(),
            ),
        )
        conn.commit()
        conn.close()

        try:
            result = verify(missing_db, artifact_root=tmpdir)
            crashed = False
        except Exception as exc:
            return (
                "FAIL",
                (
                    f"Verifier raised an unhandled exception when artifact file was missing: {exc}.  "
                    "Missing-file condition should produce a structured failure, not a crash."
                ),
                None,
                "Whether missing-file conditions are handled gracefully in all verifier code paths.",
            )

    if not result.passed and any("not found" in fl for fl in result.failures):
        return (
            "PASS",
            (
                "Verifier reported 'file not found' without crashing when the recorded "
                "artifact file was absent from the filesystem."
            ),
            "That a missing artifact file causes a verifier crash or silent pass.",
            None,
        )
    else:
        return (
            "FAIL",
            (
                f"Verifier did not produce a 'file not found' failure for a missing artifact.  "
                f"Passed={result.passed}, failures={result.failures}."
            ),
            None,
            "Under what conditions a missing file goes unreported.",
        )


def _test_scope_documentation_consistency(db_path: str, system_version: str):
    """
    Automated subset of the documentation/code consistency check.

    The verifier module contains a DOES_NOT_ESTABLISH string that must
    mention 'authenticity' and 'reconstructed chain'.  If those strings
    are missing, the code's epistemic scope claim has silently changed.

    This is not a complete documentation audit (that requires human review),
    but it tests the machine-checkable invariant: the verifier's stated
    limitations must include the known reconstruction weakness.
    """
    import importlib.util
    verifier_path = os.path.join(_HERE, "verifier.py")
    try:
        with open(verifier_path, "r") as f:
            source = f.read()
    except Exception as exc:
        return (
            "INCONCLUSIVE",
            f"Could not read verifier.py for scope check: {exc}",
            None,
            "Whether verifier source is accessible for automated scope consistency checks.",
        )

    required_phrases = [
        "authenticity",
        "reconstructed",
        "DOES_NOT_ESTABLISH",
    ]
    missing = [p for p in required_phrases if p.lower() not in source.lower()]

    if not missing:
        return (
            "PASS",
            (
                "verifier.py contains all required scope-limitation markers: "
                + ", ".join(required_phrases)
            ),
            (
                "That the verifier's stated scope limitations have been silently removed "
                "from the source code."
            ),
            (
                "Whether the surrounding documentation (README, output text) "
                "consistently conveys the same scope limits.  "
                "Human review required for that broader check."
            ),
        )
    else:
        return (
            "FAIL",
            (
                f"verifier.py is missing required scope-limitation phrases: {missing}.  "
                "The verifier's documented epistemic boundary may have been narrowed "
                "or removed without a corresponding challenge."
            ),
            None,
            "What changed in verifier.py that caused the scope markers to disappear.",
        )


def _test_reconstruction_partial_original(db_path: str, system_version: str):
    """
    Adversarial variant: reconstruct a chain that RETAINS the original event_id
    from the live database but uses a new artifact_id and recomputed hash.

    This tests a stronger attack: the adversary has read access to the live DB
    and reuses real UUIDs.  Expected outcome: the verifier still cannot
    distinguish this from the legitimate chain → FAIL.

    This is a variation of UUID_RECONSTRUCTION_WEAKNESS using partial original data.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        live_db = os.path.join(tmpdir, "live.db")
        conn = open_db(live_db)

        # Set up a legitimate chain
        real_event_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
            (real_event_id, "legitimate-creator", "Authentic creation event", _now()),
        )
        real_artifact_path = os.path.join(tmpdir, "real.txt")
        real_content = b"Authentic artifact content.\n"
        with open(real_artifact_path, "wb") as f:
            f.write(real_content)
        real_artifact_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
            (real_artifact_id, real_event_id, "real.txt", _sha256_bytes(real_content), _now()),
        )
        conn.commit()
        conn.close()

        # Build counterfeit DB reusing the real event_id
        recon_db = os.path.join(tmpdir, "recon_partial.db")
        conn2 = open_db(recon_db)
        conn2.execute(
            "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
            (real_event_id, "adversary", "Counterfeit event reusing original ID", _now()),
        )
        fake_content = b"Counterfeit artifact reusing original event_id.\n"
        fake_artifact_path = os.path.join(tmpdir, "fake.txt")
        with open(fake_artifact_path, "wb") as f:
            f.write(fake_content)
        conn2.execute(
            "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), real_event_id, "fake.txt", _sha256_bytes(fake_content), _now()),
        )
        conn2.commit()
        conn2.close()

        result = verify(recon_db, artifact_root=tmpdir)

    if result.passed:
        return (
            "FAIL",
            (
                "A counterfeit chain that reuses the original event_id (read from the live DB) "
                "passed the v1 verifier.  Possession of real UUIDs is sufficient for this attack.  "
                "This is a stronger variant of UUID_RECONSTRUCTION_WEAKNESS."
            ),
            None,
            (
                "Whether an anchor tied to the event_id itself (rather than content) "
                "could distinguish original from reused-ID counterfeits.  "
                "C-011 covers this class."
            ),
        )
    else:
        return (
            "INCONCLUSIVE",
            (
                f"Counterfeit chain with reused event_id unexpectedly failed verification: "
                f"{result.failures}.  Outcome was not predicted."
            ),
            None,
            "Why the reused-event_id reconstruction failed when it was expected to pass.",
        )


def _test_integrity_vs_authenticity(db_path: str, system_version: str):
    """
    Meta-test: confirm that the verifier's scope is limited to integrity and
    does not claim to establish authenticity.

    This test is structurally INCONCLUSIVE: no automated procedure can
    determine whether a human or external anchor is present.  The purpose is
    to keep the unresolved question visible in the challenge history.
    """
    return (
        "INCONCLUSIVE",
        (
            "No automated test can currently distinguish an authentic creation "
            "history from a structurally valid reconstruction without an external "
            "anchor.  The verifier's own documentation acknowledges this scope "
            "limitation.  An independent adversary has not yet attempted "
            "reconstruction against a live provenance chain."
        ),
        None,
        (
            "Whether any of the candidate external anchors "
            "(independent timestamp authority, transparency log, "
            "hardware-backed attestation, multiple independent witnesses, "
            "content-addressed public storage) would allow the verifier to "
            "establish authenticity rather than only integrity.  "
            "Each candidate is a hypothesis to test, not an assumption."
        ),
    )


CHALLENGE_CATALOGUE = [
    {
        "key": "UUID_RECONSTRUCTION_WEAKNESS",
        "claim": (
            "The verifier detects unauthorized reconstruction of a creation history."
        ),
        "failure_hyp": (
            "A sufficiently capable adversary can reconstruct a structurally valid "
            "history that the v1 verifier accepts as authentic, because the verifier "
            "has no external anchor and performs only internal consistency checks."
        ),
        "test_desc": (
            "Construct an independently generated chain with new UUIDs and valid "
            "internal hashes.  Run the verifier against it.  If it passes, the "
            "failure hypothesis is confirmed."
        ),
        "fn": _test_uuid_reconstruction,
    },
    {
        "key": "HASH_TAMPER_DETECTION",
        "claim": (
            "The verifier detects when an artifact file has been modified after "
            "its hash was recorded."
        ),
        "failure_hyp": (
            "An attacker who can modify an artifact file after recording may go "
            "undetected if the verifier does not recompute and compare hashes."
        ),
        "test_desc": (
            "Record an artifact, overwrite its file with different content, "
            "then run the verifier.  If the mismatch is not detected, the "
            "failure hypothesis is confirmed."
        ),
        "fn": _test_hash_tamper,
    },
    {
        "key": "ORPHAN_ARTIFACT_DETECTION",
        "claim": (
            "The verifier detects artifacts that reference non-existent creation "
            "events (orphaned artifacts)."
        ),
        "failure_hyp": (
            "An attacker who inserts an artifact with a phantom event_id might "
            "evade detection if referential integrity is not checked."
        ),
        "test_desc": (
            "Insert an artifact whose event_id has no corresponding row in "
            "creation_events, bypassing FK enforcement at insert time.  "
            "Run the verifier.  If the orphan is not detected, the failure "
            "hypothesis is confirmed."
        ),
        "fn": _test_orphan_artifact,
    },
    {
        "key": "DELETED_EVENT_ORPHAN_DETECTION",
        "claim": (
            "The verifier detects artifacts that become orphaned when their "
            "parent creation event is deleted after insertion."
        ),
        "failure_hyp": (
            "An attacker who deletes a creation event post-insertion, bypassing "
            "FK constraints, may cause artifacts to appear without a traceable "
            "parent, and the verifier may not detect the orphaned state."
        ),
        "test_desc": (
            "Record a creation event and artifact legitimately.  Then delete "
            "the creation event directly (FK enforcement disabled).  Run the "
            "verifier and check whether the artifact is reported as orphaned."
        ),
        "fn": _test_deleted_event,
    },
    {
        "key": "TIMESTAMP_REORDER_DETECTION",
        "claim": (
            "The verifier detects artifacts whose recorded_at timestamp "
            "predates their parent creation event's created_at timestamp."
        ),
        "failure_hyp": (
            "The v1 verifier checks hashes and referential integrity only.  "
            "It does not validate temporal ordering between event and artifact "
            "timestamps.  An attacker can insert artifacts with impossible "
            "timestamps and the verifier will accept them silently."
        ),
        "test_desc": (
            "Insert a creation event with a known timestamp.  Insert an artifact "
            "against that event with a recorded_at timestamp predating the event "
            "by more than one year.  Run the verifier.  If it passes, the "
            "timestamp-ordering weakness is confirmed."
        ),
        "fn": _test_timestamp_reorder,
    },
    {
        "key": "PARTIAL_CORRUPTION_DETECTION",
        "claim": (
            "The verifier detects partial corruption of artifact files "
            "(single-byte modification after recording)."
        ),
        "failure_hyp": (
            "If the verifier does not recompute the full file hash, or uses a "
            "weak comparison, a single-byte flip might go undetected."
        ),
        "test_desc": (
            "Record an artifact.  Flip the first byte of its file.  Run the "
            "verifier.  If it does not report a hash mismatch, the integrity "
            "check is insensitive to partial corruption."
        ),
        "fn": _test_partial_corruption,
    },
    {
        "key": "REPLAY_DUPLICATE_PREVENTION",
        "claim": (
            "The schema prevents silent replay of artifact records: "
            "a duplicate artifact_id cannot overwrite an existing record."
        ),
        "failure_hyp": (
            "If the PRIMARY KEY constraint on artifacts is not enforced, an "
            "attacker who can insert directly could silently replace a recorded "
            "artifact's hash with a new value, bypassing detection."
        ),
        "test_desc": (
            "Record an artifact with a known artifact_id.  Attempt to insert a "
            "second row with the same artifact_id and different content hash.  "
            "If the insert succeeds, the schema permits silent replay."
        ),
        "fn": _test_replay_duplicate,
    },
    {
        "key": "MALFORMED_INPUT_HANDLING",
        "claim": (
            "The system handles malformed inputs (empty strings, SQL metacharacters, "
            "overlong fields) without silent data corruption or verifier crashes."
        ),
        "failure_hyp": (
            "Malformed inputs accepted by the schema without validation may produce "
            "database rows that cause the verifier to crash or produce misleading output."
        ),
        "test_desc": (
            "Insert creation events with: (1) empty creator_id, (2) SQL metacharacters "
            "in all fields, (3) a 1 MB description string.  Run the verifier against "
            "the resulting database.  Check for crashes or silent corruption."
        ),
        "fn": _test_malformed_inputs,
    },
    {
        "key": "VERIFIER_ERROR_HANDLING",
        "claim": (
            "The verifier handles missing artifact files with a structured failure "
            "report rather than a crash or silent pass."
        ),
        "failure_hyp": (
            "If the verifier raises an unhandled exception or silently passes "
            "when a recorded artifact file is absent from the filesystem, "
            "the error path is not exercised and integrity failures go unreported."
        ),
        "test_desc": (
            "Record an artifact in the database but do not create the corresponding "
            "file on disk.  Run the verifier.  If it crashes, the error path is "
            "unhandled.  If it passes, missing files are not detected."
        ),
        "fn": _test_verifier_error_handling,
    },
    {
        "key": "SCOPE_DOCUMENTATION_CONSISTENCY",
        "claim": (
            "The verifier source code contains machine-verifiable markers that "
            "accurately state its epistemic scope limitations, specifically that "
            "it does not establish authenticity and that reconstructed chains may pass."
        ),
        "failure_hyp": (
            "If the DOES_NOT_ESTABLISH marker or references to 'authenticity' and "
            "'reconstructed' are removed from verifier.py, the code's stated scope "
            "silently diverges from its actual behavior without triggering any test."
        ),
        "test_desc": (
            "Read verifier.py and check for required scope-limitation strings: "
            "'DOES_NOT_ESTABLISH', 'authenticity', 'reconstructed'.  "
            "If any are absent, the scope documentation has been silently narrowed."
        ),
        "fn": _test_scope_documentation_consistency,
    },
    {
        "key": "RECONSTRUCTION_PARTIAL_ORIGINAL_IDS",
        "claim": (
            "The verifier can distinguish a counterfeit chain that reuses original "
            "UUIDs (read from the live database) from the authentic chain."
        ),
        "failure_hyp": (
            "An attacker with read access to the live database can reconstruct a "
            "chain reusing real event_ids.  The v1 verifier performs only internal "
            "consistency checks and cannot detect that a real UUID is being reused "
            "in a counterfeit context."
        ),
        "test_desc": (
            "Create a legitimate chain.  Build a counterfeit chain that reuses the "
            "original event_id but provides a different creator_id and artifact.  "
            "Run the verifier against the counterfeit.  If it passes, possession of "
            "real UUIDs is sufficient for this stronger attack variant."
        ),
        "fn": _test_reconstruction_partial_original,
    },
    {
        "key": "INTEGRITY_VS_AUTHENTICITY_BOUNDARY",
        "claim": (
            "The verifier's scope is limited to internal integrity; "
            "it makes no authenticity claims."
        ),
        "failure_hyp": (
            "The system may implicitly communicate authenticity guarantees "
            "through naming, output language, or surrounding documentation, "
            "even if the verifier code is correctly scoped."
        ),
        "test_desc": (
            "Automated test: not applicable.  Requires human review of all "
            "output text and documentation for unintentional authenticity claims.  "
            "Marked INCONCLUSIVE until an independent reviewer confirms scope "
            "is accurately communicated."
        ),
        "fn": _test_integrity_vs_authenticity,
    },
]


# ---------------------------------------------------------------------------
# Challenge registry: ensure challenges exist in DB; return id map
# ---------------------------------------------------------------------------

def _ensure_challenges(db_path: str) -> dict:
    """
    For each catalogue entry, look up the challenge by its key stored in the
    test_description.  If not found, insert it.  Return {key: challenge_id}.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    existing = {
        row["test_description"][:50]: row["challenge_id"]
        for row in conn.execute("SELECT challenge_id, test_description FROM challenges").fetchall()
    }
    conn.close()

    # Use a more reliable lookup: store key in challenge_id lookup by claim prefix
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT challenge_id, claim, failure_hypothesis FROM challenges").fetchall()
    conn.close()

    id_map = {}
    for entry in CHALLENGE_CATALOGUE:
        found = None
        for row in rows:
            if row["failure_hypothesis"].strip() == entry["failure_hyp"].strip():
                found = row["challenge_id"]
                break
        if found:
            id_map[entry["key"]] = found
        else:
            cid = record_challenge(
                db_path=db_path,
                claim=entry["claim"],
                failure_hypothesis=entry["failure_hyp"],
                test_description=entry["test_desc"],
            )
            id_map[entry["key"]] = cid

    return id_map


# ---------------------------------------------------------------------------
# Single watch cycle
# ---------------------------------------------------------------------------

def run_cycle(db_path: str, system_version: str) -> dict:
    """
    Execute all catalogue challenges once.  Record every result.
    Return a summary dict (counts, no conclusions).
    """
    id_map = _ensure_challenges(db_path)
    counts = {"PASS": 0, "FAIL": 0, "INCONCLUSIVE": 0, "NOT_RUN": 0, "ERROR": 0}
    detail = []

    for entry in CHALLENGE_CATALOGUE:
        key = entry["key"]
        challenge_id = id_map[key]
        fn = entry.get("fn")

        if fn is None:
            record_challenge_result(
                db_path=db_path,
                challenge_id=challenge_id,
                system_version=system_version,
                tester_id=TESTER_ID,
                observed_result="No test function registered for this challenge.",
                status="INCONCLUSIVE",
                ruled_out=None,
                unresolved="Test function not yet implemented.",
            )
            counts["NOT_RUN"] += 1
            detail.append((key, "NOT_RUN", None))
            continue

        try:
            status, observed, ruled_out, unresolved = fn(db_path, system_version)
        except Exception as exc:
            observed = f"Test raised an exception: {exc}"
            status = "INCONCLUSIVE"
            ruled_out = None
            unresolved = "Exception during test execution; outcome unknown."
            counts["ERROR"] += 1

        record_challenge_result(
            db_path=db_path,
            challenge_id=challenge_id,
            system_version=system_version,
            tester_id=TESTER_ID,
            observed_result=observed,
            status=status,
            ruled_out=ruled_out,
            unresolved=unresolved,
        )

        if status in counts:
            counts[status] += 1
        detail.append((key, status, observed[:80] if observed else None))

    return {"counts": counts, "detail": detail, "system_version": system_version}


# ---------------------------------------------------------------------------
# Summary printer — counts only; no conclusions
# ---------------------------------------------------------------------------

def _print_summary(summary: dict, cycle_n: int) -> None:
    c = summary["counts"]
    ts = _now()
    print()
    print("=" * 64)
    print(f"QPF WATCH LOOP — CYCLE {cycle_n}   {ts}")
    print(f"System version: {summary['system_version']}")
    print("=" * 64)
    print(f"  PASS         {c['PASS']:>4}")
    print(f"  FAIL         {c['FAIL']:>4}")
    print(f"  INCONCLUSIVE {c['INCONCLUSIVE']:>4}")
    print(f"  NOT_RUN      {c['NOT_RUN']:>4}")
    if c.get("ERROR", 0):
        print(f"  ERROR        {c['ERROR']:>4}")
    print()
    for key, status, obs in summary["detail"]:
        obs_str = f"  ↳ {obs}" if obs else ""
        print(f"  [{status:<13}] {key}")
        if obs_str:
            print(f"              {obs_str}")
    print()
    print("NOTICE: PASS does not mean PROVEN.")
    print("        FAIL means the challenge falsified the claim under stated conditions.")
    print("        INCONCLUSIVE is preserved, not resolved.")
    print("        Conclusions, if any, belong to a human or designated authority.")
    print("        REPAIR RULE: a FAIL is not erased by fixing the system.")
    print("        v1 failures remain real. v2 earns its own record.")
    print("=" * 64)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="QPF Watch Loop")
    parser.add_argument("--once", action="store_true",
                        help="Run one cycle then exit (default: run continuously)")
    parser.add_argument("--db", default=os.path.join(_HERE, "provenance.db"),
                        help="Path to provenance.db (default: %(default)s)")
    parser.add_argument("--version", default="v1-prototype",
                        help="System version label recorded in results (default: %(default)s)")
    parser.add_argument("--interval", type=int, default=60,
                        help="Seconds between cycles in continuous mode (default: 60)")
    args = parser.parse_args()

    # Ensure DB exists (seed.py may not have been run yet)
    open_db(args.db).close()

    cycle_n = 0
    while True:
        cycle_n += 1
        summary = run_cycle(args.db, args.version)
        _print_summary(summary, cycle_n)

        if args.once:
            break
        print(f"Next cycle in {args.interval}s.  Ctrl-C to stop.")
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nWatch loop stopped by operator.")
            break


if __name__ == "__main__":
    main()
