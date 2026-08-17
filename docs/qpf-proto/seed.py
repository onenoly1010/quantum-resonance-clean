"""
QPF Prototype – Seed script.

Populates provenance.db with:
  1. A sample creation event and artifact (demonstrates normal operation).
  2. Challenge #1: the UUID-reconstruction weakness.
  3. A challenge_results row recording the known v1 behavior (INCONCLUSIVE —
     the challenge has not yet been executed by a skeptical stranger).

Challenge rows are immutable after insertion.  The original challenge
definition will not change as the system evolves; future test attempts
add new challenge_results rows against the same challenge_id.

Run once:  python seed.py
"""

import os
import sys
from provenance import record_creation, record_artifact, record_challenge, record_challenge_result
from schema import open_db

DB = "provenance.db"
ARTIFACT = "seed_artifact.txt"


def seed():
    if os.path.exists(DB):
        print(f"{DB} already exists – delete it first to re-seed.")
        sys.exit(1)

    # --- Create a sample artifact file ---
    with open(ARTIFACT, "w") as f:
        f.write("This is a sample artifact for the QPF prototype.\n")
        f.write("Its hash will be recorded in provenance.db.\n")

    # --- Record a creation event ---
    event_id = record_creation(
        DB,
        creator_id="prototype-seed",
        description="Initial QPF prototype creation event",
    )
    print(f"creation_event: {event_id}")

    artifact_id = record_artifact(DB, event_id, ARTIFACT)
    print(f"artifact:       {artifact_id}")

    # --- Challenge #1: UUID-reconstruction weakness (immutable definition) ---
    challenge_id = record_challenge(
        db_path=DB,
        claim=(
            "The verifier detects unauthorized reconstruction of a creation history."
        ),
        failure_hypothesis=(
            "A sufficiently capable adversary can reconstruct a structurally valid "
            "history that the v1 verifier accepts as authentic, because the verifier "
            "has no external anchor and performs only internal consistency checks.  "
            "This is a hypothesis.  Whether it survives the skeptical-stranger test "
            "is what the test determines."
        ),
        test_description=(
            "Construct an independently generated chain representing the same apparent "
            "history, using new identifiers and valid internal hashes, then run "
            "verification against the reconstructed chain.  Compare the result to "
            "verification of the authentic chain."
        ),
    )
    print(f"challenge:      {challenge_id}")

    # --- Result #1: known v1 behavior, not yet stranger-tested ---
    # Status is INCONCLUSIVE because the challenge has not yet been executed
    # by an independent adversary.  The verifier is known to perform only
    # internal consistency checks, but whether a stranger will exploit this
    # is what the test determines.
    result_id = record_challenge_result(
        db_path=DB,
        challenge_id=challenge_id,
        system_version="v1-prototype",
        tester_id="prototype-seed-self-analysis",
        observed_result=(
            "Self-analysis only (not a stranger test).  The verifier performs "
            "internal consistency checks only.  A chain with new UUIDs and "
            "recomputed hashes is expected to pass based on code inspection.  "
            "Empirical confirmation by an independent adversary: PENDING."
        ),
        status="INCONCLUSIVE",        ruled_out=(
            "Nothing.  No independent adversarial reconstruction has been attempted."
        ),
        unresolved=(
            "Whether provenance can distinguish an authentic historical chain from "
            "a structurally valid counterfeit chain.  "
            "What external anchor, if any, is required to establish that distinction.  "
            "Candidate anchors (not yet evaluated): independent timestamps, "
            "human signatures, hardware-backed signatures, external publication, "
            "append-only witnesses, multiple independent witnesses, "
            "content-addressed storage, transparency logs.  "
            "None of these are assumed correct; each is a hypothesis to test."
        ),
    )
    print(f"result:         {result_id}")
    print()
    print("Seeding complete.")
    print("Run  python verify.py  to check integrity of the seeded chain.")
    print()
    print("IMPORTANT: A passing verification does not establish authenticity.")
    print("Challenge #1 is immutable.  Record stranger-test outcomes via")
    print("record_challenge_result() against the same challenge_id.")


if __name__ == "__main__":
    seed()

