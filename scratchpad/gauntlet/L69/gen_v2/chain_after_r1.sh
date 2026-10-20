#!/bin/bash
# gen_v2 retrain + selection, chained strictly AFTER the R1 driver (one GPU job at a time). Reactive play for ALL 4
# epochs (--top 4), so the pick rests on complete reactive play, not on the joint-metric definition.
cd /c/Users/benpe/ClashBot
G=scratchpad/gauntlet/L69/gen_v2
until grep -q "\[r1drv\] all done" scratchpad/gauntlet/L69/rl/r1_driver.log 2>/dev/null; do sleep 120; done
echo "[g2] train start $(date)" >> $G/chain.log
bash $G/train_gen_v2.sh > $G/train_gen_v2.out 2>&1
echo "[g2] train exit $? $(date)" >> $G/chain.log
bash $G/select.sh --top 4 > $G/select.out 2>&1
echo "[g2] select exit $? $(date)" >> $G/chain.log
