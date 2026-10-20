"""HEAD is the pre-continuation oracle; read-only Git, one CPU thread runner."""
import copy
import subprocess
import types
import sys
from pathlib import Path
import numpy as np
import pytest
import torch
from pipeline import dataset_gen as D, model_gen as M, train_gen as T, live_gen as L
from pipeline.tests.gen_v3.test_legacy import same
from pipeline.tests.test_model_gen import toy
from pipeline.tests.test_live_mem import FRAME

ROOT = Path(__file__).resolve().parents[2]


def head(name):
    key = 'pipeline._v31_head_'+name
    if key not in sys.modules:
        mod = types.ModuleType(key); mod.__package__ = 'pipeline'
        mod.__file__ = str(ROOT/'pipeline'/f'{name}.py')
        source = subprocess.check_output(['git','show','HEAD:pipeline/'+name+'.py'], cwd=ROOT)
        sys.modules[key] = mod
        exec(compile(source, mod.__file__, 'exec'), mod.__dict__)
    return sys.modules[key]


@pytest.mark.parametrize('version', [1, 2, 3])
def test_dataset_init_inference_and_loss_bytes(version):
    sample = str(ROOT/'.foreman/codex_autopilot/runs/native_full_sample.json')
    a = head('dataset_gen').replay_rows(sample, feature_version=version)
    b = D.replay_rows(sample, feature_version=version)
    assert 'error' not in a and 'error' not in b
    same(a, b)
    rows = toy(16)['gen']
    if version == 3:
        rows.update(unit_form=np.zeros(len(rows['tok']), np.int64),
                    opp_past=np.tile([0, 3, -1, -1, -1], (16, 3, 1)).astype(np.float32))
    batch = T.GenRows(rows, np.arange(16), 'cpu').batch(np.arange(16))
    torch.manual_seed(37); old = head('model_gen').GenModel(d=16, layers=1, d_c=8, n_cards=9, feature_version=version).eval()
    torch.manual_seed(37); new = M.GenModel(d=16, layers=1, d_c=8, n_cards=9, feature_version=version).eval()
    same(old.state_dict(), new.state_dict())
    with torch.no_grad():
        same(old(batch), new(batch))
        for mirrored in (False, True):
            x, xp = head('train_gen').losses(old, batch, mirrored, grid='lattice')
            y, yp = T.losses(new, batch, mirrored, grid='lattice')
            assert torch.equal(x, y) and xp == yp


@pytest.mark.parametrize('checkpoint', ['icebow/data/bench/rl_royale/rseries_r1/rseries_r1_u0155.pt',
                                      'icebow/data/pipeline/gen_v3_s0/gen_s0.pt'])
def test_real_legacy_live_inputs_and_decisions(checkpoint):
    a = head('live_gen').GenPilot(ROOT/checkpoint)
    b = L.GenPilot(ROOT/checkpoint)
    for tick in (206, 230):
        frame = copy.deepcopy(FRAME); frame['game_tick'] = tick
        a.observe(frame); b.observe(frame)
        x, _ = a.row(frame); y, _ = b.row(frame); same(x, y)
        with torch.no_grad(): same(a.model(x), b.model(y))


@pytest.mark.parametrize('version', [1, 2, 3])
def test_head_simulation_rows_actions_trajectory_and_rng(version):
    from pipeline import e1_eval as E, royale_env as RE, rl_royale as RL
    from pipeline.tests.gen_v3.test_sim_integration import policy, NAMES
    from pipeline.tests.test_rl_gen import _cfg
    from pipeline.tests.test_royale_forms import digest
    oldE, oldRE = head('e1_eval'), head('royale_env')
    p = policy(version); op = oldE.GenPolicy(p.model, list(p.gid))
    spec=dict(tag='head-parity',learner_side=0,learner_deck=NAMES,opp_deck=NAMES,seed=3,opp={'id':'old'})
    cfg=_cfg(obs='live',extrapolate_ticks=26,action_delay_ticks=26,entry_index=0)
    a=oldE.SelfPlayMatch(oldRE.RoyaleSelfPlayEnv(forms_mode='deck',tail_cap=400),spec,0,cfg,cfg,op,op)
    b=E.SelfPlayMatch(RE.RoyaleSelfPlayEnv(forms_mode='deck',tail_cap=400),spec,0,cfg,cfg,p,p)
    while True:
        da,db=a.due(),b.due()
        assert len(da)==len(db)
        if not da: break
        for sa,sb in zip(da,db):
            sa.prepare();sb.prepare()
            ra,rb=sa.gen_row(op),sb.gen_row(p);same(ra,rb)
            ea,ha,pa,ma=op.forward_batch([ra]);eb,hb,pb,mb=p.forward_batch([rb])
            same(ea,eb);same(ha,hb);assert pa==pb and ma.tobytes()==mb.tobytes()
            xa=sa.decide_row(op,ea,ha,pa[0],ma[0]);xb=sb.decide_row(p,eb,hb,pb[0],mb[0])
            assert digest(xa)==digest(xb)
            sa.apply(pa[0],xa);sb.apply(pb[0],xb)
            assert sa.rng_obs.bit_generator.state==sb.rng_obs.bit_generator.state
            assert sa.rng_behave.bit_generator.state==sb.rng_behave.bit_generator.state
    assert digest(a.result())==digest(b.result())
    assert a.env.core.save_state()==b.env.core.save_state()
    results=[a.result(),b.result()]
    x,xs=head('rl_royale').collate(results,advantage='gae')
    y,ys=RL.collate(results,advantage='gae')
    same(x,y);assert xs==ys
