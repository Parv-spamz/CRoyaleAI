**ClashAI model update — October 6, 2026**

**Work completed**
We tested whether learning from late decisions makes match outcomes more useful for training. Both models started from ordinary_v5, our unchanged development control. The full-game model learned from all decisions; the late-game model learned from the final half of overtime. Both played every game from start to actual termination with full public history. Each trained on 1,024 simulated games with the same 256 optimizer steps. No tactical switch or reward for casting spells was added.

All 2,048 games, 512 optimizer steps, saved public inputs, outcomes, probability calculations and training draws passed independent checks, including 17 deliberately corrupted cases. Training took about 3 hours 50 minutes. Both final models were evaluated once on the same 54,723 recorded decisions from 405 replay groups. The earlier late-game readiness check also passed, with no weight updates.

**What we found**
Numbers below are in this order: R1e with corrected inputs; ordinary_v5; full-game model; late-game model. This R1e comparison is not its original live-input configuration.

- Rocket aim within one tile of the recorded expert coordinate: 290, 292, 298, 293 of 955 decisions across 336 replay groups.
- Complete Rocket action agreement: 54, 77, 85, 81 of 955. Late Rocket agreement: 14, 22, 23, 25 of 320 decisions across 171 groups.
- Against ordinary_v5, full-game Rocket aim improved only 0.63 percentage points, complete action 0.84 points and late action 0.31 points. Late-game gains were 0.10, 0.42 and 0.94 points. Required gains were 5, 2 and 2 points.
- Against the matched full-game model, late-game aim fell 0.52 points and complete Rocket agreement fell 0.42 points; late Rocket agreement rose only 0.63 points. Complete Rocket agreement improved in 7 replay groups, worsened in 11 and tied in 318.

**Protections and tradeoffs**
Correct Barrel lane choices were 36, 40, 38, 41 of 63; wrong lane choices were 20, 22, 23, 21, with 7, 1, 2, 1 not fired. Complete Barrel action agreement was 18, 20, 20, 20.

Complete action agreement around Witch was 332, 339, 319, 328 of 726; Night Witch 156, 161, 152, 162 of 373; Furnace 538, 549, 526, 537 of 1,174. Defensive sequences scored 3,952, 4,011, 3,849, 3,916 of 8,183. All late decisions scored 1,949, 1,984, 1,832, 1,929 of 6,422. General card agreement was 11,348, 11,403, 11,329, 11,319 of 17,192 expert PLAY decisions; both candidates stayed within the allowed half-point decline.

**What it means**
Late-only learning preserved more of the starting model's behavior than the matched full-game recipe, but it did not produce the required Rocket gains and still lost Witch, Furnace, defense and late-action agreement against ordinary_v5. The full-game model also failed several protections. This weakens this specific late-row curriculum as a remedy at the registered budget; it does not disprove late-game strategy. Aggregate action metrics include WAIT decisions. These measurements do not establish damage, safe Rocket cycles, finishing, adaptation, statistical superiority or wins against R1e. Parent-model exposure remains disclosed; these are development data, not untouched confirmation.

**Decision**
Both new models are rejected for continuation. Neither is accepted or deployed, and neither qualifies for a new gameplay acceptance test. Live play remains stopped. All final physical, statistical, component, gameplay and public-input requirements remain unchanged.

**Next**
Before another learning recipe, inspect Rocket training fit and joint card/placement errors to distinguish poor fit to available examples from poor generalization. This is a diagnostic proposal, not active training; no larger budget, best-checkpoint substitution or relaxed criterion has been authorized by these results.
