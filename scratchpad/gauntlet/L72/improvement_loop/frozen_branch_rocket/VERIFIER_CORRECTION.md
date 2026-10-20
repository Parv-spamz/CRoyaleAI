# Load compressed detail arrays once

The original independent verifier repeatedly accessed compressed NPZ members
inside its 54723-row loop, inflating the same arrays for every row. This is a
performance defect, not a changed metric or an observed data mismatch. Codex
stopped only the exact verifier process58876 after checking its command line.
Preserve verify.py, started.json, producer results and the original nonzero
l72-frozen-branch-rocket-independent receipt (256.28s, no success token).

Separate ../verify_frozen_branch_rocket_v2.py materializes every detail array
once before the loop. All original source/input bindings, raw-array reads,
scalar computations, controls, rows and comparisons remain unchanged. The
helper additionally requires the failed receipt and binds its own source hash.
Write verified_v2.json under a fresh independent-v2 receipt. No producer, policy,
optimizer, old completed test or gameplay rerun; no threshold change.
