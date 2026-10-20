# Native Rocket context audit — October 3, 2026

MEASURED descriptive census:14,661 unique native replay tags,1,012,450 accepted non-ability plays,
10,045 accepted Rockets. All14,818 fetched recordings passed source verification;157 duplicate-tag
variants are excluded in the same first-corpus order as dataset_gen. Every retained recording is
native/full. This is reconstructed replay-engine evidence, not a new policy comparison.

There are6,307 geometric enemy-crown-tower targeting candidates. Their projectiles and a following
tower-HP observation are recorded for all6,307. A3.5-tile audit envelope and compatible HP changes
do not independently establish causal hits. Confirmed-hit labels remain unavailable.

| Candidate context | Rockets | At/below497 HP | Above497 HP | Median tower HP | Median own elixir |
|---|---:|---:|---:|---:|---:|
| Native tiebreak-labelled ending |2808|46|2762|2044.5|8.298|
| Other labelled ending |3256|454|2802|1863.5|8.516|
| Ending unclassified |243|21|222|1756|7.726|
| All tower candidates |6307|521|5786|1967|8.390|

The497-HP split is the requested live diagnostic, not a universal native Rocket-damage threshold
or a rule for loss weighting. Native level11 diagnostic samples showed342-HP drops. These data
support studying repeated tower Rockets at substantially higher HP; they do not identify intent.

Tower-candidate phases:783 single-elixir,1586 double-elixir regulation,3938 overtime. Median remaining
time to the five-minute boundary is88.6s (10th–90th percentiles12.7–202.4s). Median pre-cast total
own-minus-enemy tower HP is-342 (10th–90th:-2024 to1162). Pre-cast crown scores (own:enemy):0:0=6142,
1:1=30,0:1=87,1:0=44,0:2=2,2:0=1,2:1=1. All candidate context snapshots match the cast tick.

| Rockets targeting one tower by one side in one replay | Tower sequences |
|---|---:|
|1|1405|
|2|666|
|3|388|
|4|247|
|5|142|
|6|69|
|7|28|
|8|10|
|9|2|

There are1552 sequences with at least two candidates. The3350 repeat-cast gaps have median32.5s
(10th–90th:15.75–101.35s). These are targeting sequences, not a claim that every Rocket hit.

Native tiebreak evidence is explicit `native_tiebreak_hp_drain`/tiebreak termination information,
not elapsed-time inference. The bridge surfaces the native core's HP-drain result; its existing
fixture is `research/ext/cr-native-sandbox/scripts/accept_match_rules.py`. This corrects the
earlier small-sample coverage limitation: the full corpus does contain native tiebreak labels.
It does not prove that the original human match or the player's strategy was tiebreak-driven.

Among1022 replay/side endpoints with a tower candidate and a native tiebreak label, final recorded
own-minus-enemy tower HP has median-430 (10th–90th:-2258 to1441). These are post-drain endpoints,
one per replay/side; they are not Rocket-weighted or a baseline-model acceptance result.

The pooled mixed-deck Rocket share is10,045/1,012,450=0.992%. It must not be compared as though it
were the separate S1 Icebow5.8% reference. No classifier or held-out loss weight is selected here.
True hit attribution and complete timing/area source validation remain required for gen_v3.1.

Evidence: `native_mining_1552/{report.json,manifest.json,rockets.jsonl}` and
`native_rocket_contexts_1839.json` (source hashes and all requested context distributions).
The failed first Barrel audit is separate; exact duplicate-frame handling passed7 tests and
its preserved-output retry is running in `native_barrels_1837`.
