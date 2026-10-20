# First updated-runtime closed-loop development comparison

October5 16:10 EDT. Iterations2-6 failed their declared continuation criteria.
Only iteration1 ordinary_v6's isolated learned projectile-target residual passed
its comparison against ordinary_v5. Test that supported pair in reactive games
before another loss recipe. This is development, not final confirmation, power
completion, a new checkpoint, RL optimization or deployment qualification.

Three frozen policies: original R1e31u0155, verified portable ordinary_v5 and
ordinary_v6. Primary architectural contrast v6 versus v5; R1e is the broader
reference with its original feature4 observations. The two fine-tunes use corrected
features5/6. Do not call R1e's gameplay inputs identical to corrected-input offline
R1e. All three use the same source/runtime, deterministic existing live decoder,
tau.35, affordability, existing stall handling,26tick delay/extrapolation, noise
off, no filtered sampling/area aim/search/tactical overrides. Production unchanged.

Pin main RoyaleSim0.1.13/RoyaleGym0.1.15 via royale_runtime.activate and all pipeline
Python source hashes, checkpoint/ability/census/runtime manifest hashes. Fixed
opponents gen_v1_s0 and S1_icebow_v6aug_s1, opponent tau.27. Gen uses the existing
evo/hero census L70/pool_forms/loadable_decks.json; S1 uses original Icebow. Deck
forms and abilities-v2 remain active. Reject setup form fallbacks before prediction;
never silently accept substitutions. Preserve failed setup attempts. No reserved
human replay is read, no old validation or owner bot labels used.

Freeze32 consecutive development seeds2026100500..2026100531, both opponent
families, seed parity sets learner side. Use inherited deterministic census
proposal sequence seed*1000+j (j0..49); choose first vocab-compatible, native-loadable,
form-preserving setup before any game prediction. Save every rejected proposal.
S1 setup failure or exhaustion fails preparation. Freeze all64 exact decks/sides/
seeds/tags and initial engine-state hashes. Independently reproduce manifests and
check each setup against all3policies, no game outcome inspection. Do not replace
a difficult scenario after gameplay. These are synthetic development scenarios,
not substitutes for missing fresh expert or final component evidence.

192 serial matches: scenario outer, R1e/v5/v6 inner. OneGPU chain and file lock
through subprocess gaps. Fixed7200tick cap, preserve truncation/refusals/fallbacks;
any incomplete/mismatched game makes the comparison incomplete. No adaptive
seed additions, early stopping for score, automatic resume or repeated full jobs.
Tuesday cutoff preserves completed records and active match, starts no next match.

Save raw public telemetry frames/accepted plays compressed in ignored data plus
full learner result and raw terminal tower state. Standard behavior summaries
retain their existing geometric/estimated-impact limitations. Never equate summed
towerHP with weakest-standing-tower margin or X-Bow placement with a lock. No new
physical-damage/strategy labels are introduced. Public telemetry is not policy
input. Native emulator is not used; no live restart or change.

Before launch: verify runtime/sources/checkpoints, all setup pairs/forms and standard
loaders; a separate fixed CPU short-horizon telemetry-on/off control must have equal
accepted commands/final engine state and confirms wrapper isolation. Smoke games
use a separate seed and cap, never count toward192. Synthetic count controls must
reject missing/duplicate/mismatched scenarios, altered outcome/crowns and truncated
records. Do not repeat the already completed upstream mechanics suite.

After collection independently recount exact membership/source/checkpoint/runtime
bindings,64complete paired scenarios permodel, wins/losses/draws byfamily, outcome
and crown differences, accepted/refused/unlanded plays and behavior denominators.
Use32seed-cluster paired bootstrap (both opponent families together),10000 draws,
seed2026100507, percentile95% intervals; these are descriptive development intervals.
No final multiplicity/power claim. Raw behavior events and missingness retained.

Development continuation only if v6 win point estimate is no lower than v5 in
either family and no lower than R1e overall, no new form/legality/runtime errors,
all matches complete, and supported iteration1 component checks remain bound.
Inconclusive/failed outcomes remain so. A pass supports a separately registered
next development/RL proposal; it never meets final acceptance by itself. All
PLAN.md final gameplay/material component/untouched/statistical/Q4/Q5 gates remain.
Preparation environment correction, before any prediction: initial prepare.py
failed importing gymnasium under icebow/.venv, with no files in its created OUT.
Keep that source/nonzero receipt. prepare_v2.py requires that exact failed receipt
and empty directory, then uses the existing research/ext/Royale/.venv interpreter
already used by the pinned runtime's successful checks. No installation, runtime
artifact replacement, source-policy change or gameplay measurement occurred.
