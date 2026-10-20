"""Independent original-command, identity and repeated-capture qualification."""
from collections import Counter
import csv,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
LOOP=HERE.parent
sys.path[:0]=[str(LOOP),str(ROOT)]
from verify_reserved_icebow_corrected import recount
from verify_native_preflight import compare_frames
from deal_recovery.verify_reserved import opening
from research.sandbox_tools.validate_public_capture import inspect

def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def csvrows(p):
    with Path(p).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    out=HERE/'collection_verified.json';assert not out.exists()
    report=read(HERE/'collection_complete.json');prepared=read(HERE/'prepared.json');started=read(HERE/'collection_started.json')
    assert report['complete'] and report['started_sha256']==sha(HERE/'collection_started.json')
    assert report['prepared_sha256']==sha(HERE/'prepared.json')==started['prepared_sha256']
    for p,h in started['sources'].items():assert sha(ROOT/p)==h,p
    for p,h in prepared['csv_hashes'].items():assert sha(ROOT/p)==h,p
    assert sha(prepared['jobs_path'])==prepared['jobs_sha256'];jobs=read(prepared['jobs_path'])
    old=read(LOOP/'native_compatibility_corrected.json');expected=sorted(r['tag'] for r in old['exact_icebow'] if not r['compatible'])
    assert expected==[j['tag'] for j in jobs]==[r['tag'] for r in report['rows']]
    assert started['original_form_validated_decks']==2*len(expected)
    reservation=read(LOOP/'replay_reservation.json');assert sha(reservation['reservation_file'])==reservation['reservation_sha256']
    reserved={r['tag']:r for line in Path(reservation['reservation_file']).read_text().splitlines() if (r:=json.loads(line))}
    counts=Counter();component_casts=Counter();component_replays=Counter();qualified=[]
    icebow={'ice-wizard','knight','rocket','skeletons','tesla','the-log','tornado','x-bow'}
    base=lambda s:s.split('-ev')[0].removesuffix('-hero')
    for job,row in zip(jobs,report['rows']):
        assert job['split']==row['split']==reserved[job['tag']]['split']=='confirmation'
        assert job['signature']==reserved[job['tag']]['signature']
        commands=csvrows(ROOT/job['crawl']/'plays_ext.csv');battle=csvrows(ROOT/job['crawl']/'battles.csv')[0]
        assert len(row['attempts'])==2;captures=[]
        for a in row['attempts']:
            assert sha(ROOT/a['path'])==a['sha256'];rec=read(ROOT/a['path']);captures.append(rec)
            if a['status']=='unresolved_opening':
                assert len(rec['reset_history'])<=rec['budget']==61 and rec['total_reset_budget']==64 and not row['usable'];continue
            assert rec['seed']==424242 and rec['level']==11 and rec['tick_after_reset']==10
            grade,why=recount(rec,commands,battle)
            assert grade==a['grade'] and why==a['reasons'] and a['usable']==(not why)
            assert not inspect(rec)['errors'];opening(rec,commands,job)
            assert rec.get('deal_recovery',{}).get('resets',0)+3<=64
        a,b=captures;assert row['attempts'][0]['status']==row['attempts'][1]['status']
        if row['attempts'][0]['status']=='unresolved_opening':assert a==b;counts['unresolved']+=1
        else:
            for k in ('final','log','grade','opening_deal_verified'):assert a[k]==b[k],k
            for k in ('frames','play_frames'):compare_frames(a[k],b[k])
            assert row['usable']==row['attempts'][0]['usable'];counts['captured_source_commands']+=len(commands)
            counts['captured_accepted_commands']+=a['grade']['accepted']
            if row['usable']:
                counts['usable']+=1;qualified.append(dict(tag=job['tag'],signature=job['signature'],split=job['split'],decks=job['decks'],**row['attempts'][0]))
                for i,d in enumerate(job['decks']):
                    if {base(c) for c in d}!=icebow:continue
                    own=1-i;cards=Counter(base(c['attr_card']) for c in commands if c['attr_ability']=='0' and {'red':0,'blue':1}[c['attr_s']]!=own)
                    for card in ('goblin-barrel','witch','night-witch','furnace'):
                        component_casts[card]+=cards[card];component_replays[card]+=int(cards[card]>0)
        counts['selections']+=1;counts['repeats']+=1
    assert counts['usable']==report['usable']
    proof=dict(complete=True,counts=dict(counts),component_casts=dict(component_casts),component_replays=dict(component_replays),
        qualified=qualified,complete_sha256=sha(HERE/'collection_complete.json'),script_sha256=sha(__file__),
        model_predictions=0,N2_complete=False,limits=['Casts/replays are not qualified tactical opportunities or sufficient power.'])
    out.write_text(json.dumps(proof,indent=2));print(json.dumps({k:proof[k] for k in ['counts','component_casts','component_replays']}));print('VOID_RECONSTRUCTION_INDEPENDENT_PASS')

if __name__=='__main__':main()
