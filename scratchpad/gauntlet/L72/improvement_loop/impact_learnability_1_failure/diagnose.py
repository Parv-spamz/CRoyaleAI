"""Saved evidence only; no simulator or models imported."""
import copy, hashlib, json, re
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[4]
OLD=HERE.parent/'impact_learnability_1'
OUT=ROOT/'icebow/data/bench/impact_learnability_1_20261005'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def check(st):
    assert len(st)==2 and st[0]['results'][0]['status']==0
    q=st[1]; c=q['command']; r,=q['results']
    assert r['status']==7 and r['tick']==181 and r['card_id']==3
    assert all(r[k]==c[k] for k in ('team','hand_slot','x','y'))
    assert q['before']==q['after']
    k,=[e for e in q['before']['entities'] if e['team']==c['team'] and e['kind']==2 and e['card_id']==-1]
    x0,y0,x1,y1=k['footprint']; assert x0<c['x']<x1 and y0<c['y']<y1
    return dict(status='NO_DEPLOY',command=c,king_uid=k['uid'],king_footprint=k['footprint'],elixir_spent=0)
def main():
    assert not (HERE/'report.json').exists()
    started=read(OLD/'started.json')
    for p,h in started['sources'].items(): assert sha(ROOT/p)==h
    rec=CHECKS/'l72-impact-learning1-collect.json'; receipt=read(rec); log=rec.with_suffix('.out')
    assert receipt['exit_code']==1 and not receipt['matched']
    assert hashlib.sha256(log.read_text(encoding='utf-8').encode()).hexdigest()==receipt['output_sha256']
    assert 'collect.py", line 28' in log.read_text() and 'AssertionError' in log.read_text()
    protocol=ROOT/'research/ext/Royale-20261005/runtime/royalegym/protocol.py'
    assert re.search(r'^    NO_DEPLOY = 7$',protocol.read_text(),re.M)
    setup=read(OUT/'r152_setup.json'); failure=check(setup)
    negative=0
    for i in range(4):
        bad=copy.deepcopy(setup)
        if i==0: bad[1]['results'][0]['status']=0
        if i==1: bad[1]['command']['x']=0
        if i==2: bad[1]['after']['elixir'][1]-=1
        if i==3: bad[1]['results'][0]['tick']=180
        try: check(bad)
        except (AssertionError,ValueError): negative+=1
        else: raise AssertionError('corruption accepted')
    metas=sorted(OUT.glob('r*_meta.json')); raws=sorted(OUT.glob('r*_a*.json.gz'))
    assert len(metas)==152 and len(raws)==152*16
    assert [p.stem for p in metas]==[f'r{i:03}_meta' for i in range(152)]
    assert not any((OLD/n).exists() for n in ('collected.json','data_verified.json','training_started.json','trained.json','results_verified.json'))
    inventory={str(p.relative_to(ROOT)):sha(p) for p in sorted(OUT.iterdir()) if p.is_file()}
    (HERE/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    result=dict(complete=True,original_gate_pass=False,producer_completed_roots=152,independently_qualified_roots=0,
        saved_cast_branches=len(raws),saved_total_branches=len(list(OUT.glob('*.json.gz'))),failure=failure,
        controls=dict(positive=1,negative=negative),optimizer_updates=0,
        source_sha256=sha(Path(__file__)),original_sources=started['sources'],original_receipt_sha256=sha(rec),
        original_output_sha256=sha(log),original_seconds=receipt['seconds'],protocol_sha256=sha(protocol),
        inventory_sha256=sha(HERE/'inventory.json'),original_started_sha256=sha(OLD/'started.json'),
        original_failure_sha256=sha(OLD/'chain_failed.json'))
    (HERE/'report.json').write_text(json.dumps(result,indent=2)+'\n'); print('IMPACT_LEARNING_FAILURE_BOUND')
if __name__=='__main__': main()
