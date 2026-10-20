# Checkpoint metadata recovery, before resuming

The original chain exited after successful R1e evaluation and1000finite ordinary_v5
updates. v5 evaluation failed before prediction: development_iteration_1.torch was
saved as torch.torch_version.TorchVersion rather than builtin str. The standard
weights-only loader rejected that metadata. This is an agent serialization bug,
not a measured model failure or reason to repeat training. Preserve the failed
evaluator directory, receipt and every original bound source/checkpoint.

Use a separate converter on the hash-pinned checkpoint made by this run. Keep
weights_only=True with only the inspected installed TorchVersion string subclass
temporarily allowlisted. Replace only TorchVersion metadata with plain strings,
write candidate_portable.pt separately, then prove every tensor/key/shape/dtype/
byte hash and every other metadata value unchanged. The portable artifact must
load using the standard unrestricted-by-us weights-only model loader. Never use
weights_only=False or modify system policy. Synthetic positive/negative controls
must reject tensor mutations and demonstrate the original metadata error.

After conversion checks, a separate continuation verifies original source/data/
draw hashes, successful R1e/v5 training receipts and failed v5 evaluation receipt.
It skips completed jobs: v5 portable evaluation in a new directory; ORIGINAL v6
1000-update training; v6 same metadata conversion; v6 portable evaluation; original
metric/threshold independent recount using the separately named caches. No change
to training, initial weights, update count, recipe, metric definitions or selection.
R1e predictions are retained. Each portable checkpoint remains the same trained
model, not another model or extra optimization. All remaining jobs run serially.

Freeze new wrapper/converter hashes and preserve explicit new receipts. No final
acceptance or live deployment follows automatically. After reviewed results send
the owner's reports for the two new learned models, with failures/limitations.
