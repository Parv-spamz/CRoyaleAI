"""Qualify the entire setup matrix before collecting any Rocket branches."""
import importlib.util,sys
from common import *
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('qualified_impact_v4',HERE.parent/'moving_impact_readiness_v4/collect.py')
v4=importlib.util.module_from_spec(spec);spec.loader.exec_module(v4)

def main():
    cutoff();assert not (HERE/'prepared.json').exists();OUT.mkdir(exist_ok=False)
    frozen=sources();members=specs()
    write(HERE/'started.json',dict(sources=frozen,runtime=v4.STAMP,specs=members,models_loaded=0,optimizer_updates=0))
    cat={c.name:c for c in v4.RustEngine().cards()};catalogue={n:dict(card_id=cat[n].card_id,cost=cat[n].elixir) for n in NAMES};deck=[cat[n].card_id for n in NAMES]
    records=[]
    for s in members:
        cutoff();rid=s['root_id'];side=s['side'];enemy=1-side;level=s['level']
        write(HERE/'progress.json',dict(root=rid,completed=len(records),stage='prepare'))
        core=v4.RustEngine();core.reset(s['seed'],v4.MatchSetup(decks=[deck,deck],shuffle=v4.ShuffleMode.NONE,forms=[[0]*8]*2,levels=[[level]*8]*2,tower_levels=[level]*2))
        core.step([],180);x=int(18000*(s['x'] if s['lane']==0 else 18-s['x']));y=int(18000*(s['y'] if enemy==0 else 32-s['y']))
        setup=[]
        for i in range(s['count']):
            if i:core.step([],1)
            before=v4.frame(core);cmd=dict(team=enemy,hand_slot=i+1,x=x+i*(-18000 if s['lane']==0 else 18000),y=y)
            rr=core.step([v4.DeployCommand(**cmd)],0);after=v4.frame(core)
            setup.append(dict(command=cmd,results=[v4.item(r) for r in rr],before=before,after=after))
            write(OUT/(rid+'_setup.json'),setup)
            assert len(rr)==1 and rr[0].status==0
            assert before['elixir'][enemy]-after['elixir'][enemy]==1000*catalogue[NAMES[i+1]]['cost']
        core.step([],230-core.state().tick);past=v4.frame(core);core.step([],10);root=v4.frame(core)
        bodies=[e for e in root['entities'] if e['card_id']!=-1]
        assert len(bodies)==s['count'] and all(e['team']==enemy and e['hp']==e['max_hp'] and e['level']==level for e in bodies)
        rootpath=OUT/(rid+'_root.bin');rootpath.write_bytes(bytes(core.save_state()))
        public=projected([past,root],side,level);pubpath=OUT/(rid+'_public.json');write(pubpath,public)
        metadata=dict(spec=s,setup=setup,past=past,root=root,deck=deck,forms=[[0]*8]*2,levels=[[level]*8]*2,tower_levels=[level]*2,root_sha256=sha(rootpath),public_sha256=sha(pubpath))
        metapath=OUT/(rid+'_meta.json');write(metapath,metadata)
        record=dict(spec=s)
        for prefix,path in (('root',rootpath),('meta',metapath),('public',pubpath),('setup',OUT/(rid+'_setup.json'))):
            record[prefix+'_path']=str(path.relative_to(ROOT));record[prefix+'_sha256']=sha(path)
        records.append(record)
    assert len(records)==192 and sources()==frozen
    write(HERE/'prepared.json',dict(complete=True,sources=frozen,runtime=v4.STAMP,roots=records,catalogue=catalogue,commands=sum(s['count'] for s in members),models_loaded=0,optimizer_updates=0))
    print('IMPACT_LEARNING_ROOTS_PREPARED')
if __name__=='__main__':main()
