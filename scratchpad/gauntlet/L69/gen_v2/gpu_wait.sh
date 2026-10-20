# Sourced by train_gen_v2.sh and select.sh. gpu_wait blocks until the GPU has been idle for GPU_FREE_POLLS
# consecutive polls GPU_POLL_S apart. Busy = nvidia-smi memory.used > GPU_BUSY_MB, OR any process (not powershell)
# whose command line matches GPU_BUSY_PAT (rl_royale, and the drivers/tools that run between its phases; command
# lines naming gpu_wait / train_gen_v2 / select.sh are skipped so our own launcher shell never matches), OR
# nvidia-smi / the process query failed (fail closed). Several free polls in a row so a seconds-long gap between two
# phases of a driver (e.g. run_r1.sh: R0' screens -> reactive -> R1) is not mistaken for an idle GPU.
GPU_BUSY_MB=${GPU_BUSY_MB:-2048}          # calibration knob: the desktop's own baseline use is not measured yet
GPU_BUSY_PAT=${GPU_BUSY_PAT:-'rl_royale|run_r1\.sh|run_r0p\.sh|search_s0|run_screen'}
GPU_POLL_S=${GPU_POLL_S:-120}
GPU_FREE_POLLS=${GPU_FREE_POLLS:-3}

gpu_state() {   # prints "<mem MiB> <matching processes>"
  local mem n
  mem=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -dc '0-9')
  n=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process | Where-Object { \$_.Name -notlike 'powershell*' -and \$_.CommandLine -match '$GPU_BUSY_PAT' -and \$_.CommandLine -notmatch 'gpu_wait|train_gen_v2|select\.sh' }).Count" 2>/dev/null | tr -dc '0-9')
  echo "${mem:-NA} ${n:-NA}"
}

gpu_busy() {
  local s mem n
  s=$(gpu_state); mem=${s% *}; n=${s#* }
  [ "$mem" = NA ] || [ "$n" = NA ] || [ "$mem" -gt "$GPU_BUSY_MB" ] || [ "$n" -gt 0 ]
}

gpu_wait() {
  local free=0 last=0
  while [ "$free" -lt "$GPU_FREE_POLLS" ]; do
    if gpu_busy; then
      free=0
      if [ $(( $(date +%s) - last )) -ge 1800 ]; then echo "[gpu_wait] busy (mem MiB, procs) = $(gpu_state) $(date)"; last=$(date +%s); fi
    else
      free=$((free + 1)); echo "[gpu_wait] free poll $free/$GPU_FREE_POLLS $(gpu_state) $(date)"
    fi
    [ "$free" -ge "$GPU_FREE_POLLS" ] || sleep "$GPU_POLL_S"
  done
}
