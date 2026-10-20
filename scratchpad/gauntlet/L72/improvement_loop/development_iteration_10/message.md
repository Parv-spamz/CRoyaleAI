ClashAI model update — October 6, 2026, 8:00 AM Eastern

**Work completed**
We tested whether removing training dropout helped beyond the successful small-set diagnostic. Dropout randomly suppresses parts of the network during training. This new model started fresh from ordinary v5, the earlier imitation-learning control. It used the original architecture, labels and loss, with exactly the same 8,000 updates and 1,024,000 training draws as the completed extended-training control. The small-set diagnostic weights were never reused.

All 8,000 updates were finite. Independent checks reconciled the draws, final weights, all 96 optimizer states, and 54,723 development predictions from 405 replay groups. Existing control predictions were reused. Preparation, training, evaluation and both independent checks passed their execution checks, including malformed-data controls; the separate evidence review also passed.

**What we found**
The following recorded-action counts name the models in this order: R1e with corrected inputs; ordinary v5; extended v5 with ordinary dropout; the new model without dropout.

- Rocket aim within one tile: 290, 292, 276 and 276 of 955 expert Rocket decisions.
- Complete Rocket actions, requiring the play decision, card and aim to agree: 54, 77, 88 and 84 of 955.
- Complete late Rocket actions: 14, 22, 23 and 22 of 320.
- Goblin Barrel responses aimed correctly: 36, 40, 42 and 41 of 63. Wrong responses: 20, 22, 21 and 22; no response: 7, 1, 0 and 0. Complete action agreement was 18, 20, 20 and 19.
- Witch action agreement: 332, 339, 334 and 339 of 726. Night Witch: 156, 161, 165 and 172 of 373. Furnace: 538, 549, 558 and 564 of 1,174.
- Defensive-sequence action agreement: 3,952, 4,011, 3,883 and 3,922 of 8,183. Late-phase agreement: 1,949, 1,984, 1,962 and 1,997 of 6,422.
- General card agreement: 11,348, 11,403, 11,435 and 11,452 of 17,192 expert PLAY decisions. Overall action agreement: 30,968, 31,962, 31,627 and 31,847 of 54,723 decisions.

Against v5, the new model changed Rocket aim by −1.675 percentage points, complete Rocket actions by +0.733 points, and late Rocket actions by zero. These all miss the required +5, +2 and +2 points. Against the matched extended control, the changes were zero, −0.419 and −0.313 points, also failing. Defense regressed against v5; both correct and wrong Barrel-response protections failed against the extended control. Other passing protections cannot offset these failures.

Across the 336 replay groups containing Rocket decisions, aim improved in 14 and worsened in 28 versus v5; complete Rocket actions improved in 19 and worsened in 12. Against the extended control, those pairs were 10 better/10 worse for aim and 2 better/6 worse for complete actions. Remaining groups tied. Late Rocket groups were 3 better/3 worse versus v5 and 0 better/1 worse versus the extended control, out of 171 groups.

Overall agreement also needs its PLAY/WAIT breakdown. Compared with v5, the new model gained 187 correct PLAY decisions but lost 302 correct WAIT decisions, producing a net loss of 115. Compared with the extended control it gained 29 PLAY and 191 WAIT decisions, a net gain of 220. In defense, it gained 41 PLAY but lost 130 WAIT decisions versus v5. WAIT is a legitimate action; these counts do not establish harmful passivity or physical defensive value.

Mean logged training loss over the first and last 256 updates was 5.0905 and 4.9610. Its components changed as follows: aim-cell loss 2.9980 to 2.9441; card 0.7907 to 0.7669; wait 0.5091 to 0.4950; gate 0.4128 to 0.3928; value 0.3799 to 0.3621. These are means over training draws, not a fixed-sample comparison proving the cause of the development failure.

**What it means**
Removing dropout passed the earlier small-set fitting test but did not produce the required broader development improvement. This rejects this fixed recipe. It does not prove that dropout, model capacity or generalization alone caused the remaining errors.

These are agreements with recorded expert actions, not new simulator wins, measured spell damage, safe Rocket cycles or live results. Replay rows are correlated. The parent had prior exposure to this inner split, so this is not untouched confirmation. R1e here uses corrected observations and is not the original live-input R1e comparison. The rejected extended control remains rejected and was only a comparator.

**Decision**
REJECTED for continuation. NOT ACCEPTED and NOT DEPLOYED. No additional gameplay test qualifies for this candidate. All final statistical, component, physical, gameplay and public-input requirements remain open. Live play remains stopped; there was no fallback restart.

**Next**
Prepare a separate, fixed-weight training-fit comparison of the extended and no-dropout models, reusing their existing development predictions. This proposed diagnostic asks whether broader training fit improved without carrying over to development, before choosing another learning change. No new training recipe or deployment is authorized by this failed result.
