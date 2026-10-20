import hashlib,json,sys
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
ROOT=Path(__file__).resolve().parents[5];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE/'sequence_data'))
from verify import reference
from pipeline.opponent_hand_v2 import belief_at,belief_tokens
OLD=HERE.parent/'opponent_hand_reader';RAW=ROOT/'icebow/data/bench/opponent_hand_reader_20261006'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
def counts(c,b,truth):
    inside=set(b['in_hand']);outside=set(b['out_of_hand']);actual=set(truth)
    c['queries']+=1;c['full']+=bool(b['full_hand']);c['full_exact']+=bool(b['full_hand'] and inside==actual)
    c['in_claims']+=len(inside);c['in_correct']+=len(inside&actual)
    c['out_claims']+=len(outside);c['out_correct']+=len(outside-actual)
    c['issues']+=bool(b['issues']);c['mirror_queries']+=bool(b.get('inferred_mirror_plays',0))
def main():
    assert not (HERE/'mirror_replays_verified.json').exists()
    original=read(OLD/'collected.json');verified=read(OLD/'verified.json');assert verified['complete']
    for name in ('events.jsonl','predictions.jsonl'):assert sha(RAW/name)==original['outputs'][name]
    streams={e['tag']:e for e in map(json.loads,(RAW/'events.jsonl').read_text().splitlines())}
    cv=read(HERE.parent/'match_adaptation/prepared.json')['card_vocab'];gid={c:i for i,c in enumerate(cv)}
    totals=defaultdict(Counter);per=defaultdict(lambda:defaultdict(Counter));changes=[]
    for line in (RAW/'predictions.jsonl').read_text().splitlines():
        row=json.loads(line);side=1-row['side'];events=streams[row['tag']]['public'][side]
        new=belief_at(events,row['tick'],side);tokens=belief_tokens(events,row['tick'],side,gid)
        ti,qi,_=reference(events,row['tick'],side,gid)
        np.testing.assert_array_equal(ti,tokens['opp_hand']);np.testing.assert_array_equal(qi,tokens['opp_hand_quality'])
        old=row['predictions']['public'];assert not old['certified'] and not new['certified']
        for name,b in [('old',old),('mirror_successor',new)]:
            key='/'.join([row['part'],row['cohort'],name]);counts(totals[key],b,row['truth']);counts(per[row['tag']][key],b,row['truth'])
        if old['in_hand']!=new['in_hand'] or old['out_of_hand']!=new['out_of_hand']:
            changes.append(dict(tag=row['tag'],tick=row['tick'],side=row['side'],truth=row['truth'],old=old,new=new))
    result=dict(complete=True,totals=dict(totals),per_replay=dict(per),changed_queries=len(changes),
        changed=changes,all_new_tokens_independent=True,certified=False,inputs={str(p.relative_to(ROOT)):sha(p) for p in
            [Path(__file__),HERE/'MIRROR_REPLAY_METRICS.md',OLD/'collected.json',OLD/'verified.json',RAW/'events.jsonl',
             RAW/'predictions.jsonl',HERE/'sequence_data/verify.py',ROOT/'pipeline/opponent_hand_v2.py']})
    (HERE/'mirror_replays_verified.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(totals=totals,changed_queries=len(changes))));print('MIRROR_REPLAYS_VERIFIED')
if __name__=='__main__':main()
