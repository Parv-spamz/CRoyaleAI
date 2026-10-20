#!/bin/bash
# league1b crashed at u0049 (01:45) on a CUDA out-of-memory in backward (desktop apps hold ~3 GB of the 8 GB GPU;
# league1b batches run ~9% larger than league1's). Owner rule (league1): no GPU space -> CPU. So: wait for the one
# orphaned acceptance screen (league1b_u0020) to finish (never two GPU jobs), resume on GPU; if it dies on OOM again
# and no STOP file is present, resume on CPU. The 06:00 STOP (stop_at_0600.sh) ends it; then run the acceptance.
cd /c/Users/benpe/ClashBot
A=scratchpad/gauntlet/L68/rl/league1b_accept
O=scratchpad/gauntlet/L68/overnight0929
R=scratchpad/gauntlet/L68/rl/league1b
PY=research/ext/Royale/.venv/Scripts/python.exe
ARGS="--config pipeline/rl_royale.yaml --run league1b --resume init=icebow/data/pipeline/gen_v1_s0/gen_s0.pt league=true noise_off=all opp_elixir=counter action_delay_ticks=26 extrapolate_ticks=26 max_updates=200 screen_seeds=[0]"
until grep -q '"DONE"' $A/train_league1b_u0020.out 2>/dev/null; do sleep 30; done
echo "[res] orphan screen done $(date)" >> $O/driver.log
for dev in gpu cpu; do
  [ -f $R/STOP ] && break
  extra=""; [ $dev = cpu ] && extra="learner_device=cpu actor_device=cpu"
  echo "[res] resume league1b on $dev $(date)" >> $O/driver.log
  $PY -m pipeline.rl_royale $ARGS $extra > $O/league1b_resume_$dev.out 2> $O/league1b_resume_$dev.out.err
  echo "[res] league1b ($dev) exited $? $(date): $(tail -1 $R/train.log | cut -c1-160)" >> $O/driver.log
  grep -q "out of memory" $O/league1b_resume_$dev.out $O/league1b_resume_$dev.out.err || break
done
bash $A/accept.sh
