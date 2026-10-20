import copy
from types import SimpleNamespace as NS
import numpy as np
import pytest
from pipeline.projectile_observation import objects, sim_objects, tokens_from_objects, recording_tokens
from pipeline.projectile_motion import ProjectileMotion
from pipeline.public_observation import _native_ids
from pipeline.projectile_observation import require_complete_training,PROJECTILE_COLS,EFFECT_COLS


@pytest.mark.parametrize('gap', [1, 10])
@pytest.mark.parametrize('side', [0, 1])
def test_actual_three_adapters_share_catalog_tti_and_area_lifetime(gap, side):
    gid={'rocket':1,'poison':2}; ids=_native_ids()
    motions={s:ProjectileMotion(catalog_fallback=True) for s in ('native','sim','reader')}
    frames=[]
    for tick,x in ((0,3000),(gap,3350)):
        p=dict(side=1,x=x,y=21000,target_x=4500,target_y=6500,card_id=ids['rocket',0])
        e=dict(side=0,x=4000,y=7000,card_id=ids['poison',0],remaining_ms=1000)
        native=dict(tick=tick,public_objects=dict(projectiles=[dict(p,time_to_impact_ms=999999)],area_effects=[dict(e,source_remaining_ms=1000)]))
        reader=dict(projectiles=[p],effects=[e])
        state=NS(projectiles=[],spells=[NS(team=1,card_id=3,motion=0,x=x*1000,y=21000000,aim_x=4500000,aim_y=6500000,delay_ticks=7),
            NS(team=0,card_id=4,motion=4,x=4000000,y=7000000,delay_ticks=20)])
        sim=sim_objects(state,{3:'Rocket',4:'Poison'},1000)
        encoded=[]
        for source,frame in [('native',native),('sim',sim),('reader',reader)]:
            frame['players']=[dict(elixir=999,hand=['hidden'])]*2
            observed=motions[source].update(objects(frame,source=source),tick)
            encoded.append(tokens_from_objects(observed,side,gid))
        for other in encoded[1:]:
            for key in other:np.testing.assert_array_equal(other[key],encoded[0][key])
        frames.append(native)
    built=recording_tokens(dict(frames=frames),[gap],[side],['rocket','poison'],{})
    for key in built:np.testing.assert_array_equal(built[key][0],encoded[0][key])
    assert encoded[0]['projectiles'][0,-1]==1
    assert encoded[0]['effects'][0,-2:].tolist()==[1,1]


def test_multi_stage_motion_and_no_future_rewrite():
    motion=ProjectileMotion(catalog_fallback=True)
    def row(x):return dict(projectiles=[('the-log',0,x,0,5000,0,None)],effects=[])
    first=motion.update(row(0),0)
    assert first['projectiles'][0][-1] is None
    second=motion.update(row(1000),10)
    assert second['projectiles'][0][-1]==2000
    motion.update(row(4900),20)
    assert second['projectiles'][0][-1]==2000


@pytest.mark.parametrize('card,name', [('lightning','Lightning'),('graveyard','Graveyard'),('lumberjack','Lumberjack'),('void','Void')])
def test_unavailable_area_lifetimes_masked_identically(card,name):
    cid=_native_ids()[card.replace('-','_'),0]
    native=dict(public_objects=dict(area_effects=[dict(side=0,card_id=cid,x=0,y=0,source_remaining_ms=900)]))
    reader=dict(effects=[dict(side=0,card_id=cid,x=0,y=0,remaining_ms=900)])
    sim=dict(effects=[dict(side=0,name=name,x=0,y=0,remaining_ms=None)])
    encoded=[]
    for source,frame in [('native',native),('reader',reader),('sim',sim)]:
        stats={};encoded.append(tokens_from_objects(objects(frame,source=source),0,{card:1},stats=stats))
        assert stats['effects_capability_masked']==1
    for e in encoded[1:]:np.testing.assert_array_equal(e['effects'],encoded[0]['effects'])


def test_subtick_area_clock_and_missing_target_mask():
    cid=_native_ids()['poison',0]
    native=dict(public_objects=dict(area_effects=[dict(side=0,card_id=cid,x=0,y=0,source_remaining_ms=981)]))
    sim=dict(effects=[dict(side=0,name='Poison',x=0,y=0,remaining_ms=1000)])
    a=tokens_from_objects(objects(native,source='native'),0,{'poison':1})
    b=tokens_from_objects(objects(sim,source='sim'),0,{'poison':1})
    np.testing.assert_array_equal(a['effects'],b['effects'])
    projectile=dict(projectiles=[('rocket',0,0,0,None,None,None)],effects=[])
    encoded=tokens_from_objects(ProjectileMotion(catalog_fallback=True).update(projectile,0),0,{'rocket':1})
    assert encoded['projectiles'][0,4:].tolist()==[-1,-1,-1,0]


def test_only_declared_area_capability_masks_pass_training_gate():
    meta=dict(feature_version=4,projectile_cols=list(PROJECTILE_COLS),effect_cols=list(EFFECT_COLS),
        stats=dict(projectiles_observed=2,projectiles_motion_estimated=1,effects_observed=3,effects_missing_timing=2,effects_capability_masked=2))
    require_complete_training(meta,allow_causal_tti_unknowns=True)
    meta['stats']['effects_missing_timing']=3
    with pytest.raises(ValueError,match='incomplete'):require_complete_training(meta,allow_causal_tti_unknowns=True)


def test_lead_r7_rare_overflow_tolerance_boundary_is_preserved():
    meta=dict(feature_version=4,projectile_cols=list(PROJECTILE_COLS),effect_cols=list(EFFECT_COLS),
        stats=dict(projectiles_observed=2,projectiles_motion_estimated=1,effects_observed=10000,effects_overflow=1))
    require_complete_training(meta,allow_causal_tti_unknowns=True)
    meta['stats']['effects_overflow']=2
    with pytest.raises(ValueError,match='incomplete'):require_complete_training(meta,allow_causal_tti_unknowns=True)


def _calibration_module():
    import importlib.util
    from pathlib import Path
    path=Path(__file__).resolve().parents[2]/'scratchpad/gauntlet/L70/gen_v31/public_xbow_calibrate.py'
    spec=importlib.util.spec_from_file_location('calibrate',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_calibrated_reach_pass_and_overlap_negative_control():
    m=_calibration_module()
    rows=[dict(hit=True,distance_milli=13038,own_y=.609375)]*20+[dict(hit=False,distance_milli=15000,own_y=.703125)]*20
    report=m.calibrate(rows)
    assert report['status']=='R1_REVISED_CALIBRATION_PASS' and report['modal_offensive']
    bad=rows+[dict(hit=False,distance_milli=13038,own_y=.609375)]*20
    assert m.calibrate(bad)['status']=='STOP_TELL_LEAD'
    # Class imbalance cannot conceal a false-negative-only rule.
    assert m.calibrate([dict(hit=False,distance_milli=13038,own_y=.609375)]*100)['status']=='STOP_TELL_LEAD'


def test_calibration_unknown_controller_is_not_a_miss():
    m=_calibration_module()
    rec=dict(tag='missing',frames=[dict(tick=100,towers=[[1,'princess',0,3500,25500,100]],entities=[],public_objects={})],
             log=[dict(tick=100,side=0,card='Xbow',x=3500,y=12500,accepted=True)])
    row=m.inspect(rec)[0]
    assert row['hit'] is None and row['excluded']=='controller_not_found'


def test_skipped_terminal_plays_are_never_labels():
    from pipeline.public_outcomes import label_recording
    skipped=[dict(tick=3526,side=1,card='x-bow',skipped='episode already terminal'),
             dict(tick=3530,side=1,card='Rocket',skipped='episode already terminal')]
    rec=dict(tag='skipped',frames=[],log=skipped)
    assert _calibration_module().inspect(rec)==[]
    assert label_recording(rec)==dict(rockets=[],xbows=[],plays=[])


def test_outcome_tiebreak_evidence_is_not_silently_false():
    from pipeline.public_outcomes import label_recording
    from pipeline.tests.test_public_delivery import fixture
    rec=fixture()
    assert label_recording(rec,normalized=True)['rockets'][0]['tiebreak'] is None
    rec['final']=dict(tiebreaker=True)
    row=label_recording(rec,normalized=True)['rockets'][0]
    assert row['tiebreak'] is True and row['seconds_left']==175
    rec['final']=dict(terminated=True,tick=5990)
    assert label_recording(rec,normalized=True)['rockets'][0]['tiebreak'] is False


def test_public_aim_reconstruction_is_cadence_invariant_without_area():
    from pipeline.public_outcomes import label_recording
    from pipeline.tests.test_public_delivery import fixture
    rec=fixture()
    for frame in rec['frames']:
        frame['areas']=[]
        for q in frame['projectiles']:q['y']=25500-(120-frame['tick'])*350
    for gap in (1,2,4,10):
        sparse=dict(rec,frames=[f for f in rec['frames'] if f['tick']%gap==0])
        row=label_recording(sparse,normalized=True)['rockets'][0]
        assert row==label_recording(sparse,normalized=True,reconstruct_rocket_landing=True)['rockets'][0]
        assert row['landing_source']=='public_aim_catalog_speed'
        assert row['landing_tick']==120 and row['landing_point']==[3500,25500]
        assert row['tower_rocket'] and row['defensive_rocket']
        assert row['tower_hits'][0]['hp_confirmed']
        # The old last-observation fallback is a negative control for this
        # regression: it must disagree when the last frame precedes impact.
        old=label_recording(sparse,normalized=True,reconstruct_rocket_landing=False)['rockets'][0]
        assert old['landing_tick']<row['landing_tick']
        from pipeline.behaviour_telemetry import BehaviourTelemetry
        from pipeline.public_outcomes import summarize
        telemetry=BehaviourTelemetry()
        telemetry.frames=sparse['frames'];telemetry.plays=sparse['log']
        assert telemetry.result(0)==summarize(sparse,0,normalized=True,
            labels=label_recording(sparse,normalized=True,reconstruct_rocket_landing=True))


def test_rocket_first_combo_covers_entire_flight():
    from pipeline.public_outcomes import combo_orders
    p=dict(card='Tornado',side=0,tick=110,x=3000,y=20000)
    assert combo_orders([p],0,100,190,p)==(True,False)
    assert combo_orders([dict(p,tick=90)],0,100,190,p)==(False,False)
    assert combo_orders([dict(p,tick=90)],0,100,130,p)==(False,True)


def test_native_crown_entities_are_not_troop_targets():
    from pipeline.public_outcomes import normalize
    frame=dict(tick=10,towers=[[1,'princess','right',14500,25500,3052,3052]],
        entities=[[1,14500,25500,'-1',3052,3052,13,-1,5000005],
                  [1,14000,25000,'Knight',100,100,1,26000000,72]],public_objects={})
    result=normalize(frame)
    assert [e['id'] for e in result['bodies']]==[72]
    assert len(result['towers'])==1


def test_multi_rocket_history_survives_overtime_boundary():
    from pipeline.public_outcomes import label_recording
    from pipeline.tests.test_public_delivery import fixture
    frames=[];plays=[]
    for shift in (3400,3500):
        rec=fixture()
        for frame in rec['frames']:
            frame['tick']+=shift;frame['towers'][0]['hp']=1000;frames.append(frame)
        p=rec['log'][0];p['tick']+=shift;plays.append(p)
    rows=label_recording(dict(tag='cross-phase',frames=frames,log=plays),normalized=True)['rockets']
    assert [r['phase'] for r in rows]==['regulation','overtime']
    assert [r['tower_hits'][0]['prior_rockets'] for r in rows]==[0,1]
    assert rows[1]['tower_hits'][0]['gap_s']==5
