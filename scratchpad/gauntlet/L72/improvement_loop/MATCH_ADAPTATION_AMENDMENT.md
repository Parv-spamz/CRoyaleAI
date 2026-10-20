# Owner clarification: Rocket damage leads and adaptation within a match

October 5, 2026. This expands the currently over-narrow finishing emphasis. It
does not change a completed experiment's definitions, loosen acceptance, prescribe
a live tactic or authorize training on reserved confirmation.

The owner describes tower Rockets as a main damage source when defending is more
effective than repeatedly attempting offensive X-Bow locks. Finishing with one
to three Rockets is one use. Another is gaining and preserving a damage lead for
the tiebreaker: the lowest-HP friendly tower remains healthier than the lowest-HP
enemy tower. In overtime, the rest of the deck, including defensive X-Bows, may
protect that lead while Rockets damage the enemy princess tower. This objective
applies even when the target is above the old 1400/1500 HP finishing inventory.

The owner's hypotheses to measure are that offensive lock success falls as
elixir generation increases, and some matchups repeatedly deny locks earlier.
The learned policy should adapt to phase, public opponent behavior/counters and
the outcomes of previous offensive commitments. This is not a fixed rule that
every late X-Bow is wrong or every affordable tower Rocket is right. Defending
without taking damage, choosing offensive pressure when useful, and choosing not
to Rocket must remain learnable expert choices.

## Earlier record found

- `.foreman/codex_autopilot/TICKET.md`, owner October3 at lines191-196, explicitly
  says tower Rockets may "build a tower-damage lead and let the end-of-match
  TIEBREAKER decide". It also requires learning from pros, not a hand-defined
  Rocket condition. This unrelated dirty file was read without editing.
- `scratchpad/gauntlet/L68/overnight0929/rl_framework_brainstorm.md` records
  adaptation within a match as a goal and proposes opponent predictions conditioned
  on that match's history. A proposal is not evidence that adaptation was implemented
  or that a current model performs it successfully. Its old hidden-information/search
  suggestions do not override the present public-only boundary.
- `scratchpad/gauntlet/L71/rocket_diag/results.json` is a completed historical
  audit of **gen_v31a_s0**, not current R1e. Its overtime/behind subset has1407
  PLAY rows/141 replays: expert Rocket share18.34%, model argmax10.09%, gated at
  tau.35 9.03%. On72 expert tower-Rocket rows in overtime/behind, decoded argmax
  geometry hits an alive tower in5 cases. This is decoded aim, not causal damage.
  Its deficit uses **summed normalized tower HP**, unlike the owner's weakest-
  tower margin. Do not rebrand it as a new/current audit or reuse its inspected
  validation for tuning.

## Implications for development and measurement

1. Keep separate results for damage-lead creation, lead preservation, one/two/three-
   Rocket finishes, troop defense and Rocket-then-Tornado. Do not count only expert
   issued Rockets, successful finishes or low-HP states as all relevant decisions.
2. At equal crowns, measure `min(own standing crown-tower HP) - min(enemy standing
   crown-tower HP)` in actual HP when provenance supports it. Keep crown difference,
   king/princess identity, alive/known flags and both lanes. Destroyed towers are
   accounted through crowns, not included as zero-HP standing towers. Unknown is
   not zero. Report princess-only and normalized diagnostics separately, never
   substitute summed HP or fractions for the stated absolute margin. No arbitrary
   "significant lead" threshold or Rocket trigger is introduced here.
3. Separate overtime from elixir multiplier. `pipeline/obs_contract.py` supplies
   elapsed time, double and overtime flags, tower HP fractions/known/alive flags;
   `pipeline/model_gen.py` consumes these along with own/opponent public play
   history and revealed opponent cycle tokens. The inspected input has no explicit
   triple flag or persistent per-X-Bow outcome summary. Elapsed time can distinguish
   late overtime; available information does not prove effective use. Verify each
   recording's rules rather than treating all overtime as triple elixir.
4. Diagnose successful versus blocked offensive X-Bows using only outcomes already
   observable before each decision. Separate attack-capable placement, target lock,
   actual tower damage and unsupported/unknown outcome. Opponent identities/counters
   are revealed history at decision time, not a future full-deck or hidden-hand leak.
5. Retain all original expert PLAY/WAIT/card/aim labels, failures, non-Rocket choices
   and incomplete defenses. Low HP, overtime, a deficit or failed X-Bow does not
   manufacture a Rocket label. Owner bot actions remain diagnostic, not expert labels.
6. Outcomes must charge X-Bow, support, Rocket and abilities; measure remaining
   elixir, both-lane damage, tower loss, lead change/retention, fixed post-Rocket
   response windows and actual match/tiebreak results. Aim/usage/imitated actions
   alone cannot establish a useful strategic transition. Final paired tests must
   include matchup/phase strata and replay/match uncertainty with adequate power.

The immediate next leaf is `match_adaptation/PLAN.md`: a bounded existing-data
diagnosis before another exposure/loss recipe. It is allowed by
DEVELOPMENT_AMENDMENT.md and does not wait for RoyaleAPI. Completed iteration2
rejected a particular20% defense exposure recipe; iteration3 rejected3x Rocket
aim loss. Neither tests or disproves the whole phase/matchup adaptation objective.
All final component, gameplay, statistical, public-audit and deployment gates stay.
