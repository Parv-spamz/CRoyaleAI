#!/bin/bash
# L68 ranking check: both checkpoints on RoyaleSim, all loadable held-out ghosts, live rule, 4 shards each.
cd /c/Users/benpe/ClashBot
P=research/ext/Royale/.venv/Scripts/python.exe
for ck in v6lat_s0 v6aug_s1; do for s in 0 1 2 3; do
  $P -m pipeline.e1_eval --engine royale --subs Tornado=Arrows --port 0 \
     --ckpt icebow/data/pipeline/s1_icebow_${ck}.pt --split heldout --entries all --seeds 0 \
     --shard $s/4 --threads 2 --out scratchpad/gauntlet/L68/rank/${ck}_sh$s > scratchpad/gauntlet/L68/rank/${ck}_sh$s.log 2>&1 &
done; done
wait
echo ALL_DONE
