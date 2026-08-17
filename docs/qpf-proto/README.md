# QPF Creation-Provenance Prototype

A minimal Python + SQLite prototype for the Quantum Pi Forge (QPF)
creation-provenance system.  No frameworks.  No external dependencies.

---

## Structure

```
provenance.db
    │
    ├── creation_events    when something was created and by whom
    ├── artifacts          content hashes linked to creation events
    ├── challenges         immutable challenge definitions
    └── challenge_results  outcomes of executing a challenge (one per attempt)
```

`challenges` rows are **immutable** — enforced by a database trigger.
No challenge definition may be altered after insertion.

`challenge_results` records each execution attempt against a frozen
challenge.  Multiple result rows may exist per challenge, one per
system version or tester:

```
same challenge_id → system v1 → result (INCONCLUSIVE: not yet stranger-tested)
same challenge_id → system v1 → result (stranger attempt #1)
same challenge_id → system v2 → result (after any change)
```

This produces a verifiable empirical history: same question, different
answers over time.

`challenges` is **not** an evidence ledger and **not** a proof ledger.
It is a test record.  Each challenge row answers:

| Column | Question |
|---|---|
| `claim` | What is the system supposed to do? |
| `failure_hypothesis` | Specifically how might that claim be false? |
| `test_description` | How is the challenge to be run? |

Each `challenge_results` row answers:

| Column | Question |
|---|---|
| `observed_result` | What actually happened? |
| `ruled_out` | What does the result eliminate? (stated narrowly) |
| `unresolved` | What remains open after this attempt? |
| `status` | PASSED / FAILED / INCONCLUSIVE |

A result with `status = PASSED` establishes only that this particular
attempt did not falsify the system under the stated conditions.  It does
not establish correctness.

---

## The core distinction this prototype exposes

> **Integrity ≠ Authenticity**

The verifier checks internal consistency: hashes match, artifacts
reference real events.  A reconstructed chain — new UUIDs, recomputed
hashes, same artifact files — passes every integrity check.

This is not a bug.  It is the boundary of what a purely internally-chained
history can prove.

**Challenge #1 (KNOWN_LIMITATION)** documents this boundary explicitly.

The open research question is:

> What external anchor, if any, is required to distinguish an intact
> record from an authentic historical record?

Candidate anchors (hypotheses to test, not answers):
- Independent timestamps
- Human signatures
- Hardware-backed signatures
- External publication
- Append-only witnesses
- Multiple independent witnesses
- Content-addressed storage
- Transparency logs

None of these are assumed correct.  Each is a candidate for the
skeptical-stranger test.

---

## Files

| File | Purpose |
|---|---|
| `schema.py` | DDL + `open_db()` helper; immutability trigger on challenges |
| `provenance.py` | Record creation events, artifacts, challenges, and results |
| `verifier.py` | Integrity checks (not authenticity checks) |
| `seed.py` | Populate DB with sample event + challenge #1 + result #1 |
| `verify.py` | Run verifier and print structured report |

---

## Quick start

```bash
cd /tmp/qpf-proto
python seed.py      # creates provenance.db + seed_artifact.txt
python verify.py    # integrity check – will PASS
                    # read the report: note what it does NOT establish
```

---

## Next gate: skeptical-stranger test

Give someone the database, verifier, artifact, and challenge. Let them attack it.
Record exactly what happens.

Three possible outcomes — all valid findings:

**If the reconstruction succeeds:**
Record: *Internal integrity does not establish historical authenticity.*
That is a significant empirical result.

**If the reconstruction fails:**
Do not conclude: *"Integrity therefore equals authenticity."*
Record: *This particular reconstruction attempt did not falsify the verifier's
authenticity boundary.*  Then design a stronger attack.

**If something unexpected happens:**
Record it without forcing it into success/failure.
The `challenges` schema exists precisely for this case.

No blockchain. No new authority. No premature fix.
The experiment decides what the prototype actually demonstrates.



This prototype graduates to the canonical repo only after:

1. A skeptical-stranger tamper test is executed.
2. The result is recorded in the `challenges` table.
3. The integrity ≠ authenticity distinction is empirically demonstrated
   (or refuted) by that test.

The outcome — whatever it is — is the finding.

---

## What this is not

- Not a proof system.
- Not a warrant system (`WARRANT` is intentionally absent from the schema).
- Not a blockchain.  Blockchain is a candidate anchor hypothesis, not a
  built-in assumption.

The `challenges` table schema enforces epistemic humility: `ruled_out`
and `unresolved` are mandatory design choices, not optional fields.
