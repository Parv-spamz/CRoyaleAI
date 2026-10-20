# D1: isolate generic learned projectile aiming under ordinary imitation

Status: prepare and verify data/recipe now. Launch only after the separate
development trainer and check gates pass. Final model acceptance stays closed.
See ../DEVELOPMENT_AMENDMENT.md for the owner-requested workflow reassessment.

Data: the existing verified v5 corrected-body archive, bound to the original v4
expert dataset and unchanged expert context pool. Only original split0 Icebow
rows may enter this development experiment. Assign each complete replay tag by
SHA256(`clashbot-l72-development-1-20261005:` + tag), first8 bytes big endian,
modulo5: zero is development, the other four values training. Both observer sides
and every row of a replay share assignment. No old split1/validation, fresh pro
confirmation, or owner live records enter optimization or development selection.
Do not alter original source arrays or splits. Save explicit row-index vectors.
R1e parent exposure to both inner subsets is disclosed; no untouched-test claim.

Fixed one-factor comparison, from the same R1e31 u0155 checkpoint:
- ordinary_v5: model version5, corrected body data, ordinary100% exposure.
- ordinary_v6: identical data and draws, adding the zero-initialized generic
  projectile-target residual. No Rocket, Barrel or X-Bow exposure reweighting.

Each arm runs exactly1000 finite updates, batch128, seed20261005, AdamW weight
decay.01, base learning rate1e-5, target-module learning rate1e-3 for v6, clip norm1,
50% horizontal mirroring, unchanged expert losses. Reset base dropout RNG after
architecture construction. Same batch-index/mirror stream, final step only.
No automatic resume or extra steps, no deployment, no live settings changes.
Do not reuse the old trainer unchanged: it automatically predicts on the old
L71 validation set. The new driver must load only this manifest's row vectors
and must never invoke that validation path. A smoke saves no candidate and is
not counted as a full experiment. Run GPU arms serially after process inspection.

Before training, record exact source/data/checkpoint/runtime fingerprints and
freeze development metric definitions/selection in the trainer manifest. Use the
existing action definition (correct WAIT, or gated correct expert card plus aim
within1tile), card agreement, separate Witch/NightWitch/Furnace, and separate
known single-Barrel gated correct/wrong lanes. Preserve unclear/WAIT cases and
per-replay paired counts. No adaptive metric thresholds or use of fresh test
results. Report all development denominators; insufficient subgroups stay
inconclusive. Candidate continuation requires improved Barrel correct responses
without increased wrong-lane responses, <=0.5pp general card decline, and no
point regression in any spawner family's action agreement versus ordinary_v5.
These are development filters, not substitutes for final statistical acceptance.

Every completed new checkpoint receives the owner's requested Discord report
against R1e with clearly labeled developmental statistics and deployment verdict
NOT ACCEPTED pending the unchanged final gates. Pre-training preparation is not
a new model and needs no model report. All raw arrays/checkpoints remain ignored.
