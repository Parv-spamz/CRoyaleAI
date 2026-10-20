"""Exercise the inspected log-parser function without starting a supervisor."""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[4]
BASH='C:/Program Files/Git/bin/bash.exe'
script=ROOT/'scratchpad/gauntlet/L70/live/run_live.sh'
subprocess.run([BASH,'-n',str(script)],check=True)
function=next(line for line in script.read_text().splitlines() if line.startswith('last_stop()'))
with tempfile.TemporaryDirectory(prefix='clashbot-reason-') as temporary:
    folder=Path(temporary)
    expected='[live] new checkpoint deployed (accepted.pt) -- ending this run so the supervisor restarts on it'
    (folder/'overnight.out').write_text('[nav] run stopped before match 2: old reason\n'+expected+'\n')
    # Pass the path as argv, not interpolated shell source. Only the inspected
    # one-line parser is evaluated; no supervisor or notification code runs.
    parsed=subprocess.run([BASH,'-c','L="$1"\n'+function+'\nlast_stop','reason-check',folder.as_posix()],
                          check=True,capture_output=True,text=True)
    assert parsed.stdout.strip()==expected, parsed.stdout
    print(json.dumps(dict(shell_syntax=True,latest_reason=parsed.stdout.strip(),supervisor_started=False)))
print('SUPERVISOR_CHECKPOINT_REASON_PASS')
