"""
QPF Prototype – Database schema.

provenance.db contains three tables:
  creation_events  – when something was created and by whom
  artifacts        – content hashes linked to creation events
  challenges       – structured test records (not an evidence ledger)

'challenges' records what was tested, what happened, what was ruled out,
and what remains unresolved.  Nothing in this table constitutes a warrant
or proof.  A row with status=PASS establishes only that the particular
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

-- challenges rows are immutable after insertion.
-- The BEFORE UPDATE trigger below enforces this.
-- To record a new result against the same challenge, insert a row in
-- challenge_results instead.  This preserves the original challenge
-- definition so that the same challenge can be run against future
-- versions and compared over time.
CREATE TABLE IF NOT EXISTS challenges (
    challenge_id       TEXT PRIMARY KEY,
    claim              TEXT NOT NULL,   -- what the system is supposed to do
    failure_hypothesis TEXT NOT NULL,   -- specific way the claim might be false
    test_description   TEXT NOT NULL,   -- how the challenge was/will be run
    created_at         TEXT NOT NULL    -- ISO-8601 UTC
);

-- Immutability trigger: no column of a challenges row may be changed
-- after insertion.  Attempting an UPDATE raises an error.
CREATE TRIGGER IF NOT EXISTS challenges_immutable
BEFORE UPDATE ON challenges
BEGIN
    SELECT RAISE(ABORT, 'challenges rows are immutable: record a new challenge_results row instead');
END;

-- challenge_results records each attempt to execute a challenge.
-- Multiple results rows may exist for the same challenge_id, enabling
-- version-over-version comparison:
--   same challenge_id → system_version v1 → result
--   same challenge_id → system_version v2 → result
--   same challenge_id → system_version v3 → result
CREATE TABLE IF NOT EXISTS challenge_results (
    result_id      TEXT PRIMARY KEY,
    challenge_id   TEXT NOT NULL REFERENCES challenges(challenge_id),
    system_version TEXT NOT NULL,       -- label for the system under test
    tester_id      TEXT NOT NULL,       -- who executed the challenge
    observed_result TEXT NOT NULL,      -- what actually happened
    ruled_out      TEXT,                -- what the result eliminates (narrow)
    unresolved     TEXT,                -- what remains open after this attempt
    status         TEXT NOT NULL        -- PASS | FAIL | INCONCLUSIVE | NOT_RUN | SUPERSEDED
        CHECK(status IN ('PASS', 'FAIL', 'INCONCLUSIVE', 'NOT_RUN', 'SUPERSEDED')),
    executed_at    TEXT NOT NULL        -- ISO-8601 UTC
);
"""


def open_db(path: str = "provenance.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(DDL)
    conn.commit()
    return conn
