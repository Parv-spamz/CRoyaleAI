"""Independent raw-log recount and observed normalization check; no model calls."""
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    report=json.loads((HERE/'live_barrel_landings.json').read_text())
    counts=Counter();errors=[];matched_keys=[];normalization=[]
    found=set()
    by_file={name:[r for r in report['flights'] if r['file']==Path(name).name] for name in report['source_sha256']}
    for name,digest in report['source_sha256'].items():
        path=ROOT/name;assert sha(path)==digest
        events=[json.loads(l) for l in path.open()]
        frames=[r for r in events if r['event']=='decision' and r.get('public')]
        indexed=list(enumerate(frames))

        def single(item):
            p=item[1]['public'];rows=[x for x in p['raw_projectiles'] if x.get('card_id')==28000004 and x['side']!=p['observer_side']]
            if len(rows)!=1:return None
            return rows[0]['side'],rows[0].get('target_x'),rows[0].get('target_y')

        for key,group in itertools.groupby(indexed,key=single):
            items=list(group)
            if key is None:continue
            first,last=items[0],items[-1]
            existing=[r for r in by_file[name] if (r['first_tick'],r['last_tick'],tuple(r['key']))==(first[1]['tick'],last[1]['tick'],key)]
            assert len(existing)==1
            row=existing[0];found.add((path.name,first[1]['tick'],last[1]['tick']))
            counts['segments']+=1
            if row.get('matched'):
                index=last[0]+1
                assert index<len(frames)
                after=frames[index]
                assert after['tick']-last[1]['tick']<=40
                prior={(b.get('address'),b.get('category')) for f in frames[:index] for b in f['public']['raw_bodies']}
                spawned=[b for b in after['public']['raw_bodies'] if b.get('card_id')==28000004 and b['side']==key[0]
                         and b['hp']>0 and (b.get('address'),b.get('category')) not in prior]
                assert len(spawned)==3 and all(b['kind']==14 for b in spawned)
                centre=[sum(b[k] for b in spawned)/3 for k in ('x','y')]
                error=math.dist(centre,key[1:])/1000
                assert abs(error-row['error_tiles'])<1e-12
                assert (centre[0]<9000)==(key[1]<9000)
                errors.append(error);counts['matched']+=1
                matched_keys.append((path.name,first[1]['tick']))
            # Independently match actual attempted/confirmed Log events.
            attempts=[r for r in events if r['event']=='play' and r.get('name')=='Log'
                      and first[1]['tick']<=r['tick']<=last[1]['tick']]
            assert len(attempts)==len(row['preemptive_log_attempts'])
            side=first[1]['public']['observer_side']
            for attempt,saved in zip(attempts,row['preemptive_log_attempts']):
                assert saved['tick']==attempt['tick'] and saved['xy']==attempt['xy']
                ownx=(18000-key[1])/18000 if side==1 else key[1]/18000
                correct=(attempt['xy'][0]<.5)==(ownx<.5)
                assert correct==saved['correct_lane']
                later=[r for r in events if r['event'] in ('confirmed','unconfirmed') and r.get('name')=='Log'
                       and r['tick']>=attempt['tick']]
                assert later and (later[0]['event']=='confirmed')==saved['confirmed']
                counts['confirmed_correct' if correct else 'confirmed_wrong']+=1
        for frame in frames:
            p=frame['public'];side=p['observer_side']
            for raw in p['raw_projectiles']:
                if raw.get('card_id')!=28000004 or raw['side']==side:continue
                normalized=p['normalized_current_projectiles']
                xy=[(18000-raw['x'])/18000,raw['y']/32000] if side==1 else [raw['x']/18000,(32000-raw['y'])/32000]
                target=[(18000-raw['target_x'])/18000,raw['target_y']/32000] if side==1 else [raw['target_x']/18000,(32000-raw['target_y'])/32000]
                candidates=[v for v in normalized if int(v[0])==42 and int(v[1])==1]
                distances=[max(abs(a-b) for a,b in zip(v[2:6],xy+target)) for v in candidates]
                assert distances and min(distances)<1e-6,(name,frame['tick'])
                normalization.append(min(distances))
    assert counts['segments']==len(report['flights'])==len(found)
    assert counts['matched']==report['counts']['matched_spawns']
    assert counts['confirmed_correct']==report['counts']['preemptive_log:confirmed:correct_lane']
    assert counts['confirmed_wrong']==report['counts']['preemptive_log:confirmed:wrong_lane']
    out=dict(complete=True,counts=dict(counts),normalization_frames=len(normalization),
        normalization_max_error=max(normalization),matched_spawn_keys=matched_keys,
        report_sha256=sha(HERE/'live_barrel_landings.json'),script_sha256=sha(__file__),
        model_predictions=0,notes='Actual public spawn proxy and emitted raw-to-model coordinate transform; no candidate acceptance.')
    (HERE/'live_barrel_verified.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out));print('LIVE_BARREL_LANDINGS_INDEPENDENTLY_VERIFIED')


if __name__=='__main__':main()
