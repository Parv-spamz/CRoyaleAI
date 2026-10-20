**October 6, 5:44 AM ET — Small-set learning test completed**

**Work completed**
After broader training failed to improve the required metrics, we tested whether the existing network and loss could learn a small fixed training set. The test started from ordinary_v5, the previous ordinary imitation model, and ran exactly 4,096 updates. It used 64 PLAY examples for each of eight cards and 512 WAIT examples: 1,024 original rows from 798 replays, with the existing mirroring and learning settings.

Preparation, training and independent checks completed. The checks reconciled all 524,288 training draws, final optimizer states, original labels and 6,144 prediction views across the final test model, ordinary_v5 and R1e. No development evaluation or games were run.

**What we found**
For the native orientation, correct full PLAY actions were 69 for R1e, 80 for ordinary_v5 and 417 for the test model, out of 512. Mirrored results were 75, 83 and 418 respectively. Correct WAIT results out of 512 were 381, 398 and 512 native; 378, 395 and 512 mirrored.

On the 64 Rocket examples, forced aim within one tile was 20 for R1e, 20 for ordinary_v5 and 51 for the test model native; mirrored counts were 16, 17 and 49. Full Rocket actions were 3, 7 and 51 native, and 2, 7 and 49 mirrored. The test model chose the correct card on all 512 PLAY examples in both orientations, including every Rocket.

Full-action counts below show ordinary_v5 → test model, each out of 64:
- Ice Wizard: 7 → 45 native; 12 → 51 mirrored.
- Knight: 15 → 51 native; 16 → 52 mirrored.
- Rocket: 7 → 51 native; 7 → 49 mirrored.
- Skeletons: 6 → 50 native; 5 → 51 mirrored.
- Tesla: 14 → 61 native; 15 → 57 mirrored.
- Log: 15 → 57 native; 11 → 57 mirrored.
- Tornado: 4 → 45 native; 5 → 47 mirrored.
- X-Bow: 12 → 57 native; 12 → 54 mirrored.

Late Rocket full actions, out of 21 examples, were 2 for R1e, 3 for ordinary_v5 and 15 for the test model native; mirrored counts were 2, 4 and 15. Average training loss fell from 4.895 in the first 256 updates to 0.823 in the last 256.

**What it means**
The model learned card choice and WAIT on this set, and substantially improved aim. Placement errors still account for 94 native and 93 mirrored full-action failures; one further failure in each orientation is the PLAY gate. This shows learning on these examples, but does not identify why the remaining aim errors persist or why broader training failed.

All examples were used for fitting. The balanced card mix is not a natural match distribution, and mirrored views are not independent examples. R1e received the same corrected public inputs here; these numbers are not its original live performance. This test does not establish generalization, physical damage, safer defense or more wins.

**Decision**
The fixed diagnostic fit criterion FAILED in both orientations: full PLAY reached 81.4% and 81.6%, below 90%; Rocket aim reached 79.7% and 76.6%, below 95%. Card-choice and WAIT criteria passed but cannot rescue the failure. The test weights remain quarantined and cannot become a policy, a training parent or a live checkpoint. NOT ACCEPTED and NOT DEPLOYED. All replacement criteria remain unchanged; live play remains stopped.

**Next**
Register a separate analysis of the saved remaining aim errors and the cell representation before selecting another learning change. That analysis is not yet run. The finished training test will not be extended or repeated.
