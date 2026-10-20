Local placement-head test - October 6, 2026

**Work completed**
A cached error analysis found most remaining small-set aim misses inside the correct two-tile patch. We tested a generic learned refinement for the 16 cells inside each patch. It used the same 1,024 training examples, draw sequence and 4,096-update budget as the earlier fit test, starting again from the ordinary v5 parent. Neither test model is eligible for live play or use as a training parent.

Preflight checked exact initial outputs, all 2,304 cell mappings, local-input dependence and finite gradients. Independent verification reconciled all 524,288 draws, 100 optimizer states, final weights and predictions, including corruption controls. Only the new model made 2,048 predictions; three earlier control caches were reused.

**What we found**
The comparisons below use corrected-input R1e, the ordinary v5 parent, the earlier small-set fit, and the new local-cell fit, in that order. Each number is native / mirrored; mirrored views are the same examples, not independent matches.

- Full PLAY actions (out of 512 per orientation): 69 / 75; 80 / 83; 417 / 418; 424 / 425.
- Correct WAIT (out of 512 per orientation): 381 / 378; 398 / 395; 512 / 512; 512 / 512.
- Rocket aim within one tile (out of 64 per orientation): 20 / 16; 20 / 17; 51 / 49; 51 / 49.
- Rocket card choice (out of 64 per orientation): 10 / 9; 18 / 19; 64 / 64; 64 / 64.
- Full Rocket actions (out of 64 per orientation): 3 / 2; 7 / 7; 51 / 49; 51 / 49.
- Full late Rocket actions (out of 21 per orientation): 2 / 2; 3 / 4; 15 / 15; 15 / 15.

Full actions by card, out of 64 each. Again: R1e; v5; prior fit; new fit (native / mirrored).
- ice-wizard: 7 / 15; 7 / 12; 45 / 51; 46 / 54.
- knight: 12 / 18; 15 / 16; 51 / 52; 53 / 51.
- rocket: 3 / 2; 7 / 7; 51 / 49; 51 / 49.
- skeletons: 8 / 5; 6 / 5; 50 / 51; 52 / 52.
- tesla: 12 / 14; 14 / 15; 61 / 57; 61 / 57.
- the-log: 14 / 6; 15 / 11; 57 / 57; 58 / 59.
- tornado: 4 / 5; 4 / 5; 45 / 47; 47 / 47.
- x-bow: 9 / 10; 12 / 12; 57 / 54; 56 / 56.

Both fitted models retained 512/512 correct card choices and 512/512 correct WAITs in each orientation. The new model has one missed PLAY gate per orientation; its remaining first-stage action errors are 87 native and 86 mirrored aim errors. Its mean loss fell from 4.89414 over the first 256 updates to 0.80144 over the last 256, compared with 4.89511 to 0.82253 for the earlier fit.

**What it means**
The refinement produced a small training-set gain, with no Rocket aim gain. The fixed 90% full-PLAY and 95% Rocket-aim criteria failed in both orientations. Card and WAIT protections passed, but cannot rescue that verdict. This does not prove the architecture cannot learn placement. All examples were used for fitting: 798 replay groups overall, 439 with PLAY examples, and 64 groups per card. Balanced card sampling does not represent normal gameplay. Corrected-input R1e here is not the original live-input baseline. No generalization, physical damage, strategic or gameplay improvement was measured.

**Decision**
Diagnostic fit FAILED. NOT ACCEPTED and NOT DEPLOYED. Both assay checkpoints remain quarantined. Live STOP and every final acceptance floor remain unchanged.

**Next**
Register a fixed-checkpoint diagnostic to measure the learned branch contribution and its effect when removed from the same model. This will test whether the branch materially changed placement scores before any further learning change; no new training is registered yet.
