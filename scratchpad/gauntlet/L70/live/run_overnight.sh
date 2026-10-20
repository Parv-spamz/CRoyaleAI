#!/bin/bash
# Overnight ladder run (owner 2026-10-02 evening): league1c_u0075 (the only RL checkpoint with a measured gain), tau 0.35
# (the live setting since 09-30), Trophy Road via ladder_nav (Play Again; after the day's 4th win OK -> chests -> Battle;
# Trophy Road rewards collected), overlaid replays OFF except one 60-s clip to Discord at the start and every 30 min.
# Restarts after a stop, at most MAX_RESTARTS (default 10; owner 2026-10-02 21:4x, was 5), each stop posted to Discord.
# Ends at 09:00 or when $L/STOP exists (touch it to stop between matches).
# If a ladder live_play is ALREADY running when this starts (a supervisor swap), it is adopted: waited for, and its stop
# counts as the first restart -- never a second live_play beside it.
cd /c/Users/benpe/ClashBot
L=scratchpad/gauntlet/L70/live
PY=icebow/.venv/Scripts/python.exe
MAX=${MAX_RESTARTS:-10}
post() { printf '%s\n' "$1" > $L/_msg.txt; $PY scratchpad/gauntlet/L69/discord/post.py $L/_msg.txt >> $L/supervisor.log 2>&1; }
running() {   # number of ladder live_play python processes (fail -> 1: assume running, never start a second one)
  local n
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object {\$_.CommandLine -like '*live_play.py*--ladder*'}).Count" 2>/dev/null | tr -dc '0-9')
  echo "${n:-1}"
}
last_stop() { grep -aE '\[live\] run stopped|\[nav\] run stopped|\[ladder\] STOP|stop file' $L/overnight.out | tail -1; }
state() { cat scratchpad/gauntlet/L68/live_reader/ladder_state.json 2>/dev/null; }
end_day=today; [ "$(date +%H)" -ge 9 ] && end_day=tomorrow
( sleep $(( $(date -d "$end_day 09:00" +%s) - $(date +%s) )); touch $L/STOP ) &
restarts=0
if [ "$(running)" -gt 0 ]; then
  echo "[sup] adopting the running live_play $(date) (restart counter reset, limit $MAX)" >> $L/supervisor.log
  while [ "$(running)" -gt 0 ]; do sleep 20; done
  why=$(last_stop)
  echo "[sup] adopted run exited $(date): $why" >> $L/supervisor.log
  if [ ! -e $L/STOP ]; then
    restarts=1
    post "ClashAI live run stopped $(date +%H:%M): ${why:-no reason logged}. State $(state). Restart $restarts/$MAX in 60 s."
    sleep 60
  fi
fi
while [ ! -e $L/STOP ]; do
  echo "[sup] start (restarts used $restarts/$MAX) $(date)" >> $L/supervisor.log
  $PY -u scratchpad/gauntlet/L68/live_reader/live_play.py --ladder --matches 400 \
    --ckpt icebow/data/bench/rl_royale/league1c/league1c_u0075.pt --tau 0.35 --max-seconds 600 \
    --clip-every 1800 --overlay reader --stop-file $L/STOP >> $L/overnight.out 2>&1
  rc=$?
  why=$(last_stop)
  echo "[sup] exit $rc $(date): $why" >> $L/supervisor.log
  [ -e $L/STOP ] && break
  if [ $restarts -ge $MAX ]; then
    post "ClashAI live run stopped $(date +%H:%M) (rc $rc): ${why:-no reason logged}. Restart limit $MAX reached -- NOT restarting. State $(state)."
    break
  fi
  restarts=$((restarts + 1))
  post "ClashAI live run stopped $(date +%H:%M) (rc $rc): ${why:-no reason logged}. State $(state). Restart $restarts/$MAX in 60 s."
  sleep 60
done
post "ClashAI overnight ladder run ended $(date +%H:%M). Tally $(state)"
echo "[sup] done $(date)" >> $L/supervisor.log
