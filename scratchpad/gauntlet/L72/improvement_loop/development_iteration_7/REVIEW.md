# Frozen-base projectile trial: useful Barrel isolation, rejected candidate

October5 17:12 EDT. Training119.37s and evaluation52.42s completed, exactly1000
finite updates/all54723 rows. Independent v1 failed the registered exact gate-logit
cache criterion. All original v5 base tensors passed byte-identical comparison.
Separate recount_development7_v2.py outside the frozen directory completed full
independent statistics in40.97s, preserving the FALSE exact-output filter. No
retraining, evaluation rerun or changed threshold. Original failed source/output/
chain remain. B1/B3 complete, B2 exact-output gate failed/abandoned for this fixed
candidate. The overall new-model objective and final gates remain unfinished.

| Metric | R1e corrected | ordinary_v5 | frozen-base candidate |
|---|---:|---:|---:|
| Barrel correct/wrong/not-fired /63 |36/20/7|40/22/1|56/6/1|
| Full Barrel action /63 |18|20|32|
| Expert Rocket aim<=1tile /955 |290|292|290|
| Expert Rocket full action /955 |54|77|76|
| Late Rocket action /320 |14|22|22|
| Late-all action /6422 |1949|1984|1992|
| Witch /726 |332|339|341|
| Night Witch /373 |156|161|161|
| Furnace /1174 |538|549|549|
| Defensive action /8183 |3952|4011|4012|
| General card /17192PLAY |11348|11403|11403|
| All action /54723 |30968|31962|31984|

Barrel correct+25.40pp and wrong22->6 pass the branch criteria; all spawner/
defense/late action protections pass. Rocket aim -2 and full action -1 fail both
registered nonregression checks, independently of the exact-output failure.
The candidate is REJECTED; no stronger gameplay, physical defense, Rocket cycle,
resource efficiency or phase/matchup adaptation has been demonstrated.

156/54723 gate logits differ from v5, maximum1.1920928955078125e-6;625/218892
card logits differ, maximum2.86102294921875e-6. All chosen cards and>.35 gate
decisions are unchanged. CPU smoke exactness did not establish bitwise equality
of all separately computed GPU caches. These differences are small; their origin
is not established by this audit. Exact criterion remains failed, never silently
replaced by a tolerance. The base-tensor invariant itself passes.

reviewed_results.json binds all cache/model/per-replay hashes,1000 finite updates,
five successful receipts and the original independent failure. Requested model
report delivered ONCE,oneHTTP204,l72-development7-discord; review receipt exit0.
No duplicate reports, optimization, evaluation or completed-check reruns. Parent
exposure remains disclosed. All same-corrected-input R1e/v5/v6 comparisons retained.

Next useful work is a bounded cached-error diagnosis of this branch's remaining
Rocket regressions by original expert card/aim and public projectile-target
context, including improvements and no-target cases. It must retain the fixed
data/labels and all failures before selecting another architecture or outcome
learning recipe. Do not launch a blind learning-rate/loss grid, combine rejected
recipes or claim the useful Barrel component alone meets replacement gates.
The separate terminal-wrapper accounting issue also remains documented; fixing
it requires accepted-command/final-state neutrality. No active GPU/native job,
no live worker/restart, ownerSTOP13:39:32 intact. This is not objective completion.

## Archived launch record

# Frozen-base projectile trial launched

October5 17:03 EDT. B1 complete; B2/B3 active. Launcher42584/chain51696 runs a serial1000-step
training/evaluation/independent-recount chain under the existing GPU file lock.
Inspect launch.json,chain_started/progress.json,chain.out/.err and ignored
icebow/data/bench/development_iteration_7_20261005/frozen_base_projectile_v6/train.jsonl.
Fail closed; no automatic resume, duplicate launch or bound Python/PLAN/METRICS edits.
Place future reporting helpers outside this frozen directory.

The completed gameplay comparison rejected ordinary_v6's overall continuation:
39/64 wins vs v5 42/64 and original R1e45/64. Its offline Barrel benefit remains
a component observation. The independent common-state audit finds both aim and
card/timing differences after shared-base training. This new experiment tests
whether freezing all v5 base weights can isolate useful projectile learning.
It does not establish the cause of losses or rescue the earlier candidate.

Start from verified ordinary_v5 portable weights, not R1e or ordinary_v6. Add
the same zero-initialized generic target residual and train only its five tensors.
Frozen base in eval mode, no dropout in the new modules. Original expert losses,
all213995train/1573groups and54723dev/405groups, original ordinary1000x128 draws/
mirror bits,seed20261005,targetLR1e-3,AdamWwd.01,clip1,fp32,final-only. No pipeline,
live, runtime, labels, target-rule, sampling or loss-weight change. Parent exposure
remains explicit; no reserved/old-validation/owner-bot expert training.

New preflight68.08s exit0/token matched. Exact migration reproduces all v5 outputs
and loss. Two training-only smoke losses5.106794834136963/5.106081962585449, finite
nonzero residual output/upstream gradients; every base tensor unchanged after both
updates. Gate/card/value/WAIT outputs exact with nonzero learned branch. No-valid
target, padding and unknown coordinates give zero residual and full v5 equality.
Standard weights-only metadata/tensor roundtrip passes. No smoke checkpoint saved.
Existing data/schedule/mask/source/runtime prerequisites checked, not rerun.

Fixed continuation versus v5: Barrel correct responses+15pp, wrong lanes at least
halved, full Barrel actions nondecreasing; exact gate/card logits across all54723;
no Rocket aim/action/late-Rocket, late-all, W/NW/F or defensive-action decline.
Independent recount includes same-corrected-input R1e and end-to-end v6 references.
All final untouched/material-component/gameplay/statistical/Q4/Q5 gates remain.
No new-model report due at launch; review the final checkpoint and all receipts
before reporting once to Discord. No accepted replacement or live restart.
