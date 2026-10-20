# Fresh confirmation discovery: rules before inspecting new model outcomes

The existing re-driven corpus audit finds52,129 files but only14,661 unique replay IDs; all are historically exposed. Its first pass incorrectly accepted only32-character HF IDs; v2 also covers12-character RoyaleAPI IDs and reports zero unparsed dataset tags. Preserve both reports; use v2. No local recording has yet qualified as fresh confirmation.

Next inspect the locally cached52 public FirstLight/IL_Replay parquet parts. Validate each file against the checked-in download manifest. Exclude all known dataset train/validation IDs, original labeled-source IDs and historical ghost/evaluation IDs. Also exclude cross-source replay duplicates using the project's conservative signature: unordered base-deck pair, number of non-ability commands, and first12 sorted(tick,base-card) commands. Build signatures for both historical HF records and original RoyaleAPI crawl2 timelines; group remaining duplicates together. Inspect only schema, command availability and deck/card eligibility. No model scores, tower outcomes or finishing success are inspected.

Record candidates and counts for exact Icebow; decks containing Rocket/Tornado; Log versus Barrel; and each Witch/Night Witch/Furnace opponent family. These are discovery strata, not claims of adequate final component denominators. Exact Icebow evidence cannot be replaced silently with another deck. Retain form identities in the eventual data; base-card normalization here is for conservative duplicate exclusion only. Anonymous player data cannot prove player-disjoint splits; require replay-command-disjoint groups and state this limit.

Before any successor training, assign whole verified replay groups deterministically using a declared hash salt to training/development/locked confirmation, freeze exact IDs and native reconstruction/source hashes, and preregister effect sizes/metrics/sample-size expansion/multiplicity. Do not run a model on locked confirmation until a candidate and settings are selected. If unused Icebow or rare finish/combo windows are too few, collect additional public replays instead of relaxing the gate. This discovery inventory does not close N2 or authorize successor training by itself.

## October 5 discovery result

All52 manifest-bound parquet files verified. Of252,238 raw records,12,258 have
known historical HF IDs and41 lack positioned plays. The remaining239,939 command
groups include183 exact Icebow,5,474 Rocket/Tornado decks and4,764 Log-versus-Barrel
matches. Icebow-specific opponent counts are5 Witch,22 Night Witch and17 Furnace.
These are deck counts, not eligible component-window denominators.

The native-reconstruction follow-up materially narrows availability:167 of183
Icebow candidates have prior failed attempts, all with the missing native evolution
form error26000043;16 have no local attempt receipt. None has a qualifying local
recording yet. Do not count failed reconstruction as successful confirmation,
silently remove the evolution, or substitute simulated observations for native
evidence. Public additional-data acquisition or supported faithful reconstruction
is still required. There is no active local native engine listener on ports37031–34
as of06:09 EDT. The updated RoyaleSim runtime and this old native-engine form gap
are separate systems.

Evidence: replay_inventory_v2.json, unused_hf_inventory.json,
candidate_reconstruction_inventory.json and their integration/checks receipts.
