"""
QPF Prototype – Database schema.

provenance.db contains three tables:
  creation_events  – when something was created and by whom
  artifacts        – content hashes linked to creation events
  challenges       – structured test records (not an evidence ledger)

'challenges' records what was tested, what happened, what was ruled out,
and what remains unresolved.  Nothing in this table constitutes a warrant
or proof.  A row with status=PASSED establishes only that the particular
challenge did not falsify the system under the stated conditions.
"""

import sqlite3


DDL = """
CREATE TABLE IF NOT EXISTS creation_events (
    event_id     TEXT PRIMARY KEY,
    creator_id   TEXT NOT NULL,
    description  TEXT NOT NULL,
    created_at   TEXT NOT NULL          -- ISO-8601 UTC
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id  TEXT PRIMARY KEY,
    event_id     TEXT NOT NULL REFERENCES creation_events(event_id),
    filename     TEXT NOT NULL,
    sha256       TEXT NOT NULL,
    recorded_at  TEXT NOT NULL          -- ISO-8601 UTC
);

CREATE TABLE IF NOT EXISTS challenges (
    challenge_id       TEXT PRIMARY KEY,
    claim              TEXT NOT NULL,   -- what the system is supposed to do
    failure_hypothesis TEXT NOT NULL,   -- specific way the claim might be false
    test_description   TEXT NOT NULL,   -- how the challenge was/will be run
    observed_result    TEXT,            -- NULL means not yet executed
    ruled_out          TEXT,            -- what the result rules out (narrow)
    unresolved         TEXT,            -- what remains open after the test
    status             TEXT NOT NULL    -- OPEN | PASSED | FAILED | KNOWN_LIMITATION
        CHECK(status IN ('OPEN', 'PASSED', 'FAILED', 'KNOWN_LIMITATION')),
    created_at         TEXT NOT NULL    -- ISO-8601 UTC
);
"""


def open_db(path: str = "provenance.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(DDL)
    conn.commit()
    return conn
