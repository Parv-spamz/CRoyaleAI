#!/bin/bash
# league1b acceptance (rev 2, 2026-09-30 01:0x). league1b is stopped by a STOP file at 06:00 (CPU contention from
# other jobs made it ~7 min/update). EQUAL-BUDGET comparison: for league1b AND league1, the same rule restricted to
# updates <= league1b's last: top-2 held-out-screen checkpoints (screen line uN = ckpt _u(N+1)) + the final
# (last multiple of 5), each vs init on the 299 train-split tags, NEW engine, live condition, tau 0.27, seed 0, paired.
cd /c/Users/benpe/ClashBot
O=scratchpad/gauntlet/L68/rl/league1b_accept
# (invoked by resume_league1b.sh once league1b has stopped)
echo "[acc] league1b ended $(date)" > $O/accept.log
PY=research/ext/Royale/.venv/Scripts/python.exe
RS=scratchpad/gauntlet/L68/generalist/screen_gen/run_screen.py
OLD=scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl
INIT=scratchpad/gauntlet/L68/overnight0929/train_tau0.27.jsonl
CK=icebow/data/bench/rl_royale
CANDS=$(icebow/.venv/Scripts/python.exe - <<'PY'
import json
def log(run): return [json.loads(l) for l in open(f'scratchpad/gauntlet/L68/rl/{run}/train_log.jsonl')]
b = log('league1b')
last = max(r['update'] for r in b if r.get('type') == 'update') + 1
final = last - last % 5
out = []
for run in ('league1b', 'league1'):
    S = [(r['update'], r['screen']['winrate']) for r in log(run) if r.get('type') == 'update' and r.get('screen')
         and r['update'] + 1 <= final]
    top = [u + 1 for u, w in sorted(S, key=lambda x: (-x[1], -x[0]))[:2]]
    out += [f'{run}/{run}_u{u:04d}.pt' for u in sorted(set(top + [final]))]
print(' '.join(out))
PY
)
echo "[acc] candidates: $CANDS" >> $O/accept.log
for c in $CANDS; do
  t=$(basename $c .pt)
  $PY $RS --ckpt $CK/$c --out $O/train_$t.jsonl --split train --noise-off all --opp-elixir counter --action-delay 26 \
      --extrapolate 26 --seeds 0 --device cuda --only-tags-from $OLD --resume > $O/train_$t.out 2>&1
  $PY $RS --pair $INIT $O/train_$t.jsonl > $O/pair_$t.out 2>&1
  echo "[acc] $t $(grep -E '"delta_pp"|"ci_lo_pp"|"ci_hi_pp"' $O/pair_$t.out | tr -d ' \n') $(date)" >> $O/accept.log
done
echo "[acc] done $(date)" >> $O/accept.log
