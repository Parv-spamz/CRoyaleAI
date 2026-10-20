"""Serial fixed-game collector; no checkpoint creation or policy changes."""
import datetime,gzip,os,time
from common import *
def main():
    assert not (HERE/'collection_started.json').exists()
    p=check();pre=read(HERE/'prelaunch.json');assert pre['complete'] and pre['collection_allowed']
    assert pre['prepared_sha256']==sha(HERE/'prepared.json') and pre['verified_sha256']==sha(HERE/'verified.json')
    stamp,S,runners=initialize('cuda');assert stamp==p['runtime']
    write(HERE/'collection_started.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runtime=stamp,prelaunch_sha256=sha(HERE/'prelaunch.json')))
    records=OUT/'records';records.mkdir();fh=(OUT/'matches.jsonl').open('x');n=0
    for i,spec in enumerate(p['scenarios']):
        for arm in ARMS:
            if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,6,4,tzinfo=datetime.timezone.utc):
                write(HERE/'cutoff.json',dict(next_scenario=i,next_arm=arm,matches_complete=n));return
            check();run=runners[arm];m=setup(run,spec);start=blobsha(m.env.core.save_state());assert start==spec['initial_state_sha256']
            r=run.play('plain',m);st=m.env.core.state();full=run.last_result
            raw=dict(end_tick=int(m.env.tick),terminated=bool(m.env.terminated),core_game_over=bool(st.game_over),winner_side=int(m.env.episode.get('winner',-1)),core_winner=int(st.winner),crowns=[int(x.crowns) for x in st.players],terminal_towers=m.env.raw()['episode']['crown_towers'])
            telemetry=m.env.behaviour_telemetry
            rec=dict(model=arm,tag=spec['tag'],runtime=stamp,checkpoint_sha256=sha(CKPTS[arm]),initial_state_sha256=start,match=r,full_result=full,raw=raw,frames=telemetry.frames,accepted_plays=telemetry.plays)
            path=records/f'{i:03d}_{arm}.json.gz'
            with gzip.open(path,'wt',encoding='utf-8') as f:json.dump(rec,f,allow_nan=False)
            index=dict(model=arm,tag=spec['tag'],path=str(path.relative_to(ROOT)),sha256=sha(path),outcome=r['outcome'])
            fh.write(json.dumps(index)+'\n');fh.flush();n+=1
            write(HERE/'progress.json',dict(matches_complete=n,total=192,last=index,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
            print(f'{n}/192 {arm} {spec["opp"]} {spec["seed"]} {r["outcome"]}',flush=True)
    fh.close();check();write(HERE/'collection_complete.json',dict(complete=True,matches=n,index_sha256=sha(OUT/'matches.jsonl'),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runtime=stamp))
    print('DEVELOPMENT_GAMEPLAY_COLLECTION_COMPLETE')
if __name__=='__main__':main()
