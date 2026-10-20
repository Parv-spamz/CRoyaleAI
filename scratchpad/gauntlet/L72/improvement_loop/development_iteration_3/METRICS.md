# Unchanged measurements, new one-factor comparison

Reuse iteration1 METRICS and iteration2 defense masks byte-for-byte. Independently
reconstruct original masks/defense membership from raw labels/row IDs. Candidate
and ordinary_v6/R1e use same54723 development rows and corrected observations.
Reuse existing verified control prediction caches; no new baseline inference.

Primary comparisons: expert Rocket forced aim1/955 and full action/955. Full
action requires gate>0.35, affordable correct expert card and expert-forced aim
within1tile, or correct WAIT on WAIT contexts. Card agreement is on PLAY rows.
All original Barrel/multiple/ambiguous/WAIT, spawner parent/child-only, narrow
finish/combo/X-Bow and defense/Rocket-defense subgroups remain reported.

Apply PLAN continuation: Rocket aim+5pp, Rocket action+2pp; general card decline
<=0.5pp; spawner action, Barrel correct/wrong and defensive-sequence action
nonregression; all denominators present. Report per-replay paired deltas and
source hashes. This does not measure physical spell impact, elixir efficiency,
safe Rocket cycles, generalization, match win rate or final statistical power.
