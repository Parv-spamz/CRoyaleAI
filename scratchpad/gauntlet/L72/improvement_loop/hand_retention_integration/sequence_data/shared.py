import hashlib
import json
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
LOOP=HERE.parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'icebow/data/bench/hand_retention_sequence_20261006'
ROWFILE=ROOT/'icebow/data/bench/match_adaptation_20261005/rows.npz'
BINDING=LOOP/'match_adaptation/prepared.json'
OLD=LOOP/'opponent_hand_reader'
CACHE=ROOT/'icebow/data/bench/opponent_hand_reader_20261006/events.jsonl'
DATA=ROOT/'icebow/data/bench/spawner_identity_20261005/gen_dataset_v5_public.npz'
ORIGINAL=ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,allow_nan=False,separators=(',',':'))+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arrays(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def sources():
    names=['opponent_hand.py','opponent_hand_v2.py','public_observation.py','native_recording.py',
           'dataset_gen.py','obs_contract.py','opp_elixir_count.py','vocab.py','projectile_motion.py',
           'projectile_observation.py','own_ability.py','train_rocket_curriculum.py']
    files=[ROOT/'pipeline'/n for n in names]+list(HERE.glob('*.py'))+[HERE/'PLAN.md',HERE/'METRICS.md',
        BINDING,ROWFILE,OLD/'started.json',OLD/'collected.json',CACHE,DATA,ORIGINAL]
    return {str(p.relative_to(ROOT)):sha(p) for p in files}

def descriptor(events,tick,side,hand,final_tick,gid,revealed):
    # All future information stays in the audit descriptor, never belief_tokens.
    result=np.array([0,0,0,-1,-1,0,0,0,int(final_tick<tick+500)],np.int32)
    enemy=[e for e in events if e['side']!=side and tick<e['tick']<=tick+400]
    if not enemy:return result
    first=min(e['tick'] for e in enemy);batch=[e for e in enemy if e['tick']==first]
    result[3]=first
    if len(batch)!=1:result[0]=2;return result
    e=batch[0];result[1]=gid.get(e['card'],0);result[7]=int(e['card'] in revealed)
    own=[p for p in events if p['side']==side and first<p['tick']<=first+100]
    if not own:result[0]=1;return result
    response_tick=min(p['tick'] for p in own);batch=[p for p in own if p['tick']==response_tick]
    result[4]=response_tick
    if len(batch)!=1:result[0]=2;return result
    card=batch[0]['card'];result[2]=gid.get(card,0)
    before=[p for p in events if p['side']==side and tick<=p['tick']<first]
    result[5]=len(before);result[6]=sum(p['card']==card for p in before)
    result[0]=3 if result[2] not in hand else (5 if result[6] else 4)
    return result

AUDIT_COLUMNS=['status','opponent_card','response_card','opponent_tick','response_tick',
               'own_plays_before','response_spends_before','opponent_revealed','truncated']

def summary(features,quality,audit,rows):
    from collections import Counter
    result={}
    for part in (0,1):
        m=rows['part']==part;a=audit[m];q=quality[m]
        pairs=Counter('/'.join(map(str,x)) for x in a[np.isin(a[:,0],[4,5])][:,[0,1,2]])
        result[str(part)]=dict(rows=int(m.sum()),status=np.bincount(a[:,0],minlength=6).tolist(),
            truncated=int(a[:,8].sum()),full_hand=int(q[:,1].sum()),issues=int(q[:,2].sum()),
            mirror_inferred=int(q[:,3].sum()),pairs=dict(sorted(pairs.items())))
    return result
