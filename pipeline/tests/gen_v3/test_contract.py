"""CPU-only gen_v3 contract checks. No training, ADB, or live matches."""
import copy
import json
from pathlib import Path
from collections import Counter

import numpy as np
import pytest
import torch

from pipeline import dataset_gen as D, obs_contract as O
from pipeline.dataset import PAST_K, OPP_PAST_K
from pipeline.model_gen import GenModel, load_model
from pipeline.train_gen import GenRows, losses
from pipeline.tests.test_model_gen import toy

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "scratchpad/gauntlet/ext/corpus_v6/icebow"


def recording():
    return json.loads(sorted(CORPUS.glob("replay_*.json"))[0].read_text())


def test_cycle_is_per_card_per_side_and_refusals_do_not_count():
    r = {"final_decks": {"0": ["Knight@evolution", "Witch@evolution", "MiniPekka@hero"],
                          "1": ["Knight@evolution"]}, "log": []}
    seq = [(0, "knight", True), (0, "witch", True), (1, "knight", True),
           (0, "knight", False), (0, "knight", True), (0, "witch", True),
           (0, "knight", True), (0, "knight", True), (0, "mini-pekka", True)]
    for i, (side, card, accepted) in enumerate(seq):
        r["log"].append(dict(tick=i+1, play_index=i, side=side, card=card, accepted=accepted, x=9000,y=10000))
    assert [p["form"] for p in D.played_forms(r)] == [0,0,0,0,1,1,0,2]
    assert D.evolution_cycles()["witch"] == 1
    assert PAST_K == OPP_PAST_K == 3


def test_opponent_history_strict_time_and_both_side_mirrors():
    plays = [dict(tick=t, side=s, card="knight", form=t%3, x=3000, y=8000, accepted=True)
             for t,s in [(10,0),(20,1),(30,1),(40,1),(50,1)]]
    p = D.opponent_past(plays, 50, 0, {"knight":1})
    np.testing.assert_array_equal(p[:,0], [1,1,1])
    np.testing.assert_allclose(p[:,4], [.5,1,1.5])
    np.testing.assert_allclose(p[:,2:4], [[1/6,.75]]*3)
    q = D.opponent_past(plays,50,1,{"knight":1})
    np.testing.assert_allclose(q[0,2:4],[5/6,.25])
    np.testing.assert_array_equal(q[1:],[ [0,3,-1,-1,-1] ]*2)


def test_real_recording_heroes_and_evo_cohorts():
    r=recording(); st={}; tagged=D.tag_recording(r,D.played_forms(r),st)
    counts=Counter()
    for source in ("frames","play_frames"):
        for f in tagged[source]:
            for e, form in zip(f["entities"],f["unit_forms"]):
                if e[3] == "MiniPekka" and e[4]>0:
                    assert form == 2
                if form:
                    counts[e[3],form]+=1
    assert counts == {("MiniPekka",2):30,("ElectroDragon",1):15,("BabyDragon",1):23,("Knight",1):29}
    assert {len(e) for f in r["play_frames"] for e in f["entities"]} == {7}
    assert {e[6] for f in r["play_frames"] for e in f["entities"]} <= {12,13,14,15}


def test_real_hero_goblin_flag_and_summons():
    r=json.loads((CORPUS / "replay_002YLQQ0J90P.json").read_text()); st={}
    r=D.tag_recording(r,D.played_forms(r),st); hp=Counter()
    for source in ("frames","play_frames"):
        for f in r[source]:
            for e,form in zip(f["entities"],f["unit_forms"]):
                if e[0] == 0 and e[3] == "Goblins" and e[4]>0:
                    assert form == 2
                    hp[e[5]]+=1
    assert hp[202]>0 and hp[2560]>0


def test_ambiguous_overlap_is_base_and_future_does_not_change_past():
    r={"final_decks":{"0":["Knight@evolution"]},"log":[],"frames":[],"play_frames":[]}
    for i,t in enumerate([10,100,200,250]):
        r["log"].append(dict(tick=t,play_index=i,side=0,card="knight",accepted=True,x=9000,y=10000))
    for t, present in [(0,False),(180,False),(220,True),(240,True),(260,True)]:
        r["frames"].append(dict(tick=t,entities=[[0,9000,10000,"Knight",100,100]] if present else []))
    out=D.tag_recording(r,D.played_forms(r),{})
    assert [f["unit_forms"] for f in out["frames"]] == [[],[],[1],[1],[0]]
    short=copy.deepcopy(r);short["log"]=short["log"][:3];short["frames"]=short["frames"][:4]
    assert D.tag_recording(short,D.played_forms(short),{})["frames"] == out["frames"][:4]


def test_explicit_ids_retain_birth_form_through_overlap():
    r={"final_decks":{"0":["Knight@evolution"]},"log":[],"frames":[],"play_frames":[]}
    for i,t in enumerate([10,100,200,250]):
        r["log"].append(dict(tick=t,play_index=i,side=0,card="knight",accepted=True,x=9000,y=10000))
    r["frames"]=[dict(tick=180,entities=[],entity_ids=[]),
       dict(tick=220,entities=[[0,9000,10000,"Knight",100,100]],entity_ids=[99]),
       dict(tick=270,entities=[[0,9000,10000,"Knight",100,100],[0,9100,10000,"Knight",100,100]],entity_ids=[99,100])]
    out=D.tag_recording(r,D.played_forms(r),{})
    assert out["frames"][1]["unit_forms"] == [1]
    assert out["frames"][2]["unit_forms"] == [1,0]


def test_sim_bits_and_native_form_ids_are_separate_namespaces():
    for flags,form in [(0,0),(8,1),(16,2),(-1,0)]:
        assert O.entity_form(dict(status_flags=flags,card_id=26000000)) == form
    catalog=json.loads((ROOT/'research/ext/cr-native-sandbox/native_core/data/live_card_catalog.json').read_text())
    for c in catalog["cards"]:
        for key,f in [("card_id",0),("evolution_form_id",1),("hero_form_id",2)]:
            if c.get(key) is not None:
                assert O.catalog_card_form(c[key]) == (c["display_name"],f)


def test_v3_forward_batch_and_checkpoint_round_trip():
    a=toy(n=4)["gen"]
    a["unit_form"]=np.arange(len(a["tok"]),dtype=np.int8)%3
    a["opp_past"]=np.tile(np.array([1,1,.2,.3,2],np.float32),(4,3,1))
    rows=GenRows(a,np.arange(4),torch.device("cpu")); b=rows.batch(np.arange(4))
    m=GenModel(d=16,layers=1,d_c=8,n_cards=9,feature_version=3).eval()
    with torch.no_grad():
        o=m(b,card=b["card"],form=b["form"])
        loss,_=losses(m,b,mirror=True)
    assert o["cell"].shape == (4,2304) and torch.isfinite(loss)
    b2=dict(b,unit_form=torch.zeros_like(b["unit_form"]))
    with torch.no_grad():
        assert not torch.equal(m(b)["g"],m(b2)["g"])
    path=Path(__file__).parent/'roundtrip_v3.pt'
    torch.save(dict(gen=True,args=dict(d=16,layers=1,feature_version=3),d_c=8,card_vocab=list(range(9)),model=m.state_dict()),path)
    loaded,st=load_model(path,torch.device("cpu"));loaded.eval()
    with torch.no_grad():
        assert torch.equal(m(b)["g"],loaded(b)["g"])


def test_real_v3_row_keeps_own_past_and_every_legacy_feature():
    path=str(sorted(CORPUS.glob("replay_*.json"))[0])
    a=D.replay_rows(path);b=D.replay_rows(path,feature_version=3)
    assert "error" not in a and "error" not in b
    for k,v in a.items():
        if isinstance(v,np.ndarray):
            assert v.tobytes()==b[k].tobytes(),k
    assert (b["unit_form"]==1).any() and (b["unit_form"]==2).any()


def test_live_actual_form_history_privacy_and_reset():
    from pipeline.tests.test_live_gen_afford import pilot
    from pipeline.tests.test_live_mem import FRAME
    from pipeline.opp_elixir_count import LiveOppElixir
    p=pilot([1,2,3,4]);p.feature_version=3;p.use_counter=True;p.opp=LiveOppElixir()
    catalog=json.loads((ROOT/'research/ext/cr-native-sandbox/native_core/data/live_card_catalog.json').read_text())
    knight=next(c for c in catalog['cards'] if c['display_name']=='Knight')
    f=copy.deepcopy(FRAME)
    enemy=copy.deepcopy(f['entities'][-1]);enemy.update(side=0,address='enemy-hero',card_id=knight['hero_form_id'],x=3000,y=8000)
    f['entities'].append(enemy);p.observe(f)
    b,_=p.row(f)
    assert 2 in b['unit_form'][0].tolist()
    assert not b['opp_past'][0,:,0].any()  # this tick is excluded
    f['game_tick']+=1;p.observe(f);b,_=p.row(f)
    op=b['opp_past'][0,0].numpy()
    np.testing.assert_allclose(op,[p.gid['knight'],2,5/6,.25,.05])
    f['players'][0]['elixir_raw']=123456789
    f['players'][0]['deck_card_ids']=[999]*8
    other,_=p.row(f)
    for k in b:
        assert torch.equal(b[k],other[k]),k
    p.reset_match()
    assert p.opp.detected_plays==[]


def test_distinct_evolution_hp_crosschecks_on_real_recordings():
    checked=Counter()
    for path in sorted(CORPUS.glob('replay_*.json'))[:50]:
        r=json.loads(path.read_text());r=D.tag_recording(r,D.played_forms(r),{})
        for f in r['frames']:
            for e,form in zip(f['entities'],f['unit_forms']):
                if form==1 and e[3]=='Bats':
                    assert e[5]==122
                    checked['bats']+=1
                if form==1 and e[3]=='SkeletonBalloon' and e[5]>100:
                    assert e[5]==665
                    checked['skeleton-barrel']+=1
    assert checked['bats']>0 and checked['skeleton-barrel']>0
