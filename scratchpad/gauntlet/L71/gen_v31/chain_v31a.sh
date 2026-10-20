#!/bin/bash
# gen_v3.1a chain (lead, 2026-10-04): wait for the VM re-drive -> pack (zstd) -> fetch -> unpack -> verify counts ->
# stop live between matches (owner allowed) -> build v4 dataset (BUILD_V31.txt command, 8 workers) -> train gen_v3.1a
# (gen_v3 recipe + feature v4, NO context weighting = --inputs-only-arm). Each stage logs to chain.log; any failure stops.
set -uo pipefail
cd /c/Users/benpe/ClashBot
G=scratchpad/gauntlet/L71/gen_v31; LOG=$G/chain.log
SSH="ssh -o ConnectTimeout=20 -o HostKeyAlias=136.108.166.193 -o StrictHostKeyChecking=yes -o BatchMode=yes -i $HOME/.ssh/clashbot_gcp clashbot-gauntlet@34.24.72.244"
SCP="scp -q -o HostKeyAlias=136.108.166.193 -o StrictHostKeyChecking=yes -i $HOME/.ssh/clashbot_gcp"
say() { echo "[v31a] $* $(date '+%F %T')" >> $LOG; }
die() { say "FAILED: $*"; exit 1; }
DIRS="corpus_gen_pilot/s0_public_v1 corpus_gen_pilot/s1_public_v1 corpus_gen_pilot/s2_public_v1 corpus_gen_pilot/s3_public_v1 corpus_v6/hogeq_public_v1 corpus_v6/icebow_public_v1"
say "waiting for VM ALL_DONE"
until $SSH 'grep -q ALL_DONE ~/cb/run_public.log' 2>/dev/null; do sleep 60; done
say "VM done: $($SSH 'cd ~/cb; cat scratchpad/gauntlet/ext/corpus_*/*_public_v1/j*/summary.jsonl | wc -l') summary rows"
$SSH "cd ~/cb/scratchpad/gauntlet/ext && mkdir -p ~/fetch && for d in $DIRS; do n=\$(echo \$d | tr / _); tar -cf - \$d | zstd -q -T8 -3 -o ~/fetch/\$n.tar.zst -f || exit 1; done; ls -la ~/fetch" >> $LOG 2>&1 || die "pack"
say "packed"
mkdir -p scratchpad/gauntlet/ext/fetch_public_v1
for d in $DIRS; do n=$(echo $d | tr / _); $SCP clashbot-gauntlet@34.24.72.244:fetch/$n.tar.zst scratchpad/gauntlet/ext/fetch_public_v1/ || die "scp $n"; done
say "fetched $(du -sh scratchpad/gauntlet/ext/fetch_public_v1 | cut -f1)"
for d in $DIRS; do n=$(echo $d | tr / _); /c/Windows/System32/tar.exe -xf scratchpad/gauntlet/ext/fetch_public_v1/$n.tar.zst -C scratchpad/gauntlet/ext || die "untar $n"; done
NREP=$(find scratchpad/gauntlet/ext/corpus_gen_pilot/*_public_v1 scratchpad/gauntlet/ext/corpus_v6/*_public_v1 -name 'replay_*.json' | wc -l)
NOK=$(cat scratchpad/gauntlet/ext/corpus_gen_pilot/*_public_v1/j*/summary.jsonl scratchpad/gauntlet/ext/corpus_v6/*_public_v1/j*/summary.jsonl | grep -c '"ok": true')
say "unpacked: $NREP replay files, $NOK ok summary rows"
[ "$NREP" -ge 14700 ] || die "only $NREP replays"
$SSH "sudo poweroff" > /dev/null 2>&1; say "VM poweroff requested (data verified locally)"
touch scratchpad/gauntlet/L70/live/STOP; say "live STOP touched (ends after the current match; owner allowed, restart at deploy)"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
research/ext/Royale/.venv/Scripts/python.exe -m pipeline.dataset_gen --feature-version 4 --corpus scratchpad/gauntlet/ext/corpus_gen_pilot/s0_public_v1 scratchpad/gauntlet/ext/corpus_gen_pilot/s1_public_v1 scratchpad/gauntlet/ext/corpus_gen_pilot/s2_public_v1 scratchpad/gauntlet/ext/corpus_gen_pilot/s3_public_v1 scratchpad/gauntlet/ext/corpus_v6/hogeq_public_v1 scratchpad/gauntlet/ext/corpus_v6/icebow_public_v1 --out icebow/data/pipeline/gen_dataset_v31_public.npz --grid lattice --workers 8 --wait-stride 40 --play-window 20 --shift-ticks 0 --val-pct 10 > $G/build.out 2>&1 || die "build (see build.out)"
say "built: $(tail -c 600 $G/build.out | tr '\n' ' ')"
V3=$(icebow/.venv/Scripts/python.exe -c "import numpy as np; d=np.load('icebow/data/pipeline/gen_dataset_v31_public.npz'); print(int(d['v3val'].sum()))")
[ "$V3" -gt 0 ] || die "v3val rows = 0"
say "v3val rows $V3; train start"
unset OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS
icebow/.venv/Scripts/python.exe -u scratchpad/gauntlet/L69/gen_v2/_train_every_epoch.py --data icebow/data/pipeline/gen_dataset_v31_public.npz --seed 0 --epochs 4 --val-sample 30000 --grid lattice --feature-version 4 --amp bf16 --allow-causal-tti-unknowns --inputs-only-arm --out-dir icebow/data/pipeline/gen_v31a_s0 > $G/train_v31a.out 2>&1 || die "train (see train_v31a.out)"
say "train done: $(grep -c v3val $G/train_v31a.out) epoch lines"
say "CHAIN_DONE"
