# Pro-corpus ability presses (phase 1)

Processed 52 files / 252,238 rows; 252,238 unique replay tags. 854,195 presses: 708,608 single-candidate, 85,494 multi-candidate resolved, 60,093 unresolved/dropped.

Distribution = percent of all inferred ability-card deployments with 0 / 1 / 2+ attributed presses. Phase = percent of attributed presses in [0,60) / [60,120) / [120,180) / [180,+inf) seconds; OT begins at 180s. Median delay uses linked presses, including repeat presses. Unknowns are retained in JSON.

| Ability | n presses | n battles | Deployments: 0 / 1 / 2+ (%) | Median delay (s) | Phase split (%) |
|---|---:|---:|---|---:|---|
| archer-queen | 27,326 | 7,736 | 20.4 / 79.5 / 0.1 | 10.7 | 16.1 / 19.2 / 34.0 / 30.7 |
| balloon-hero | 35,015 | 18,757 | 62.8 / 37.2 / 0.0 | 6.9 | 13.4 / 16.8 / 38.2 / 31.5 |
| barbarian-barrel-hero | 19,091 | 10,943 | 80.2 / 19.8 / 0.0 | 5.0 | 21.9 / 22.8 / 27.7 / 27.6 |
| berserker-hero | 182,619 | 75,361 | 71.4 / 28.6 / 0.0 | 5.0 | 14.7 / 18.1 / 34.4 / 32.8 |
| boss-bandit | 16,538 | 4,551 | 38.2 / 31.4 / 30.4 | 11.7 | 23.0 / 22.9 / 31.2 / 22.9 |
| bowler-hero | 26,387 | 13,819 | 67.4 / 32.5 / 0.1 | 12.4 | 21.1 / 23.9 / 29.9 / 25.1 |
| dark-prince-hero | 11,082 | 7,149 | 84.3 / 15.6 / 0.0 | 11.1 | 12.1 / 18.2 / 33.6 / 36.1 |
| giant-hero | 14,466 | 10,021 | 82.0 / 18.0 / 0.0 | 7.8 | 12.7 / 17.9 / 41.3 / 28.0 |
| goblins-hero | 9,458 | 4,564 | 73.5 / 26.5 / 0.0 | 9.6 | 18.3 / 23.6 / 29.8 / 28.4 |
| goblinstein | 38,475 | 16,727 | 62.2 / 37.8 / 0.0 | 7.5 | 11.3 / 14.7 / 34.5 / 39.4 |
| golden-knight | 96,047 | 28,124 | 28.6 / 71.3 / 0.1 | 4.8 | 14.8 / 18.2 / 35.7 / 31.3 |
| ice-golem-hero | 10,235 | 5,902 | 88.6 / 11.4 / 0.0 | 3.5 | 7.9 / 11.7 / 40.6 / 39.8 |
| knight-hero | 19,145 | 11,959 | 86.6 / 13.4 / 0.0 | 6.8 | 10.2 / 16.2 / 37.6 / 36.0 |
| little-prince | 4,976 | 2,834 | 77.7 / 22.2 / 0.1 | 8.4 | 17.9 / 21.4 / 32.7 / 28.1 |
| magic-archer-hero | 5,890 | 3,859 | 84.5 / 15.5 / 0.0 | 7.5 | 15.6 / 16.3 / 38.0 / 30.1 |
| mega-minion-hero | 17,905 | 11,624 | 80.2 / 19.8 / 0.0 | 8.0 | 19.3 / 20.1 / 39.1 / 21.5 |
| mighty-miner | 50,829 | 18,201 | 59.5 / 40.5 / 0.0 | 8.9 | 18.4 / 21.0 / 32.6 / 28.0 |
| mini-pekka-hero | 23,761 | 15,380 | 72.2 / 27.7 / 0.1 | 10.9 | 21.0 / 29.3 / 33.2 / 16.5 |
| monk | 19,726 | 7,087 | 40.8 / 59.1 / 0.1 | 6.8 | 13.6 / 16.8 / 36.8 / 32.8 |
| musketeer-hero | 14,965 | 8,522 | 83.3 / 16.7 / 0.0 | 12.2 | 15.9 / 22.8 / 31.0 / 30.4 |
| skeleton-king | 34,078 | 14,092 | 48.7 / 51.3 / 0.0 | 10.3 | 16.6 / 20.3 / 39.1 / 23.9 |
| tombstone-hero | 14,246 | 8,208 | 79.9 / 20.1 / 0.0 | 10.6 | 13.2 / 15.4 / 37.4 / 34.0 |
| valkyrie-hero | 50,845 | 23,679 | 67.0 / 32.9 / 0.0 | 5.8 | 12.2 / 15.2 / 37.4 / 35.3 |
| wizard-hero | 50,997 | 23,783 | 48.7 / 51.3 / 0.1 | 4.8 | 12.9 / 17.0 / 37.7 / 32.4 |

Percentages are rounded to one decimal; 0.0% can represent a rare nonzero count. Exact counts are in JSON.

## Attribution and denominators

Single candidates are attributed exactly as requested, even outside the heuristic lifetime window. Multiple candidates resolve only when exactly one has a preceding deployment by that side within its window; ties remain ambiguous (no arbitrary newest-card winner). Windows use each card's single-candidate deployment-to-press p95, bounded to 10-90s; fewer than 30 samples use the pooled p95. These are activity-window proxies, not measured unit lifetimes. The most recent same-card deployment ends the previous inferred instance; death/despawn is not observed.

Event base keys are joined to a unique deck-card slot, preserving -hero/-ev1 forms. Unknown form_at_play does not establish which hero/evolution form spawned on that cycle. The denominator therefore means deployments from the hero/champion deck slot, not engine-verified ability-eligible spawns. No one-press restriction is imposed. Unresolved presses do not enter usage metrics; zero-press shares are upper bounds under attribution loss and repeat grouping is inferred. Single candidates without a deployment remain in press counts but not delay/repeat metrics.

| Ability | Single | Multi resolved | Unresolved candidate mentions | Plausible unresolved | Window (s) | Deployments | Unlinked presses |
|---|---:|---:|---:|---:|---:|---:|---:|
| archer-queen | 24,686 | 2,640 | 2,364 | 2,153 | 22.85 | 34,283 | 0 |
| balloon-hero | 31,673 | 3,342 | 3,132 | 2,767 | 14.50 | 93,916 | 0 |
| barbarian-barrel-hero | 17,742 | 1,349 | 1,895 | 1,660 | 12.90 | 96,529 | 0 |
| berserker-hero | 168,066 | 14,553 | 21,255 | 19,249 | 14.45 | 637,616 | 0 |
| boss-bandit | 15,281 | 1,257 | 740 | 645 | 20.95 | 17,943 | 0 |
| bowler-hero | 18,741 | 7,646 | 8,098 | 7,337 | 23.50 | 80,798 | 0 |
| dark-prince-hero | 9,573 | 1,509 | 2,611 | 2,423 | 20.22 | 70,767 | 0 |
| giant-hero | 11,388 | 3,078 | 7,966 | 7,575 | 23.18 | 80,285 | 0 |
| goblins-hero | 8,854 | 604 | 1,206 | 1,112 | 16.85 | 35,626 | 0 |
| goblinstein | 35,737 | 2,738 | 3,089 | 2,817 | 19.46 | 101,776 | 0 |
| golden-knight | 87,729 | 8,318 | 7,966 | 7,213 | 18.80 | 134,435 | 0 |
| ice-golem-hero | 9,695 | 540 | 2,454 | 2,279 | 11.95 | 89,959 | 0 |
| knight-hero | 18,436 | 709 | 1,727 | 1,589 | 19.50 | 142,597 | 0 |
| little-prince | 2,693 | 2,283 | 3,871 | 3,519 | 23.14 | 22,262 | 0 |
| magic-archer-hero | 5,075 | 815 | 2,056 | 1,950 | 24.20 | 37,933 | 0 |
| mega-minion-hero | 14,118 | 3,787 | 6,796 | 6,336 | 20.75 | 90,390 | 0 |
| mighty-miner | 50,138 | 691 | 755 | 673 | 20.55 | 125,387 | 0 |
| mini-pekka-hero | 20,341 | 3,420 | 5,896 | 5,637 | 19.85 | 85,333 | 0 |
| monk | 17,000 | 2,726 | 2,922 | 2,646 | 20.80 | 33,278 | 0 |
| musketeer-hero | 13,617 | 1,348 | 2,556 | 2,430 | 26.60 | 89,712 | 0 |
| skeleton-king | 33,491 | 587 | 718 | 642 | 22.00 | 66,354 | 0 |
| tombstone-hero | 10,154 | 4,092 | 9,439 | 8,731 | 29.35 | 70,698 | 0 |
| valkyrie-hero | 38,334 | 12,511 | 14,384 | 13,200 | 17.65 | 154,076 | 0 |
| wizard-hero | 46,046 | 4,951 | 6,290 | 5,815 | 19.60 | 99,217 | 0 |

Unresolved candidate mentions overlap across cards and must not be summed as unique presses.

Sensitivity (multi-candidate only):

- 0.75x windows: 93,136 resolved; 30,200 assignments differ from primary (including resolved/unresolved changes).
- 1.0x windows: 85,494 resolved; 0 assignments differ from primary (including resolved/unresolved changes).
- 1.25x windows: 73,176 resolved; 19,138 assignments differ from primary (including resolved/unresolved changes).

## When each ability is pressed

- **archer-queen:** Median press is 10.7s after deployment; 34.0% fall in 120-180. 16.0% precede a friendly card within 1s; 0.1% of deployments have repeat presses.
- **balloon-hero:** Median press is 6.9s after deployment; 38.2% fall in 120-180. 4.3% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **barbarian-barrel-hero:** Median press is 5.0s after deployment; 27.7% fall in 120-180. 6.8% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **berserker-hero:** Median press is 5.0s after deployment; 34.4% fall in 120-180. 7.9% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **boss-bandit:** Median press is 11.7s after deployment; 31.2% fall in 120-180. 8.0% precede a friendly card within 1s; 30.4% of deployments have repeat presses.
- **bowler-hero:** Median press is 12.4s after deployment; 29.9% fall in 120-180. 2.3% precede a friendly card within 1s; 0.1% of deployments have repeat presses.
- **dark-prince-hero:** Median press is 11.1s after deployment; 36.1% fall in OT. 3.3% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **giant-hero:** Median press is 7.8s after deployment; 41.3% fall in 120-180. 4.6% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **goblins-hero:** Median press is 9.6s after deployment; 29.8% fall in 120-180. 8.4% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **goblinstein:** Median press is 7.5s after deployment; 39.4% fall in OT. 5.4% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **golden-knight:** Median press is 4.8s after deployment; 35.7% fall in 120-180. 5.6% precede a friendly card within 1s; 0.1% of deployments have repeat presses.
- **ice-golem-hero:** Median press is 3.5s after deployment; 40.6% fall in 120-180. 10.9% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **knight-hero:** Median press is 6.8s after deployment; 37.6% fall in 120-180. 4.2% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **little-prince:** Median press is 8.4s after deployment; 32.7% fall in 120-180. 7.9% precede a friendly card within 1s; 0.1% of deployments have repeat presses.
- **magic-archer-hero:** Median press is 7.5s after deployment; 38.0% fall in 120-180. 6.9% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **mega-minion-hero:** Median press is 8.0s after deployment; 39.1% fall in 120-180. 7.6% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **mighty-miner:** Median press is 8.9s after deployment; 32.6% fall in 120-180. 18.4% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **mini-pekka-hero:** Median press is 10.9s after deployment; 33.2% fall in 120-180. 4.9% precede a friendly card within 1s; 0.1% of deployments have repeat presses.
- **monk:** Median press is 6.8s after deployment; 36.8% fall in 120-180. 6.7% precede a friendly card within 1s; 0.1% of deployments have repeat presses.
- **musketeer-hero:** Median press is 12.2s after deployment; 31.0% fall in 120-180. 13.2% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **skeleton-king:** Median press is 10.3s after deployment; 39.1% fall in 120-180. 3.6% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **tombstone-hero:** Median press is 10.6s after deployment; 37.4% fall in 120-180. 2.1% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **valkyrie-hero:** Median press is 5.8s after deployment; 37.4% fall in 120-180. 5.0% precede a friendly card within 1s; 0.0% of deployments have repeat presses.
- **wizard-hero:** Median press is 4.8s after deployment; 37.7% fall in 120-180. 6.8% precede a friendly card within 1s; 0.1% of deployments have repeat presses.

## Timing, combos and repeat presses

| Ability | Delay p10 / p50 / p90 (s) | First-press median (s) | Combo within 1s | Repeat gaps n; p10 / p50 / p90 (s) |
|---|---|---:|---:|---|
| archer-queen | 2.2 / 10.7 / 20.1 | 10.7 | 16.0% | 35; 2.7 / 6.0 / 14.0 |
| balloon-hero | 3.9 / 6.9 / 12.0 | 6.9 | 4.3% | 35; 1.4 / 4.1 / 13.8 |
| barbarian-barrel-hero | 2.8 / 5.0 / 10.4 | 5.0 | 6.8% | 8; 0.1 / 2.8 / 5.2 |
| berserker-hero | 1.6 / 5.0 / 12.4 | 5.0 | 7.9% | 88; 0.6 / 2.7 / 7.7 |
| boss-bandit | 5.3 / 11.7 / 18.7 | 9.8 | 8.0% | 5,455; 4.3 / 5.7 / 10.4 |
| bowler-hero | 3.7 / 12.4 / 19.7 | 12.4 | 2.3% | 44; 1.0 / 5.1 / 20.6 |
| dark-prince-hero | 5.5 / 11.1 / 17.9 | 11.1 | 3.3% | 5; 3.3 / 5.0 / 6.3 |
| giant-hero | 2.4 / 7.8 / 19.7 | 7.8 | 4.6% | 27; 1.2 / 4.3 / 10.6 |
| goblins-hero | 5.0 / 9.6 / 15.1 | 9.6 | 8.4% | 5; 1.0 / 5.7 / 8.8 |
| goblinstein | 2.1 / 7.5 / 16.9 | 7.5 | 5.4% | 15; 2.3 / 4.8 / 11.3 |
| golden-knight | 1.4 / 4.8 / 15.6 | 4.8 | 5.6% | 88; 0.9 / 5.6 / 22.2 |
| ice-golem-hero | 1.5 / 3.5 / 8.4 | 3.5 | 10.9% | 1; 4.4 / 4.4 / 4.4 |
| knight-hero | 1.9 / 6.8 / 16.4 | 6.8 | 4.2% | 8; 0.6 / 2.6 / 8.4 |
| little-prince | 1.7 / 8.4 / 19.2 | 8.3 | 7.9% | 14; 2.6 / 4.5 / 18.0 |
| magic-archer-hero | 3.5 / 7.5 / 20.1 | 7.5 | 6.9% | 1; 6.6 / 6.6 / 6.6 |
| mega-minion-hero | 3.2 / 8.0 / 17.2 | 8.0 | 7.6% | 23; 1.0 / 4.7 / 10.2 |
| mighty-miner | 2.2 / 8.9 / 18.1 | 8.9 | 18.4% | 5; 1.0 / 3.5 / 11.3 |
| mini-pekka-hero | 6.5 / 10.9 / 17.5 | 10.9 | 4.9% | 48; 1.2 / 4.0 / 9.4 |
| monk | 2.0 / 6.8 / 18.1 | 6.8 | 6.7% | 23; 0.7 / 2.9 / 17.5 |
| musketeer-hero | 1.9 / 12.2 / 23.2 | 12.2 | 13.2% | 8; 2.1 / 4.7 / 14.0 |
| skeleton-king | 4.5 / 10.3 / 19.6 | 10.3 | 3.6% | 7; 2.4 / 4.5 / 9.1 |
| tombstone-hero | 3.4 / 10.6 / 24.6 | 10.6 | 2.1% | 29; 1.1 / 7.0 / 22.5 |
| valkyrie-hero | 1.8 / 5.8 / 14.6 | 5.7 | 5.0% | 75; 1.1 / 4.0 / 10.8 |
| wizard-hero | 1.6 / 4.8 / 16.7 | 4.8 | 6.8% | 54; 1.1 / 4.0 / 12.6 |

Combo is the next chronological card play by the same side, within an inclusive 1s after the press; same-tick later events count, and their count is separate in JSON. It measures proximity, not tactical intent. Repeat gaps use consecutive presses linked to the same deployment, never across redeployments.

## Coordinates and crown context

Press coordinates: 0 non-null / 0 valid native coordinates across 854,195 presses. Deployment coordinates and deployment-to-press delay by location are summarized below and fully in JSON. A deployment location is not the unit position at the press. Lane is left/right relative to the blue/native frame (x<9000/x>9000; center at x=9000); own half is y<16000 for team and y>16000 for opponent.

| Ability | Linked presses with deployment coordinates | Own-half deployment share | Left / center / right | Median delay by deployment lane/half (s) | Crowns tied known / unknown |
|---|---:|---:|---|---|---|
| archer-queen | 27,326 | 97.4% | 13621 / 0 / 13705 | left/enemy: 2.9; left/own: 11.0; right/enemy: 3.0; right/own: 10.9 | 6 / 27,320 |
| balloon-hero | 35,015 | 93.9% | 17295 / 0 / 17720 | left/enemy: 5.7; left/own: 7.0; right/enemy: 5.6; right/own: 7.0 | 4 / 35,011 |
| barbarian-barrel-hero | 19,091 | 97.2% | 9533 / 0 / 9558 | left/enemy: 3.5; left/own: 5.0; right/enemy: 3.7; right/own: 5.0 | 3 / 19,088 |
| berserker-hero | 182,619 | 97.2% | 90907 / 0 / 91712 | left/enemy: 4.3; left/own: 5.0; right/enemy: 4.2; right/own: 5.0 | 32 / 182,587 |
| boss-bandit | 16,538 | 98.4% | 8079 / 0 / 8459 | left/enemy: 5.5; left/own: 11.7; right/enemy: 6.7; right/own: 11.7 | 0 / 16,538 |
| bowler-hero | 26,387 | 99.8% | 13178 / 0 / 13209 | left/enemy: 6.0; left/own: 12.4; right/enemy: 3.6; right/own: 12.3 | 0 / 26,387 |
| dark-prince-hero | 11,082 | 96.6% | 5564 / 0 / 5518 | left/enemy: 7.0; left/own: 11.3; right/enemy: 6.6; right/own: 11.2 | 2 / 11,080 |
| giant-hero | 14,466 | 89.2% | 7186 / 0 / 7280 | left/enemy: 5.7; left/own: 8.3; right/enemy: 5.5; right/own: 8.2 | 0 / 14,466 |
| goblins-hero | 9,458 | 98.5% | 4723 / 0 / 4735 | left/enemy: 8.5; left/own: 9.7; right/enemy: 9.3; right/own: 9.5 | 0 / 9,458 |
| goblinstein | 38,475 | 98.4% | 18978 / 0 / 19497 | left/enemy: 5.0; left/own: 7.5; right/enemy: 5.0; right/own: 7.5 | 0 / 38,475 |
| golden-knight | 96,047 | 95.0% | 47933 / 0 / 48114 | left/enemy: 1.6; left/own: 5.1; right/enemy: 1.6; right/own: 5.1 | 12 / 96,035 |
| ice-golem-hero | 10,235 | 97.7% | 5111 / 0 / 5124 | left/enemy: 3.8; left/own: 3.5; right/enemy: 3.8; right/own: 3.5 | 0 / 10,235 |
| knight-hero | 19,145 | 94.1% | 9440 / 0 / 9705 | left/enemy: 3.5; left/own: 7.0; right/enemy: 3.4; right/own: 7.2 | 2 / 19,143 |
| little-prince | 4,976 | 99.1% | 2447 / 0 / 2529 | left/enemy: 4.2; left/own: 8.4; right/enemy: 5.1; right/own: 8.4 | 0 / 4,976 |
| magic-archer-hero | 5,890 | 99.4% | 2959 / 0 / 2931 | left/enemy: 5.0; left/own: 7.7; right/enemy: 4.2; right/own: 7.5 | 2 / 5,888 |
| mega-minion-hero | 17,905 | 97.6% | 8966 / 0 / 8939 | left/enemy: 5.3; left/own: 8.1; right/enemy: 5.5; right/own: 8.2 | 0 / 17,905 |
| mighty-miner | 50,829 | 95.9% | 25356 / 0 / 25473 | left/enemy: 4.8; left/own: 9.4; right/enemy: 4.6; right/own: 9.2 | 0 / 50,829 |
| mini-pekka-hero | 23,761 | 92.9% | 11890 / 0 / 11871 | left/enemy: 8.7; left/own: 11.1; right/enemy: 8.6; right/own: 11.2 | 3 / 23,758 |
| monk | 19,726 | 97.5% | 9848 / 0 / 9878 | left/enemy: 3.2; left/own: 7.0; right/enemy: 3.1; right/own: 7.0 | 6 / 19,720 |
| musketeer-hero | 14,965 | 98.6% | 7252 / 0 / 7713 | left/enemy: 4.0; left/own: 12.3; right/enemy: 4.2; right/own: 12.4 | 0 / 14,965 |
| skeleton-king | 34,078 | 93.1% | 17089 / 0 / 16989 | left/enemy: 5.7; left/own: 10.9; right/enemy: 5.5; right/own: 10.9 | 7 / 34,071 |
| tombstone-hero | 14,246 | 98.7% | 7000 / 0 / 7246 | left/enemy: 3.0; left/own: 10.6; right/enemy: 2.7; right/own: 10.8 | 0 / 14,246 |
| valkyrie-hero | 50,845 | 96.0% | 25100 / 0 / 25745 | left/enemy: 3.4; left/own: 6.0; right/enemy: 3.5; right/own: 6.0 | 1 / 50,844 |
| wizard-hero | 50,997 | 98.9% | 25417 / 0 / 25580 | left/enemy: 2.5; left/own: 4.8; right/enemy: 2.6; right/own: 4.8 | 5 / 50,992 |

Final crown totals do not reveal when towers fell. Only final 0-0 proves tied at every press (crowns are monotonic); all other presses have unknown crown lead. No final-score backfill is used.

## Missing context and phase-2 replay path

The observed action events provide no living unit/entity roster, enemy proximity or targeting, unit HP/shield, current unit position, death/despawn time, damage, projectile state, exact elixir at the press, ability cooldown/charges/readiness, ability acceptance/effect, or timed tower damage/destruction. Final tower HP, final crowns, deck average elixir and total leaked elixir are end-of-battle aggregates, not per-press state. Hand/cycle and elixir can only be modeled under assumptions; they are not observed here. Phase 2 needs preserved ability commands, source/entity attribution, and state captured immediately before each press. Simulation will reconstruct context subject to simulator parity; it will not make missing historical state authoritative.

- `research/sandbox_tools/replay_drive.py:402`: drive() logs and skips ability presses; no ability action is sent.
- `pipeline/e1_pool.py:271`: Pool construction preserves skipped presses as ability commands with no card/entity identity.
- `pipeline/e1_pool.py:536`: The parity merge drops ability commands before execution.
- `scratchpad/gauntlet/L62/engine_env.py:215`: The base ghost loader drops ability commands before building its execution schedule (lines 325-327).

## Repeat attribution evidence

Rare repeat groups can be created by mistaken multi-source attribution. The counts below separate groups where every press had a single candidate from groups requiring at least one heuristic assignment. Even the former lack an authoritative unit ID.

| Ability | Repeat deployments: all single-candidate | Repeat deployments: includes heuristic |
|---|---:|---:|
| archer-queen | 1 | 34 |
| balloon-hero | 5 | 30 |
| barbarian-barrel-hero | 0 | 8 |
| berserker-hero | 6 | 82 |
| boss-bandit | 5,115 | 331 |
| bowler-hero | 7 | 37 |
| dark-prince-hero | 0 | 5 |
| giant-hero | 0 | 27 |
| goblins-hero | 0 | 5 |
| goblinstein | 0 | 15 |
| golden-knight | 28 | 60 |
| ice-golem-hero | 1 | 0 |
| knight-hero | 1 | 7 |
| little-prince | 0 | 14 |
| magic-archer-hero | 0 | 1 |
| mega-minion-hero | 1 | 22 |
| mighty-miner | 0 | 5 |
| mini-pekka-hero | 1 | 47 |
| monk | 7 | 16 |
| musketeer-hero | 1 | 7 |
| skeleton-king | 0 | 7 |
| tombstone-hero | 0 | 29 |
| valkyrie-hero | 8 | 67 |
| wizard-hero | 7 | 47 |

## Concerns and reproducibility

- Candidate sources are inferred, not authoritative; multi-source resolution depends on empirical activity windows. See sensitivity.
- No measured death/entity identity or form-at-play; deployment linkage and repeat counts are estimates. Windows are not biological lifetimes.
- Anonymized corpus membership does not independently prove every participant is a professional. Both sides and all battle types are included without filtering.
- Unresolved presses are dropped from usage statistics, not silently assigned; per-card ambiguous mentions overlap.
- Raw replay tags deduplicate identical payloads; conflicting same-tag payloads use the first occurrence and are counted explicitly.
- Phase shares are counts of observed presses, not exposure-adjusted press rates; OT duration and ability deck popularity affect them.
- Observed repetitions are reported for every card, without enforcing the proposed once-only expectation.
- Inputs are read only; file size/mtime are checked after mining, not cryptographic proof of immutable source bytes.
- Golden Knight repeats on 88/134,435 deployments (0.0655%), versus Boss Bandit 30.3517%. The expected frequent Golden Knight repetition is not supported by these inferred deployment groups; this is not a claim about its game mechanics.
- 35,126 single-candidate presses exceed their card's window and are retained as instructed; all attributed presses have a preceding matching deployment.

Run `python -B scratchpad/gauntlet/L70/abilities/mine_abilities.py`; verify with the same command plus `--verify`. Only this directory is written. `abilities.json` contains all counts, denominators, quantiles, coordinate breakdowns, calibration and input metadata. `presses.jsonl.gz` preserves one auditable record per unique-replay ability event, including dropped ambiguities. No engine or project module is imported.
