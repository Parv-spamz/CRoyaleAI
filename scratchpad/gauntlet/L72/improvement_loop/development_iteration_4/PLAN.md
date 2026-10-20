# One-factor phase-balanced expert exposure

October5 15:03 EDT. The match_adaptation producer finds late-clock expert Rocket
choices rise while X-Bow choices fall, but ordinary_v6 retains poor late expert
Rocket full-action agreement. Final selection of this leaf requires the completed
independent diagnostic recount; no optimization before that evidence and P1-P3.

Test phase_balanced_v6 against the independently verified iteration1 ordinary_v6.
Start from the SAME R1e31u0155 weights, corrected-v5 inputs, v6 architecture and
original expert losses. The ONLY change is the training draw schedule:32 rows
uniformly with replacement from each of the four existing clock bins per batch,
then shuffle the128 positions. All training rows remain eligible, including WAIT,
non-Rocket choices, failed/truncated defenses, high-HP states and native grade
mismatches. No filtering by future outcome, chosen card, margin or cached error.
No extra damage, phase, opponent or history input is introduced.

Use sorted original training IDs for each pool; NumPy default_rng(20261007), one
choice(pool,32) call for phases0,1,2,3 in that order, then permutation(128), repeated
1000 times. Reuse iteration1's exact mirror vector, model/dropout seed20261005,
1000 updates, batch128, AdamW weight decay.01, baseLR1e-5, targetLR1e-3, clip1,
fp32 and final-step-only evaluation. Do not warm-start from an optimized candidate.
Do not combine the rejected defense mixture or3x Rocket aim-loss recipes.

Clock bins are the frozen [0,2400),[2400,3600),[3600,4800),[4800,infinity) ticks
at20Hz. Historical records lack explicit multiplier/game-mode observations;
these are clock strata, not proof of measured1x/2x/3x elixir or a forced tactic.
Independent raw native joins already bound these row ticks. Existing model time
inputs are unchanged. Actual lock success remains unknown in this corpus.

Preparation independently regenerates the full schedule, split exclusions and
phase membership from original row ticks, verifies all labels unchanged and binds
source/data/control hashes. Then a checkpoint-free first-training-batch smoke
checks the new schedule plumbing with the unchanged loss/optimizer, plain metadata
roundtrip, and independently derived development masks before activation.

Development continuation versus ordinary_v6 requires late-clock full-action gain
at least2pp and late expert Rocket full-action gain at least2pp. General card and
each other phase's full-action decline must be no worse than0.5pp. Global expert
Rocket forced aim and full action must not decline. No Witch/Night Witch/Furnace
or defensive-sequence action point decline; primary Barrel correct-lane count
must not fall and wrong-lane count must not rise. Missing strata are inconclusive.
These are fixed development filters, not relaxed or substituted final gates.

Use only the existing whole-replay213995 training/54723 development rows; parent
exposure is disclosed. No old validation, reserved confirmation or owner-live
expert labels. No frequency target/reward or policy rule. Report every phase,
weakest-tower-margin/history subgroup and whole-replay paired changes, including
regressions. Cached control results remain unchanged. Imitation is not safety,
causal damage-lead retention, lock attribution or gameplay improvement.

Run one fail-closed serial train/eval/independent chain under the existing GPU
lock. Preserve failures, no automatic resume or adaptive extra updates. Report
the new model once to Discord after reviewed results, marked developmental and
NOT ACCEPTED. No live restart or deployment before all final gates.
