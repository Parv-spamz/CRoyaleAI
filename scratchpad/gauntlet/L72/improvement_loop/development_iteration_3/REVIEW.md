# Registered Rocket aim-loss experiment

The20% defensive-sequence curriculum failed its fixed development criteria:
defense action -0.33pp, fewer correct Rocket actions within sequences and small
Witch/Furnace regressions. Preserve that outcome. Iteration1 isolated generic
projectile targeting passes its development continuation criteria but Rocket
aim remains weak. PLAN/METRICS register a separate one-factor cell-loss emphasis
on all original expert Rocket PLAY labels, including troop targets.

No exposure change, inferred tower/low-HP target, second model forward pass,
card/gate/WAIT/value weighting, tactical rule or Rocket-frequency reward. Weight1
must reproduce original loss/gradients; weight3 adds twice the Rocket cell CE
sum divided by the unchanged total PLAY count. The same v6 architecture, R1e
initialization, ordinary draws/mirroring and fixed1000-step recipe are retained.

Preflight completed October5 14:05 in129.91s, exit0/token matched. Weight1 reproduces
original loss and every parameter gradient exactly with the same dropout RNG.
All base/non-cell terms remain unchanged; added cell gradient is zero outside
original expert PLAY Rocket rows and positive within them. Removing Rocket cards
or their PLAY gates removes the added term. Independent original/defense masks
match; standard weights-only in-memory roundtrip preserves tensors. CPU smoke
loss5.9850544929504395 (two expert Rockets) is not full training and saves no
checkpoint; no development predictions occurred during preflight.

A2/A3 COMPLETE at14:12:16 EDT. Exactly1000 finite updates and all54723 development
rows/405 replay groups independently reconcile. Training/evaluation/recount
receipts exit0. Existing verified R1e/ordinary_v6 predictions were reused.

The candidate is REJECTED under the unchanged development criteria. Counts below
are R1e on the SAME corrected observations / ordinary_v6 / rocket_aim3_v6:

| Metric | R1e | Control | Candidate | Denominator |
|---|---:|---:|---:|---:|
| Expert Rocket forced aim within1 tile | 290 | 293 | 286 | 955 |
| Full expert Rocket action | 54 | 73 | 74 | 955 |
| Barrel correct / wrong / not fired | 36/20/7 | 55/7/1 | 56/6/1 | 63 |
| Witch action | 332 | 341 | 341 | 726 |
| Night Witch action | 156 | 161 | 162 | 373 |
| Furnace action | 538 | 550 | 548 | 1174 |
| Defensive-sequence action | 3952 | 4009 | 4015 | 8183 |
| Defense expert Rocket action | 15 | 23 | 21 | 223 |
| General card agreement | 11348 | 11399 | 11393 | 17192 PLAY |
| All full actions | 30968 | 31988 | 32006 | 54723 |

Rocket aim -0.733pp versus required+5pp; action+0.105pp versus required+2pp.
Furnace action falls2 rows, failing its protection. Rocket aim improves7 replay
groups, worsens14, ties315; full Rocket action improves4/worsens3/ties329. Furnace
action improves1/worsens2/ties17. Other protection point filters pass. These are
clustered descriptive counts, not independent-row significance or gameplay wins.

reviewed_results.json binds cache/replay/checkpoint hashes,1000 finite log entries,
five process/delivery receipts, message hash and both control paired summaries.
l72-development3-reviewed provides separate review process evidence. The requested
new-model report was delivered ONCE via the intended sender, one HTTP204 chunk.
Do not resend. The report says DEVELOPMENT/NOT ACCEPTED, not fresh generalization.
No live change or deployment. All original sources and failed criteria remain.

The owner clarified the broader objective while this frozen run completed: learn
phase/matchup adaptation and damage-lead Rocket cycling, not just finishes. See
../MATCH_ADAPTATION_AMENDMENT.md and ../match_adaptation/PLAN.md. This failed cell-
loss recipe does not settle that strategic hypothesis. Next diagnose context and
causal history before choosing another controlled recipe; do not launch a blind
weight grid or re-tune completed criteria.
