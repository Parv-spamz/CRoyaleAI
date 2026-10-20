# Ability press policy v2: timing term + calibration

`ability_models_v2.json` (v1 untouched; `predict(ab, x, version='v2')`). Fit script `calibration_v2.py`. Labels = native_targets_2326 first presses joined to the phase-2 frame sequences by tag/side/play_index; 80% of replays fit, 20% held out by replay (the phase-2 split).
Model: v1 standardized features + piecewise-linear timing term in seconds-since-deploy (13 knots, 1-40 s) + intercept, discrete-time survival MLE; then the knot values are moved by fixed point until the model's first-press mass per age bin equals the pro mass on the fit replays, so share and first-delay distribution match together. The two GBT abilities keep their v1 trees (one scale + timing + intercept). Boss Bandit's second charge adds `second_charge_offset`: held-out repeat share model 29.5% vs pro 38.2% (n=89). Shares and delays are analytic over the recorded frames (no RNG).

Held-out (20% of replays), shares in %. "pro all / reach": native linked share / share whose press falls inside the recorded frames (1-4% of presses come after the phase-2 recording ends and no frame policy can reproduce them; they are censored in the fit and the error is against "reach"). Delay errors are model minus pro in seconds (se = replay-cluster bootstrap SE of the pro median); IQR error = model IQR width minus pro. 5-fold RMS = RMS of the share error over 5 replay folds (pp).

| Ability | n | pro all / reach | v1 | v2 | err pp | median err s | IQR err s | AUC v1 -> v2 | 5-fold RMS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| archer-queen | 312 | 80.8 / 78.8 | 86.5 | 80.1 | +1.2 | -0.45 (se 0.87; v1 -3.65) | -0.8 | 0.840 -> 0.794 | 2.2 |
| balloon-hero | 939 | 38.3 / 38.1 | 56.6 | 34.6 | -3.5 | +0.00 (se 0.25; v1 -1.10) | +0.0 | 0.718 -> 0.740 | 2.0 |
| barbarian-barrel-hero | 837 | 21.6 / 21.0 | 34.3 | 20.9 | -0.1 | +0.10 (se 0.21; v1 -0.35) | -0.1 | 0.810 -> 0.782 | 2.1 |
| berserker-hero | 5776 | 25.7 / 25.1 | 37.9 | 25.1 | -0.0 | +0.00 (se 0.18; v1 -0.45) | +0.2 | 0.826 -> 0.818 | 0.9 |
| boss-bandit | 89 | 76.4 / 76.4 | 77.5 | 63.6 | -12.8 | +0.85 (se 1.00; v1 -0.85) | -1.4 | 0.819 -> 0.819 | 3.7 |
| bowler-hero | 710 | 35.4 / 34.8 | 51.6 | 35.7 | +0.9 | -0.40 (se 0.45; v1 -1.40) | -0.8 | 0.825 -> 0.832 | 1.5 |
| dark-prince-hero | 426 | 16.9 / 16.2 | 28.2 | 15.9 | -0.3 | -0.95 (se 1.30; v1 -1.50) | -0.1 | 0.839 -> 0.850 | 1.6 |
| giant-hero | 800 | 18.8 / 18.6 | 28.2 | 17.4 | -1.2 | +0.05 (se 0.74; v1 -0.20) | +0.8 | 0.815 -> 0.811 | 1.4 |
| goblins-hero (fallback) | 498 | 24.9 / 24.9 | 39.0 | 25.6 | +0.7 | +0.20 (se 0.30; v1 -0.05) | +0.2 | 0.661 -> 0.639 | n/a |
| goblinstein | 1038 | 33.1 / 32.5 | 50.2 | 32.4 | -0.1 | +0.70 (se 0.44; v1 +0.30) | -0.0 | 0.774 -> 0.772 | 1.1 |
| golden-knight | 901 | 70.9 / 70.0 | 86.4 | 71.0 | +1.0 | +0.00 (se 0.38; v1 -1.90) | +0.1 | 0.714 -> 0.705 | 0.7 |
| ice-golem-hero | 719 | 10.4 / 10.4 | 15.8 | 9.9 | -0.5 | +0.35 (se 0.28; v1 +0.15) | -0.2 | 0.840 -> 0.832 | 1.6 |
| knight-hero | 2324 | 12.7 / 12.4 | 20.5 | 12.1 | -0.3 | +0.70 (se 0.52; v1 +0.55) | -0.4 | 0.700 -> 0.707 | 1.1 |
| little-prince | 143 | 18.9 / 18.9 | 31.4 | 14.6 | -4.3 | -1.80 (se 1.57; v1 -6.70) | +0.4 | 0.694 -> 0.770 | 4.1 |
| magic-archer-hero | 234 | 10.7 / 10.7 | 20.1 | 9.2 | -1.5 | -1.95 (se 1.80; v1 -2.25) | -3.7 | 0.804 -> 0.811 | 1.9 |
| mega-minion-hero | 667 | 15.4 / 15.3 | 30.9 | 17.6 | +2.3 | +0.35 (se 0.78; v1 +0.20) | +0.0 | 0.650 -> 0.693 | 1.5 |
| mighty-miner | 2495 | 35.9 / 34.9 | 50.9 | 35.4 | +0.5 | +0.10 (se 0.45; v1 -1.00) | +0.0 | 0.741 -> 0.736 | 0.9 |
| mini-pekka-hero | 696 | 30.5 / 29.3 | 42.2 | 26.5 | -2.9 | -0.50 (se 0.35; v1 -1.35) | -0.2 | 0.818 -> 0.825 | 1.4 |
| monk | 108 | 74.1 / 74.1 | 82.3 | 65.8 | -8.3 | -0.65 (se 0.78; v1 -1.75) | -1.3 | 0.763 -> 0.771 | 1.6 |
| musketeer-hero | 531 | 16.4 / 16.0 | 29.6 | 15.0 | -1.0 | -1.35 (se 0.97; v1 -3.95) | +0.1 | 0.863 -> 0.878 | 2.0 |
| skeleton-king | 687 | 47.5 / 46.1 | 68.3 | 49.3 | +3.2 | -0.20 (se 0.40; v1 -1.90) | +0.3 | 0.776 -> 0.802 | 1.2 |
| tombstone-hero (fallback) | 363 | 10.2 / 10.2 | 17.3 | 19.9 | +9.7 | +1.40 (se 2.28; v1 +2.40) | +0.9 | 0.799 -> 0.802 | n/a |
| valkyrie-hero | 1357 | 36.8 / 36.4 | 58.3 | 37.0 | +0.6 | -0.15 (se 0.42; v1 -0.80) | -0.4 | 0.809 -> 0.807 | 1.1 |
| wizard-hero | 418 | 47.1 / 46.7 | 65.9 | 47.2 | +0.5 | +0.70 (se 0.52; v1 +0.50) | +1.3 | 0.774 -> 0.771 | 2.5 |

Fallback (hero Goblins 388/2,842 linked, hero Tombstone 36/2,641): shape from phase-2 context presses, level set to the phase-1 share (26.5% / 20.1%, abilities.md); their "pro" column is the phase-2 context share, not their target, so Tombstone's +9.7 pp is the phase-1 vs phase-2 disagreement (20.1% vs 10.2%), not a fit error.

Findings
- v1 over-presses the held-out frames by 1 to 22 pp; v2 fit-set share error is at most 1.6 pp and fit-set median delay error at most 0.25 s (reliable abilities). Fit-set share not matched to within 0.5 pp: {'archer-queen': -1.6} (archer-queen's late presses fall where few recorded frames survive, so the late age bins cannot be filled).
- Held-out share error is within 3 pp for 17 of 22 reliable abilities. Above 3 pp: {'balloon-hero': -3.5, 'boss-bandit': -12.8, 'little-prince': -4.3, 'monk': -8.3, 'skeleton-king': 3.2}. Their error in held-out share standard errors (replay-cluster bootstrap) is {'balloon-hero': 1.9, 'boss-bandit': 2.5, 'little-prince': 1.0, 'monk': 1.4, 'skeleton-king': 1.4}: small samples, listed rather than hidden.
- Held-out median delay is within max(1 SE, 0.25 s) for 14 of 22.
- AUC (native 1 s press label) fell by more than 0.01 for {'archer-queen': -0.046, 'barbarian-barrel-hero': -0.029, 'goblins-hero': -0.021}: matching the delay marginal costs some ranking inside the unit's life.
- Native acceptances are re-drive timing, not human timing; board frames omit ability effects (NATIVE_TARGETS_REPORT.md).
