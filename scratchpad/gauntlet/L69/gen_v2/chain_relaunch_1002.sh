#!/bin/bash
# Relaunch of chain_after_r1.sh after the 2026-10-02 15:07 reboot killed train_gen_v2 mid-epoch 4 (partial run kept in
# icebow/data/pipeline/gen_v2_s0_partial_reboot1002). Same recipe from scratch (train_gen has no resume and no optimizer
# state was saved). NO_GPU_WAIT=1: owner go-ahead 10-02 evening; the 2048-MiB threshold blocked 10 h on desktop baseline.
cd /c/Users/benpe/ClashBot
G=scratchpad/gauntlet/L69/gen_v2
echo "[g2] relaunch (after 15:07 reboot) train start $(date)" >> $G/chain.log
NO_GPU_WAIT=1 bash $G/train_gen_v2.sh > $G/train_gen_v2.out 2>&1
echo "[g2] train exit $? $(date)" >> $G/chain.log
NO_GPU_WAIT=1 bash $G/select.sh --top 4 > $G/select.out 2>&1
echo "[g2] select exit $? $(date)" >> $G/chain.log
