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
