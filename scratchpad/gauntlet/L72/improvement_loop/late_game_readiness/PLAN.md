# Full-history late-game learning readiness

Registered October5 after the movement-input effect predictor failed all three
body continuation filters. Both prior full-game outcome RL recipes also failed
the owner's target metrics. This tests a different hypothesis: concentrating
optimization on complete late-game situations may reduce dilution by earlier
decisions and focus outcome credit. It does not claim missing motion inputs,
prove a credit bug, or make a tactical late-game switch.

This leaf is engineering readiness ONLY. ZERO optimizer updates/new models.
Collect16 fresh complete interactive native simulated games with the verified
ordinary_v5 parent,8 generalist/8 S1 opponents, both learner sides balanced.
Seeds2026101400..415; first8 gen decks from the already exposed fixed gameplay
schedule, interleaved with Icebow/S1. No result-dependent deck/seed selection.
Same public sampler tau.35/T.5,26tick delay/extrapolation,10tick cadence,noiseoff,
updated MAIN runtime, deck forms, abilitiesv2 and qualified terminal adapter.
Four simultaneous games per batch in one GPU process/shared chain lock.

Play every game from its normal initial state through actual native termination.
After completion, create a separate learning view containing decisions at or
after regular_ticks + overtime_ticks//2 (4800 in the pinned standard schedule).
Use public phase durations, never HP/cards/rewards/observed outcome to choose
membership. Keep full raw trajectories, all early terminal games (empty late
views), all pending/refused/unlanded actions, full initial/final native bytes and
actual outcome. Never reset public history, truncate a match, alter a decision,
add an action or resample a missing late game. This tests suffix selection, not
snapshot restoration or a new policy driver. The current policy plays both
prefix and suffix; a future recipe must specify this distribution explicitly.

Verify exact selected observation/action/probability fields, including past,
opp_past, opp_cycle/projectiles/effects, against their full trajectories. Before
any future optimizer, qualify original sampled probability recomputation (<1e-4),
native terminal rewards and terminal gap, exact shared-row raw GAE/returns for
lambda.95 and1.0, and finite nonzero actor/critic backward gradients with every
weight unchanged. Rebuilding match weights and advantage normalization on the
late batch is intentional; require independent calculation. Preserve native
outcomes and original complete trajectories; suffix projection occurs after
engine termination and cannot change queued commands. No result filtering.

Budget fixed16 games, no adaptive increase. Readiness requires at least4 games
with contributing late rows and at least256 late contributing rows; otherwise
record insufficient coverage, do not change the boundary or resample. This is
an engineering backward-probe minimum, not statistical power for acceptance.
No expert/reserved/L71 validation/bot labels; np.load restricted to own outputs,
stock Learner and gen_v3val blocked. Parent exposure remains disclosed.

Independent verifier reads saved arrays/records only, no model or producer/RL
helper imports. Controls must reject row/field/history/reward/probability/split
membership corruption. No gameplay strength verdict from these16 games.
Final floors unchanged. Any future optimization needs a separate frozen plan,
control/budget/final-only choice and development/gameplay acceptance afterward.
Owner's extended cutoff Oct6 13Z applies before each batch/job; preserve current
work. No automatic retry, no live change, no Discord model report due.
