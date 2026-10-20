**ClashAI update — October 5: targeting experiment completed**

**Work completed**
Tested six small models that predict whether a proposed Rocket placement damages an enemy troop or crown tower. Three used current public geometry; three also used recent movement. These are auxiliary predictors, not bots that can play matches.

All 192 synthetic scenes, 3,456 action branches and 13,824 target queries were independently checked. We trained each model for exactly 1,000 updates. Development used 64 scenes from eight separate geometry families. Mirrored scenes and repeated targets are dependent observations, not independent games.

Earlier collection attempts failed on a setup tap inside a king tower and then a tuple-versus-JSON-list comparison. Those failures remain recorded. All setup positions are now checked before expensive collection; recovery preserved exact native state bytes and every saved value.

**What we found**
Movement helped training fit but hurt the primary development measure in all three paired seeds. Balanced Brier error gives equal weight to hit and miss cases; lower is better. Mean troop error rose from **0.08356 to 0.12610**, 50.9% worse. Mean training troop error fell from 0.02550 to 0.01666.

Development troop results below compare geometry-only with geometry-plus-movement. Each seed has 104 actual hit queries and 1,432 actual misses. These repeated evaluations use the same queries.

- Seed 2026101200: balanced error 0.09899 → 0.15010; ordinary Brier error 0.06555 → 0.06754. Detected hits: 83/104 → 71/104. False alarms: 124/1,432 → 105/1,432. Training balanced error: 0.02929 → 0.01913.
- Seed 2026101201: balanced error 0.08009 → 0.09225; ordinary error 0.05220 → 0.06151. Detected hits: 92/104 → 83/104. False alarms: 98/1,432 → 108/1,432. Training balanced error: 0.02193 → 0.01746.
- Seed 2026101202: balanced error 0.07160 → 0.13595; ordinary error 0.06507 → 0.05828. Detected hits: 96/104 → 68/104. False alarms: 134/1,432 → 88/1,432. Training balanced error: 0.02529 → 0.01340.

Tower prediction was easy in these isolated scenes. At the fixed 0.5 threshold, all six models detected 256/256 tower hits with zero false alarms among 2,816 misses. Tower balanced errors by paired seed were 0.000401 → 0.000281, 0.000131 → 0.000159, and 0.000092 → 0.000228.

**What it means**
This recipe did not demonstrate a benefit from the extra movement features. Better training fit with worse development results is consistent with overfitting, but does not establish the cause. The existing game policy already receives movement information. Fixed synthetic scenes, eight development families and simulator damage labels cannot establish live targeting skill, good Rocket timing, safe cycling or match wins.

**Decision and deployment**
The movement recipe is **rejected for continuation**: it missed the required error ceiling, relative improvement and improvement in at least two seeds. Tower protection passed but cannot rescue it. The control is not accepted as a game policy either. R1e has no comparable score in this predictor assay; there was no head-to-head gameplay test. No replacement model was accepted or deployed. R1e remains selected and live play remains stopped.

**Next**
Move to a different learning hypothesis: complete late-game situations may provide more useful outcome feedback than full-match training. First qualify a way to retain the full public history and finish those situations interactively. This is an untested proposal, not a launched RL run or a promised improvement. No hand-written Rocket rule or reward for casting spells will be added.
