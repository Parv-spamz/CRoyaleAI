"""Independent integer native-frame accounting; no producer/model/engine imports."""
import copy, hashlib, itertools, json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
ARMS=('wait','wait_repeat','center','inward1','inward2','inward3','far6')
KEYS={(s,k) for s in (0,1) for k in (0,1,2)}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def crowns(frame):
    assert type(frame['tick']) is int and frame['game_over'] is False
    assert len(frame['towers'])==6 and len(frame['elixir'])==len(frame['crowns'])==2
    assert frame['crowns']==[0,0] and all(type(x)is int and 0<=x<=10000 for x in frame['elixir'])
    out={};uids=set()
    for e in frame['towers']:
        k=(e['team'],e['tower_slot']);assert k in KEYS and k not in out and e['uid'] not in uids
        assert e['card_id']==-1 and e['kind']==(2 if k[1]==0 else 3)
        assert type(e['hp'])is int and type(e['max_hp'])is int and 0<e['hp']<=e['max_hp']
        assert all(type(e[f])is int for f in ('x','y','uid','radius')) and len(e['footprint'])==4
        out[k]=e;uids.add(e['uid'])
    assert set(out)==KEYS;return out
def verify_root(r,branches,catalogue):
    assert set(branches)==set(ARMS)
    side=r['side'];phase=r['phase'];target=tuple(int(x) for x in r['target_key'].split(':'))
    root=crowns(r['root_frame']);assert root[target]==r['target'] and r['root_frame']['tick']==phase
    assert r['target']['team']==1-side and r['target']['kind']==3
    opponent=sorted([e for e in root.values() if e['team']==1-side and e['kind']==3],key=lambda e:e['x'])
    assert opponent[r['lane']]==r['target']
    wait=branches['wait'];repeated=branches['wait_repeat']
    assert wait['frames']==repeated['frames'] and wait['final_sha256']==repeated['final_sha256']
    reports={}
    for arm in ARMS:
        b=branches[arm];assert b['root_id']==r['root_id'] and b['arm']==arm and b['root_sha256']==r['root_sha256']
        assert b['before']==wait['before'] and b['before']['tick']==phase+26
        assert [x['tick'] for x in b['frames']]==list(range(phase+26,phase+327))
        curves={k:[] for k in KEYS}
        for i,(a,w) in enumerate(zip(b['frames'],wait['frames'],strict=True)):
            ca,cw=crowns(a),crowns(w)
            for k in KEYS:
                for f in ('uid','team','kind','card_id','tower_slot','x','y','max_hp','radius','footprint'):
                    assert ca[k][f]==cw[k][f]==root[k][f]
                assert cw[k]['hp']==root[k]['hp']
                delta=cw[k]['hp']-ca[k]['hp'];assert delta>=0
                curves[k].append(delta)
            assert a['elixir'][1-side]==w['elixir'][1-side]
        cost=wait['frames'][0]['elixir'][side]-b['frames'][0]['elixir'][side]
        if arm.startswith('wait'):
            assert b['command'] is b['result'] is None and cost==0
        else:
            command=b['command'];res=b['result']
            assert command['team']==res['team']==side and command['hand_slot']==res['hand_slot']==0
            assert res['card_id']==catalogue['rocket_id'] and res['status']==0 and res['tick']==phase+26
            sign=1 if r['target']['x']<162000 else -1
            dx=0 if arm in ('center','far6') else sign*int(arm[-1])*18000
            dy=(1 if r['target']['y']<288000 else -1)*108000 if arm=='far6' else 0
            assert (command['x'],command['y'])==(r['target']['x']+dx,r['target']['y']+dy)
            assert cost==catalogue['rocket_cost']*1000
        effects={}
        for k,curve in curves.items():
            assert all(a<=b for a,b in zip(curve,curve[1:])) and len(set(curve[-10:]))==1
            effects[f'{k[0]}:{k[1]}']=dict(final=curve[-1],first_tick=next((phase+26+i for i,v in enumerate(curve) if v>0),None),curve=curve)
        assert all(f['spells']==f['projectiles']==0 for f in b['frames'][-10:])
        reports[arm]=dict(effects=effects,accepted_cost_milli=cost)
    assert reports==r['summary']
    center=reports['center']['effects'];assert center[r['target_key']]['final']>0
    assert all(v['final']==0 for k,v in center.items() if k!=r['target_key'])
    assert all(v['final']==0 for a in ('wait','wait_repeat','far6') for v in reports[a]['effects'].values())
    return reports
def main():
    assert not (HERE/'verified.json').exists();report=read(HERE/'report.json')
    assert report['complete'] and report['models_loaded']==report['optimizer_updates']==0
    for path,digest in report['sources'].items():assert sha(ROOT/path)==digest
    assert sha(ROOT/report['catalogue_path'])==report['catalogue_sha256'];cat=read(ROOT/report['catalogue_path'])
    expected=list(itertools.product((90,4800),(11,14),(0,1),(0,1)))
    assert [(r['phase'],r['level'],r['side'],r['lane']) for r in report['roots']]==expected
    assert len({r['root_id'] for r in report['roots']})==16
    summaries=[];first=None
    for index,r in enumerate(report['roots']):
        assert r['seed']==2026100600+index
        assert sha(ROOT/r['root_path'])==r['root_sha256'];branches={}
        for arm,b in r['branches'].items():
            assert sha(ROOT/b['path'])==b['sha256'] and sha(ROOT/b['final_path'])==b['final_sha256']
            branches[arm]=read(ROOT/b['path']);assert branches[arm]['final_sha256']==b['final_sha256']
        values=verify_root(r,branches,cat)
        summaries.append(dict(root_id=r['root_id'],level=r['level'],side=r['side'],lane=r['lane'],phase=r['phase'],effects={a:values[a]['effects'][r['target_key']]['final'] for a in ARMS},first_tick={a:values[a]['effects'][r['target_key']]['first_tick'] for a in ARMS}))
        if first is None:first=(r,branches)
    r,b=first
    def expect_bad(mutator):
        rr,bb=copy.deepcopy((r,b));mutator(rr,bb)
        try:verify_root(rr,bb,cat)
        except (AssertionError,KeyError,ValueError,TypeError,IndexError):return
        raise AssertionError('Corrupted impact data accepted')
    corruptions=[lambda r,b:b['center']['frames'].pop(),lambda r,b:b['center']['frames'][0]['towers'].pop(),
      lambda r,b:b['center']['frames'][0]['towers'][0].update(team=7),lambda r,b:b['center']['frames'][0]['towers'][0].update(hp=1),
      lambda r,b:b['center']['frames'][0].update(tick=0),lambda r,b:b['center']['result'].update(status=4),
      lambda r,b:b['center']['command'].update(x=0),lambda r,b:b['center']['frames'][0]['elixir'].__setitem__(r['side'],10000),
      lambda r,b:b.update(extra=b['wait']),lambda r,b:r['summary']['center'].update(accepted_cost_milli=0),
      lambda r,b:b['wait_repeat'].update(final_sha256='bad'),lambda r,b:r.update(target_key='0:0')]
    for mutation in corruptions:expect_bad(mutation)
    result=dict(complete=True,report_sha256=sha(HERE/'report.json'),roots=16,branches=112,frames=112*301,controls=dict(positive=16,negative=len(corruptions)),summary=summaries,models_loaded=0,optimizer_updates=0,native_client_parity=False,policy_acceptance=False,source_sha256=sha(Path(__file__)))
    (HERE/'verified.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('TARGET_IMPACT_VERIFIED')
if __name__=='__main__':main()
