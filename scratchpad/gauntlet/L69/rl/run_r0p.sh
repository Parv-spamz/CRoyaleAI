#!/bin/bash
# R0' (control for R1): league1c settings on the 10-01 setup = new engine (RoyaleSim 369fe33) + evolutions
# (forms_mode=deck) + the 1000-deck pool. advantage match_loo (default). Same pinned entries (299/58). Starts when the
# evolutions re-baseline has finished (GPU). max_updates 150; GPU OOM -> resume on CPU.
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L69/rl
R=scratchpad/gauntlet/L68/rl/rseries_r0p
PY=research/ext/Royale/.venv/Scripts/python.exe
CFG=$O/rseries_rl_royale.yaml
until [ -s scratchpad/gauntlet/L69/rebase_1001_evo/reactive_genv1/summary.json ]; do sleep 30; done
OVR="init=icebow/data/pipeline/gen_v1_s0/gen_s0.pt league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=150 screen_seeds=[0] league_learner_icebow_share=1.0 forms_mode=deck league_decks=scratchpad/gauntlet/L69/pool/loadable_decks.json"
echo "[drv] start $(date)" >> $O/r0p_driver.log
$PY -m pipeline.rl_royale --config $CFG --run rseries_r0p $OVR > $O/r0p_gpu.out 2> $O/r0p_gpu.out.err
echo "[drv] gpu exited $? $(date): $(tail -1 $R/train.log | cut -c1-160)" >> $O/r0p_driver.log
if grep -q "out of memory" $O/r0p_gpu.out $O/r0p_gpu.out.err; then
  echo "[drv] OOM -> resume on CPU $(date)" >> $O/r0p_driver.log
  $PY -m pipeline.rl_royale --config $CFG --run rseries_r0p --resume $OVR learner_device=cpu actor_device=cpu > $O/r0p_cpu.out 2> $O/r0p_cpu.out.err
  echo "[drv] cpu exited $? $(date): $(tail -1 $R/train.log | cut -c1-160)" >> $O/r0p_driver.log
fi
echo "[drv] done $(date)" >> $O/r0p_driver.log
