# Terminal accounting and common-state divergence diagnosis complete

October5. F1-F3 complete on the192 completed development games, without new
games, policy predictions or optimization. report_v2.json/verified_v2.json bind
all192 records and64 ordinary_v5-v6 pairs. Producer34.10s/independent24.31s exit0;
accounting_controls.json executes the exact independent refusal fragment with
one positive/seven corruptions in0.13s. The independent main verifier includes
four tower positive/five malformed-tower cases, two command positives and one
prior-frame negative control. Original gameplay verdict stays REJECTED.

## Terminal-phase accounting

All learner game_over refusals land on/after tick6000, none after recorded final
tick. No accepted command from either side, including abilities, occurs>=6000.
Pinned native source explicitly rejects actions during tiebreak_frozen(), while
the existing wrapper continues until game_over resolves after the drain. Hence
most frozen "other refusals" are terminal-phase actions, not ordinary legality.

| R1e / ordinary_v5 / ordinary_v6 | R1e | v5 | v6 |
|---|---:|---:|---:|
| game_over responses |13|21|31|
| Decided before6000, landed after boundary |1|3|6|
| Decided on/after6000 |12|18|25|
| out_of_territory |1|0|1|
| match_over_before_landing |20|27|35|
| Games reaching6000 |8|10|12|
| Six-slot margins observed at6003 |6|8|9|
| Ahead / behind among those |5/1|3/5|4/5|

For all23 complete6003 snapshots, weakest-standing absolute-HP sign matches final
winner. Seven other late games have unavailable complete margins; do not infer
destroyed slots as zero or treat this selected subset as a win-rate comparison.
No safe Rocket-cycle, causal damage or resource-efficiency claim follows. Preserve
5999 and6003 fields separately; tiebreak drain HP losses are not spell damage.

The first audit failed a six-slot assertion. Raw telemetry omits some destroyed
towers. Original audit.py/started.json/nonzero receipt remain. v2 validates present
identities and returns unknown for fewer than six slots; fully observed HP checks
remain strict. Malformed complete snapshots and duplicates are rejected. Partial
snapshots do not supply a usable margin, regardless of remaining HP values.

## First divergence

23/64 v5-v6 pairs have identical accepted commands throughout. In41 pairs, the
first accepted-command difference is a learner command, with the entire preceding
public frame sequence exactly identical. All64 scenarios retained, no outcome
selection. The first differences include29 same-card pairs (different placement),
two different-card pairs and10 one-sided commands (not evidence of an explicit
WAIT prediction). Same-card counts: Knight9,IceWizard5,Tornado5,Skeletons4,Tesla2,
Xbow2,Log2. Different cards: Tesla->Skeletons1,Tesla->Xbow1.

These common-state changes demonstrate that the trained policies differ beyond
Log aim. The projectile branch directly touches only spatial features, whereas
end-to-end training also changed the base weights. A first action difference
does not prove that action caused the final loss. No model calls were needed.

Next registered experiment development_iteration_7 freezes all verified ordinary_v5
base parameters and trains only the same generic projectile-target branch on the
original expert training split/draws. This tests shared-weight interference as a
hypothesis, preserving exact gate/card/value predictions. It is not a deployment,
handwritten card rule, combination of failed loss/exposure recipes or an asserted
complete Rocket remedy. Final strategy, component, gameplay and statistical gates
remain open. A separate future wrapper change should suppress post-boundary
decisions while still advancing the native tiebreak to its actual outcome; it
must prove accepted-command/final-state equality before integration. No wrapper,
runtime, original data or live setting was changed in this diagnosis.
