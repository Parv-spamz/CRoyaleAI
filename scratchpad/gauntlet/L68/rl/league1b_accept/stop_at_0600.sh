#!/bin/bash
# Stop league1b cleanly after its current update at 06:00 (rl_royale checks run_dir/STOP after each update).
cd /c/Users/benpe/ClashBot
until [ "$(date +%H%M)" -ge 0600 ] && [ "$(date +%H%M)" -lt 1200 ]; do sleep 60; done
touch scratchpad/gauntlet/L68/rl/league1b/STOP && echo "STOP placed $(date)"
