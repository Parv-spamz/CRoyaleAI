"""Fixed model-free crown-impact assay on the pinned updated simulator."""
import hashlib, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
from pipeline.royale_runtime import activate
STAMP=activate()
from royalegym.rust_engine import RustEngine
from royalegym.protocol import MatchSetup, ShuffleMode, DeployCommand, DeployStatus, EntityKind
OUT=ROOT/'icebow/data/bench/target_impact_readiness_20261005'
ARMS=('wait','wait_repeat','center','inward1','inward2','inward3','far6')
FIELDS=('uid','team','kind','card_id','tower_slot','x','y','hp','max_hp','radius','footprint')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def blob(b):return hashlib.sha256(bytes(b)).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def sources():
    ps=list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE/'METRICS.md',ROOT/'pipeline/royale_runtime.py',ROOT/'scratchpad/gauntlet/L71/royale_update_20261005/build_manifest.json']
    return {str(p.relative_to(ROOT)):sha(p) for p in ps}
def frame(core):
    s=core.state();crowns=[]
    assert len(s.entities)==6 and not s.game_over
    for e in s.entities:
        assert e.kind in (EntityKind.KING_TOWER,EntityKind.PRINCESS_TOWER) and e.card_id==-1
        crowns.append({k:getattr(e,k) for k in FIELDS})
    return dict(tick=int(s.tick),towers=crowns,elixir=[p.elixir_milli for p in s.players],crowns=[p.crowns for p in s.players],
                game_over=s.game_over,winner=int(s.winner),spells=len(s.spells),projectiles=len(s.projectiles))
def effects(branch,wait,target):
    curves={f'{e["team"]}:{e["tower_slot"]}':[] for e in wait[0]['towers']}
    for a,b in zip(branch,wait,strict=True):
        assert a['tick']==b['tick']
        hp={f'{e["team"]}:{e["tower_slot"]}':e['hp'] for e in a['towers']}
        for e in b['towers']:curves[f'{e["team"]}:{e["tower_slot"]}'].append(e['hp']-hp[f'{e["team"]}:{e["tower_slot"]}'])
    return {key:dict(final=values[-1],first_tick=next((branch[i]['tick'] for i,v in enumerate(values) if v>0),None),curve=values) for key,values in curves.items()}
def main():
    assert not (HERE/'report.json').exists();OUT.mkdir(exist_ok=False)
    bound=sources();write(HERE/'started.json',dict(sources=bound,runtime=STAMP,models_loaded=0,optimizer_updates=0))
    catalogue=RustEngine();cards={c.name:c for c in catalogue.cards()}
    names=['Rocket','Knight','Skeletons','Log','Tesla','IceWizard','Tornado','Xbow']
    deck=[cards[n].card_id for n in names];rocket=cards['Rocket'];records=[]
    write(OUT/'catalogue.json',dict(deck=names,ids=deck,rocket_id=rocket.card_id,rocket_cost=rocket.elixir))
    for phase in (90,4800):
      for level in (11,14):
       for side in (0,1):
        for lane in (0,1):
            rid=f't{phase}_l{level}_s{side}_p{lane}';seed=2026100600+len(records)
            core=RustEngine();setup=MatchSetup(decks=[deck,deck],shuffle=ShuffleMode.NONE,forms=[[0]*8,[0]*8],levels=[[level]*8,[level]*8],tower_levels=[level,level])
            core.reset(seed,setup);core.step([],phase)
            root=bytes(core.save_state());rootp=OUT/(rid+'_root.bin');rootp.write_bytes(root)
            rootframe=frame(core);enemies=sorted((e for e in rootframe['towers'] if e['team']==1-side and e['kind']==int(EntityKind.PRINCESS_TOWER)),key=lambda e:e['x'])
            target=enemies[lane];targetkey=f'{target["team"]}:{target["tower_slot"]}'
            commands={};branches={}; inward=1 if target['x']<162000 else -1;towards=1 if target['y']<288000 else -1
            for arm in ARMS:
                core.load_state(root);assert bytes(core.save_state())==root
                core.step([],26);before=frame(core);s=core.state();slot=s.players[side].hand.index(rocket.card_id)
                command=None;result=None
                if arm not in ('wait','wait_repeat'):
                    dx=0 if arm in ('center','far6') else inward*int(arm[-1])*18000
                    dy=towards*6*18000 if arm=='far6' else 0
                    command=dict(team=side,hand_slot=slot,x=target['x']+dx,y=target['y']+dy)
                    r,=core.step([DeployCommand(**command)],0)
                    result={k:int(getattr(r,k)) for k in ('team','hand_slot','card_id','status','tick','x','y')}
                    assert r.status==DeployStatus.OK
                frames=[frame(core)]
                for _ in range(300):core.step([],1);frames.append(frame(core))
                finalp=OUT/(rid+'_'+arm+'_final.bin');finalp.write_bytes(bytes(core.save_state()))
                bp=OUT/(rid+'_'+arm+'.json')
                entry=dict(root_id=rid,arm=arm,root_sha256=blob(root),before=before,command=command,result=result,frames=frames,final_sha256=sha(finalp))
                write(bp,entry);branches[arm]=dict(path=str(bp.relative_to(ROOT)),sha256=sha(bp),final_path=str(finalp.relative_to(ROOT)),final_sha256=sha(finalp),frames=frames)
            base=branches['wait'];repeat=branches['wait_repeat']
            assert base['frames']==repeat['frames'] and base['final_sha256']==repeat['final_sha256']
            summaries={};waitframes=base['frames']
            for arm,b in branches.items():
                effect=effects(b['frames'],waitframes,targetkey)
                cost=waitframes[0]['elixir'][side]-b['frames'][0]['elixir'][side]
                assert cost==(0 if arm.startswith('wait') else rocket.elixir*1000)
                summaries[arm]=dict(effects=effect,accepted_cost_milli=cost)
                del b['frames']
            assert summaries['center']['effects'][targetkey]['final']>0
            assert all(v['final']==0 for k,v in summaries['center']['effects'].items() if k!=targetkey)
            assert all(v['final']==0 for v in summaries['far6']['effects'].values())
            records.append(dict(root_id=rid,seed=seed,phase=phase,level=level,side=side,lane=lane,target=target,target_key=targetkey,root_path=str(rootp.relative_to(ROOT)),root_sha256=sha(rootp),root_frame=rootframe,branches=branches,summary=summaries))
            print('ROOT',rid,'CENTER',summaries['center']['effects'][targetkey]['final'])
    assert sources()==bound
    write(HERE/'report.json',dict(complete=True,sources=bound,runtime=STAMP,roots=records,catalogue_path=str((OUT/'catalogue.json').relative_to(ROOT)),catalogue_sha256=sha(OUT/'catalogue.json'),models_loaded=0,optimizer_updates=0,native_client_parity=False,policy_acceptance=False))
    print('TARGET_IMPACT_COLLECTED')
if __name__=='__main__':main()
