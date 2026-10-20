"""Independent saved setup matrix checks; no engine or predictor imported."""
import copy,itertools,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
FIELDS=('uid','team','kind','card_id','x','y','hp','max_hp','radius','footprint','level')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(s,m,p,cat):
    enemy=1-s['side'];level=s['level'];n=s['count'];names=('Rocket','Knight','Giant','Log','Tesla','IceWizard','Tornado','Xbow')
    assert m['spec']==s and len(m['setup'])==n
    assert m['deck']==[cat[k]['card_id'] for k in names] and m['forms']==[[0]*8]*2 and m['levels']==[[level]*8]*2 and m['tower_levels']==[level]*2
    for i,q in enumerate(m['setup']):
        x=(s['x']-i) if s['lane']==0 else (18-s['x']+i)
        c=dict(team=enemy,hand_slot=i+1,x=int(x*18000),y=int(18000*(s['y'] if enemy==0 else 32-s['y'])))
        assert q['command']==c and len(q['results'])==1
        r=q['results'][0];assert r['status']==0 and r['tick']==180+i and r['card_id']==cat[names[i+1]]['card_id']
        assert all(r[k]==c[k] for k in ('team','hand_slot','x','y'))
        assert q['before']['tick']==q['after']['tick']==180+i
        assert q['before']['elixir'][enemy]-q['after']['elixir'][enemy]==1000*cat[names[i+1]]['cost']
    for tick,f in ((230,m['past']),(240,m['root'])):
        assert f['tick']==tick and not f['projectiles'] and not f['spells'] and not f['game_over'] and f['winner']==-1 and f['crowns']==[0,0]
        assert len({e['uid'] for e in f['entities']})==len(f['entities'])==6+n
        assert all(e['hp']==e['max_hp']>0 and e['attack_phase']==0 and e['level']==level for e in f['entities'])
        crowns=[e for e in f['entities'] if e['card_id']==-1]
        assert {(e['team'],e['tower_slot']) for e in crowns}==set(itertools.product((0,1),(0,1,2)))
        bodies=[e for e in f['entities'] if e['card_id']!=-1]
        assert all(e['team']==enemy for e in bodies) and sorted(e['card_id'] for e in bodies)==sorted([cat[k]['card_id'] for k in names[1:1+n]])
    old={e['uid']:e for e in m['past']['entities']};new={e['uid']:e for e in m['root']['entities']}
    assert old.keys()==new.keys()
    assert all((old[e['uid']]['x'],old[e['uid']]['y'])!=(e['x'],e['y']) for e in new.values() if e['card_id']!=-1)
    expected=dict(side=s['side'],own_level=level,history=[dict(tick=f['tick'],entities=[{k:e[k] for k in FIELDS} for e in f['entities']]) for f in (m['past'],m['root'])])
    assert p==expected
def main():
    assert not (HERE/'preparation_verified.json').exists()
    r=read(HERE/'prepared.json');assert r['complete'] and r['commands']==288 and r['models_loaded']==r['optimizer_updates']==0
    for p,h in r['sources'].items():assert sha(ROOT/p)==h
    members=list(itertools.product((3.5,4.5,5.5,6.5),(2.5,3.5,4.5),(1,2),(0,1),(0,1),(11,14)))
    assert len(r['roots'])==len(members)==192
    first=None
    for i,(record,values) in enumerate(zip(r['roots'],members,strict=True)):
        x,y,n,side,lane,level=values;s=dict(index=i,root_id=f'r{i:03}',seed=2026101300+i,x=x,y=y,count=n,side=side,lane=lane,level=level,family=f'{x}_{y}_{n}',split='development' if y==3.5 else 'training')
        assert record['spec']==s
        for prefix in ('root','meta','public','setup'):assert sha(ROOT/record[prefix+'_path'])==record[prefix+'_sha256']
        m=read(ROOT/record['meta_path']);p=read(ROOT/record['public_path'])
        assert m['setup']==read(ROOT/record['setup_path']) and m['root_sha256']==record['root_sha256'] and m['public_sha256']==record['public_sha256']
        check(s,m,p,r['catalogue'])
        if first is None:first=(s,m,p)
    negatives=0
    for i in range(7):
        s,m,p=copy.deepcopy(first)
        if i==0:m['setup'][0]['command']['x']+=1
        if i==1:m['setup'][0]['results'][0]['status']=7
        if i==2:m['setup'][0]['after']['elixir'][1-s['side']]+=1
        if i==3:m['root']['entities'].pop()
        if i==4:p['opponent_hand']=[1]
        if i==5:s['seed']+=1
        if i==6:m['root']['entities'][0]['attack_phase']=1
        try:check(s,m,p,r['catalogue'])
        except (AssertionError,ValueError,KeyError):negatives+=1
        else:raise AssertionError('unrejected preparation corruption')
    out=dict(complete=True,roots=192,commands=288,prepared_sha256=sha(HERE/'prepared.json'),controls=dict(positive=192,negative=negatives),models_loaded=0,optimizer_updates=0,source_sha256=sha(Path(__file__)))
    (HERE/'preparation_verified.json').write_text(json.dumps(out,indent=2)+'\n');print('IMPACT_LEARNING_ROOTS_VERIFIED')
if __name__=='__main__':main()
