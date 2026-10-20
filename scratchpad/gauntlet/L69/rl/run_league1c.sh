#!/bin/bash
# R0 of the owner-approved reward plan (scratchpad/gauntlet/L69/reward_plan.md): league1c = league1b + the learner
# always on icebow (league_learner_icebow_share=1.0; opponent decks unchanged). Same entries.json (299/58), same
# argv otherwise. Config = a COPY of rl_royale.yaml with the key uncommented (the repo yaml keeps it commented).
# GPU first; on a CUDA out-of-memory exit, resume on CPU. A STOP file at 07:00 ends it (league1b reached u74).
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L69/rl
R=scratchpad/gauntlet/L68/rl/league1c
PY=research/ext/Royale/.venv/Scripts/python.exe
CFG=$O/league1c_rl_royale.yaml
OVR="init=icebow/data/pipeline/gen_v1_s0/gen_s0.pt league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=200 screen_seeds=[0] league_learner_icebow_share=1.0"
( until [ "$(date +%H%M)" -ge 0700 ] && [ "$(date +%H%M)" -lt 1200 ]; do sleep 60; done; touch $R/STOP; echo "[drv] STOP placed $(date)" >> $O/league1c_driver.log ) &
echo "[drv] start $(date)" >> $O/league1c_driver.log
$PY -m pipeline.rl_royale --config $CFG --run league1c $OVR > $O/league1c_gpu.out 2> $O/league1c_gpu.out.err
echo "[drv] gpu exited $? $(date): $(tail -1 $R/train.log | cut -c1-160)" >> $O/league1c_driver.log
if grep -q "out of memory" $O/league1c_gpu.out $O/league1c_gpu.out.err && [ ! -f $R/STOP ]; then
  echo "[drv] OOM -> resume on CPU $(date)" >> $O/league1c_driver.log
  $PY -m pipeline.rl_royale --config $CFG --run league1c --resume $OVR learner_device=cpu actor_device=cpu > $O/league1c_cpu.out 2> $O/league1c_cpu.out.err
  echo "[drv] cpu exited $? $(date): $(tail -1 $R/train.log | cut -c1-160)" >> $O/league1c_driver.log
fi
echo "[drv] done $(date)" >> $O/league1c_driver.log
