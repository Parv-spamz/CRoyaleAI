# Higher WAIT agreement masked lower PLAY agreement

October5 20:10 EDT. The new cached decomposition independently reconciles all
54723 development rows/405 replay groups/three caches/19 groups and955 Rocket
details. Producer130.45s,independent11.41s,review0.55s exit0/token. Controls include
all eight PLAY bit states, both WAIT states, no affordable card,2positive/8negative.
No new inference, optimizer updates, native matches, labels or confirmation use.

ordinary_v5 -> outcome_rl_v5:

| Original cohort | Correct PLAY | Correct WAIT | Total full-action change |
|---|---:|---:|---:|
| All rows |2602 ->2465|29360 ->30219|+722|
| Defense |369 ->364|3642 ->3728|+81|
| Witch |41 ->40|298 ->302|+3|
| Night Witch |29 ->27|132 ->139|+5|
| Furnace |91 ->84|458 ->472|+7|
| Late clock |489 ->477|1495 ->1572|+65|

All six aggregates improve only because correct WAIT increases more than correct
PLAY falls. WAIT is a legitimate expert decision, so this does not prove harmful
passivity in gameplay. It does show that the earlier aggregate defense/spawner
gains are not evidence of better execution of expert defensive plays. All-row
improvement is +859 WAIT minus137 PLAY. No causal resource/gameplay benefit is known.

On955 expert Rocket rows, gates fire845 ->816, card agreement269 ->253 and forced
aim292 ->288. Twelve prior correct full actions are lost:5 change from state7
to3 (gate stops),4 to5 (card becomes wrong),3 to6 (aim becomes wrong). Three are
gained:1 via card and2 via aim. The three late-Rocket losses split one each
across gate/card/aim. Row-level aim gains9/losses13 differ from the previously
reported replay-level7better/13worse/316ties; units are explicitly distinct.

Arithmetic hybrid Rocket full-action counts for control/candidate fire/card/aim
bits0..7 are77,76,74,73,72,71,69,68. Thus retaining control fire alone would give
73 in this cached head arithmetic, still below the control77. No single changed
head explains all losses, and these hybrids are not evaluated or deployable
policies. No predicted aim was fabricated for nonexpert Rocket choices.

Original labels/IDs/cache hashes and every group/per-replay transition agree with
the independent implementation. report/verified/reviewed bind full outputs. The
outer review's slash-prefix source-path branch does not match Windows backslash
paths; rl_failure_bindings.py separately checks Path.parts without rerunning any
counter, preserving the original review source/receipt. See bindings_verified.json.

The candidate stays REJECTED; its report was already delivered once. This leaf
creates no new model and sends no duplicate report. Owner STOP is intact. Final
N2-N7/physical/component/gameplay/statistical/Q4/Q5 requirements remain open.

Next supported mechanism check: measure policy versus critic contributions to
shared-encoder gradients on the saved training trajectories/checkpoints. The
original recipe allowed critic loss into the shared encoder after warmup, and
the isolated driver did not record the stock vf_grad_share monitor. This is a
hypothesis to test before a remedy, not proof that critic learning caused these
PLAY regressions. No learning-rate/loss grid or tactical rule is justified here.
