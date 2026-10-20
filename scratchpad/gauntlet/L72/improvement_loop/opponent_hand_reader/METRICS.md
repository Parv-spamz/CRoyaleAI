# Frozen reader measurements

T1: all 1,680 distinct starting hand-set/ordered-queue configurations, 48 valid
plays each, direct queue oracle after every play; ambiguous order enumerated as
possible worlds. No false in/out deduction, incorrect full set, or incorrect
return bounds. Public/private/future/own-side controls and unchanged v4 features.
Initial unit receipt failed one incorrect hand-written test expectation (d had
three later plays and remained queued). The independent exhaustive oracle passed.
Preserve receipt; corrected fixture also checks the actual ambiguous boundary.

C1: 32 training + 128 development replays selected before result inspection; both
sides. All log entries retained in accounting. Query if hand_before is four
distinct canonical cards, at engine_tick (fallback original tick), before current
play. Direct hand_before must equal the matching play_frame player's hand when
available, otherwise record missing/conflicting oracle. Conflicting or missing
truth is excluded explicitly, never reconstructed from the rotation rule. A
prior accepted same-side play at exactly that tick makes strict-before-tick
truth ambiguous: retain and report separately, exclude from primary precision.

Ideal-events arm: accepted, non-ability commands strictly before query, card
identity only; diagnostic separation of cycle arithmetic from public detection.
These command events are NOT qualified public model input. Public-board arm:
regular board frames -> existing observer -> public plays strictly before query.
Neither arm receives hidden deck/hand; only the independent scorer reads truth.

Per arm/split/replay: evaluated decisions, full predictions/exact/full errors,
full coverage=full/eligible, exact rate=exact/full, in-claims/correct in-claims,
out-claims/correct out-claims, average correctly identified hand cards per query,
unknown deck slots, contradiction/gap counts, observed-vs-accepted play totals,
first full estimate. In/out claims remain conditional on complete detection;
public-board estimates NEVER certified. Do not turn all-unknown abstention into
accuracy or measure only the played card. Card forms share identity, hand slot
positions and next evo readiness are not assessed. Four-card hand oracle only;
other modes unsupported.

V1 independently rereads raw selected logs/play_frames, canonicalizes original
hands, reconstructs ideal prefix conclusions with a separate last-occurrence
formula, verifies exact public query prefixes and all scalar/per-replay counts.
Saved event streams carry source hashes; privacy/unit tests establish the source
adapter boundary. Deliberate truth/prefix/count/hand/deck corruption must fail.
No new training, inference, model acceptance, live deployment or pro-intent claim.
