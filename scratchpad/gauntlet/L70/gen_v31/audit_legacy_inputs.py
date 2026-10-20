"""Read-only full-scalar inventory and checkpoint/result provenance sidecar.

Never changes historical data, checkpoints or numbers. Chunked NPZ reading
bounds memory; model checkpoints are loaded on CPU with weights_only=True.
"""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
    os.environ[name]='1'
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from audit_runtime import lower_own_priority


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def scalar_inventory(path):
    with zipfile.ZipFile(path) as archive:
        if 'sc.npy' not in archive.namelist():
            return dict(path=str(path.relative_to(ROOT)),status='NO_SC_ARRAY_UNCLASSIFIED')
        with archive.open('sc.npy') as f:
            version=np.lib.format.read_magic(f)
            if version == (1, 0):
                shape,fortran,dtype=np.lib.format.read_array_header_1_0(f)
            elif version == (2, 0):
                shape,fortran,dtype=np.lib.format.read_array_header_2_0(f)
            else:
                raise ValueError(f'Unsupported NPY header version: {version}')
            if fortran or len(shape)!=2 or shape[1]<7 or dtype.hasobject:
                raise ValueError('Unsupported scalar schema')
            total,known,nonzero,invalid=0,0,0,0
            while total<shape[0]:
                n=min(8192,shape[0]-total)
                size=n*shape[1]*dtype.itemsize
                data=f.read(size)
                if len(data)!=size:raise ValueError('Truncated scalar array')
                rows=np.frombuffer(data,dtype=dtype).reshape(n,shape[1])
                known+=int((rows[:,6]>0).sum());nonzero+=int((rows[:,5]!=0).sum())
                invalid+=int((~np.isfinite(rows[:,5:7])).any(axis=1).sum());total+=n
                time.sleep(.001)
    return dict(path=str(path.relative_to(ROOT)),sha256=sha(path),rows=total,
                opponent_known_rows=known,opponent_nonzero_rows=nonzero,invalid_scalar_rows=invalid,
                status='RECORDED_OPPONENT_ELIXIR_IN_LEGACY_MODEL_INPUT' if known else 'OPPONENT_SCALAR_MASKED_REVIEW_OTHER_INPUTS',
                provenance='dataset.build_replay -> obs_contract.from_engine -> encode scalar 5/6; features<4 retain truth')


def metric_numbers(value,path=''):
    out=[]
    if isinstance(value,dict):
        for key,v in value.items():out.extend(metric_numbers(v,path+'/'+key))
    elif isinstance(value,list):
        for i,v in enumerate(value):out.extend(metric_numbers(v,path+'/'+str(i)))
    elif isinstance(value,(int,float)) and any(k in path.lower() for k in
            ('top1','gate_acc','gate_bal','n_play','/n','place_hit','place_1t','place_dist','emb_cosine','nll')):
        out.append(dict(field=path,value=value))
    return out


def run(out):
    import torch
    torch.set_num_threads(1)
    out.mkdir(parents=True,exist_ok=False)
    base=ROOT/'icebow/data/pipeline'
    datasets=[]
    for p in sorted(base.rglob('*.npz')):
        datasets.append(scalar_inventory(p));print('DATASET',p.name,flush=True)
    checkpoints=[]
    for p in sorted(base.rglob('*.pt')):
        item=dict(path=str(p.relative_to(ROOT)),sha256=sha(p))
        try:
            ck=torch.load(p,map_location='cpu',weights_only=True)
            args=ck.get('args',{})
            if not isinstance(args,dict):raise ValueError('Non-dict args')
            fv=int(args.get('feature_version',1))
            item.update(feature_version=fv,data=args.get('data'),epoch=ck.get('epoch'),
                        checkpoint_val_numbers=metric_numbers(ck.get('val',{})),
                        status='LEGACY_PRIVILEGED_INPUT_TRAINING_LINEAGE' if fv<4 else 'REQUIRES_PUBLIC_PROVENANCE_VERIFICATION')
            del ck
        except Exception as e:
            item.update(status='UNCLASSIFIED_DO_NOT_CALL_CLEAN',error_type=type(e).__name__)
        checkpoints.append(item)
        time.sleep(.05)
    results=[]
    for p in sorted(base.rglob('*.json')):
        if p.name.startswith(('hist_','final_')):
            raw=p.read_bytes();values=json.loads(raw)
            results.append(dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest(),
                status='PRIVILEGED_INPUT_OFFLINE_AGREEMENT_NOT_PUBLIC_INPUT_VALIDATION',
                numbers=metric_numbers(values),
                play_rate_note='n_play/n is dataset prevalence, not predicted play rate; do not quote agreement without predicted play rate.'))
    # Enumerate every RL descendant artifact without loading hundreds of weights.
    descendants=[]
    rl=ROOT/'icebow/data/bench/rl_royale'
    for p in sorted(rl.rglob('*.pt')):
        descendants.append(dict(path=str(p.relative_to(ROOT)),
            status='LEGACY_INIT_LINEAGE_REVIEW_RUN_CONFIG_FOR_RUNTIME_INPUT',
            note='Training lineage is affected; this alone does not prove hidden elixir in RL rollouts or counter-mode ghost evaluation.'))
    report=dict(status='MEASURED_PIPELINE_DATASET_AND_CHECKPOINT_INVENTORY_WITH_HISTORICAL_RELABEL',
        scope='Every current NPZ/PT under icebow/data/pipeline; every hist/final JSON there; all RL checkpoint paths under icebow/data/bench/rl_royale.',
        datasets=datasets,checkpoints=checkpoints,results=results,rl_descendants=descendants,
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'pipeline/obs_contract.py',ROOT/'pipeline/dataset.py',ROOT/'pipeline/dataset_gen.py',Path(__file__)]},
        limitations=['Numbers are preserved, not corrected into hypothetical public-only performance.',
                    'Earlier deleted/external artifacts and ad-hoc results outside these roots require additional provenance review.',
                    'Ghost/reactive records explicitly using public counter remain counter-runtime measurements of legacy-trained policies; do not relabel their runtime as hidden without evidence.',
                    'Masked opponent scalars alone do not certify all other features public.'])
    (out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Historical opponent-elixir relabel', '',
        'All listed legacy IL/pro-agreement results are **privileged-input offline measurements**, not public-input validation. Numeric artifacts are preserved. The clean gen_v3.1 retrain is a new experiment.','',
        '| Dataset | Rows | Opponent-known rows | Label |','|---|---:|---:|---|']
    for d in datasets:lines.append(f"| {d['path']} | {d.get('rows','?')} | {d.get('opponent_known_rows','?')} | {d['status']} |")
    lines+=['',f'{len(checkpoints)} pipeline checkpoints, {len(results)} numeric result artifacts and {len(descendants)} RL descendant paths are enumerated in inventory.json with individual labels.',
        '', 'Training contamination and evaluation runtime are different claims. gen_v3 and R1t ghost run manifests specify counter input. Their measured wins/HP remain counter-runtime results of policies initialized from legacy IL; they are not clean public-only training results.',
        '', 'Affected headline: HANDOFF gen_v3 v3val cell 0.1973/card 0.6444/gate_bal 0.7626 versus gen_v1 0.2071/0.6457/0.7669, n_play 3796, is privileged-input agreement. Predicted play rate is absent from that headline: do not present those figures alone as clean policy quality.',
        '', 'Each saved checkpoint val and hist/final metric is listed verbatim by JSON pointer in inventory.json. Dataset n_play/n is prevalence, not predicted play rate. Other scratchpad/ad-hoc agreement claims require this same label when they use these datasets; their full textual inventory is still outstanding.',
        '', 'Live reader/u0155 remains unchanged. This audit does not claim the live process reads hidden opponent elixir.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(datasets=len(datasets),checkpoints=len(checkpoints),results=len(results),rl_descendants=len(descendants))),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    lower_own_priority();run(a.out)
