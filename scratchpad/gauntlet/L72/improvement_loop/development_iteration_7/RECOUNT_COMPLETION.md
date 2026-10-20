# Finish the statistics while preserving the failed exact-output gate

Original train and evaluation completed with zero-exit/token receipts. All base
checkpoint tensors passed exact comparison with the v5 parent. The independent
recount failed at its required exact gate-logit cache comparison. Preserve the
original source, checkpoint, caches, failed receipt and chain_failed.json.

Measured differences:156/54723 gate logits,max1.1920928955078125e-6;
625/218892 card logits,max2.86102294921875e-6. No chosen-card or>.35 gate decision
changes. Small numerical differences are not permission to change the registered
exact criterion. Their source is not established by these counts alone.

Separate recount_development7_v2.py OUTSIDE the frozen directory finishes the
independent raw-label/cache/per-replay statistics. It retains the required exact
gate/card comparison as a FALSE filter, reports each discrepancy, and leaves
the candidate rejected. It must first verify both completed train/eval receipts,
the exact original failure and unchanged frozen sources/checkpoints. No training,
evaluation, baseline inference, accepted deployment or threshold relaxation.
