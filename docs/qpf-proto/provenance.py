"""
QPF Prototype – Provenance recording.

Records creation events and artifact hashes into provenance.db.
Does not make claims about authenticity.  Records only what is
directly observable: content, identity, and time.
"""

import hashlib
import os
import uuid
from datetime import datetime, timezone
from schema import open_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def record_creation(db_path: str, creator_id: str, description: str) -> str:
    """Insert a creation event; return its event_id."""
    conn = open_db(db_path)
    event_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO creation_events VALUES (?, ?, ?, ?)",
        (event_id, creator_id, description, _now()),
    )
    conn.commit()
    conn.close()
    return event_id


def record_artifact(db_path: str, event_id: str, filepath: str) -> str:
    """Hash a file and record it against an event; return artifact_id."""
    conn = open_db(db_path)
    artifact_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?)",
        (artifact_id, event_id, os.path.basename(filepath), _sha256(filepath), _now()),
    )
    conn.commit()
    conn.close()
    return artifact_id


def record_challenge(
    db_path: str,
    claim: str,
    failure_hypothesis: str,
    test_description: str,
) -> str:
    """Insert an immutable challenge definition; return its challenge_id.

    Challenge rows cannot be modified after insertion (enforced by a
    database trigger).  To record the outcome of executing a challenge,
    use record_challenge_result().
    """
    conn = open_db(db_path)
    challenge_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO challenges VALUES (?, ?, ?, ?, ?)",
        (challenge_id, claim, failure_hypothesis, test_description, _now()),
    )
    conn.commit()
    conn.close()
    return challenge_id


def record_challenge_result(
    db_path: str,
    challenge_id: str,
    system_version: str,
    tester_id: str,
    observed_result: str,
    status: str,
    ruled_out: str | None = None,
    unresolved: str | None = None,
) -> str:
    """Record the outcome of one execution attempt against a frozen challenge.

    Multiple results rows may exist for the same challenge_id, one per
    system version or tester.  The challenge definition itself is never
    modified.
    """
    conn = open_db(db_path)
    result_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO challenge_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            result_id,
            challenge_id,
            system_version,
            tester_id,
            observed_result,
            ruled_out,
            unresolved,
            status,
            _now(),
        ),
    )
    conn.commit()
    conn.close()
    return result_id
