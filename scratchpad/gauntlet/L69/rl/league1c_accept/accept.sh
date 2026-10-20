#!/bin/bash
# league1c acceptance, same instrument as league1b_accept (pinned 299 train-split tags, live condition, tau 0.27,
# seed 0, paired vs init on the SAME engine build as league1b's acceptance): u0075 (league1b's budget), u0010 (best
# early screen 0.966 at update 9), u0140 (final). Reactive-play acceptance follows separately (search_s0 --opp-gen).
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L69/rl/league1c_accept
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
INIT=scratchpad/gauntlet/L68/overnight0929/train_tau0.27.jsonl
for u in 0075 0010 0140; do
  t=league1c_u$u
  $PY $RS --ckpt icebow/data/bench/rl_royale/league1c/$t.pt --out $O/train_$t.jsonl --split train --noise-off all \
      --opp-elixir counter --action-delay 26 --extrapolate 26 --seeds 0 --device cuda --only-tags-from $OLD > $O/train_$t.out 2>&1
  $PY $RS --pair $INIT $O/train_$t.jsonl > $O/pair_$t.out 2>&1
  echo "[acc] $t $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $O/pair_$t.out | tr -d ' \n') $(date)" >> $O/accept.log
done
echo "[acc] done $(date)" >> $O/accept.log
