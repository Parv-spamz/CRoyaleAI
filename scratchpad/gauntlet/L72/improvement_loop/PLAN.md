# New-model improvement loop, October 5 05:05 EDT

October5 owner strategy clarification: read MATCH_ADAPTATION_AMENDMENT.md and
match_adaptation/PLAN.md. Tower Rocket cycling also creates/preserves a weakest-
tower damage lead for a tiebreaker, including above finishing HP. Phase, elixir
multiplier, public matchup and prior offensive X-Bow outcomes must inform learned
adaptation. Finishing is one use case; no fixed tactical switch is authorized.

October5 coverage correction: DEVELOPMENT_AMENDMENT.md supersedes the blanket
dependency requiring complete final-confirmation coverage before all development
training. A frozen, verified development-only split/recipe is still required
before optimization. All untouched final-evidence and deployment floors below
remain mandatory. coverage_recheck v2 separates actual overnight observations
from pro confirmation and includes unplayed low-HP Rocket-cycle targets.

## Owner amendment

The owner's latest instruction supersedes the earlier R1e fallback deployment:

> I want a new and better model to replace R1e in live play, which means i don't want a fallback; i want iterative improvements made until the new model is very significantly better than R1e in all the metrics we care about (rocket, barrel, spawners, sampling, spell aim, etc.)

Continue diagnosis, implementation and bounded learning experiments rather than
closing the queue after the first rejected generation. No further permission is
needed for this authorized scope or accepted deployment. Keep live stopped while
no new candidate qualifies. Preserve R1e as the immutable comparator and recovery
artifact; that is not authorization to restart it as the final fallback outcome.
The existing Tuesday cutoff/Claude takeover remains in force: preserve jobs and
write an explicit handoff if the objective is not achieved by then.

## Evidence carried forward

Q3's eight sampling/aim options all failed their original adoption rules. The
eight L71 IL runs each completed exactly1,000 updates; all nine prediction caches
independently agree over38,317 rows each. None of the requested-fix arms passes
all learning gates. Do not revise those verdicts or the running frozen PLAN.

The original-observation Rocket arm illustrates the tradeoff: ghost Rockets
42->226, tower Rockets5->41, but wins285->274/299; paired delta-3.68pp,
95% CI[-7.02,-0.33]. Reactive wins32->25/48. More Rocket use alone is harmful
here. The strongest held-out Barrel arm moves23 correct/11 wrong to37/1 across39
clear cases, but is a combined model with other failed gates. All arms still
have0/10 correctly aimed gated finishing Rockets. Corrected-body action agreement
must be compared with the ordinary-IL control, not merely untrained R1e; that
component failed, including the required Night Witch protection.

Observation fixes, version6's generic projectile-target residual, public decision
auditing, Q5 repairs and updated runtime selection are implemented/published.
They do not by themselves establish a stronger learned policy. The X-Bow fork
found no eventual resource/tower benefit in its lone qualifying case; archived
Barrel targets do not prove actual live landing coordinates.

## Ordered work

1. Preserve the current34-job chain and finish its full receipt/gameplay review.
   No duplicate GPU work, source edits in that worktree, interruption or early
   stopping. Main integration is already complete. Do independent CPU diagnosis
   and dataset provenance work while this chain runs.
2. Audit training/development versus confirmation provenance. L71's inspected
   validation stays a historical regression instrument; never train or tune on
   its labels/results, and do not present it as untouched final confirmation.
   Find additional unused, replay-separated labeled evidence and freeze its
   membership/hashes. Record any parent-model exposure. If no genuinely untouched
   confirmation corpus exists, collecting it is required work, not a waived gate.
   Predeclare fresh gameplay scenarios/seeds and forbid adaptive confirmation
   reuse. Select and tune only on train/development evidence.
3. Diagnose damage-lead cycling and finishing on training/development examples by separating
   legality, gate, card selection, target representation/aim and subsequent
   decisions. Check one-, two- and three-Rocket cycle finishes separately,
   including positive low-HP states where no Rocket was issued. Inspect
   compact Rocket-only and spread Rocket-then-Tornado opportunities, and both
   sequence heads. Do not assume the ten validation misses identify the cause.
   Include high-HP/non-finishing tower pressure, weakest-standing-tower HP margin,
   defense/lead retention and history of successful/blocked offensive X-Bows.
   Separate elixir multiplier from overtime. Existing narrow labels and total-HP
   audits are not the full adaptation objective; validate new outcome attribution
   on training/development before final tests. See match_adaptation/PLAN.md.
4. Diagnose spawner regressions on matched training/development contexts and
   ordinary-IL controls, separately for Witch, Night Witch and Furnace. Verify
   parent/child identity and model adaptation to changed tokens; investigate
   loss/mixture/representation issues before attributing a fix to more updates.
5. Isolate the generic spatial residual from Rocket/X-Bow mixture changes. The
   Barrel improvement is worth testing as its own one-factor candidate, with
   public input and unknown-target/mirroring checks preserved. Collect public
   flight-to-landing evidence when legitimate live observation is available;
   do not claim archive coordinate validation substitutes for it.
6. Pre-register each bounded successor IL recipe, controls, update budget,
   development selection rule and outputs before launch. Use learned card,
   gate, aim and sequence choices. Longer training, a revised curriculum or
   representation change is a separate attributable experiment, not an
   unrecorded continuation or held-out rescue. Combine only supported changes.
7. Updated-runtime validation is now complete for the applicable mechanics checks.
   The owner's unchanged-binary retry ran all16 previously blocked Rust executables:
   62 additional passes, yielding1603 passes,0 assertion failures and3 ignored timings.
   No agent security-policy or binary change. Retain the optional RoyaleLearn-example,
   skipped-test and private-capture limitations. See rust_retry_owner.json and its
   receipt; do not repeat completed validation. Every new RL run must use the
   pinned new runtime, never the old worktree.
8. After learning/runtime prerequisites, run bounded PPO/RL from a qualified IL
   checkpoint under a predeclared one-factor recipe. Game outcomes/resource
   efficiency remain the objective; no reward for merely issuing more Rockets
   or a hand-written tactical override. Replay/development regressions detect
   forgetting. Final-step/best-development selection is declared in advance.
9. Revisit confidence-filtered sampling and area-aware Rocket aim on a qualified
   learned candidate through separate same-checkpoint A/Bs. These are methods,
   not desired action frequencies: leave an option off if it worsens decisions
   or wins. Original failed options stay rejected. Judge aim by useful impacts
   and outcomes, not only a prettier probability map.
10. Run final untouched confirmation only after a candidate and settings are
    selected. Require the gates below, Q4 diagnostics and confirmed Q5 state.
    Deploy the accepted NEW checkpoint with public audit and anti-leak OFF;
    verify one worker, exact options, normal plays and public audit events.
    The owner's later overnight amendment requests Discord model-performance and
    deployment-verdict reports; unrelated external messaging remains unauthorized.
    Failure means another documented
    development iteration, not a fallback deployment or a relaxed criterion.

## Strong replacement acceptance

These are stricter working requirements for the new objective, declared before
successor training. They do not change L71's frozen acceptance. Final cohort
membership, event definitions, sufficient sample sizes/power and paired uncertainty
method must be frozen before final confirmation policy evaluation. Controlled
development training follows DEVELOPMENT_AMENDMENT.md's separate preregistration
and data-isolation requirements. If final evidence is too sparse, collect more;
do not call a single successful example mastery or deploy from development alone.

- Same-code, same-runtime ghost wins: at least+2 percentage points over fresh
  R1e, with a paired95% confidence lower bound above zero on independent final
  scenarios. Historical299 pins remain regression evidence, not a new holdout.
- Reactive wins: at least+8pp over fresh R1e, paired95% lower bound above zero,
  on at least192 predeclared matched games, with no opponent-family regression.
  Expand using a declared power rule before results, not until a favorable p value.
- Rocket selection and aim: substantial correct opportunity recall improvement,
  at least+10pp aimed-action agreement on eligible expert Rocket opportunities,
  and at least50% correct one-Rocket finishes on at least30 independent windows.
  Two-Rocket finishing sequences and defensive net value must also improve in
  their own cohorts. False fires/wasted elixir must not rise materially.
- Broader Rocket-cycle strategy: demonstrate useful creation/preservation of a
  weakest-standing-tower damage lead and improved late-game/tiebreak outcomes,
  with full resource/punishment accounting. Include phase and public-matchup
  strata and responses to blocked offensive X-Bows. Freeze meaningful effects,
  denominators/power and paired uncertainty before final tests; neither spell
  frequency nor the existing finishing floor substitutes for this objective.
- Rocket-then-Tornado: at least+10pp joint sequence agreement on a sufficiently
  populated independent cohort, plus demonstrated useful defensive combinations
  in gameplay. Two isolated head improvements alone are insufficient.
- Barrel: at least75% fewer wrong-lane fired Logs and at least+15pp correct gated
  lane responses on at least100 unambiguous independent opportunities. Validate
  actual public landing interpretation separately; report missing coverage.
- Spawners: at least+5pp action agreement for each Witch/Night Witch/Furnace
  cohort, with paired uncertainty supporting improvement, and improved defense
  outcomes against spawner decks. Pooling must not hide a family regression.
- X-Bow support: improve appropriate support decisions and show repeated
  resource/tower outcome benefit in matched real-opponent probes; useful X-Bow
  defense must not degrade. The existing one-event probe is insufficient.
- Preserve general card quality (no more than0.5pp decline versus R1e), legal
  plays, public-only inputs and stable live latency. For sampling/area aim, show
  a benefit against the same new checkpoint's deterministic alternative before
  enabling; an option can remain disabled without forcing inferior play.

Require all applicable component/control results, not one winning aggregate.
Use replay/match clustered paired uncertainty, report denominators and failures,
and account for multiple confirmation metrics in the preregistered analysis.
No claim of a very significantly better model until these requirements are met.

## Execution boundary

Owner October5 defensive-X-Bow amendment: add expert efficient-defense to
princess-tower Rocket cycling to the successor research, with spending/remaining
resources and punishment in both lanes measured. DEFENCE_CYCLE_PLAN.md declares
the training-only audit and conditional one-factor learned curriculum;
DEFENCE_CYCLE_FINDINGS.md records the observational evidence. This is not a rule
to deploy X-Bow or Rocket and does not change the frozen L71 comparisons.

One GPU chain at a time. No extra paid infrastructure, account changes, security
policy changes or external communications are implied. Healthy long jobs can be
left running between the existing20-minute same-thread follow-ups. A hard data,
runtime or account blocker must be reported plainly while independent work
continues. Do not promise a successful new model by morning; improvement is an
empirical result to achieve, not a guaranteed consequence of running longer.
