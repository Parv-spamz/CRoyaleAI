"""Mine current public recordings only. Unknown defensive labels await lead ruling."""
import argparse, hashlib, json, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from pipeline.public_outcomes import label_recording, summarize, normalize
from pipeline.public_geometry import load_calibration

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,nargs='+',required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--xbow-calibration',type=Path)
    ap.add_argument('--labels-only',action='store_true',help='C2 labels without repeating full C3 behaviour summaries')
    ap.add_argument('--reconstruct-rocket-landing',action='store_true',default=True,help='Use lead-approved R2c public aim/catalog speed fallback (default)')
    a=ap.parse_args()
    reach=load_calibration(a.xbow_calibration) if a.xbow_calibration else None
    a.out.mkdir(parents=True,exist_ok=True);manifest=[];counts=Counter();allrows=[];metrics=[];seen=set()
    fingerprint=hashlib.sha256(Path(__file__).read_bytes()+(ROOT/'pipeline/public_outcomes.py').read_bytes()+
        (ROOT/'pipeline/public_geometry.py').read_bytes()+(ROOT/'pipeline/projectile_observation.py').read_bytes()+
        (a.xbow_calibration.read_bytes() if a.xbow_calibration else b'')+
        str((a.labels_only,a.reconstruct_rocket_landing)).encode()).hexdigest()
    cache=a.out/'record_cache.jsonl';cached={}
    if cache.is_file():
        for line in cache.read_text().splitlines():
            try:item=json.loads(line)
            except json.JSONDecodeError:continue
            if item.get('code_sha256')==fingerprint:cached[item['source']['path']]=item
    for corpus in a.corpus:
        for p in sorted([*corpus.glob('replay_*.json'),*corpus.glob('j*/replay_*.json')]):
            raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest();old=cached.get(str(p))
            if old and old['source']['sha256']==sha:
                tag=old['source']['tag']
                if tag in seen:continue
                seen.add(tag);manifest.append(old['source']);allrows.extend(old['rows']);metrics.extend(old['metrics']);counts.update(old['counts'])
                print('labelled',tag,'cached',flush=True);continue
            r=json.loads(raw)
            if r['tag'] in seen:continue
            seen.add(r['tag'])
            if not all('public_objects' in f for f in r['frames']):raise ValueError('Old/proxy corpus rejected')
            from pipeline.dataset_gen import card_key
            accepted=[v for v in r.get('log',[]) if v.get('accepted') is True and not v.get('skipped') and not v.get('ability') and v.get('card')]
            if a.labels_only and not any(card_key(v['card']) in ('rocket','x-bow') for v in accepted):
                labels=dict(rockets=[],xbows=[],plays=accepted)
            else:
                r=dict(r,frames=[normalize(f) for f in r['frames']+r.get('play_frames',[])])
                r['frames']=sorted({f['tick']:f for f in r['frames']}.values(),key=lambda f:f['tick'])
                labels=label_recording(r,normalized=True,xbow_reach=reach,reconstruct_rocket_landing=a.reconstruct_rocket_landing)
            allrows.extend(labels['rockets']+labels['xbows'])
            source=dict(path=str(p),tag=r['tag'],sha256=sha);manifest.append(source)
            local=Counter(replays=1,rockets=len(labels['rockets']),xbows=len(labels['xbows']),accepted_plays=len(labels['plays']))
            for row in labels['rockets']:
                for key in ('tower_rocket','defensive_rocket','rocket_then_tornado','tornado_then_rocket'):
                    local[key+('_unknown' if row[key] is None else '_positive' if row[key] else '_negative')]+=1
            local_metrics=[]
            for side in (() if a.labels_only else (0,1)):
                metric=summarize(r,side,normalized=True,xbow_reach=reach,labels=labels)
                if reach is None:
                    for key in ('defensive_xbows','xbow_dead_lane','offensive_lock_cells','offensive_diversity_by_lane_state'):
                        metric[key]=None
                    metric['defensive_xbow_label_status']='awaiting_R1_REVISED_calibration'
                local_metrics.append(dict(tag=r['tag'],side=side,**metric))
            if reach is None:
                # Preserve public placement/tower context, but never reuse the
                # superseded literal R1 tactical labels as current targets.
                for row in labels['xbows']:
                    for key in ('defensive_xbow','offensive_xbow','dead_lane_xbow','offensive_lock_cell'):
                        row[key]=None
            counts.update(local);metrics.extend(local_metrics)
            with cache.open('a') as stream:stream.write(json.dumps(dict(source=source,code_sha256=fingerprint,counts=local,
                rows=labels['rockets']+labels['xbows'],metrics=local_metrics))+'\n')
            print('labelled',r['tag'],flush=True)
    (a.out/'labels.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in allrows))
    (a.out/'behaviour.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in metrics))
    (a.out/'manifest.json').write_text(json.dumps(dict(counts=counts,sources=manifest,
        defensive_xbow_status=json.loads(a.xbow_calibration.read_text())['status'] if reach is not None else 'UNVALIDATED_NOT_FOR_CONTEXT_WEIGHTING',
        xbow_calibration_sha256=hashlib.sha256(a.xbow_calibration.read_bytes()).hexdigest() if a.xbow_calibration else None,
        method='lead_R2b_interpolated_geometry_HP_confirmation',code_sha256=fingerprint,labels_only=a.labels_only,
        combo_windows=dict(rocket_then_tornado='entire_flight_through_landing_plus_2_ticks',tornado_then_rocket='landing_within_50_ticks_of_prior_cast'),
        rocket_landing='public_aim_catalog_speed' if a.reconstruct_rocket_landing else 'last_projectile'),indent=2))
    print(json.dumps(counts),flush=True)
if __name__=='__main__':main()
