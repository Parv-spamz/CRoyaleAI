ClashAI development update — October 6, 05:06 EDT

**Work completed**
We first checked how well the ordinary model fits the examples used in its earlier training. Rocket action agreement was weak on both actual training draws (175 of 2,366) and development examples (77 of 955), with no large training advantage. That motivated a fixed test of more ordinary imitation learning.

The new model, ordinary_extended_v5, received 8,000 additional updates from verified ordinary_v5, using unchanged expert labels, architecture, learning rate and uniform sampling. Its optimizer started fresh because the earlier optimizer state was not saved. All 1,024,000 draws, 8,000 finite updates and 54,723 development predictions were independently checked. Only the final checkpoint was evaluated.

**What we found**
Counts below are R1e with corrected inputs, ordinary_v5, then the new model. This offline R1e comparison is not equivalent to R1e's original live inputs.

- Rocket aim within one tile: 290, 292, 276 of 955 examples. Complete Rocket actions: 54, 77, 88. Late Rocket actions: 14, 22, 23 of 320.
- Against ordinary_v5, the new model changed Rocket aim by -1.68 percentage points, complete actions by +1.15 points and late actions by +0.31 points. All three miss the required +5, +2 and +2 points.
- Goblin Barrel correct-lane responses: 36, 40, 42 of 63; wrong-lane responses: 20, 22, 21; no response: 7, 1, 0. Complete actions: 18, 20, 20.
- Witch agreement: 332, 339, 334 of 726; Night Witch: 156, 161, 165 of 373; Furnace: 538, 549, 558 of 1,174.
- Defensive agreement: 3,952, 4,011, 3,883 of 8,183. Late-game agreement: 1,949, 1,984, 1,962 of 6,422. General card agreement: 11,348, 11,403, 11,435 of 17,192 expert PLAY examples.

**What it means**
More ordinary training improved card selection and some complete actions, but did not solve Rocket aiming. Against the control, Rocket aim improved in 10 replay groups and worsened in 25; complete Rocket actions improved in 19 and worsened in 8. These examples belong to 336 Rocket replay groups, not 955 independent games.

Overall agreement fell from 31,962 to 31,627 of 54,723 rows: correct PLAY actions rose from 2,602 to 2,760, while correct WAIT decisions fell from 29,360 to 28,867. Defensive PLAY successes rose from 369 to 393, but correct WAIT fell from 3,642 to 3,490. Neither aggregate changes nor recorded-coordinate agreement prove better physical damage, safe Rocket cycles or winning gameplay. Parent exposure to this inner development split remains disclosed.

**Decision**
Rejected for continuation: all required Rocket improvements were missed, and Witch, defense and late-game protections failed. No new gameplay test qualifies. Not accepted or deployed; live play remains stopped. All final statistical, component, physical, gameplay and public-input requirements remain unchanged.

**Next**
Before another candidate recipe, register a bounded training-only fit-capacity test: can the unchanged network and loss learn a small fixed set? This is an untested diagnostic proposal, not an accepted remedy or a deployment candidate. The completed experiment will not be extended or rerun.
