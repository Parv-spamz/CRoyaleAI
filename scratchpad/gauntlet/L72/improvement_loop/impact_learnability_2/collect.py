import gzip, importlib.util, sys
from common import *

sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('qualified_impact_v4',HERE.parent/'moving_impact_readiness_v4/collect.py')
v4=importlib.util.module_from_spec(spec);spec.loader.exec_module(v4)
RustEngine=v4.RustEngine;MatchSetup=v4.MatchSetup;ShuffleMode=v4.ShuffleMode;DeployCommand=v4.DeployCommand

def save_raw(path,data):
    path.write_bytes(gzip.compress(json.dumps(data,allow_nan=False,separators=(',',':')).encode(),mtime=0))

def main():
    cutoff();assert not (HERE/'collected.json').exists()
    prep=read(HERE/'prepared.json');pv=read(HERE/'preparation_verified.json')
    assert prep['complete'] and pv['complete'] and pv['prepared_sha256']==sha(HERE/'prepared.json')
    frozen=sources();assert frozen==prep['sources']
    members=specs();catalogue=prep['catalogue'];rows=[];records=[]
    write(HERE/'collection_started.json',dict(sources=frozen,prepared_sha256=sha(HERE/'prepared.json'),preparation_verified_sha256=sha(HERE/'preparation_verified.json')))
    for s,prepared in zip(members,prep['roots'],strict=True):
        cutoff();rid=s['root_id'];side=s['side'];enemy=1-side;level=s['level']
        write(HERE/'progress.json',dict(root=rid,index=s['index'],completed=len(records),stage='collect'))
        assert prepared['spec']==s
        for prefix in ('root','meta','public','setup'):assert sha(ROOT/prepared[prefix+'_path'])==prepared[prefix+'_sha256']
        rootpath=ROOT/prepared['root_path'];metapath=ROOT/prepared['meta_path'];pubpath=ROOT/prepared['public_path']
        metadata=read(metapath);root=metadata['root'];public=read(pubpath);root_bytes=rootpath.read_bytes()
        core=RustEngine();core.load_state(root_bytes);assert bytes(core.save_state())==root_bytes and v4.frame(core)==root
        bodies=[e['uid'] for e in root['entities'] if e['card_id']!=-1];assert len(bodies)==s['count']
        arms=[('wait',None),('wait_repeat',None)]+[(f'a{i:02}',(int(xx*18000),int((yy if enemy==0 else 32-yy)*18000))) for i,(xx,yy) in enumerate(itertools.product((2.5,6.5,11.5,15.5),(3.5,7.5,11.5,15.5)))]
        wait=None;branches={};summary={}
        for arm,aim in arms:
            core.load_state(root_bytes);assert bytes(core.save_state())==root_bytes
            frames=[v4.frame(core)]
            for _ in range(25):core.step([],1);frames.append(v4.frame(core))
            core.step([],1);before=v4.frame(core);command=result=None
            if aim is not None:
                command=dict(team=side,hand_slot=0,x=aim[0],y=aim[1]);rr,=core.step([DeployCommand(**command)],0);result=v4.item(rr);assert rr.status==0
            frames.append(v4.frame(core))
            for _ in range(130):core.step([],1);frames.append(v4.frame(core))
            finalpath=OUT/(rid+'_'+arm+'_final.bin');finalpath.write_bytes(bytes(core.save_state()))
            raw=dict(root_id=rid,arm=arm,command=command,result=result,before=before,frames=frames,root_sha256=sha(rootpath),final_sha256=sha(finalpath))
            rawpath=OUT/(rid+'_'+arm+'.json.gz');save_raw(rawpath,raw)
            branches[arm]=dict(path=str(rawpath.relative_to(ROOT)),sha256=sha(rawpath),final_path=str(finalpath.relative_to(ROOT)),final_sha256=sha(finalpath))
            if arm=='wait':wait=frames;wait_hash=sha(finalpath)
            if arm=='wait_repeat':assert frames==wait and sha(finalpath)==wait_hash
            for f in wait:
                assert {e['uid']:e['hp'] for e in f['entities']}=={e['uid']:e['hp'] for e in root['entities']}
                assert not f['spells'] and not f['projectiles']
            cost=before['elixir'][side]-frames[26]['elixir'][side];assert cost==(6000 if aim else 0)
            effects=v4.describe(frames,wait,bodies,side);summary[arm]=effects
            if aim is not None:
                resolved=[result['x'],result['y']]
                for e in root['entities']:
                    if e['team']==enemy:
                        effect=effects[str(e['uid'])]['final']
                        rows.append(dict(root_id=rid,family=s['family'],split=s['split'],arm=arm,uid=e['uid'],kind='body' if e['card_id']!=-1 else 'crown',aim=resolved,features=features(public,resolved,e['uid'],catalogue),label=int(effect>0),damage=effect))
        records.append(dict(spec=s,meta_path=str(metapath.relative_to(ROOT)),meta_sha256=sha(metapath),root_path=str(rootpath.relative_to(ROOT)),root_sha256=sha(rootpath),public_path=str(pubpath.relative_to(ROOT)),public_sha256=sha(pubpath),setup_path=str((OUT/(rid+'_setup.json')).relative_to(ROOT)),setup_sha256=sha(OUT/(rid+'_setup.json')),branches=branches,effects=summary))
        print('ROOT',rid,'completed',len(records),'of',len(members),flush=True)
    assert len(rows)==13824 and sources()==frozen
    data=OUT/'dataset.json';write(data,dict(rows=rows,catalogue=catalogue))
    write(HERE/'collected.json',dict(complete=True,sources=frozen,runtime=v4.STAMP,prepared_sha256=sha(HERE/'prepared.json'),preparation_verified_sha256=sha(HERE/'preparation_verified.json'),roots=records,catalogue=catalogue,data_path=str(data.relative_to(ROOT)),data_sha256=sha(data),rows=len(rows),models_loaded=0,optimizer_updates=0))
    print('IMPACT_LEARNING_DATA_COLLECTED')

if __name__=='__main__':main()
