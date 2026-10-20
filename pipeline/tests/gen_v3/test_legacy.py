"""Pre-edit source snapshots, not git, are the legacy byte-identity oracle."""
import copy
import sys
import types
from pathlib import Path
import numpy as np
import torch

from pipeline import dataset_gen as D, e1_eval as E, live_gen as L, model_gen as M
from pipeline.tests.test_live_mem import FRAME
from pipeline.tests.test_obs_contract import raw_obs, ENGINE_DECK
from pipeline import obs_contract as O, engine_play as EP
from pipeline.dataset import _past

ROOT=Path(__file__).resolve().parents[3]
CHECKPOINT=ROOT/'icebow/data/bench/rl_royale/rseries_r1/rseries_r1_u0155.pt'


def baseline(name):
    key='pipeline._gen_v3_baseline_'+name
    if key not in sys.modules:
        mod=types.ModuleType(key)
        mod.__file__=str(ROOT/'pipeline'/f'{name}.py')
        mod.__package__='pipeline'
        sys.modules[key]=mod
        source=(Path(__file__).parent/'baseline'/f'{name}.py.txt').read_text()
        exec(compile(source,mod.__file__,'exec'),mod.__dict__)
    return sys.modules[key]


def same(a,b):
    assert set(a)==set(b)
    for k in a:
        x,y=a[k],b[k]
        if isinstance(x,torch.Tensor):
            x,y=x.detach().cpu().numpy(),y.detach().cpu().numpy()
        if isinstance(x,np.ndarray):
            assert x.shape==y.shape and x.dtype==y.dtype and x.tobytes()==y.tobytes(),k


def test_default_dataset_and_explicit_v2_byte_identity():
    path=str(sorted((ROOT/'scratchpad/gauntlet/ext/corpus_v6/icebow').glob('replay_*.json'))[0])
    old=baseline('dataset_gen').replay_rows(path)
    for version in (1,2):
        same(old,D.replay_rows(path,feature_version=version))


def test_real_checkpoint_live_rows_and_forward_byte_identity():
    old=baseline('live_gen').GenPilot(CHECKPOINT,device='cpu')
    new=L.GenPilot(CHECKPOINT,device='cpu')
    assert new.feature_version<3
    for t in (206,230,260):
        f=copy.deepcopy(FRAME);f['game_tick']=t
        old.observe(f);new.observe(f)
        a,_=old.row(f);b,_=new.row(f);same(a,b)
        with torch.no_grad():
            same(old.model(a),new.model(b))


def test_real_checkpoint_e1_row_heads_and_model_forward_byte_identity():
    st=torch.load(CHECKPOINT,map_location='cpu'); args=st['args']
    old=baseline('model_gen').GenModel(d=args['d'],layers=args['layers'],d_c=st['d_c'],n_cards=len(st['card_vocab'])).eval()
    new=M.GenModel(d=args['d'],layers=args['layers'],d_c=st['d_c'],n_cards=len(st['card_vocab'])).eval()
    old.load_state_dict(st['model']);new.load_state_dict(st['model'])
    pol0=baseline('e1_eval').GenPolicy(old,st['card_vocab']);pol1=E.GenPolicy(new,st['card_vocab'])
    deck=O.load_deck('icebow');state=raw_obs(0)
    bs=O.from_engine(EP.compact_raw(state),0,deck,engine_deck=ENGINE_DECK,unmapped=set())
    tok,mask,sc=O.to_tokens(bs)
    args=(tok,mask,sc,_past([],state['tick']),*pol0.slot_ident(ENGINE_DECK,{i:i for i in range(8)}))
    a,b=pol0.row(*args),pol1.row(*args);same(a,b)
    ea,ha,pa,ma=pol0.forward_batch([a]);eb,hb,pb,mb=pol1.forward_batch([b])
    same(ea,eb);same(ha,hb);assert pa==pb and ma.tobytes()==mb.tobytes()
    with torch.no_grad():
        slot=torch.tensor([0]);assert torch.equal(pol0.cell_logits(ea,slot),pol1.cell_logits(eb,slot))


def test_seeded_model_initialization_unchanged():
    torch.manual_seed(81);a=baseline('model_gen').GenModel(d=16,layers=1,d_c=8)
    torch.manual_seed(81);b=M.GenModel(d=16,layers=1,d_c=8)
    same(a.state_dict(),b.state_dict())
