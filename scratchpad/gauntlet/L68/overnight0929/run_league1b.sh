#!/bin/bash
# league1b relaunch (the first launch refused the pre-seeded entries.json; rl_royale now allows it).
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L68/overnight0929
research/ext/Royale/.venv/Scripts/python.exe -m pipeline.rl_royale --config pipeline/rl_royale.yaml --run league1b \
    init=icebow/data/pipeline/gen_v1_s0/gen_s0.pt league=true noise_off=all opp_elixir=counter action_delay_ticks=26 \
    extrapolate_ticks=26 max_updates=200 'screen_seeds=[0]' > $O/league1b_launch.out 2> $O/league1b_launch.out.err
echo "[drv] league1b exited $? $(date): $(tail -2 $O/league1b_launch.out)" >> $O/driver.log
