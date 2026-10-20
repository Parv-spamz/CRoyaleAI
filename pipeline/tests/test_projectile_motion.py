import copy
import numpy as np
import pytest

from pipeline.projectile_motion import ProjectileMotion
from pipeline.projectile_observation import recording_tokens
from pipeline.public_observation import PublicObserver, _native_ids


def obs(x, *, extra=False):
    rows = [('rocket', 1, x, 0, 1000, 0, None)]
    return dict(projectiles=rows*2 if extra else rows, effects=[])


def test_causal_linear_motion_same_tick_and_reset():
    m = ProjectileMotion()
    assert m.update(obs(0), 0)['projectiles'][0][-1] is None
    assert m.update(obs(100), 2)['projectiles'][0][-1] == 900
    assert m.update(obs(100), 2)['projectiles'][0][-1] == 900
    assert m.update(obs(200), 4)['projectiles'][0][-1] == 800
    assert m.update(obs(0), 0)['projectiles'][0][-1] is None


@pytest.mark.parametrize('x,tick,extra', [(0, 2, False), (-100, 2, False), (100, 21, False), (100, 2, True)])
def test_unknown_when_motion_not_identifiable(x, tick, extra):
    m = ProjectileMotion(); m.update(obs(0), 0)
    assert m.update(obs(x, extra=extra), tick)['projectiles'][0][-1] is None


def test_disappearance_and_ambiguity_break_tracks():
    m = ProjectileMotion(); m.update(obs(0), 0)
    m.update(dict(projectiles=[], effects=[]), 1)
    assert m.update(obs(100), 2)['projectiles'][0][-1] is None
    m.update(obs(200, extra=True), 4)
    assert m.update(obs(300), 6)['projectiles'][0][-1] is None


@pytest.mark.parametrize('side', [0, 1])
def test_dataset_sim_reader_causal_parity_and_future_privacy(side):
    cid = _native_ids()['rocket', 0]
    frames = [dict(tick=t, entities=[], projectiles=[[1,x,0,1000,0,'Rocket']], area_effects=[])
              for t,x in [(0,0),(2,100),(4,200)]]
    rec = dict(frames=frames)
    expected = recording_tokens(rec,[2,4],[side,side],['rocket'],{})['projectiles']
    for source in ('native','sim','reader'):
        observer = PublicObserver(side)
        for f in frames:
            if source == 'native':
                frame = copy.deepcopy(f)
            else:
                p=f['projectiles'][0]
                frame=dict(tick=f['tick'],game_tick=f['tick'],entities=[],effects=[],projectiles=[
                    dict(side=1,x=p[1],y=0,target_x=1000,target_y=0,name='Rocket',card_id=cid)])
            frame['players']=[dict(elixir=999,hand=['hidden'])]*2
            observer.update(frame,source=source)
        for i,t in enumerate((2,4)):
            np.testing.assert_array_equal(observer.features(t,{'rocket':1})['projectiles'],expected[i])
        # A later observation cannot rewrite earlier estimates.
        frame = dict(frame, tick=6,game_tick=6,projectiles=[])
        observer.update(frame,source=source)
        np.testing.assert_array_equal(observer.features(2,{'rocket':1})['projectiles'],expected[0])
    assert expected[0,0,-2] == pytest.approx(900/350*.05)


def test_recorded_timing_preserved_and_nonfinite_rejected():
    m=ProjectileMotion(); m.update(obs(0),0)
    row=obs(100); row['projectiles'][0]=(*row['projectiles'][0][:-1],42)
    assert m.update(row,2)['projectiles'][0][-1]==42
    with pytest.raises(ValueError): m.update(obs(float('nan')),4)
