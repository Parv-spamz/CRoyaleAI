# Public opponent hand reader

Owner request October 6, after the overnight cutoff: build a hand reader from
public plays and verify it against past matches. This separately authorizes this
reader and its offline checks; no worker automation, training or live restart.

Implement a standalone eight-card/four-hand FIFO belief tracker and an opt-in
adapter to the existing PublicObserver. Existing feature-version-4 tensors and
policy remain unchanged. Input is already-public played card identity, never a
hidden hand/deck, future reveal, command or elixir. Base/evolution/hero forms share
a deck identity; abilities do not rotate cards. Mirror must be identified as the
played Mirror slot, not its resulting body. Unknown identity, gaps, duplicates,
contradictions, same-tick unknown order, reset and unsupported modes are explicit.
Do not invent probabilities or turn detector completeness into a fact. Expose
conditional in/out/unknown states and coverage separately from trusted evidence.

Rules source: Supercell, October Update 2025, September 25 2025:
https://supercell.com/en/games/clashroyale/blog/release-notes/october-update-2025/
Champions now cycle like ordinary cards; Mirror can copy Champions. Historical
three-card Champion mode and special deck modes are unsupported, not silently
treated as modern eight-card FIFO. Hand means card identity set, not UI positions,
affordability, ability readiness or next evolved form.

Offline cohort frozen before results: first 32 training and first 128 development
tags sorted lexically from the already exposed development_iteration_1 assignment,
joined to match_adaptation/prepared.json sources. All selected replays and both
sides retained, regardless of success, matchup, detector error or hand accuracy.
No reserved confirmation, L71 validation or bot actions as expert labels. These
are recorded native re-drives of past pro sequences, not original client/video
hand truth or live-reader validation. The first inspected source was schema-only.

Score all log decisions with a directly recorded four-card hand_before, strictly
before that decision. Check matching play_frame player hand where available.
Truth is isolated in the scorer; it never fills missing public cards or repairs
the tracker. Compare (1) ideal accepted-card event sequence, diagnostic only and
(2) actual PublicObserver events from public regular frames, production-like.
Never feed command-timed play_frames to the public detector. Freeze code before
collection and bind source hashes, raw predictions, truth and all denominators.

Report per split and per replay: full-hand exactness AND coverage, per-card in/out
precision, unknown fraction, first full estimate, contradictions, missing truth,
event detection counts and timing limitations. Complete event logic must pass
independent queue fixtures. Public-detector reliability is measured, not assumed;
if it fails, leave its estimates explicitly untrusted and document the concrete
failure rather than promote them to hard model features. No automatic tactics.

Execution: T1 unit/compatibility/privacy controls; C1 frozen replay audit; V1
independent raw hand/event/scalar recount with deliberate corruptions; R1 review
and scoped publish. New tests may be repaired before frozen collection; preserved
failed receipts are never relabeled. No rerun of any overnight experiment.
