# Native pro X-Bow census, October 3 20:45 EDT

MEASURED: 11,852 accepted X-Bows in 14,661 unique source-verified native/full
replays, covering 1,012,450 accepted plays. The original 14,818-file corpus has
duplicate replay tags; first-corpus selection exactly matches the earlier Rocket
audit. All X-Bow contexts were recorded at the accepted cast tick. Every selected
replay hash matches the verified VM manifest. Independent verification rejects an
omitted replay and an incorrect count (`runs/xbow_verification_2020.json`).

The full rows, source manifest, context distributions and replay-clustered 95% CIs
are in `native_xbows_2020/`. This is a descriptive native re-drive census, not a
paired policy comparison or original-human tactical-intent ground truth.

There are 12 normalized y rows. Most frequent: .609375 (8,067), .703125 (1,514),
.671875 (934), .578125 (812), .734375 (312). Forward is decreasing y for BOTH
sides. Exact rows and signed distance from the river are primary. The inherited
`y>0.58` bucket contains 10,961/11,852 (92.48% [91.94,92.98]); it is a geometric
bucket, not a validated defensive-versus-bridge label. Strategic defensive share
remains null. Phase counts: single 3,858, double 3,941, overtime 4,053. Median own
elixir before X-Bow is 8.642. No opponent private field is used.

| Public crown state, ours:enemy | X-Bows | Dead-lane placements when an enemy princess is down | 95% CI |
|---|---:|---:|---:|
| 1:0 | 244 | 136/244 = 55.74% | [49.03,62.24] |
| 0:1 | 216 | undefined: no enemy princess down | undefined |
| 1:1 | 47 | 11/47 = 23.40% | [7.55,42.00] |
| All eligible crown states | 297 | 152/297 = 51.18% | [44.86,57.69] |

These are location counts, not a mistake label. In particular, a dead-lane share
alone cannot determine whether an X-Bow placement was strategically wrong.
They must not become a scripted lane rule or an automatic penalty. The earlier
live audit's 10/18 comes from a different, small cohort; no paired pro/live effect
is claimed here. Full joint context weighting remains unfitted.

383/11,852 X-Bows are followed within 10 seconds by a same-side geometric
tower-Rocket candidate: 3.23% [2.91,3.55]. In double elixir/overtime it is
379/7,994 = 4.74% [4.25,5.24]; overtime alone 269/4,053 = 6.64% [5.85,7.46].
The y>0.58 subset has 353/10,961 such sequences overall and 350/7,390 late.
Candidates retain the earlier 3.5-tile envelope, not verified damage attribution.
One Rocket may follow several X-Bows; the denominator is X-Bow placements.

This completes the requested public placement/context census and candidate
sequence distributions. It does not complete validated tactical labels, confirmed
Rocket hits, classifier fitting, loss-weight selection, gen_v3.1 training or the
required model behaviour acceptance. Future outcome fields are offline labels,
never model inputs. No live or active R1t path changed.
