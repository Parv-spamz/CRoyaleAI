"""Independent saved-data verification; no engine/model/collector import."""
import copy, gzip, hashlib, itertools, json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
FIELDS=('uid','team','kind','card_id','x','y','hp','max_hp','radius','footprint','level')

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dh(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def entity_map(f):
    assert not f['game_over'] and f['winner']==-1 and f['crowns']==[0,0]
    assert not f['projectiles']
    out={}
    for e in f['entities']:
        assert e['uid'] not in out and e['attack_phase']==0 and 0<e['hp']<=e['max_hp']
        out[e['uid']]=e
    crowns=[e for e in out.values() if e['card_id']==-1]
    assert len(crowns)==6 and {(e['team'],e['tower_slot']) for e in crowns}==set(itertools.product((0,1),(0,1,2)))
    return out

def reference_features(public,aim,uid,cat):
    side=public['side'];old,current=public['history'];prev={e['uid']:e for e in old['entities']};now={e['uid']:e for e in current['entities']}
    sign=-1 if side==0 else 1
    def pos(e):return ((324000 if side==0 else 0)+sign*e['x'],(576000 if side==0 else 0)+sign*e['y'])
    def vel(e):return (sign*(e['x']-prev[e['uid']]['x'])/18000,sign*(e['y']-prev[e['uid']]['y'])/18000)
    e=now[uid];tx,ty=pos(e);ax,ay=pos(dict(x=aim[0],y=aim[1]));foot=e['footprint']
    width,height=(0,0) if foot is None else ((foot[2]-foot[0])/18000,(foot[3]-foot[1])/18000)
    row=[tx/324000,ty/576000,ax/324000,ay/576000,(ax-tx)/324000,(ay-ty)/576000,e['radius']/18000,width,height,e['hp']/10000,
         e['level']/14,int(e['kind']==0),int(e['kind']==2),int(e['kind']==3),int(e['card_id']==cat['Knight']['card_id']),int(e['card_id']==cat['Giant']['card_id']),public['own_level']/14,*vel(e)]
    bodies=sorted((q for q in now.values() if q['card_id']!=-1),key=lambda q:q['card_id'])
    for index in (0,1):
        if index==1:row.append(int(len(bodies)==2))
        if index>=len(bodies):row.extend([0,0,0,0])
        else:
            x,y=pos(bodies[index]);row.extend([x/324000,y/576000,*vel(bodies[index])])
    assert len(row)==28
    return row

def check_scene(r,meta,public,branches,cat,rows):
    s=r['spec'];side=s['side'];enemy=1-side
    assert meta['spec']==s and public==dict(side=side,own_level=s['level'],history=[dict(tick=f['tick'],entities=[{k:e[k] for k in FIELDS} for e in f['entities']]) for f in (meta['past'],meta['root'])])
    assert meta['past']['tick']==230 and meta['root']['tick']==240
    original=entity_map(meta['root']);past=entity_map(meta['past']);assert original.keys()==past.keys()
    bodies={u:e for u,e in original.items() if e['card_id']!=-1}
    assert len(bodies)==s['count'] and sorted(e['card_id'] for e in bodies.values())==sorted([cat['Knight']['card_id']]+([cat['Giant']['card_id']] if s['count']==2 else []))
    assert all(e['team']==enemy and e['level']==s['level'] and e['hp']==e['max_hp'] for e in bodies.values())
    names=('Rocket','Knight','Giant','Log','Tesla','IceWizard','Tornado','Xbow');assert meta['deck']==[cat[n]['card_id'] for n in names]
    assert meta['forms']==[[0]*8]*2 and meta['levels']==[[s['level']]*8]*2 and meta['tower_levels']==[s['level']]*2
    assert len(meta['setup'])==s['count']
    for index,st in enumerate(meta['setup']):
        cmd=dict(team=enemy,hand_slot=index+1,x=int(18000*(s['x'] if s['lane']==0 else 18-s['x']))+index*(-18000 if s['lane']==0 else 18000),y=int(18000*(s['y'] if enemy==0 else 32-s['y'])))
        assert st['command']==cmd and len(st['results'])==1
        result=st['results'][0];assert result['status']==0 and result['tick']==180+index and result['card_id']==cat[names[index+1]]['card_id'] and result['team']==enemy and result['hand_slot']==index+1
        assert st['before']['tick']==st['after']['tick']==180+index
        assert st['before']['elixir'][enemy]-st['after']['elixir'][enemy]==1000*cat[names[index+1]]['cost']
        entity_map(st['before']);entity_map(st['after'])
    arms=['wait','wait_repeat']+[f'a{i:02}' for i in range(16)];assert set(branches)==set(arms)
    wait=branches['wait']['frames'];assert wait==branches['wait_repeat']['frames'] and branches['wait']['final_sha256']==branches['wait_repeat']['final_sha256']
    for f in wait:
        assert not f['spells'] and {u:e['hp'] for u,e in entity_map(f).items()}=={u:e['hp'] for u,e in original.items()}
    final=entity_map(wait[-1]);assert all((e['x'],e['y'])!=(final[u]['x'],final[u]['y']) for u,e in bodies.items())
    expected=[];summaries={}
    points=list(itertools.product((2.5,6.5,11.5,15.5),(3.5,7.5,11.5,15.5)))
    for arm in arms:
        b=branches[arm];assert b['root_id']==s['root_id'] and b['arm']==arm and b['root_sha256']==r['root_sha256']
        assert [f['tick'] for f in b['frames']]==list(range(240,397)) and b['frames'][:26]==wait[:26] and b['before']==wait[26]
        cost=b['before']['elixir'][side]-b['frames'][26]['elixir'][side]
        if arm.startswith('wait'):assert cost==0 and b['command'] is b['result'] is None
        else:
            x,y=points[int(arm[1:])];cmd=dict(team=side,hand_slot=0,x=int(18000*x),y=int(18000*(y if enemy==0 else 32-y)))
            assert b['command']==cmd and cost==6000
            a=b['result'];assert a['status']==0 and a['tick']==266 and a['team']==side and a['hand_slot']==0 and a['card_id']==cat['Rocket']['card_id']
            assert (a['x'],a['y'])==tuple((cmd[k]//18000)*18000+9000 for k in ('x','y'))
        curves={u:[] for u in original}
        for f,w in zip(b['frames'],wait,strict=True):
            current=entity_map(f);reference=entity_map(w);assert current.keys()==original.keys() and f['elixir'][enemy]==w['elixir'][enemy]
            assert all(q['team']==side and q['card_id']==cat['Rocket']['card_id'] for q in f['spells'])
            for u,e in current.items():
                assert all(e[k]==original[u][k] for k in ('team','kind','card_id','max_hp','level'))
                if e['card_id']==-1:assert all(e[k]==original[u][k] for k in ('x','y','footprint','tower_slot'))
                delta=reference[u]['hp']-e['hp'];assert delta>=0
                if e['team']==side:assert delta==0
                curves[u].append(delta)
        assert not b['frames'][-1]['spells']
        effects={}
        for u,values in curves.items():
            assert all(a<=c for a,c in zip(values,values[1:])) and len(set(values[-10:]))==1
            effects[str(u)]=dict(final=values[-1],first_tick=next((240+i for i,v in enumerate(values) if v),None),curve_sha256=hashlib.sha256(json.dumps(values,separators=(',',':')).encode()).hexdigest())
        summaries[arm]=effects
        if not arm.startswith('wait'):
            aim=[b['result']['x'],b['result']['y']]
            for e in meta['root']['entities']:
                if e['team']==enemy:
                    damage=effects[str(e['uid'])]['final']
                    expected.append(dict(root_id=s['root_id'],family=s['family'],split=s['split'],arm=arm,uid=e['uid'],kind='body' if e['card_id']!=-1 else 'crown',aim=aim,features=reference_features(public,aim,e['uid'],cat),label=int(damage>0),damage=damage))
    assert summaries==r['effects'] and expected==rows
    canonical=sorted((reference_features(public,[0,0],u,cat) for u,e in original.items() if e['team']==enemy))
    return dh(canonical)

def main():
    assert not (HERE/'data_verified.json').exists()
    report=read(HERE/'collected.json');assert report['prepared_sha256']==sha(HERE/'prepared.json') and report['preparation_verified_sha256']==sha(HERE/'preparation_verified.json')
    assert report['complete'] and report['models_loaded']==report['optimizer_updates']==0
    for name,h in report['sources'].items():assert sha(ROOT/name)==h
    assert sha(ROOT/report['data_path'])==report['data_sha256'];data=read(ROOT/report['data_path']);assert data['catalogue']==report['catalogue']
    rows=data['rows'];assert len(rows)==13824
    members=list(itertools.product((3.5,4.5,5.5,6.5),(2.5,3.5,4.5),(1,2),(0,1),(0,1),(11,14)))
    assert len(report['roots'])==192;position=0;hashes={'training':set(),'development':set()};first=None;counts={};families={}
    for i,(r,m) in enumerate(zip(report['roots'],members,strict=True)):
        s=r['spec'];x,y,n,side,lane,level=m
        assert s==dict(index=i,root_id=f'r{i:03}',seed=2026101300+i,x=x,y=y,count=n,side=side,lane=lane,level=level,family=f'{x}_{y}_{n}',split='development' if y==3.5 else 'training')
        for prefix in ('meta','root','public','setup'):assert sha(ROOT/r[prefix+'_path'])==r[prefix+'_sha256']
        meta=read(ROOT/r['meta_path']);public=read(ROOT/r['public_path']);assert read(ROOT/r['setup_path'])==meta['setup'] and meta['root_sha256']==r['root_sha256'] and meta['public_sha256']==r['public_sha256']
        branches={}
        for arm,b in r['branches'].items():
            assert sha(ROOT/b['path'])==b['sha256'] and sha(ROOT/b['final_path'])==b['final_sha256']
            branches[arm]=json.loads(gzip.decompress((ROOT/b['path']).read_bytes()))
            assert branches[arm]['final_sha256']==b['final_sha256']
        subset=rows[position:position+16*(3+n)];position+=len(subset)
        h=check_scene(r,meta,public,branches,data['catalogue'],subset);hashes[s['split']].add(h)
        families.setdefault(s['split'],set()).add(s['family'])
        for row in subset:
            key=row['split']+'_'+row['kind']+'_'+str(row['label']);counts[key]=counts.get(key,0)+1
        if first is None:first=(r,meta,public,branches,subset)
    assert position==13824 and not hashes['training']&hashes['development']
    assert len(families['training'])==16 and len(families['development'])==8
    assert sum(r['split']=='training' for r in rows)==9216 and all(counts.get(s+'_'+k+'_'+v,0)>0 for s in hashes for k in ('body','crown') for v in ('0','1'))
    negative=0
    for i in range(16):
        r,m,p,b,q=copy.deepcopy(first);e=b['a00']['frames'][100]['entities'][0]
        if i==0:b.pop('a00')
        if i==1:b['a00']['frames'].pop()
        if i==2:e['hp']-=1
        if i==3:e['uid']=999
        if i==4:e['attack_phase']=1
        if i==5:b['a00']['frames'][100]['projectiles']=[dict(card_id=-1)]
        if i==6:b['a00']['command']['x']+=1
        if i==7:b['a00']['result']['status']=1
        if i==8:b['a00']['frames'][26]['elixir'][r['spec']['side']]+=1
        if i==9:b['wait_repeat']['final_sha256']='bad'
        if i==10:p['opponent_hand']=[1,2,3,4]
        if i==11:q[0]['split']='development'
        if i==12:q[0]['features'][0]+=1
        if i==13:q[0]['label']=1-q[0]['label']
        if i==14:m['setup'][0]['results'][0]['tick']+=1
        if i==15:b['a00']['frames'][100]['entities'].pop()
        try:check_scene(r,m,p,b,data['catalogue'],q)
        except (AssertionError,KeyError,ValueError,IndexError):negative+=1
        else:raise AssertionError(f'Unrejected corruption {i}')
    # Exercise only the public projection implementation; scoring above is independent.
    from common import projected
    r,m,p,b,q=first;private_controls=0
    for key,value in (('elixir',[123,9876]),('opponent_hand',[99]),('future_position',[999,999]),('native_state_bytes','PRIVATE_SENTINEL')):
        history=copy.deepcopy([m['past'],m['root']])
        for frame in history:frame[key]=value
        assert projected(history,r['spec']['side'],r['spec']['level'])==p;private_controls+=1
    result=dict(complete=True,report_sha256=sha(HERE/'collected.json'),data_sha256=report['data_sha256'],rows=13824,training_rows=9216,development_rows=4608,roots=192,branches=3456,frames=542592,families={k:len(v) for k,v in families.items()},counts=counts,controls=dict(positive=192,negative=negative,private_invariance=private_controls),cross_split_state_overlap=0,source_sha256=sha(Path(__file__)),policy_acceptance=False)
    (HERE/'data_verified.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('IMPACT_LEARNING_DATA_VERIFIED')

if __name__=='__main__':main()
