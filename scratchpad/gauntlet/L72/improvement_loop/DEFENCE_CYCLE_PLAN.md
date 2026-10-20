# Defensive X-Bow and princess-tower Rocket cycles

Owner hypothesis, October5: efficient defense and useful defensive X-Bows may
fund repeated princess-tower Rockets without the observed win-rate loss. Test
this as learned behavior. Increasing X-Bow or Rocket frequency alone is not the
objective; both cards consume resources and can expose the other lane.

Source inspection found that L70 fit_public_context.py's retained API target
`defensive_xbow_rocket_cycle` labels only defensive placement, explicitly without
a following Rocket. Do not relabel that historical artifact or running/frozen
experiments. The existing L71 X-Bow exposure primarily concerns dead-lane support,
so its result does not directly test this new joint-sequence hypothesis.

First implement a CPU training-only observational audit, before new training:
use only original Icebow pool rows with split0, retaining all qualified X-Bow
events and failures. Join hash-verified pro native recordings and existing
calibrated X-Bow/Rocket outcome labels. Report defensive versus other placements,
bridge distance and phase. A deeper placement is at least3 tiles from the river
on its owner's side, for offline stratification only. Use fixed10/30/60-second
windows,30s primary descriptive horizon. Count HP-confirmed princess-tower
Rockets, repeated hits to the same tower, all accepted own/opponent spending
(including the initial X-Bow and abilities), remaining own elixir and own
princess-tower damage. Missing coverage is unknown, never a zero outcome.

Spending balance is not a proven positive trade: a troop can survive, distract,
or remain dangerous. Label observations as association, not causality or proof
that defensive X-Bows win. Include non-Rocket responses and WAITs in future
teaching windows, rather than inventing targets. Opponent true elixir/future
outcomes may be evaluation labels only, never model inputs.

After usable new train/development/confirmation evidence and statistical design
are frozen, register a bounded one-factor IL comparison of ordinary imitation
against expert defense-to-Rocket sequence exposure, with the same initialization,
total updates and other curricula. Select using development only. Charge bad
X-Bows, follow-up support and Rocket investment in matched updated-runtime
reactive tests; inspect both lanes, retained defense and the opponent's response.
Outcome-driven RL is conditional on the existing learning/runtime gates. No
deployment rule to force a defensive X-Bow, save6 elixir or cast a Rocket.

Require actual useful princess damage/cycling plus preserved or improved defense
and gameplay, and every existing new-model/component gate. This adds an experiment
to L72; it does not alter L71 outcomes or relax replacement acceptance.
