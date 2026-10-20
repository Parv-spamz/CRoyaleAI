"""Independent public scalar and geometry oracles for the new representation."""
import copy
import numpy as np
import torch
from experiment import c,HERE

def expected_features(sc):
    output=[]
    for row in sc.tolist():
        slots=[]
        for i in range(6):
            alive=row[64+i]>.5;known=alive and row[58+i]>.5 and np.isfinite(row[52+i])
            slots.append([int(i>=3),int(i%3!=0),row[52+i] if known else 0.,float(known),float(alive)])
        output.append(slots)
    return torch.tensor(output,dtype=sc.dtype)

def geometry(anchors,rows):
    expected=np.asarray(anchors)
    assert expected.shape==(6,2)
    for observer in (0,1):
        actual={}
        for side,kind,lane,x,y,hp,maximum in rows:
            if observer==1:x,y=18000-x,32000-y
            x,y=x/18000,1-y/32000
            own=int(side==observer)
            slot=(0 if own else 3)+(0 if kind=='king' else 1 if x<.5 else 2)
            assert slot not in actual;actual[slot]=(x,y)
        assert set(actual)==set(range(6))
        assert np.allclose(np.array([actual[i] for i in range(6)]),expected,rtol=0,atol=1e-7)

def check(model,b):
    from tower_model import anchors
    offsets={};n=0
    from pipeline.obs_contract import SCALAR_FEATURES
    for key,count in SCALAR_FEATURES:offsets[key]=(n,n+count);n+=count
    assert [offsets[k] for k in ('tower_hp_frac_6','tower_hp_known_6','tower_alive_6')]==[(52,58),(58,64),(64,70)]
    sc=b['sc'].detach().clone();sc[:,52:58]=torch.tensor([.91,.12,.73,.89,.34,.56]);sc[:,58:70]=1
    sc[:,58]=0;sc[:,61]=0;sc[0,65]=0
    expected=expected_features(sc);actual,alive=model.tower_features(sc)
    assert torch.equal(actual,expected)
    bad=sc.clone();bad[:,52]=float('nan');bad[:,55]=999
    assert torch.equal(model.tower_features(bad)[0],expected)
    assert torch.equal(model.tower_unspread(bad),model.tower_unspread(sc))
    dead=sc.clone();dead[:,64:70]=0
    assert torch.count_nonzero(model.tower_unspread(dead))==0
    flip=sc.clone()
    for start in (52,58,64):flip[:,start:start+6]=sc[:,start+torch.tensor([0,2,1,3,5,4])]
    assert torch.equal(model.tower_unspread(flip),model.tower_unspread(sc).flip(-1))
    rejected=0
    # These mutations alter semantic identity, rather than only repeating implementation.
    for mutate in ('hp','known','alive','side','kind'):
        wrong=actual.clone();col={'hp':2,'known':3,'alive':4,'side':0,'kind':1}[mutate]
        wrong[0,2,col]+=1
        try:assert torch.equal(wrong,expected)
        except AssertionError:rejected+=1
        else:raise AssertionError('Scalar corruption accepted')
    binding=c.read(HERE.parent/'match_adaptation/prepared.json')
    with np.load(c.ROOT/'icebow/data/bench/match_adaptation_20261005/rows.npz') as z:
        ids=z['ids'] if 'ids' in z.files else z['id']
        reps=z['rep'];train=np.isin(ids,c.indices('train'))
        tags=sorted({binding['tags'][int(rep)] for rep in reps[train]})[:4]
    sources={}
    for tag in tags:
        src=binding['sources'][tag];path=c.ROOT/src['path'];assert c.sha(path)==src['sha256']
        record=c.read(path);rows=record['frames'][0]['towers'];geometry(anchors(),rows);sources[src['path']]=src['sha256']
        if tag==tags[0]:
            for mutation in ('x','wrong_kind','missing'):
                wrong=copy.deepcopy(rows)
                if mutation=='x':wrong[1][3]+=1000
                elif mutation=='wrong_kind':wrong[1][1]='king'
                else:wrong.pop()
                try:geometry(anchors(),wrong)
                except AssertionError:rejected+=1
                else:raise AssertionError('Geometry corruption accepted')
    assert rejected==8 and len(sources)==4
    return dict(scalar_layout=True,unknown_hp_invariant=True,dead_zero=True,mirror_scatter=True,
        geometry_sources=sources,observer_sides=2,positive_controls=2,corruptions_rejected=rejected)
