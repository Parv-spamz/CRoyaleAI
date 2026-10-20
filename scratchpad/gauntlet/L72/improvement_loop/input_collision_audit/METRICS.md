# Frozen descriptive counts

Scope213995native trainingrows only. Group all rows by strict16tensor byte equality.
Report unique inputgroups,duplicate groups,rows in duplicategroups,distinctreplays,
maximumgroup size; conflicting gate groups/rows and sum(min(nPLAY,nWAIT)); PLAY-card
conflict groups/rows and sum(nPLAY-largestcardcount). Condition aim on expertcard
ANDform; report groups with multiple latticeclasses, sum(n-largestclasscount),
and sum(n-largest<=1tile coverage) under original continuous geometry. These
three per-head minima overlap and must not be summed. Report Rocket separately.
All denominators count native rows, not independent games or practical ambiguity.

Producer fixtures cover2duplicate groups with gate/card/lattice conflict, separate
same-card nearby labels with shared1tile coverage, and every16input field's
inclusion versus label exclusion. Verifier uses independent fixtures and rejects
7saved-result corruptions: membershipID,publichash,gate,card,form,xy,summary.
Require exact inputhashes,original labels,lattice targets,groupmembership and every
scalar count; no tolerance,epsilon,labelrepair or hypothesis-based filtering.

No success threshold selects a model. Empty collision counts cannot rule out
semantic equivalents,lossy encoding,nearby state ambiguity,optimization failure,
capacity limits,missinghistory or expert multimodality.
