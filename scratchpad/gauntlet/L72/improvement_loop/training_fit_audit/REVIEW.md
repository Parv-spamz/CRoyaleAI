# Training-fit diagnosis complete, October6 04:32 EDT

P1/C1/V1/R1 complete. Preparation2.672112s,collection198.023819s,
independent15.603543s and outside review.355999s all exit0/expected token.
All267305 fresh views (213995native plus53310unique actually mirrored training
views) and cached54723development views reconcile against raw original labels.
Original128000draws include66560native/61440mirrored and96327unique source rows.
All68 input/source hashes, orientation weights and per-replay counts reconcile.
Preparation2positive6malformed; independent4positive10corruptions.
Weights unchanged,zero backward/optimizer updates,zero development inference,
zero new models. All workers exited. Do not repeat completed jobs.

## Findings

| View | Rocket rows or weighted draws | Card | Forced aim <=1tile | Full action |
|---|---:|---:|---:|---:|
| Native training |3852|958|1098|256|
| Drawn native unique |1050|279|302|74|
| Undrawn native unique |2095|506|580|135|
| Drawn mirrored unique |978|250|267|69|
| Weighted native draws |1236|335|357|94|
| Weighted mirrored draws |1130|293|317|81|
| Cached development |955|269|292|77|

Combined weighted training draws: full Rocket175/2366 (7.40%),aim674/2366
(28.49%),card628/2366 (26.54%). Development full77/955 (8.06%),aim292/955
(30.58%),card269/955 (28.17%). Native training1343Rocket replay groups,
development336. Repeated draws/orientations are not independent matches.
Combined weighted late Rocket51/797 full actions,163/797 aim; development22/320
full,62/320 aim. Native late74/1298 full,257/1298 aim. Undrawn means not drawn
in either orientation; drawn-native and drawn-mirrored cohorts can overlap.

All native expert PLAY succeeds9957/67106 (14.84%); development2602/17192
(15.13%). Native all-row agreement125296/213995 includes115339 correct WAIT;
development31962/54723 includes29360 correct WAIT. Native Rocket exclusive
first failures:397gate,2589card,610aim,plus256success. Development110gate,
609card,159aim,77success. Ordering is arithmetic, not causal attribution.
Continuous distances remain reconstructable from saved cells and exact targets.

## Interpretation and next test

The final model fits its actually drawn examples poorly, with no large
train/development advantage. This weakens a simple claim that weak Rocket
agreement is mainly an inner-split generalization gap. It does not prove
insufficient optimization, capacity failure, label ambiguity or which head
causes gameplay losses. Parent exposure to both subsets remains disclosed.
Evaluation-mode final fit is not per-step training loss or physical spell impact.

A separately registered additional ordinary imitation budget is supported as
the next test: unchanged verified ordinary_v5 starting point, labels, learning
rate, architecture and sampling distribution; no rejected exposure/aim mixture.
Freeze extra budget and final-only evaluation before optimization. Original Adam
state was not saved, so a fresh optimizer must be explicitly disclosed. Do not
rerun the completed1000-update original job or select a best intermediate.
All material/protection and final acceptance floors remain unchanged.
No new model Discord report is due for this diagnostic. Owner STOP intact.
