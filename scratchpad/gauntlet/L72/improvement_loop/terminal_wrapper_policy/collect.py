import datetime,gzip,os,time
from common import *
def main():
    assert not (HERE/'started.json').exists();assert read(HERE.parent/'terminal_wrapper/verified.json')['complete']
    bound=sources();stamp,S,runners=initialize();ss=scenarios();OUT.mkdir(exist_ok=False);(OUT/'records').mkdir()
    write(HERE/'started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources=bound,runtime=stamp,scenarios=ss))
    setups={};matches={}
    for i,scenario in enumerate(ss):
        for arm in ARMS:
            for mode in MODES:
                m=setup(S,runners[arm],scenario,mode=='enabled');key=f'{i}_{arm}_{mode}'
                matches[key]=m;setups[key]=dict(initial=blobsha(m.env.core.save_state()),forms=m.env.loaded_forms,side=m.learner.side)
        assert len({v['initial'] for k,v in setups.items() if k.startswith(str(i)+'_')})==1
        assert all(v['forms']==setups[f'{i}_r1e_disabled']['forms'] for k,v in setups.items() if k.startswith(str(i)+'_'))
    assert sources()==bound;write(HERE/'setups_verified.json',dict(complete=True,setups=setups,policy_predictions=0))
    records=[]
    for i,scenario in enumerate(ss):
        for arm in ARMS:
            for mode in MODES:
                if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,4,tzinfo=datetime.timezone.utc):
                    write(HERE/'cutoff.json',dict(completed=len(records),next=[i,arm,mode]));return
                key=f'{i}_{arm}_{mode}';m=matches.pop(key);run=runners[arm];decisions=[];ordinary=run.round
                def track(match,ds,*args,**kwargs):
                    decisions.extend(dict(tick=int(match.env.tick),side=s.side) for s in ds)
                    return ordinary(match,ds,*args,**kwargs)
                run.round=track
                try:result=run.play('plain',m)
                finally:run.round=ordinary
                st=m.env.core.state();telemetry=m.env.behaviour_telemetry
                raw=dict(key=key,scenario=i,arm=arm,mode=mode,tag=scenario['tag'],seed=scenario['seed'],opp=scenario['opp'],runtime=stamp,checkpoint=sha(g.CKPTS[arm]),initial=setups[key],
                    boundary=int(st.regular_ticks+st.overtime_ticks),decisions=decisions,accepted=telemetry.plays,frames=telemetry.frames,plays={str(s.side):s.plays for s in m.sides},
                    native=dict(state_sha256=blobsha(m.env.core.save_state()),tick=int(st.tick),game_over=bool(st.game_over),terminated=m.env.terminated,winner=int(st.winner),crowns=[int(p.crowns) for p in st.players],episode=m.env.episode),result=result)
                path=OUT/'records'/f'{key}.json.gz'
                with gzip.open(path,'wt',encoding='utf-8') as f:json.dump(raw,f,allow_nan=False)
                records.append(dict(key=key,path=str(path.relative_to(ROOT)),sha256=sha(path)))
                write(HERE/'progress.json',dict(games=len(records),total=32,last=key,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
                print('COMPLETE',len(records),key,raw['native']['tick'],flush=True);m.env.close()
    assert sources()==bound
    write(HERE/'report.json',dict(complete=True,records=records,runtime=stamp,sources=bound,setups_sha256=sha(HERE/'setups_verified.json'),new_models=0,performance_acceptance=False))
    print('TERMINAL_POLICY_COLLECTION_COMPLETE')
if __name__=='__main__':main()
