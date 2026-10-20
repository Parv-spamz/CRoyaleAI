# Public opponent hand reader

`pipeline/opponent_hand.py` provides a standard eight-card / four-card-hand FIFO
tracker. It deduces card identities from observed plays, not from opponent memory.
It does not prescribe which counter to hold or change the policy checkpoint.

```python
from pipeline.opponent_hand import PublicHandObserver

reader = PublicHandObserver(side=0)  # our side
reader.update(public_reader_frame, source="reader")
belief = reader.hand_at(decision_tick)
# in_hand, out_of_hand, uncertain, unrevealed_slots, plays_to_return,
# full_hand, certified, issues
```

`hand_at(tick)` uses only events strictly before `tick`, matching existing v4
history semantics. Native frames first require the existing `tag_native_recording`
normalizer; `source="sim"` uses the existing public SIM schema. Call `reset()` at
match boundaries. The companion's `features()` returns existing v4 features
unchanged. This implementation is opt-in: no live worker or trained model calls
it automatically. It is a separate public belief API ready for a future versioned
feature/training comparison, not an untrained input added to an old checkpoint.

For a separate qualified public play feed, use `HandBelief.observe(cards, tick=...)`
or `from_public_plays(events, tick, own_side)`. Pass all same-tick events together.
Use stable event IDs to deduplicate retransmissions. Normalize card forms to their
base deck identity. Hero/Champion abilities do not advance rotation. A copied
troop produced by Mirror must be attributed to the **Mirror slot** if that fact
is publicly established; otherwise mark its identity unknown. `gap()` explicitly
invalidates rotation while preserving previously revealed identities.

After a card is played, its return requires four further card plays. Once back,
it stays in the inferred hand until played again. Before all eight cards have
been revealed, the reader can still give partial in/out deductions; it does not
guess missing deck cards. Same-tick unknown order yields conservative intervals.
Return counts are counts of card plays, not time or affordable-play estimates.
Only identity sets are inferred, not UI slot positions or upcoming evolved form.

All results are conditional on correctly identified, complete public play events.
`PublicHandObserver` always reports `certified=False`: board sightings have delay,
and the existing detector can miss or confuse casts. **No issues is not proof of
complete detection.** Do not turn these beliefs into hard legality or tactical
masks. `complete_events=True` is reserved for an independently qualified event
contract; it is not a way to upgrade the board detector's confidence.

Supported rules are modern standard eight-card FIFO. Supercell's October 2025
update made Champions rotate normally and allowed Mirror to copy them:
https://supercell.com/en/games/clashroyale/blog/release-notes/october-update-2025/
Historical three-card Champion cycling and special deck modes are unsupported;
passing another rules identifier abstains. Unknown rules must not be silently
declared standard. Mirror's public identity is not reliably resolved by the
existing body/spell detector, so Mirror-specific accuracy remains unqualified.

See REVIEW.md for direct saved-hand accuracy and coverage. Replays are native
re-drives of past pro sequences, not untouched original-client or live validation.
