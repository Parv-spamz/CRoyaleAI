# Owner clarification: learn the future value of keeping a counter available

October 6, 2026, after the overnight handoff. This records the owner's added
learning objective and a proposed investigation. It does not restart the paused
worker, launch training, change existing acceptance floors or prescribe tactics.

## Direct owner instruction

> One more thing that might play into better overall performance: when pros find the enemy has a specific card that can only be reliably countered by one of their cards, they try to hold their counter in their hand for when the opponent plays their specific card. For example. If I know the opponent has goblin barrel, I would try to hold my log in my hand until the opponent plays that goblin barrel, instead of using it for another purpose (even if it’s tempting). Another example is saving the Tesla for the enemy’s win condition (hog rider, balloon, royal hogs, royal giant, etc.), or using rocket on the opponent’s elixir pump, large enemy push, or troop placed behind the king tower. I believe there is pro replay evidence for all of these. if a card being held is still dominantly the top choice for a certain board state, it would still be played regardless of the card holding rule. I want to bring it up because sometimes I observe the model playing a card in an earlier step that could’ve been used to counter an opponent play in a later step, and I think giving the model a sense of “what card should I hold for the opponent’s X?”is a good habit to build. These should be learnt by the model as profitable habits, not hard-coded rules.

## Intended behavior and limits

Learn the opportunity cost of spending a card now: its immediate benefit versus
the future loss of an effective response to a publicly revealed threat. The
relationship depends on the current board, available alternative responses,
resources, phase, public opponent history and whether the card can cycle back
before it is needed. It is conditional, uncertain and changes within the match.

The examples are owner-provided hypotheses and desired coverage, not a fixed
counter table or proof that any card is always the only reliable response. Log /
Goblin Barrel, Tesla / the named win conditions, and Rocket / Pump, large pushes
or backline troops must retain context and the possibility of better alternatives.
Relevant pro replay coverage and profitable retention have NOT yet been measured
by a dedicated audit. Prior encounter counts are not evidence of this behavior.

Holding one card can coexist with playing other cards. The model should also
learn when spending the retained card is decisively better, such as a necessary
immediate defense or a more valuable opportunity. This exception belongs in the
learned action value; do not implement a card mask, hand-written reservation
penalty, fixed logit-margin override, or a rule to wait for a named enemy card.
No reward for holding duration, counter frequency, spell frequency or mere card
availability. Avoid replacing premature spending with passive hoarding.

## Current source evidence, not a new performance result

- `pipeline/model_gen.py:115` consumes own hand/deck/next-card identities, own
  recent plays, opponent recent plays and opponent cycle tokens in global features.
- `pipeline/public_observation.py:206` constructs up to eight distinct observed
  opponent cards with form, subsequent observed-play count and time since last
  sighting, using only plays strictly before the decision. It explicitly does not
  equate four sightings with known readiness. Hidden opponent hand/next card and
  future full-deck knowledge remain forbidden inputs.
- `pipeline/eval_gen.py:34` defines the WAIT target as the deck position of the
  expert's next played card. It is not an explicit target for preserving a counter
  while taking other actions. Existing information and supervision may support
  learning retention implicitly; their presence does not prove that the policy
  uses them effectively, and no missing-input cause has been established.

## Proposed sequence analysis before a learning change

This is an unlaunched proposal, not a frozen executable experiment. A future leaf
must define exact allowed replay membership, sources, public event joins, horizons,
metrics, controls and independent verification before collection or optimization.

1. Start from allowed expert training/development trajectories and original labels.
   At each decision reconstruct only information already public: revealed threats,
   sightings/counts/ages with uncertainty, own hand and next card, known own
   resources and prior spending, alternative actions and current board pressure.
   Preserve unknown/gapped observations and full replay boundaries. Do not use
   reserved confirmation, inspected historical validation or owner bot actions as
   expert demonstrations.
2. Include all relevant decisions, including threat-not-yet-revealed controls,
   no later threat, retained-card unused cases, early card spending, cycling back
   in time, alternative defenses, failed defenses, and justified immediate use.
   Do not select only cases where a later enemy play punishes spending. Holding
   time or later use alone does not reveal the expert's intention.
3. Reconstruct the temporal chain: what was known when the card was spent or
   retained; whether it and sufficient resources were available at a later threat;
   whether another response was available; the actual response and subsequent
   damage/resource/match outcomes. Enemy cycle estimates remain public beliefs,
   not hidden-hand facts. Future observations may annotate training outcomes only,
   never leak into earlier input or be relabeled as known anticipation.
4. Separate failures to retain, failures to anticipate timing, resource shortages,
   card-choice mistakes and poor response placement/timing. Preserve uncertainties;
   observed replay associations cannot prove the alternate choice would win.
   Reuse existing prediction caches only where they answer the exact question.
5. If the evidence supports this behavior, compare one bounded learning change
   against an unchanged control: sequence-conditioned expert learning or an
   auxiliary learned estimate of future response value are possible approaches.
   They are not selected architectures or validated remedies. No manual counter
   map or fabricated hold/spend action labels; retain original expert actions.
   Any outcome learning must measure the downstream consequences rather than
   rewarding the habit itself.
6. Evaluate both useful retention and justified spending, including unseen replay
   groups, different revealed matchups, multiple competing threats, cycle recovery,
   and urgent situations. Measure avoidable damage, full defense cost, unused
   resources, missed offensive opportunities and wins, with paired match/replay
   uncertainty. Higher hold rate alone is not improvement. Final untouched,
   physical, component, statistical, gameplay, public-input and Q4/Q5 requirements
   remain mandatory before deployment.

This adds a temporal decision-quality objective alongside aim fitting and the
existing match-adaptation/damage-lead objective. The overnight optimizer diagnostic
proposal is still relevant to trainability, but it does not test retention. The
new owner hypothesis is recorded separately so it is not lost in that work.
