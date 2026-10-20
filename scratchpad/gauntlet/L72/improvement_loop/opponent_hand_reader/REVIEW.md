# Opponent hand reader: implemented and verified offline

The reader is a new opt-in public-information component. Existing v4 inputs and
the selected policy are unchanged. No model training, optimization, deployment,
live match, automated-worker restart or Discord model report occurred.

## Work and evidence

- Independent queue tests cover all 1,680 starting hand-set / ordered-queue
  configurations and 48 plays each (80,640 checked states), plus possible-world
  same-tick ambiguity, partial reveals, gaps, invalid early replay, unknown
  identity, Mirror, forms, abilities, event duplication and reset.
- Public/private and future-event invariance controls pass, including a public
  positive control. The companion returns byte-identical existing v4 features.
- Eighteen new/relevant tests pass. The original test receipt preserves one wrong
  hand-written expectation; it was corrected before collection. The independent
  queue oracle already passed that original run. No old result was relabeled.
- Fixed cohort: 32 training and 128 development replays, selected lexically from
  already exposed inner split membership. Both sides and all selected replays
  retained. There were 13,047 log entries: 12,696 usable hand queries and 351 with
  missing/non-four-card hand data. Every usable hand_before exactly matches its
  separate saved play-frame player hand. No conflicting oracle, missing second
  hand or same-tick ambiguity exclusion was needed among usable queries.
- The independent verifier rereads original hands and accepted events, reconciles
  every prefix prediction and per-replay/scalar result, and passes 3 positive / 8
  deliberate corruption controls. It does not import the tracker or producer.

## Measured accuracy and coverage

| Cohort / event source | Decisions | Full estimates | Exact full hands | Exactness when full | Full coverage |
|---|---:|---:|---:|---:|---:|
| Training / ideal accepted events | 2,272 | 1,058 | 1,058 | 100% | 46.57% |
| Training / public board detector | 2,272 | 1,008 | 980 | 97.22% | 44.37% |
| Development / ideal accepted events | 10,424 | 4,692 | 4,692 | 100% | 45.01% |
| Development / public board detector | 10,424 | 4,354 | 4,245 | 97.50% | 41.77% |

In development, public in-hand deductions were correct 28,448 / 28,611 (99.43%);
out-of-hand deductions were correct 38,370 / 38,620 (99.35%). These denominators
count only explicitly deduced states: unknown cards are not counted as correct.
Partial deductions are useful even when the complete hand is unknown. Complete
accepted-event history gave zero in/out mistakes in both cohorts.

The perfect-event arm uses accepted command identity ONLY as a diagnostic oracle
for event detection; those command records are not qualified public model inputs.
The actual reader arm sees only regular public board frames, stripped of players,
elixir, decks, commands, opening hand and command-timed play frames. Hand truth is
read only by the separate scorer. No hidden field repairs a public estimate.

## Findings and limitations

The user's cycle hypothesis works: explicit hand reconstruction is feasible from
complete observed card plays. Existing model cycle tokens already contain related
information; this result does not prove the old model failed to use it or that an
explicit new feature improves decisions.

Full coverage is limited principally by incomplete public deck revelation. On
development, all eight identities had been detected at only 4,428 / 10,424 queries.
Even ideal accepted events gave a full hand at only 45.01% of decisions. A card
that remains unrevealed must remain unknown, not be filled from the final deck.

There were 109 wrong full public estimates across 48 development replays; only 15
had an explicit tracker issue. Lack of a contradiction is therefore not sufficient
to certify an estimate. One saved example at tick5641 has Skeletons played at5636,
but the board detector's visible history still ends at Knight5591. The reader
therefore retains Skeletons instead of recognizing Tornado's return. This is an
observation-delay example, not a cycle arithmetic failure. Other misses/confusions
remain represented in the original histories; no private-timestamp repair applied.

The same-tick exclusion and typical 10-tick recording cadence are retained. No
post-hoc latency allowance changes the accuracy denominator. Native re-drives have
reconstructed deals/outcomes; these results do not establish original pro-client
hand recovery or current live-reader accuracy. Repeated decisions within a replay
are correlated; 10,424 queries are not 10,424 independent matches. Historical
Champion cycling, special deck modes, ambiguous Mirror origin and future evolved
form readiness are not qualified by this audit. Full eight-card FIFO assumptions
and event uncertainty remain explicit in the API.

## Verdict and next work

Reader implementation and bounded offline verification are complete. Public
estimates stay conditional (`certified=False`); do not use them as hard action
masks or hard-coded hold rules. No model acceptance or gameplay benefit is claimed.

The next learning comparison can use these public beliefs, uncertainty and own
cycle/resources to learn the future value of keeping a response available. It
must include justified immediate spending as well as retention, and compare
actual defensive damage/cost and wins against an unchanged policy. First qualify
the same detector against authorized live recordings with an independent oracle
where available, and examine missed/delayed casts and Mirror separately. New
versioned model inputs require training and public-input compatibility audits;
old checkpoints cannot consume a new tensor merely because the reader exists.

All original final statistical/component/physical/gameplay/public/Q4/Q5 floors,
reserved confirmation and failed-model verdicts remain unchanged. Owner STOP is
intact; no R1e fallback restart. Overnight automation remains paused.
