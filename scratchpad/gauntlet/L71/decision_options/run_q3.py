"""Sequential Q3 jobs, frozen source hashes, resumable completed-job receipts.

Does not stop/start live or deploy. Refuses a live worker or another GPU Python
process. Normal desktop graphics processes are not training jobs.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
PY = ROOT/'research/ext/Royale/.venv/Scripts/python.exe'
RUNNER = 'scratchpad/gauntlet/L71/decision_options/run_screen_v2.py'
MODELS = dict(r1e='icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt',
              r1='icebow/data/bench/rl_royale/rseries_r1/rseries_r1_u0155.pt')
ARMS = dict(baseline=[], filtered_T1=['--card-choice', 'filtered', '--card-ratio', '.7', '--card-T', '1'],
            filtered_T07=['--card-choice', 'filtered', '--card-ratio', '.7', '--card-T', '.7'],
            area=['--spell-aim', 'rocket_area'],
            combined=['--card-choice', 'filtered', '--card-ratio', '.7', '--card-T', '1', '--spell-aim', 'rocket_area'])


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sources():
    paths = list((ROOT/'pipeline').glob('*.py')) + [ROOT/RUNNER, Path(__file__),
            ROOT/'pipeline/rl_royale.yaml',
            ROOT/'scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl',
            ROOT/'scratchpad/gauntlet/L70/pool_forms/loadable_decks.json']
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}


def idle_gpu():
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    if os.name == 'nt':
        result = subprocess.run(['powershell', '-NoProfile', '-Command',
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"],
            capture_output=True, text=True, check=True, creationflags=flags)
        rows = json.loads(result.stdout or '[]')
        for p in rows if isinstance(rows, list) else [rows]:
            if 'live_play' in (p.get('CommandLine') or ''):
                raise RuntimeError('Live worker still running; wait for clean STOP')
    output = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,process_name', '--format=csv,noheader'],
                            capture_output=True, text=True, check=True, creationflags=flags).stdout
    for line in output.splitlines():
        if 'python' in line.lower():
            raise RuntimeError('GPU Python already running: ' + line)


def plan(out):
    jobs = []
    for model, ckpt in MODELS.items():
        for arm, extra in ARMS.items():
            name = model + '_' + arm
            ghost = str(out/(name+'.jsonl'))
            reactive = str(out/('reactive_'+name))
            jobs.append(dict(name='ghost_'+name, expected=[ghost], command=[str(PY), RUNNER,
                '--ckpt', ckpt, '--out', ghost, '--split', 'train', '--noise-off', 'all', '--opp-elixir', 'counter',
                '--action-delay', '26', '--extrapolate', '26', '--seeds', '0', '--device', 'cuda',
                '--forms-mode', 'deck', '--tau', '.27', '--behaviour-telemetry',
                '--only-tags-from', 'scratchpad/gauntlet/L68/generalist/lat26/screens/train_C.jsonl', *extra]))
            jobs.append(dict(name='reactive_'+name, expected=[reactive+'/matches.jsonl', reactive+'/summary.json'],
                command=[str(PY), '-m', 'pipeline.search_s0', '--out', reactive, '--gen', ckpt,
                '--opp-gen', 'icebow/data/pipeline/gen_v1_s0/gen_s0.pt', '--seeds', '0:24', '--opps', 'gen,s1',
                '--arms', 'plain', '--forms-mode', 'deck', '--device', 'cuda', '--workers', '3', '--tail-cap', '7200',
                '--census', 'scratchpad/gauntlet/L70/pool_forms/loadable_decks.json',
                '--hero-abilities', '--ability-policy', 'v2', '--behaviour-telemetry', *extra]))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    jobs = plan(a.out)
    current = dict(sources=sources(), checkpoints={k: sha(ROOT/v) for k, v in MODELS.items()}, jobs=jobs,
                   acceptance='ghost delta >=0, reactive wins >=baseline-2/48, Rocket share closer to .058 and tower Rocket hits increase',
                   changes='only learner options; fixed opponents; baseline regenerated with identical code',
                   census='evo/hero with ability policy v2; both checkpoints use this same instrument')
    if a.dry_run:
        print(json.dumps(current, indent=2))
        return
    idle_gpu()
    a.out.mkdir(parents=True, exist_ok=True)
    manifest = a.out/'plan.json'
    if manifest.exists():
        if json.loads(manifest.read_text()) != current:
            raise ValueError('Plan/source changed; do not mix baseline and candidate code')
    else:
        manifest.write_text(json.dumps(current, indent=2))
    for job in jobs:
        receipt = a.out/(job['name']+'.receipt.json')
        if receipt.exists():
            done = json.loads(receipt.read_text())
            if done['command'] != job['command'] or done['exit_code'] != 0:
                raise ValueError('Invalid prior receipt')
            for p, digest in done['outputs'].items():
                if sha(p) != digest:
                    raise ValueError('Completed output changed')
            continue
        if sources() != current['sources']:
            raise ValueError('Source changed during acceptance')
        idle_gpu()
        print(datetime.datetime.now().isoformat(), 'START', job['name'], flush=True)
        log = a.out/(job['name']+'.out')
        with log.open('w') as f:
            process = subprocess.run(job['command'], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT,
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if process.returncode:
            raise RuntimeError(f"{job['name']} failed ({process.returncode}); inspect {log}")
        outputs = {p: sha(p) for p in job['expected']}
        receipt.write_text(json.dumps(dict(command=job['command'], exit_code=0, outputs=outputs,
                                           output_sha256=sha(log)), indent=2))
        print(datetime.datetime.now().isoformat(), 'DONE', job['name'], flush=True)
    print('Q3_JOBS_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
