"""Read existing raw metadata/native receipts; no replay or model execution."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
LOOP=HERE.parent
ICEBOW={'ice-wizard','knight','rocket','skeletons','tesla','the-log','tornado','x-bow'}
def read(p): return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def base(c):return c.split('-ev')[0].removesuffix('-hero')

def main():
    out=HERE/'audit.json';assert not out.exists()
    reservation=read(LOOP/'replay_reservation.json')
    source=ROOT/'icebow/data/bench/confirmation_discovery_20261005/candidate_commands.jsonl'
    assert sha(source)==reservation['candidate_commands_sha256']
    expected=set(reservation['exact_icebow_confirmation_tags']);exact=[]
    for line in source.read_text().splitlines():
        item=json.loads(line)
        if item['tag'] not in expected:continue
        own=[i for i,d in enumerate(item['decks']) if {base(c) for c in d}==ICEBOW]
        assert own
        exact.append(dict(tag=item['tag'],decks=item['decks'],opposing={
            card:any(card in {base(c) for c in item['decks'][1-i]} for i in own)
            for card in ('goblin-barrel','witch','night-witch','furnace')}))
    assert {v['tag'] for v in exact}==expected and len(exact)==len(expected)
    records=[];sources={str(source.relative_to(ROOT)):sha(source)}
    for name in ('reserved_pilot','reserved_icebow_corrected'):
        report=LOOP/(name+'_independent.json');proof=read(report);assert proof['complete']
        data=ROOT/'icebow/data/bench/native_confirmation_20261005'/name
        summary=data/'summary.jsonl';assert sha(summary)==proof['summary_sha256']
        prepared=read(LOOP/(name+'_prepared.json'));assert sha(prepared['jobs_path'])==prepared['jobs_sha256']
        jobs=read(prepared['jobs_path']);rows=[json.loads(v) for v in summary.read_text().splitlines()]
        assert len(jobs)==len(rows)
        for p in (report,summary,LOOP/(name+'_prepared.json'),Path(prepared['jobs_path'])):
            sources[str(p.relative_to(ROOT))]=sha(p)
        for job,row in zip(jobs,rows):
            assert job['tag']==row['tag'] and job['split']==row['split']
            p=data/'recordings'/('replay_'+job['tag']+'.json')
            assert sha(p)==row['recording_sha256'];rec=read(p)
            bad=[v for v in rec['log'] if v.get('accepted') is False]
            records.append(dict(tag=job['tag'],split=job['split'],collection=name,
                usable=row['usable'],reasons=row['reasons'],recording=str(p.relative_to(ROOT)),
                recording_sha256=row['recording_sha256'],position_based=rec['deal_probe']['position_based'],
                first_rejection=bad[0] if bad else None,job=job,
                seed=rec['seed'],level=rec['level']))
    assert len({r['tag'] for r in records})==len(records)
    training=[r for r in records if r['split']=='training']
    failed=sorted((r for r in training if not r['position_based']),key=lambda r:r['tag'])
    controls=sorted((r for r in training if r['usable']),key=lambda r:r['tag'])[:3]
    assert failed and all(not r['usable'] for r in failed) and len(controls)==3
    selected=[dict(r,role='fallback') for r in failed]+[dict(r,role='unchanged_control') for r in controls]
    for r in selected:
        r['csv_hashes']={n:sha(ROOT/r['job']['crawl']/n) for n in ('battles.csv','plays_ext.csv')}
    sources[str((LOOP/'replay_reservation.json').relative_to(ROOT))]=sha(LOOP/'replay_reservation.json')
    result=dict(complete=True,model_predictions=0,optimization=False,confirmation_replayed=False,
        exact_metadata_count=len(exact),opposing_metadata_counts={c:sum(r['opposing'][c] for r in exact)
            for c in ('goblin-barrel','witch','night-witch','furnace')},exact_metadata=exact,
        record_count=len(records),training_counts=dict(Counter(
            f'position_based={r["position_based"]};usable={r["usable"]}' for r in training)),
        fallback_counts_by_split=dict(Counter(r['split'] for r in records if not r['position_based'])),
        training_trials=selected,records=records,sources=sources,
        script_sha256=sha(__file__),plan_sha256=sha(LOOP/'DEAL_RECOVERY_PLAN.md'))
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('exact_metadata_count','opposing_metadata_counts','record_count','training_counts','fallback_counts_by_split')}))
    print('DEAL_RECOVERY_SOURCE_AUDIT_PASS')

if __name__=='__main__':main()
