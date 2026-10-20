import json
from pathlib import Path
import uuid
import numpy as np
import pytest
import torch
from pipeline.dataset_spool import ArraySpool, ReplaySpool, load_mapped
from pipeline.train_gen import GenRows, losses
from pipeline.model_gen import GenModel
from pipeline import dataset_gen

ROOT = Path(__file__).resolve().parents[2]


def own_dir():
    # tempfile.mkdtemp has incompatible ACLs in this managed Windows sandbox.
    p = ROOT/'icebow/data/pipeline/gen_v31_s0'/('test_'+uuid.uuid4().hex)
    p.mkdir(parents=True); return p


def test_spooled_rows_preserve_order_and_array_bytes():
    path = own_dir(); spool = ReplaySpool(path)
    original = [dict(a=np.arange(6,dtype=np.float32).reshape(2,3)+i) for i in range(2)]
    for r in original: spool.append(r)
    arrays = ArraySpool(path)
    for old,new in zip(original,spool):
        np.testing.assert_array_equal(old['a'],new['a']); arrays.append('a',new['a'])
    np.testing.assert_array_equal(np.concatenate([r['a'] for r in original]), arrays.arrays()['a'])
    with pytest.raises(ValueError): arrays.append('a',np.ones((1,4),np.float32))


def test_mapped_dataset_batch_forward_and_weighted_gradient_match():
    sample = ROOT/'.foreman/codex_autopilot/runs/native_full_sample.json'
    if not sample.exists(): pytest.skip('local native replay fixture unavailable')
    # preflight20.npz predates own_ability despite declaring version4. Build
    # the actual current contract; never invent a missing public input.
    directory = own_dir(); corpus = directory/'corpus'; corpus.mkdir()
    (corpus/'replay_sample.json').write_bytes(sample.read_bytes())
    path = directory/'current.npz'
    built = dataset_gen.build([corpus], path, feature_version=4, workers=1, log=None)
    assert built['failed'] == 0 and built['rows'] >= 12
    with np.load(path,allow_pickle=False) as z:
        expected={k:z[k] for k in z.files if k!='meta'}
    assert 'own_ability' in expected
    mapped,meta=load_mapped(path,own_dir()/'cache')
    for k in expected: np.testing.assert_array_equal(expected[k],mapped[k])
    ids=np.arange(12); a=GenRows(expected,ids,'cpu').batch(ids); b=GenRows(mapped,ids,'cpu').batch(ids)
    for k in a: assert torch.equal(a[k],b[k])
    torch.manual_seed(3)
    model=GenModel(d=16,layers=1,d_c=8,n_cards=len(meta['card_vocab']),feature_version=4)
    model.eval()
    for batch in (a,b):
        batch['rocket_context_probability']=torch.linspace(0,1,len(ids))
    loss,_=losses(model,a,True,'lattice',2)
    assert torch.isfinite(loss)
    loss.backward()
    assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
    gradients={k:p.grad.clone() for k,p in model.named_parameters() if p.grad is not None}
    model.zero_grad(set_to_none=True)
    mapped_loss,_=losses(model,b,True,'lattice',2)
    assert torch.equal(loss,mapped_loss)
    mapped_loss.backward()
    assert gradients.keys()=={k for k,p in model.named_parameters() if p.grad is not None}
    for k,p in model.named_parameters():
        if p.grad is not None:
            assert torch.equal(gradients[k],p.grad), k
