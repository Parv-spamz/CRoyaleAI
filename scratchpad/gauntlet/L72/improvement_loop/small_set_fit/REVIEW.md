# Completed assay; diagnostic fit criteria failed

P1/T1/V1/E1/V2/R1 execution and reporting COMPLETE. All 4,096 finite updates,
524,288 draws, 96 optimizer states each at4,096, 1,024 original rows/798replay
clusters and all6,144 prediction views independently reconcile. No stage reruns.
Preparation67.421289s/train707.089823s/training verifier6.908803s/eval55.139531s/
results verifier7.540836s all exit0/token. Preparation2positive6malformed;
training1positive8corruptions; results7positive12corruptions.

Counts below are corrected-input R1e / ordinary_v5 / final diagnostic assay.
This R1e comparison is on the same corrected training inputs, not original live.

| Metric | Native | Mirrored | Denominator per orientation |
|---|---|---|---|
| Full PLAY |69 /80 /417|75 /83 /418|512 rows,439replays|
| Correct WAIT |381 /398 /512|378 /395 /512|512 rows,512replays|
| All-card agreement |310 /324 /512|307 /324 /512|512 PLAY|
| Rocket card |10 /18 /64|9 /19 /64|64 rows/replays|
| Rocket forced aim |20 /20 /51|16 /17 /49|64 rows/replays|
| Full Rocket |3 /7 /51|2 /7 /49|64 rows/replays|
| Full late Rocket |2 /3 /15|2 /4 /15|21 rows/replays|

All eight cards' exact per-replay counts are retained in counts.json and
results_verified summaries; message.md reports every card's v5-to-assay full
counts. Final all-PLAY forced aim417native/419mirrored; full417/418. First-failure
partition:1gate/0card/94aim native;1gate/0card/93aim mirrored. Original fullPLAY
90% and Rocket aim95% criteria FAIL both orientations; Rocketcard/WAIT95% PASS.
Overall diagnostic_fit=false. No thresholds changed or best orientation chosen.
Mean first256training losses4.895106190815568;last256.8225258593447506.

The unchanged model learned card, WAIT and much of aim on these selected rows.
Remaining placement errors are measured; capacity/optimization causes are not.
Failure of fixed conditions does not prove architectural incapacity. All rows
are training rows; balanced labels/mirror views are not independent matches or
representative live frequencies. No development/generalization/nativegames/
physical resource/strategy/live performance claim is supported. All weights
remain QUARANTINED, never eligible for policy selection, learningparent or live.
All final N2-N7/statistical/physical/component/gameplay/public/Q4/Q5 gates remain.

Finalcheckpoint79af2f299f8fae6efe4e0c584a7335ea53136c0ad89415ba1c131bf4b6cf69fa.
Outside evidence review ran ONCE .578288s, delivery .765301s, closeout .087099s,
all exit0/token. Report stableID model-small-set-fit-v5-diagnostic deliveredONCE
05:44:44EDT,2HTTP200parts;IDs1556965420752175196/1556965422559924255. Exacttext,
delivery,IDs and all7 prior receipts bound by reviewed_results. NEVERresend.

All workers exited; STOP13:39:32 untouched. Owner13Z/09EDT extension persists.
Next proposed separate cached remaining-aim/representation diagnostic has not
run at this closure. Inspect newer handoff before next work.
