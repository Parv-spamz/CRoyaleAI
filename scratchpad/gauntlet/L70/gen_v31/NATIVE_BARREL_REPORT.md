# Native Log/Barrel evidence — October 3, 2026

MEASURED partial evidence across 14,661 unique verified native replays:

| Observation | Count |
|---|---:|
| Accepted driven barrels |23,004|
| Goblin Barrels |12,813|
| Skeleton Barrels |10,191|
| Accepted Logs |47,703|
| Log ticks with an exact recorded frame |47,682|
| Barrels with a uniquely linked, opposite-side Log at a recorded in-flight moment |865|
| Barrels followed by any opposite-side Log, possibly much later |7,646|

The observed lower endpoint is **3.76%** (95% replay-bootstrap CI **3.27–4.28%**).
The deliberately loose upper endpoint is **33.24%** (endpoint CI **31.58–34.87%**).
These are bounds with separate endpoint intervals, not a point estimate or a single confidence
interval for the requested full preemptive-Log metric. Bootstrap: 10,000 replay-cluster resamples,
seed 20261003; zero undefined resamples.

The lower endpoint requires an exact-tick Log and a visible Goblin Barrel projectile uniquely
linked to a driven command using earlier/current observations. It does not infer a landing from
disappearance. Skeleton Barrel body/death recognition and Logs within 0.5 seconds after landing
remain unresolved. Mirror commands are not resolved into copied cards, so mirrored barrels are
outside established coverage. The denominator is accepted re-drive commands, not every original
human play. This is pro-replay evidence, not a gen_v1/u0155/gen_v3 policy baseline.

The audit collapsed 1,634 duplicate same-tick observations with equivalent public projectile
fields. First attempts stopped on an exact duplicate and an elixir-only difference after an
ability. The final implementation ignores fields this metric does not consume and still rejects
conflicting projectile observations. Eight tests cover false attribution, missing coverage,
overlaps, duplicates and private-field invariance. Failed outputs remain preserved.

All selected replay tags and input hashes match the verified VM manifest. Audit code/report
hashes are pinned in `.foreman/codex_autopilot/runs/native_audits_1552.receipt.json`.
Final outputs: `native_barrels_1846/{report.json,manifest.json,barrels.jsonl}`. The first two
directories (`native_barrels_1552` and `native_barrels_1837`) are failed attempts, not final reports.
