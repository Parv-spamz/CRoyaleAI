# Training-only Barrel residual diagnosis, October 5 11:49 EDT

The generic learned projectile-target residual materially contributes to the
earlier training-sample lane improvement. This is established by disabling only
that term within each fixed-weight v6 checkpoint. It does not establish that
training a new isolated arm will generalize or win more matches.

Selection was frozen before inference: 789 unique split0 Icebow rows from489
training replay groups, sampled once per replay per stratum with seed20261005.
The seven strata contain89 expert same-lane Log PLAYs,73 other PLAYs,103 WAITs,
81 multiple-Barrel,83 ambiguous-Barrel,200 other-projectile and200 no-valid-target
rows. Strata overlap; their counts must not be added as independent trials.
The original training rows and labels are unchanged. No held-out/fresh-confirmation
prediction or optimizer update was performed. Existing v5/v6 checkpoint files
remain hash-identical; the ablation exists only in diagnostic CPU inference.

| Existing checkpoint / condition | Correct-lane fired Logs | Wrong-lane fired Logs | Forced-Log same lane | Full expert action |
| --- | ---: | ---: | ---: | ---: |
| v5_rocket_barrel | 61/89 | 22/89 | 67/89 | 25/89 |
| v6_rocket_barrel, residual off | 62/89 | 21/89 | 68/89 | 23/89 |
| v6_rocket_barrel, full | 83/89 | 0/89 | 89/89 | 36/89 |
| v6_rocket_both, residual off | 62/89 | 21/89 | 68/89 | 23/89 |
| v6_rocket_both, full | 83/89 | 0/89 | 88/89 | 37/89 |

These are the same89 unambiguous expert-Log rows from89 replays. Both v6 ablations
retain exactly the same gates and card choices as their full models:83 Logs fired,
six did not. The residual converts21 wrong-lane fired Logs to correct lane, with
no reverse lane flip among fired Logs. v6_rocket_both loses one forced-Log lane
agreement on a non-fired row; report that distinction rather than calling every
head output correct. Full action means gate+expert card+within1tile of the expert,
not merely a correct lane. It improves16 rows and worsens3 for v6_rocket_barrel,
and improves16/worsens2 for v6_rocket_both. Thus precise aim remains incomplete.

The term makes modest action changes on the other sampled Barrel strata and
does not change action counts on the200 other-projectile rows. All200 rows with
no valid public target have exactly zero patch residual and identical full/off
expert and Log logits. WAIT choices are unaffected within each checkpoint.
Between-checkpoint differences on these controls reflect changed learned weights
and exposure, not the residual-only intervention. These small stratified samples
are not population estimates or proof that every non-Barrel situation is safe.

The independent verifier reconstructs selection from original source arrays,
checks training membership and one-row-per-replay strata, recomputes argmax and
metrics from cached full logits, and recounts paired transitions. One positive
fixture and eight corruptions pass: membership, held-out contamination, label,
logit, gate invariance, card invariance, zero-target behavior and reported-count
changes are all detected. Both actual process receipts exit0 and match their
success tokens. Raw logits remain ignored under
icebow/data/bench/train_barrel_residual_20261005; do not stage them.

Interpretation: preserve the generic learned target architecture as a candidate
for the already planned ordinary-IL controlled experiment, isolated from Rocket/
X-Bow exposure changes, after N2. This diagnosis does not transfer or enable weights
in live play. The original v6 candidates still fail gameplay/other component gates.
No new checkpoint was produced, so no new-model Discord report is due.

Fresh exact-Icebow evidence still has zero opposing Barrel casts. Training-sample
lane agreement is neither actual landing/damage verification nor untouched
confirmation. N2-N7 remain open and all replacement requirements stay unchanged.
Owner farming remains active with no settings or worker changes.
