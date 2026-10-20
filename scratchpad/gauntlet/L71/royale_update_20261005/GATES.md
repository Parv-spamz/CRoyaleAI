# RoyaleSim / RoyaleGym upstream port

Owner October5: inspect the new upstream commits, port all relevant changes, and use the updated engine for every new RL training run tonight and in future. Existing frozen comparisons must retain their original runtime; their results cannot be paired with a changed engine. The already queued expert-context jobs are imitation learning and frozen simulator acceptance, not new RL training.

- [x] U1: Record exact local/upstream revisions, every intervening commit and relevant interface/mechanic changes; preserve local runtime/data differences.
  MANUAL: Inspect inventory.json and REVIEW.md, including simulator and Gym compatibility and current compiled provenance.
- [x] U2: Build the full pinned upstream simulator and compatible Gym in isolation, with the correct card/arena/calibration data and preserved120s overtime and regen schedule.
  MANUAL: Inspect wheel/build receipts, compiled provenance, data hashes and runtime probes. Do not install over a running comparison's environment.
- [x] U3: Upstream mechanic/binding tests and ClashBot adapter/determinism/public-input checks pass on the new runtime; report skipped tests distinctly.
  MANUAL: Inspect actual process exits, success markers and outputs; exercise meaningful negative controls for runtime selection.
  Owner-requested unchanged-binary retry: all16 previously blocked targets execute,62 pass,0 fail (rust_retry_owner.json and integration/checks/owner-rust-retry.json). Combined coverage:1603 pass,0 executed failures,3 ignored timing tests. Earlier4551 failure remains recorded. No agent security-policy changes. Python/adapter checks are adjudicated in REVIEW.md; Gym's optional RoyaleLearn quickstart remains unsupported, and skips/xfails/private-capture limits remain explicit.
- [x] U4: New RL launches and spawned actors resolve the pinned updated runtime, record its fingerprint, and reject an absent/stale installation.
  MANUAL: Verify the standard training path and subprocess import path; no new RL optimization run is implied by this port alone.
- [x] U5: Publish the reviewed port/configuration and handoff, preserving frozen experiments and declaring engine versions in acceptance results.
  MANUAL: Verify scoped commits/push, active chains and durable runtime selection. Old-engine candidate acceptance is not evidence of updated-engine performance.
  Port published through f8c5bad at03:01 EDT; owner retry closes the Rust launch gap. Runtime/source validation does not imply model acceptance.
