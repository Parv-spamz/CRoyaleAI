# Preserve incomplete tower snapshots as unknown

The first producer failed its six-slot assertion while reading a5999 snapshot.
Its source, started.json and nonzero l72-gameplay-failure-audit receipt remain.
The telemetry can omit destroyed towers; it does not supply a complete six-slot
alive/dead ledger in every frame. Do not infer missing HP, identity or crowns.

v2 validates every present identity/side/kind and duplicate/finite HP constraints,
then returns unknown for fewer than six explicit slots, as the original PLAN's
missing-data rule intended. More than six/duplicate/malformed entries still fail.
Fully observed six-slot semantics are unchanged. Both independent implementations
apply this correction and the verifier adds a missing-tower positive control.
Separate started_v2/report_v2/verified_v2 outputs bind original failed sources,
the correction and fresh sources. No game/inference/optimizer rerun or relabeled
failure; only this previously incomplete diagnosis is resumed from immutable data.
