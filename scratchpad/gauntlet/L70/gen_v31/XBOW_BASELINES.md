# Paired ghost X-Bow geometry, October 3 20:35 EDT

MEASURED from the same 299 saved ghost matches per checkpoint. Source hashes and
2,000 paired bootstrap resamples are in `xbow_baselines_2020.json`. These are not
reactive or live ladder measurements, and the pro census has a different cohort.

| Checkpoint | Accepted X-Bows | X-Bow share of accepted plays | Accepted plays/min | Normalized y rows (count) |
|---|---:|---:|---:|---|
| gen_v1 | 854 | 9.022% | 10.322 | .609375 (833), .703125 (21) |
| live u0155 | 1,040 | 11.554% | 10.036 | .578125 (4), .609375 (1,001), .703125 (35) |
| gen_v3 | 778 | 8.366% | 10.327 | .578125 (1), .609375 (760), .703125 (17) |

Paired X-Bow share differences versus live: gen_v1 -2.533 percentage points,
95% CI [-3.022,-2.062]; gen_v3 -3.188 pp [-3.657,-2.774]. This establishes a
frequency difference on this instrument, not an improvement in tower/lane choice.

Forward means decreasing normalized y. All late-game X-Bows (elapsed >=120s;
401/450/333 for gen_v1/u0155/gen_v3) lie in the inherited `y>0.58` bucket. That
bucket is geometrical; it does not validate whether an X-Bow was strategically
defensive or intended to connect from the bridge. Exact rows remain primary.

X-Bow followed by any accepted Rocket within 10 seconds: 5/854 (0.585%), 5/1040
(0.481%), 3/778 (0.386%). Gen_v3 versus live: -0.095 pp [-0.712,+0.508]. These
sequences do not establish tower targeting. Timing uses accepted `land_tick`.

UNMEASURED: dead-lane share after a princess falls, validated late defensive share,
and X-Bow-to-tower-Rocket cycling. Saved logs lack tower context/validated intent.
The five earlier missing Rocket/Barrel/tiebreak metrics also remain unmeasured.
No classifier, loss-weight choice, deployment, or acceptance threshold was selected.
