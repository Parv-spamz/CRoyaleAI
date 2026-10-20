# Historical defense sequence index verified

Prepared 7,748 X-Bow windows from 1,920 historical training replays. Each window
contains all existing same-side Icebow decision rows from two seconds before the
bow through thirty seconds afterward. No future Rocket, damage, coverage or win
criterion filters membership. The index retains the original supervision and
causal per-decision history; it is not a trained model or a new recurrent model.

The ordinary training pool remains 268,718 rows. The window index has 138,108 row
references but only 126,802 unique rows, including 44,793 PLAY and 82,009 WAIT
labels. Overlap is explicit and deduplicated for future sampling:

| Window group | Windows | Unique rows | PLAY | WAIT | Expert Rocket plays |
|---|---:|---:|---:|---:|---:|
| Defensive X-Bow | 2,266 | 40,370 | 15,537 | 24,833 | 990 |
| Other X-Bow | 5,482 | 89,828 | 30,687 | 59,141 | 1,280 |

The groups share 3,396 rows. Their sums are not independent sample counts.
All eight original supervision arrays are hash-bound. An independent verifier
joins the original calibrated X-Bow labels, reconstructs every interval without
the builder's selection function, checks exact unions and original target hashes,
and confirms no held-out rows/replays. Two positive controls and twelve deliberate
membership/label/input corruptions pass. Sources, reports and output are bound
in l72-defence-sequence-controls/prepared/verified receipts.

The defensive group retains 129 incomplete endings and 1,451 windows with observed
own-princess damage. Among its 2,137 fully covered windows, 1,872 have no observed
HP-confirmed princess-Rocket cast. The prepared report's `no_princess_rocket`
field counts absence of an observed cast including truncated windows; it must
not be interpreted as a known negative outcome in those truncated windows.
No window is discarded for those outcomes. Recorded intervals are sparse:
7,712 windows have an internal decision-row gap greater than one second, with a
maximum of three seconds. Missing intermediate rows are not synthesized.

This index is deliberately marked `trainable: false`: N2 is still open. It binds
historical public-v4 data; using corrected-body features requires a verified row
crosswalk and new source binding. Ordinary and sequence arms, sampling ratio,
update budget, development selection and adequate confirmation/statistical design
still need registration before any optimization. No sampling ratio was selected.

Interpretation: the source contains the owner's requested multi-decision context,
including waits and non-Rocket choices, without requiring successful cycles.
It does not establish positive trades or a gameplay benefit. Selection around a
bow also changes the card mixture: defensive-window plays contain 2,673 X-Bows
as well as 990 Rockets. A later controlled experiment must charge those investments,
support and abilities and measure punishment in both lanes after Rocket casts.
Do not assume increased exposure will improve efficient cycling.

S1-S3 are complete for this preparation leaf. N2-N7 remain open. No successor
IL/RL, confirmation predictions, checkpoint, live setting or Discord model report
was produced. Owner farming remains untouched.
