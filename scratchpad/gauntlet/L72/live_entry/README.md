# Manual recording entry

From PowerShell in `C:\Users\benpe\ClashBot`:

```powershell
.\icebow\.venv\Scripts\python.exe .\scratchpad\gauntlet\L68\live_reader\live_play.py
```

Keep MuMu and Clash Royale open, run the command, then enter a match manually. The default handles one match, records it and saves raw and overlaid videos under `icebow/data/overlayed_replays`. It does not navigate into another match or publish anything. CPU inference uses four threads so the serialized GPU training chain can continue. `--overlay reader` selects only reader markers; default `both` includes cosmetic detector boxes.

The script loads the checkpoint named by `scratchpad/gauntlet/L70/live/CKPT_OVERRIDE`, prints its full path/source/SHA256, and never selects by modification time. Currently that pointer is R1e31 u0155, the last owner-selected live model. None of the new L71 candidates qualifies yet. The pointer should move only when a successor passes the declared acceptance checks; this manual filming path is not an autonomous R1e fallback deployment.

An explicit `--ckpt "C:\path\to\checkpoint.pt"` wins over the pointer. Missing or malformed selections fail clearly. A changed default selection ends a multi-match run between matches; an explicit selection stays fixed. `--check` loads and reports the chosen model offline without connecting to the emulator.

The current public-input pilot supports checkpoint feature versions4–6, audited PLAY and WAIT, and the public opponent-elixir counter. Defaults remain deterministic card/cell argmax and tau0.35; failed sampling/Rocket-area options stay disabled. Forced anti-leak spending has been removed. `--no-anti-leak` remains a harmless compatibility alias. The screenshot menu guard remains opt-in; tick/countdown, stale-reader, input-timeout and receipt checks still prevent accidental inputs. The owner-approved temporary hero ability behavior remains unchanged.

Periodic recording via `--clip-every` now stays local. Automatic Discord clip/connection-loss notifications were removed from the live entry and supervisor. The historical `live_play_v2.py` command delegates to this canonical entry, so it cannot drift to stale defaults.

Verification covers selected/explicit/invalid checkpoint behavior, reader/decision/audit parity on archived real frames, navigation and tap receipt regressions, and rendering/decoding a short archived video. The owner-started October5 06:27 match subsequently verified the selected R1e hash, CPU/tau.35/argmax/public-audit settings and anti-leak OFF:66 attempts,64 confirmations, one timeout and one unresolved attempt at match end;485 public decision audits, three confirmed abilities, median36ms/p95 44ms/max75ms decision latency. Both local videos saved and the supervisor exited normally after its match at06:37. See manual_match_verified.json and its receipt. This is manual-entry evidence, not acceptance of a new model. STOP remains set after the owner-authorized pause for evaluation. The single-match command above is a separate manual run and does not use that supervisor STOP file.

For repeated ladder matches from PowerShell, explicitly use Git Bash (bare `bash`
resolves to Windows' WSL launcher in the current environment):

```powershell
& "C:\Program Files\Git\bin\bash.exe" "C:/Users/benpe/ClashBot/scratchpad/gauntlet/L70/live/start_live.sh"
```

This clears the old STOP file and starts the supervisor with `--ladder --matches
400`; navigation runs before each subsequent match. The supervisor allows up to
10 restarts. Another-device pause, navigation/input failure or an explicit STOP
can end a run. For a between-match stop, use the same command with `stop_live.sh`.
The October5 06:27 run stopped before match2 because Codex set STOP for the final
evaluation under the owner's permission; its log does not show a navigation failure.
The owner restarted at06:45 after evaluation finished. At06:55 the current log
shows repeated result recognition, Play Again taps and battle-loading handoffs;
STOP is absent and one launcher/worker pair is active. Live looping is observed.
