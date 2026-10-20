"""Owner-requested live-loader compatibility, no ADB or gameplay."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import torch
import numpy as np

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from pipeline.model_gen import load_model,GenModel
from pipeline.train_rocket_curriculum import load_subset
from pipeline.eval_gen import GenRows
from pipeline.model_gen import mirror_gen


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    assert not (HERE/'loader_verified.json').exists()
    torch.set_num_threads(1)
    frozen=HERE.parent/'development_iteration_5/tower_model.py'
    spec=importlib.util.spec_from_file_location('frozen_tower_reference',frozen)
    reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
    checkpoint=ROOT/'icebow/data/bench/development_iteration_5_20261005/tower_spatial_v7/candidate.pt'
    h=sha(checkpoint)
    assert h=='2feffe4f0990d93721ceb0b6661338f52e7f935e85b80e29535ea713ad6569a0'
    actual,state=load_model(checkpoint,'cpu');expected,_=reference.load_checkpoint(checkpoint,'cpu')
    actual.eval();expected.eval()
    assert all(torch.equal(v,expected.state_dict()[k]) for k,v in actual.state_dict().items())
    with np.load(ROOT/'icebow/data/bench/development_iteration_1_20261005/indices.npz') as z:
        ids=z['train'][:128]
    data,meta=load_subset(ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz',ids)
    rows=GenRows(data,np.arange(len(ids)),'cpu')
    compared=0
    with torch.inference_mode():
        for begin in range(0,128,16):
            b=rows.batch(np.arange(begin,begin+16))
            for model in (actual,expected):model.eval()
            ea,ee=actual.encode_gen(b),expected.encode_gen(b)
            for k in ea:assert torch.equal(ea[k],ee[k]),k
            ha,he=actual.heads_gen(ea,b),expected.heads_gen(ee,b)
            for k in ha:assert torch.equal(ha[k],he[k]),k
            for cid in (b['card'],torch.full_like(b['card'],meta['card_vocab'].index('rocket'))):
                assert torch.equal(actual.cell_logits_gen(ea,cid,b['form']),expected.cell_logits_gen(ee,cid,b['form']))
            compared+=len(b['card'])
    legacy_paths=[ROOT/'icebow/data/bench/development_iteration_1_20261005/ordinary_v5/candidate_portable.pt',
                  ROOT/'icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt']
    for path in legacy_paths:
        m,st=load_model(path,'cpu');a=st['args']
        baseline=GenModel(d=int(a['d']),layers=int(a['layers']),d_c=int(st['d_c']),
            n_cards=len(st['card_vocab']),feature_version=int(a.get('feature_version',1)))
        baseline.load_state_dict(st['model']);m.eval();baseline.eval()
        with torch.inference_mode():
            ea,ee=m.encode_gen(b),baseline.encode_gen(b)
            for k in ea:assert torch.equal(ea[k],ee[k])
            ha,he=m.heads_gen(ea,b),baseline.heads_gen(ee,b)
            for k in ha:assert torch.equal(ha[k],he[k])
    corruptions=[]
    wrong=copy.deepcopy(state);wrong['architecture']='unknown';corruptions.append(wrong)
    wrong=copy.deepcopy(state);wrong['args']['feature_version']=6;corruptions.append(wrong)
    wrong=copy.deepcopy(state);wrong['model']['tower_spatial_xy'][0,0]+=.1;corruptions.append(wrong)
    wrong=copy.deepcopy(state);del wrong['model']['tower_spatial_spread.weight'];corruptions.append(wrong)
    with tempfile.TemporaryDirectory() as folder:
        for i,wrong in enumerate(corruptions):
            p=Path(folder)/f'bad{i}.pt';torch.save(wrong,p)
            try:load_model(p,'cpu')
            except (ValueError,RuntimeError,KeyError):pass
            else:raise AssertionError('Malformed extension accepted')
    assert sha(checkpoint)==h
    result=dict(complete=True,checkpoint=str(checkpoint.relative_to(ROOT)),checkpoint_sha256=h,
        native_training_rows=compared,exact_reference_tensors_and_predictions=True,
        legacy_controls=len(legacy_paths),malformed_controls=len(corruptions),
        frozen_reference_sha256=sha(frozen),sources={str(p.relative_to(ROOT)):sha(p) for p in
        [Path(__file__),ROOT/'pipeline/model_gen.py',ROOT/'pipeline/model_tower.py']},
        model_weights_changed=False,live_started=False)
    (HERE/'loader_verified.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result));print('TOWER_LIVE_LOADER_VERIFIED')


if __name__=='__main__':main()
