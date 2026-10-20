# Outcome RL setup-serialization recovery

October5 19:09 EDT, before recovery execution. Preserve the original prepared
setups, frozen sources, training_started, failed receipt/output and chain_failed.
The original trainer stopped in its first BoundMatch constructor, before the
runner's policy-decision loop and before PPO. Its output directory has no files.
No candidate optimization or completed training game is established.

R1 diagnoses the first fixed setup without decisions, inference or optimization.
Compare the exact initial native state hash, all sixteen loaded forms, and absent
fallbacks. JSON changes side dictionary keys from integers to strings. Require
the canonicalized side keys to compare exactly; altered/missing forms must fail.
Check every one of the 256 stored setup form maps structurally, without resetting
or replaying the completed preparation cohort. Preserve the original failed raw
comparison in the diagnostic evidence. No setup, scenario or threshold changes.

The proposed warmup concern was withdrawn after reading rl_royale.ppo_update:
policy=False freezes every non-value-head parameter regardless of trunk_grad.
The original learning recipe is correct here and stays byte-for-byte unchanged.

R2 resumes the previously registered chain from its uncompleted training stage,
starting from the identical parent with zero prior candidate updates. A separate
outer driver changes only the form-map serialization comparison and writes its
own training_started marker. The original 32 updates/256 games, five critic-only
warmup rounds, final-only selection, data isolation, gates and cutoff all remain.
No completed readiness, setup sweep or PPO preflight is repeated. Every actual
training match still checks the original prepared native hash and forms.

Evaluation runs the unchanged original evaluator once after complete training.
The outer independent verifier changes only the receipt name from the failed
train attempt to train-v2, while requiring both failure preservation and recovery
diagnosis. No metric, tolerance, reward, sampling or optimizer change is allowed.
One GPU lock spans train/eval/verification, fail closed without automatic resume.
New model reporting is due only after a candidate and its reviewed statistics
exist; prior reports must not be duplicated. No live/production/runtime change.
