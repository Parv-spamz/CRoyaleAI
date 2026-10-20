#!/bin/bash
# After R0' finishes: (1) R0' ghost screens on the GPU (u0075 + final; pinned 299, tau 0.27, forms deck, paired vs the
# evolutions re-baseline); (2) R1 on the GPU = R0' + advantage gae (per-decision credit, win/loss only), per-tick
# discount, critic warm-up 5 updates (policy frozen) -> max_updates 155 = 150 policy updates, matched to R0';
# (3) BEFORE R1, R0' reactive-play acceptance on the GPU (~10 min each, same device as the baseline) (plain arm vs frozen gen_v1 and S1, 24 seeds, forms deck).
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L69/rl
A=$O/r0p_accept; mkdir -p $A
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
BASE=scratchpad/gauntlet/L69/rebase_1001_evo/train_tau0.27.jsonl
CK=icebow/data/bench/rl_royale/rseries_r0p
until grep -q "\[drv\] done" $O/r0p_driver.log; do sleep 60; done
LAST=$(ls $CK/rseries_r0p_u0*.pt | sort | tail -1 | sed 's/.*_u\([0-9]*\)\.pt/\1/')
echo "[r1drv] R0' done; last ckpt u$LAST $(date)" >> $O/r1_driver.log
for u in 0075 $LAST; do
  t=rseries_r0p_u$u
  $PY $RS --ckpt $CK/$t.pt --out $A/train_$t.jsonl --split train --noise-off all --opp-elixir counter --action-delay 26 \
      --extrapolate 26 --seeds 0 --device cuda --forms-mode deck --only-tags-from $OLD > $A/train_$t.out 2>&1
  $PY $RS --pair $BASE $A/train_$t.jsonl > $A/pair_$t.out 2>&1
  echo "[r1drv] screen $t $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $A/pair_$t.out | tr -d ' \n') $(date)" >> $O/r1_driver.log
done
for u in 0075 $LAST; do
  t=rseries_r0p_u$u
  $PY -m pipeline.search_s0 --out $A/reactive_$t --seeds 0:24 --opps gen,s1 --arms plain \
      --gen $CK/$t.pt --opp-gen icebow/data/pipeline/gen_v1_s0/gen_s0.pt --forms-mode deck --device cuda --workers 3 --tail-cap 7200 \
      > $A/reactive_$t.log 2>&1
  echo "[r1drv] reactive $t exit $? $(date)" >> $O/r1_driver.log
done
CFG=$O/r1_rl_royale.yaml
OVR="init=icebow/data/pipeline/gen_v1_s0/gen_s0.pt league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=155 screen_seeds=[0] league_learner_icebow_share=1.0 forms_mode=deck league_decks=scratchpad/gauntlet/L69/pool/loadable_decks.json advantage=gae gae_gamma_unit=tick critic_warmup_updates=5"
( echo "[r1drv] R1 start $(date)" >> $O/r1_driver.log
  $PY -m pipeline.rl_royale --config $CFG --run rseries_r1 $OVR > $O/r1_gpu.out 2> $O/r1_gpu.out.err
  echo "[r1drv] R1 gpu exited $? $(date)" >> $O/r1_driver.log
  if grep -q "out of memory" $O/r1_gpu.out $O/r1_gpu.out.err; then
    echo "[r1drv] OOM -> resume on CPU $(date)" >> $O/r1_driver.log
    $PY -m pipeline.rl_royale --config $CFG --run rseries_r1 --resume $OVR learner_device=cpu actor_device=cpu > $O/r1_cpu.out 2> $O/r1_cpu.out.err
    echo "[r1drv] R1 cpu exited $? $(date)" >> $O/r1_driver.log
  fi
  echo "[r1drv] R1 done $(date)" >> $O/r1_driver.log )
echo "[r1drv] all done $(date)" >> $O/r1_driver.log
