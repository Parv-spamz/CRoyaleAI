ClashBot diagnostic update — October 6, 2026

**Work completed**
We tested whether training dropout was limiting fit on a small, fixed training set. Dropout randomly suppresses parts of the network during training. The new run disabled it, including attention dropout, while keeping the original architecture, inputs, labels, loss, optimizer, 4,096 updates and exact draw/mirror sequence. It started fresh from ordinary_v5, our existing development model. No weights from the earlier fit experiments were reused.

Preparation verified unchanged initial evaluation outputs and the intended dropout behavior. Independent checks reconciled every update, all 524,288 draws, all optimizer steps and the final prediction counts. The new model predicted 2,048 views once; 6,144 existing control views were reused. No development, reserved, simulator-game or live-game evaluation occurred.

**What we found**
All counts below compare corrected-input R1e, ordinary_v5, the earlier fit run with dropout, and the new fit run without dropout, in that order. R1e here uses the same corrected observations; it is not the original live-input R1e.

Full PLAY agreement, out of 512: native 69, 80, 417, 468; mirrored 75, 83, 418, 474. Correct WAIT, out of 512: native 381, 398, 512, 512; mirrored 378, 395, 512, 512.

Rocket aim within the unchanged one-tile threshold, out of 64: native 20, 20, 51, 64; mirrored 16, 17, 49, 63. Rocket card choice: native 10, 18, 64, 64; mirrored 9, 19, 64, 64. Full Rocket actions: native 3, 7, 51, 64; mirrored 2, 7, 49, 63. Late Rocket full actions, out of 21: native 2, 3, 15, 21; mirrored 2, 4, 15, 21.

Both fitted models chose the correct card on all 512 PLAY rows in each orientation and retained all 512 correct WAIT decisions. The new model's remaining PLAY failures were one gate failure and 43 aim failures natively, and one gate failure and 37 aim failures mirrored; zero card failures. These are first-failure categories, so they do not double-count errors.

All eight cards' full PLAY counts follow. Each has 64 examples from 64 replays; each pair is native and mirrored. Columns remain R1e, ordinary_v5, earlier fit, new dropout-free fit:
- Ice Wizard: (7,15), (7,12), (45,51), (52,59).
- Knight: (12,18), (15,16), (51,52), (53,54).
- Rocket: (3,2), (7,7), (51,49), (64,63).
- Skeletons: (8,5), (6,5), (50,51), (57,57).
- Tesla: (12,14), (14,15), (61,57), (62,63).
- Log: (14,6), (15,11), (57,57), (63,64).
- Tornado: (4,5), (4,5), (45,47), (56,56).
- X-Bow: (9,10), (12,12), (57,54), (61,58).

Mean loss fell from 4.768166 in the first 256 updates to 0.304946 in the last 256. The corresponding logged component means were cell 2.779962 to 0.243480; card 0.717917 to 0.003739; wait 0.476088 to 0.019841; gate 0.428127 to 0.007120; value 0.366072 to 0.030766.

**What it means**
The new run passed every preset fit criterion in both orientations: at least 90% full PLAY agreement, 95% Rocket card/aim agreement and 95% correct WAIT, plus preservation of the earlier fit's perfect card and WAIT counts. Disabling dropout improved fitting this particular sample under the fixed training budget. It weakens the claim that the architecture cannot fit these examples; it does not show that removing dropout improves generalization.

All 1,024 rows were training data from 798 replays. The 512 PLAY rows span 439 replays; the 21 late Rocket rows span 21 replays. Balanced card strata are not the natural distribution, and mirrored views are not independent observations. Parent exposure remains disclosed. A separate label audit corrected earlier floor-based diagnostic descriptors to the actual lattice labels; original continuous aim scores, thresholds and prior failed verdicts were unchanged. No near-boundary miss received a tolerance waiver.

**Decision and deployment**
Diagnostic fit PASS. NOT ACCEPTED as a replacement and NOT DEPLOYED. These fitted weights remain permanently quarantined and cannot become a policy, a learning parent or a live checkpoint. There is no new gameplay, physical damage, safe cycling, finishing or statistical-superiority evidence. Every final acceptance requirement remains open, and live play remains stopped.

**Next**
Register a separate development comparison of dropout-free training against the existing matched ordinary-training run, starting fresh from the original ordinary_v5 parent. This is an untested generalization hypothesis. Preserve the original development thresholds and all final requirements; never promote the small-set diagnostic weights.
