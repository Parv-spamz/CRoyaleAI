"""Separate truth-scoring harness: private truth never enters PublicObserver."""
import os
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '1'
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline.native_recording import tag_native_recording
from pipeline.public_observation import PublicObserver
from audit_runtime import lower_own_priority


def evaluate(rec):
    rec = tag_native_recording(rec, {})
    full = [PublicObserver(s) for s in (0, 1)]
    bodies = [PublicObserver(s) for s in (0, 1)]
    rows = []
    seen = set()
    for frame in sorted(rec['frames'], key=lambda f: f['tick']):
        tick = int(frame['tick'])
        for side in (0, 1):
            # Explicit allowlist: neither observer receives truth or commands.
            public = {k: frame[k] for k in ('tick', 'entities', 'entity_ids', 'native_card_ids',
                       'projectiles', 'area_effects') if k in frame}
            full[side].update(public, source='native')
            body = dict(public, projectiles=[], area_effects=[])
            bodies[side].update(body, source='native')
            if (tick, side) in seen:
                continue
            seen.add((tick, side))
            truth = frame.get('elixir', [None, None])[1-side]
            if truth is None:
                continue
            truth = float(truth)
            if not np.isfinite(truth) or not 0 <= truth <= 10.01:
                raise ValueError('Invalid audit truth')
            rows.append((full[side].estimate_at(tick)-truth, bodies[side].estimate_at(tick)-truth))
    errors = np.asarray(rows, dtype=float)
    if not len(errors):
        raise ValueError('No truth scoring rows')
    return dict(n=len(errors), signed_sum=errors.sum(axis=0).tolist(),
                absolute_sum=np.abs(errors).sum(axis=0).tolist(),
                squared_sum=(errors**2).sum(axis=0).tolist(),
                over_one=(np.abs(errors)>1).sum(axis=0).tolist(),
                missing_area_frames=sum('area_effects' not in f for f in rec['frames']))


def aggregate(rows):
    n = np.array([r['n'] for r in rows])
    absolute = np.array([r['absolute_sum'] for r in rows])
    signed = np.array([r['signed_sum'] for r in rows])
    squared = np.array([r['squared_sum'] for r in rows])
    point = absolute.sum(axis=0)/n.sum()
    rng = np.random.default_rng(20261003)
    boot = []
    for _ in range(2000):
        ix = rng.integers(len(rows), size=len(rows))
        boot.append(absolute[ix].sum(axis=0)/n[ix].sum())
    boot = np.asarray(boot)
    return dict(replays=len(rows), observations=int(n.sum()),
                columns=['public_bodies_and_observed_spells', 'bodies_only'],
                mae=point.tolist(), mae_ci95=np.percentile(boot, [2.5,97.5], axis=0).T.tolist(),
                signed_bias=(signed.sum(axis=0)/n.sum()).tolist(),
                rmse=np.sqrt(squared.sum(axis=0)/n.sum()).tolist(),
                absolute_error_over_one_share=(np.array([r['over_one'] for r in rows]).sum(axis=0)/n.sum()).tolist(),
                paired_mae_delta=float(point[0]-point[1]),
                paired_mae_delta_ci95=np.percentile(boot[:,0]-boot[:,1],[2.5,97.5]).tolist())


def run(out, per_corpus):
    manifest_path=Path(__file__).with_name('native_mining_1552')/'manifest.json'
    raw=manifest_path.read_bytes(); manifest=json.loads(raw)
    groups=defaultdict(list)
    for entry in manifest:
        groups[str(Path(entry['path']).parent)].append(entry)
    selected=[]
    for corpus, entries in sorted(groups.items()):
        selected.extend(sorted(entries,key=lambda e: hashlib.sha256(('counter2230:'+e['tag']).encode()).hexdigest())[:per_corpus])
    out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for i,entry in enumerate(selected):
        content=(ROOT/entry['path']).read_bytes()
        if hashlib.sha256(content).hexdigest()!=entry['sha256']:
            raise ValueError('Source changed')
        rec=json.loads(content)
        if rec['tag']!=entry['tag']:
            raise ValueError('Source identity mismatch')
        rows.append(dict(entry, **evaluate(rec)))
        if (i+1)%25==0: print('AUDITED',i+1,flush=True)
        time.sleep(.05)
    (out/'replay_errors.json').write_text(json.dumps(rows,indent=2)+'\n')
    report=dict(status='MEASURED_NATIVE_PUBLIC_COUNTER_ERROR_NOT_LIVE_ERROR',
        source_manifest_sha256=hashlib.sha256(raw).hexdigest(),
        source_code_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [Path(__file__),ROOT/'pipeline/public_observation.py',ROOT/'pipeline/opp_elixir_count.py']},
        selection='Lowest SHA256(counter2230:tag), equal sample per native corpus; not selected by outcome.',
        bootstrap='2000 replay-cluster paired resamples, seed 20261003; pooled observation-weighted errors',
        overall=aggregate(rows),
        by_corpus={c:aggregate([r for r in rows if str(Path(r['path']).parent)==c]) for c in groups},
        missing_area_frames=sum(r['missing_area_frames'] for r in rows),
        limitations=['The historical native recording omits actual area effects; these are not complete reader-v2 error measurements.',
                    'Same-tick plays are excluded by the model counter; native truth may be post-command at that tick.',
                    'Counter does not infer hidden ability payments, Mirror surcharge, collector production or Elixir Golem payouts.',
                    'Native re-drive truth is not original human-match truth. No live deployment or threshold conclusion.'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['overall']),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--per-corpus',type=int,default=100)
    a=p.parse_args();lower_own_priority();run(a.out,a.per_corpus)
