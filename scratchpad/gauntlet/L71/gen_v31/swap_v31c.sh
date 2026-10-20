#!/bin/bash
# Owner 2026-10-04 13:0x: "if 3.1c beats 3.1b, swap it in for live play" (and R1e starts from it). Waits for
# accept_v31c.sh. Rule (pre-registered 12:5x; in practice the paired ghost screen decides): 3.1c wins iff its ghost
# delta vs 3.1b >= 0. Also requires the reader-v2 live smoke to pass. Then writes CKPT_OVERRIDE (live switches at the
# next match boundary) and records the R1e base in R1E_BASE.txt.
cd /c/Users/benpe/ClashBot; G=scratchpad/gauntlet/L71/gen_v31; LOG=$G/chain.log
log() { echo "[v31c-swap] $* $(date '+%F %T')" >> $LOG; }
until [ $(grep -c "\[v31c-acc\] ACCEPT_DONE" $LOG) -ge 1 ] || [ $(grep -c -E "\[v31c-acc\] (SCREEN|TRAIN) FAILED" $LOG) -ge 2 ]; do sleep 30; done   # 1 stale TRAIN FAILED from 12:46
grep -q "\[v31c-acc\] ACCEPT_DONE" $LOG || { log "no acceptance -> R1e base 3.1b, live unchanged"; echo icebow/data/pipeline/gen_v31b_s0/gen_s0.pt > $G/R1E_BASE.txt; exit 0; }
D=$(python -c "import json,re;s=open('$G/pair_v31c_vs_v31b.out').read();print(re.search(r'\"delta_pp\": *(-?[0-9.e-]+)',s).group(1))")
log "3.1c vs 3.1b ghost delta $D pp"
if python -c "import sys; sys.exit(0 if float('$D') >= 0 else 1)"; then
  icebow/.venv/Scripts/python.exe .foreman/codex_autopilot/reader_v31_smoke.py --ckpt icebow/data/pipeline/gen_v31c_s0/gen_s0.pt --side 1 --out $G/smoke_v31c > $G/smoke_v31c.out 2>&1
  if grep -q TRAINED_CHECKPOINT_READER_SMOKE_PASS $G/smoke_v31c.out; then
    echo icebow/data/pipeline/gen_v31c_s0/gen_s0.pt > $G/R1E_BASE.txt
    printf '%s\n' "C:/Users/benpe/ClashBot/icebow/data/pipeline/gen_v31c_s0/gen_s0.pt" > scratchpad/gauntlet/L70/live/CKPT_OVERRIDE
    log "3.1c WINS -> live CKPT_OVERRIDE = gen_v31c; R1e base = gen_v31c"
    printf '%s\n' "ClashAI: gen_v3.1c beat gen_v3.1b (ghost $D pp) -> live switching to gen_v3.1c at the next match; R1e will start from it." > $G/_msg.txt
  else
    echo icebow/data/pipeline/gen_v31b_s0/gen_s0.pt > $G/R1E_BASE.txt; log "3.1c won the screen but FAILED the live smoke -> no swap, R1e base 3.1b"
    printf '%s\n' "ClashAI: gen_v3.1c beat 3.1b in the sim ($D pp) but failed the live-reader smoke test -> live stays on 3.1b." > $G/_msg.txt
  fi
else
  echo icebow/data/pipeline/gen_v31b_s0/gen_s0.pt > $G/R1E_BASE.txt; log "3.1c did not beat 3.1b -> live unchanged, R1e base 3.1b"
  printf '%s\n' "ClashAI: gen_v3.1c did not beat gen_v3.1b (ghost $D pp) -> live stays on 3.1b; R1e starts from 3.1b." > $G/_msg.txt
fi
icebow/.venv/Scripts/python.exe scratchpad/gauntlet/L69/discord/post.py $G/_msg.txt >> $LOG 2>&1
