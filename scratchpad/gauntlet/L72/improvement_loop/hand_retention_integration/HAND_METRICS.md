# Public hand successor, before implementation

H1 adds a separate successor, leaving opponent_hand.py and its original audit
unchanged. Normalize only accepted opponent play events, sorted causally; abilities
do not advance the cycle. In a strictly ordered stream, adjacent equal base card
identities imply Mirror's slot on the second play if standard rotation remains
consistent. Never convert third consecutive copy to another immediately playable
Mirror, never relabel a repeated frame/swarm body, and never introduce a ninth
public deck identity. Explicit Mirror events remain explicit. Missing/ambiguous
order or contradictory known deck/cycle yields uncertainty, not a hidden lookup.

Mirror inferred from the current board-derived event feed is a hypothesis under
the complete-event assumption. Preserve copied identity and provenance. Do not
claim that the optional memory object level is the player's Mirror card level,
or that a mirrored troop is always above the original troop's level.

Expose an eight-row identity/availability/return-count belief tensor plus quality
flags; unrevealed identities stay padded, no final deck filling. Include maskable
unknown state, full-hand coverage, issue count and Mirror-hypothesis status. All
fields at decision tick use strictly prior observed events; no future commands,
true hand/elixir, ability readiness, raw private deck or opponent next card.

Controls must cover normal return/retention, canonical body forms, consecutive
same-card Mirror, explicit Mirror, triple repeated copies, impossible nine-card
deck, ability interposition, same-tick ambiguity, own-side/future/rejected events,
gaps, absence and duplicate observations. Hidden truth mutation must leave every
feature byte identical; changing a past public play must change features.

Use confirmed public events as the arithmetic fixture. The existing memory-reader
schema is polled board state, not a published accepted-card command stream; its
100ms default poll, object generation identity and body levels are source facts.
Measure timing separately if a saved independent oracle permits it. Existing
replayed examples with delayed appearances remain valid evidence of event-path
delay, not image-detector errors or evidence that current live lag is identical.
