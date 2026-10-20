from collections import defaultdict
from zipfile import ZipFile
from shared import *
from pipeline.opponent_hand_v2 import belief_tokens,belief_at
from pipeline.native_recording import tag_native_recording
from pipeline.public_observation import PublicObserver
from pipeline.dataset_gen import card_key
from pipeline.train_rocket_curriculum import take

def main():
    assert not OUT.exists() and not (HERE/'started.json').exists(),'Fresh collection only'
    binding=read(BINDING);assert sha(ROWFILE)==binding['rows_sha256']
    rows=arrays(ROWFILE);assert len(rows['ids'])==268718
    assert [int((rows['part']==p).sum()) for p in (0,1)]==[213995,54723]
    assert not set(rows['rep'][rows['part']==0])&set(rows['rep'][rows['part']==1])
    cv=binding['card_vocab'];gid={c:i for i,c in enumerate(cv)}
    old=read(OLD/'started.json');old_sources={s['tag']:s for s in old['sources']}
    assert sha(CACHE)==read(OLD/'collected.json')['outputs']['events.jsonl']
    cached={v['tag']:v['public'] for v in map(json.loads,CACHE.read_text().splitlines())}
    frozen=sources();OUT.mkdir(parents=True)
    write(HERE/'started.json',dict(sources=frozen,raw_sources=binding['sources'],rows=268718))
    with ZipFile(DATA) as z:hand=take(z,'hand_card',rows['ids'])
    features=np.zeros((268718,8,6),np.float32);quality=np.zeros((268718,5),np.float32)
    audit=np.zeros((268718,9),np.int32);details=[]
    grouped=defaultdict(list)
    for i,r in enumerate(rows['rep']):grouped[int(r)].append(i)
    with (OUT/'public_events.jsonl').open('x') as streams:
        for ri,(rep,positions) in enumerate(sorted(grouped.items())):
            tag=binding['tags'][rep];source=binding['sources'][tag];path=ROOT/source['path']
            assert sha(path)==source['sha256'];rec=read(path)
            assert rec['record_native'] and rec['record_full']
            if tag in cached:
                assert source['sha256']==old_sources[tag]['sha256'];plays=cached[tag]
            else:
                public=dict(record_native=True,frames=[{k:f[k] for k in
                    ('tick','entities','projectiles','effects','public_objects') if k in f} for f in rec['frames']])
                tagged=tag_native_recording(public,{})
                obs=[PublicObserver(0),PublicObserver(1)]
                for f in tagged['frames']:
                    for o in obs:o.update(f,source='native')
                plays=[o.plays for o in obs]
            streams.write(json.dumps(dict(tag=tag,rep=rep,plays=plays))+'\n')
            events=[dict(tick=int(e.get('engine_tick',e['tick'])),side=int(e['side']),card=card_key(e['card']))
                    for e in rec['log'] if e.get('accepted') and e.get('card') and not e.get('ability')]
            final_tick=max(int(f['tick']) for f in rec['frames'])
            memo={}
            for i in positions:
                tick=int(rows['tick'][i]);side=int(rows['side'][i]);key=(side,tick)
                if key not in memo:
                    b=belief_tokens(plays[side],tick,side,gid)
                    reveal=belief_at(plays[side],tick,side)['revealed']
                    memo[key]=(b,reveal)
                b,reveal=memo[key];features[i]=b['opp_hand'];quality[i]=b['opp_hand_quality']
                audit[i]=descriptor(events,tick,side,hand[i],final_tick,gid,reveal)
            ix=np.array(positions);part=int(rows['part'][ix[0]])
            details.append(dict(tag=tag,rep=rep,part=part,rows=len(ix),
                status=np.bincount(audit[ix,0],minlength=6).tolist(),full_hand=int(quality[ix,1].sum()),
                issues=int(quality[ix,2].sum()),mirror_inferred=int(quality[ix,3].sum()),
                truncated=int(audit[ix,8].sum()),reused_public_stream=tag in cached))
            if (ri+1)%25==0:
                streams.flush();write(HERE/'progress.json',dict(replays=ri+1,total=1978));print('REPLAYS',ri+1,flush=True)
    assert len(details)==1978 and sources()==frozen
    # Feature archive deliberately contains no future audit columns.
    np.savez_compressed(OUT/'features.npz',ids=rows['ids'],opp_hand=features,opp_hand_quality=quality)
    np.savez_compressed(OUT/'audit.npz',ids=rows['ids'],descriptors=audit,columns=AUDIT_COLUMNS,hand_card=hand)
    write(OUT/'by_replay.json',details)
    write(HERE/'collected.json',dict(complete=True,rows=268718,replays=1978,summary=summary(features,quality,audit,rows),
        started_sha256=sha(HERE/'started.json'),outputs={p.name:sha(p) for p in OUT.iterdir()},
        model_calls=0,optimizer_updates=0,new_labels=False))
    print('HAND_SEQUENCE_COLLECTED')
if __name__=='__main__':main()
