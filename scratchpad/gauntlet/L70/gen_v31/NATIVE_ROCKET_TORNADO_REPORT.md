# Native Rocket/Tornado census — 2026-10-03 22:08 EDT

**Measured:** 14,661 unique verified replays, 10,045 accepted Rockets and 19,261 accepted Tornados. All source hashes and Rocket event identities reconcile with the earlier native census. This is the mixed-deck corpus, not the IceBow-only 5.8% reference population.

Rocket-first is more common under the historical **cast** prior: same side, cast gap at most 2.5 seconds, normalized aim distance at most 0.11. This prior is a measurement definition, not an action rule or validated hit label. Forward board direction is decreasing normalized y.

| Rocket group | Rocket → Tornado | Tornado → Rocket |
|---|---:|---:|
| All 10,045 Rockets | 494/10,045 = 4.918% [4.443, 5.429] | 21/10,045 = 0.209% [0.127, 0.302] |
| 3,738 non-tower candidates | 184/3,738 = 4.922% [4.194, 5.720] | 16/3,738 = 0.428% [0.240, 0.646] |
| 6,307 tower candidates | 310/6,307 = 4.915% [4.334, 5.550] | 5/6,307 = 0.079% [0.016, 0.160] |

Intervals are 95% replay-cluster bootstrap intervals, 2,000 draws, seed 20261003. Each numerator counts Rockets with at least one qualifying pair; one Rocket can appear in both orders. The paired difference, Rocket-first minus Tornado-first, is **+4.709 percentage points [4.222, 5.231]** across all Rockets and **+4.494 [3.684, 5.272]** for non-tower candidates, resampling the same replay clusters for both orders.

Of the 494 Rocket-first candidates, **489** have an unambiguous aim-matched Rocket visible in every recorded frame at the exact Tornado tick (179 non-tower and 310 tower). This establishes concurrent flight, not a successful pull or Rocket hit. For Tornado-first, only two pairs have a sampled disappearance bracket wholly within 0–2.5 seconds after Tornado. Disappearance is not validated impact time, so this is **not** a count of confirmed landing synergy. The report's structural zero for “Rocket already in flight at an earlier Tornado” is inapplicable to Tornado-first, not evidence against later landing synergy.

Sensitivity at radius 0.11, for all Rockets:

| Maximum cast gap | Rocket → Tornado | Tornado → Rocket |
|---|---:|---:|
| 0.5 s | 18 | 2 |
| 1 s | 126 | 7 |
| 2.5 s | 494 | 21 |
| 5 s | 560 | 45 |

At 2.5 seconds, radii 0.055/0.11/0.165 produce 271/494/515 Rocket-first and 5/21/25 Tornado-first candidates. The radius uses anisotropic normalized board coordinates, not tiles. Full grids and unrestricted 5-second cast-gap distributions are retained in the JSON report; they do not silently redefine the historical prior.

## Non-tower troop context

The 3,738 non-tower candidates are outside the earlier 3.5-tile crown-target envelope. **Non-tower does not automatically mean defensive.** A Rocket can target troops near a crown tower, so these groups do not partition troop damage.

- Aim half: 2,283 own side and 1,455 enemy side.
- Phase: 1,161 single-elixir, 1,341 double-elixir, 1,236 overtime.
- Own elixir before cast: median 8.2539, 10th/90th percentiles 6.673/10.0. All-Rocket median 8.3415; tower-candidate median 8.39. These are descriptive mixed-corpus values, not a paired bot/pro comparison or a replacement for the earlier IceBow audit.
- 3,702 have an unambiguous observed flight context. At the last observed flight, 2,893 contain living enemy **troop** candidates within 2 tiles of aim, with 5,381 troop-body sightings. Other candidate bodies are 481 buildings and 47 spell-kind entities, explicitly excluded from this troop-only total.
- Most common troop-body sightings: Royal Hogs 635, Balloon 510, Hog Rider 305, Inferno Dragon 203, Minion Horde 181, Lava Hound 169, Witch 164, Baby Dragon 163. These are body sightings across Rocket contexts, not unique cards or confirmed hits.
- In 2,244 nonempty troop contexts with complete nominal costs, the median summed base-card cost per body is **5.0**. Base cost divided by base spawn count is only a nominal proxy. Summons, evolved forms, repeated bodies and partial health prevent interpreting it as elixir spent, destroyed or hit. **Actual elixir value hit remains null.**

The row-level data retains native IDs, entity IDs, positions through aim distance, HP, sampled compatible HP changes/disappearances, and exact timing evidence. Neither compatible HP loss nor disappearance is attributed causally to Rocket. Confirmed defensive-Rocket rate and troop hits remain unmeasured.

## Policy baselines and training implications

The same paired 299 ghost matches have **zero qualifying cast-prior events in either direction** for all five policies: gen_v1 (72 Rockets), live u0155 (50), gen_v3 (83), R1t update80 (52), R1t update155 (100). Accepted plays/min are respectively 10.322, 10.036, 10.327, 10.112 and 9.552; paired differences and intervals are in `rocket_tornado_baselines_2140.json`. Zero-event bootstrap [0,0] intervals are degenerate, not population upper confidence bounds. Saved policy logs lack flight/pull/hit telemetry, so these zeros do not complete either synergy acceptance metric. The pro mixed-deck corpus and policy ghost matches are not paired populations.

The version4 weighting preflight requires all six context targets: tower Rocket, X-Bow lane, defensive X-Bow/Rocket cycle, defensive Rocket, Rocket→Tornado, and Tornado→Rocket. **No classifier or weight knob has been fitted, and no scripted Rocket/X-Bow/Tornado rule was added.** Validated public timing/area sources and reviewed label semantics still gate the full dataset/retrain. Future acceptance explicitly retains 11 missing behaviour metrics; historical R1t numerical reports are unchanged and hash-bound to a current coverage supplement.

## Evidence and verification

- `native_rocket_tornado_2140/{manifest.json,rockets.jsonl,report.json}`: full census, source hashes and sensitivity grids.
- `compare_combo_orders.py`, `combo_order_comparison_2140.json`: paired order comparison and source hash.
- `.foreman/codex_autopilot/runs/combo_verification_2140.json`: source/event/count verification, troop-only breakdown, omitted-row negative control passed.
- `pipeline/tests/test_rocket_tornado_audit.py`: 8 passing orientation/timing/privacy/prior tests, included in the final 59-test pipeline suite.
- `rocket_tornado_baselines_2140.json` and `.foreman/codex_autopilot/runs/behaviour_coverage_2140.json`: paired policy proxies and current acceptance gaps.

Live checkpoint and reader are unchanged. No GPU job or paid capture was started for this audit.
