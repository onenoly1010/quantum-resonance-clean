"""
QPF Prototype – Seed script.

Populates provenance.db with:
  1. A sample creation event and artifact (demonstrates normal operation).
  2. Challenge #1: the UUID-reconstruction weakness (KNOWN_LIMITATION).

Run once:  python seed.py
"""

import os
import sys
from provenance import record_creation, record_artifact, record_challenge
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

    # --- Challenge #1: UUID-reconstruction weakness ---
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
        observed_result=(
            "Known v1 behavior: reconstruction is currently accepted.  "
            "The verifier passes a chain with new UUIDs and recomputed hashes "
            "because it performs only internal consistency checks."
        ),
        ruled_out=(
            "Nothing about adversarial reconstruction has been ruled out.  "
            "This challenge has not yet been executed against a skeptical stranger."
        ),
        unresolved=(
            "Whether provenance can distinguish an authentic historical chain from "
            "a structurally valid counterfeit chain.  "
            "What external anchor, if any, is required to establish that distinction.  "
            "Candidate anchors (not yet evaluated): independent timestamps, "
            "human signatures, hardware-backed signatures, external publication, "
            "append-only witnesses, multiple independent witnesses, "
            "content-addressed storage, transparency logs.  "
            "None of these are to be assumed correct; each is a hypothesis to test."
        ),
        status="KNOWN_LIMITATION",
    )
    print(f"challenge:      {challenge_id}")
    print()
    print("Seeding complete.")
    print("Run  python verify.py  to check integrity of the seeded chain.")
    print()
    print("IMPORTANT: A passing verification does not establish authenticity.")
    print("See challenge #1 (UUID_RECONSTRUCTION_WEAKNESS) for what remains unresolved.")


if __name__ == "__main__":
    seed()
