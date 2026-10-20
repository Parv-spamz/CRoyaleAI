# Fixed-checkpoint branch contribution diagnostic, registered before collection

The completed local_cell_fit adds seven correct PLAY examples per orientation
over its matched small_set_fit control, but leaves Rocket aim51/64native and
49/64mirrored unchanged. Both fixed fit criteria failed. Before changing learning,
measure whether the new branch changes placement scores and decisions at all.

Use ONLY the final quarantined local_cell_fit checkpoint and its original1024
training rows, same128-row evaluation batching, native and mirrored orientations.
One new2048-view forward collection is necessary to expose the previously unsaved
patch/query activations and separate base/residual scores. This is a registered
same-checkpoint ON/OFF intervention, not a rerun of the completed evaluation.
Reuse its saved gate/card/prediction caches as exact choice anchors. No old-model
inference, backward, optimizer, checkpoint, development, reserved, nativegame or
live access. No branch scaling search; coefficients exactly1 and0 only.

Save all512PLAY views per orientation with original row/replay/card/xy/tick,
patch activations, card-conditioned query, base and residual logits, full logits,
and the old saved prediction. Base is the original GenModel cell formula using
this SAME final trained trunk; it is not the prior fit or ordinary_v5 model.
Prove ON=base+residual exactly and both ON choices and gate/card decisions match
the completed cache. All weights/checkpoint bytes unchanged, no learning.

Independent verifier reloads original labels and original caches; reconstructs
base and local residual scores from saved patch/query tensors and final parameter
bytes in float64 CPU arithmetic. It independently recomputes per-row/per-replay
choice, geometry, CE, target margin and aggregate statistics. Positive and
malformed controls must establish that metadata, decomposition and scores can fail.
R1 binds both receipts and records limitations. One common GPU/native chain lock
spans collection and independent verification; cutoff13Z, failclosed/no unchanged
retry. Frozen previous sources and all fit/deployment criteria stay unchanged.

This establishes only the direct effect of the learned residual at fixed final
weights on the fitted sample. It cannot isolate training dynamics, prove learning
rate/capacity causes, generalization or tactical benefit. No new-model report due.
Quarantine and STOP remain; all final N2-N7/statistical/material/physical/gameplay/
public-input/Q4/Q5 gates remain OPEN. No successor training is authorized by a
favorable descriptive statistic alone; it needs a separately registered rationale.
