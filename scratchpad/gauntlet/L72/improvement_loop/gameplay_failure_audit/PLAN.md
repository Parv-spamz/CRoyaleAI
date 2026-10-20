# Diagnose the completed development gameplay failure

October5, after development_gameplay_1 failed its frozen win-point criteria.
No new policy inference, training, simulator games, source changes, acceptance
reclassification or final-confirmation access. Bind the completed 192 raw records,
index/results/review hashes and exact pinned simulator/adapter sources first.
Preserve the existing frozen refusal filter and rejected verdict verbatim.

F1: distinguish raw learner refusal reasons for every match. The original filter
excludes only match_over_before_landing and includes game_over. Pin the source
contract: normal play ends at tick6000 for this exact runtime/setup; the native
tiebreak may drain before game_over becomes true. Record every rejected command's
decision/landing/end ticks, reason and card. No out_of_territory or unknown reason
is relabeled. Require all game_over responses to land >=6000 and <=final tick,
and no accepted ordinary/ability command after the runtime's play boundary.
Count preboundary decisions landing after boundary separately from decisions
made during the drain. Retain all original accepted/unlanded/refused totals.

For every match reaching6000, record exact raw crown-tower margin at ticks5999
and6003 when present. Require six unique explicit tower identities (side/kind/x/y),
positive HP for standing; dead towers count toward crowns, not minima. No raw HP
inference from fractions. Unknown/missing remains unknown. Report final outcomes
and whether those margin signs agree, but do not call a clock/sign correlation
proof of damage attribution or a safe Rocket cycle. Include draws and crown
differences; a match may end before/inside the freeze. Do not use drain HP losses
as spell damage. Missing king visibility would be outcome-only, never a new input.

F2: all64 paired ordinary_v6-v5 scenarios, without selecting by wins. Normalize
accepted commands by tick,side,card,x,y,ability and compare simultaneous multisets.
Locate the first different accepted-command tick. Compare exact complete public
frame lists strictly BEFORE that tick and both-side command prefixes; identify
the learner/opponent role(s) of different commands, card and geometry changes.
Absent command is not a fabricated WAIT prediction. If frame prefixes differ or
are unavailable, mark nonidentical/unknown rather than claiming a common state.
Record paired final outcomes descriptively; first divergence is NOT causal proof
that a particular action lost the match. Do not use future outcomes as input.

F3: independent raw recount with a separately implemented command comparison and
tower-margin/refusal accounting. Positive fixtures plus wrong side/kind/duplicate
tower/dead/unknown HP, simultaneous ordering, post-divergence frame leakage and
reason/tick corruption controls. Exact per-match/per-pair output equality required.
Review before selecting further learning or an isolated runtime-wrapper repair.
No completed native/model/mechanics/test jobs are rerun. Owner STOP stays intact.
