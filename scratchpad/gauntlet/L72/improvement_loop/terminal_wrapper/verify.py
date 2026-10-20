"""Independent result accounting without simulator, policy or producer imports."""
import copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def validate(rows):
    expected={(s,cap,mode) for s,cap in [(i,7200) for i in range(8)]+[(i,5995) for i in range(2)] for mode in ('original','disabled','enabled')}
    ix={(r['seed'],r['cap'],r['mode']):r for r in rows}
    assert len(rows)==len(ix)==30 and set(ix)==expected
    details=[]
    for seed,cap in sorted({(s,c) for s,c,m in expected}):
        a,b,c=[ix[seed,cap,m] for m in ('original','disabled','enabled')]
        assert {k:v for k,v in a.items() if k!='mode'}=={k:v for k,v in b.items() if k!='mode'}
        assert a['boundary']==c['boundary']==6000
        for key in ('initial','prefix_state','accepted','final_state','end_tick','native_game_over','terminated','winner','crowns','outcome','episode'):
            assert a[key]==c[key],key
        assert all(d['tick']<6000 for d in c['decisions'])
        assert [d for d in a['decisions'] if d['tick']<6000]==c['decisions']
        assert all(p['tick']<6000 for p in c['accepted'])
        if cap>6000:assert c['native_game_over'] and c['terminated'] and c['end_tick']>6000
        else:assert c['end_tick']==cap and a['decisions']==c['decisions']
        # Already-committed pre-boundary command accounting stays identical.
        # Side play records keep original decision tick separately from landing.
        details.append(dict(seed=seed,cap=cap,original_decisions=len(a['decisions']),enabled_decisions=len(c['decisions']),outcome=c['outcome'],end_tick=c['end_tick']))
    full=[v for (s,c,m),v in ix.items() if c==7200 and m=='enabled']
    assert any(v['outcome'][0]=='draw' for v in full) and any(v['outcome'][0]!='draw' for v in full)
    assert sum(x['original_decisions']-x['enabled_decisions'] for x in details)>0
    return details
def main():
    assert not (HERE/'verified.json').exists()
    report=read(HERE/'report.json');assert report['complete'] and report['runs']==30
    receipt=read(ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-terminal-wrapper-native.json')
    assert receipt['exit_code']==0 and receipt['matched']
    for p,h in report['sources'].items():assert sha(ROOT/p)==h
    rows=[]
    for p,h in report['records'].items():assert sha(ROOT/p)==h;rows.append(read(ROOT/p))
    details=validate(rows);bad=[rows[:-1],rows+[rows[0]]]
    pos=next(i for i,r in enumerate(rows) if r['mode']=='enabled' and r['cap']==7200)
    for key,value in [('final_state','bad'),('accepted',[dict(tick=6001)]),('winner',99),('native_game_over',False),('end_tick',6000),('decisions',[dict(tick=6000)]),('mode','wrong'),('prefix_state','wrong')]:
        c=copy.deepcopy(rows);c[pos][key]=value;bad.append(c)
    for test in bad:
        try:validate(test)
        except (AssertionError,KeyError):pass
        else:raise AssertionError('Bad fixture result accepted')
    result=dict(complete=True,report_sha256=sha(HERE/'report.json'),receipt_sha256=sha(ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-terminal-wrapper-native.json'),details=details,
        controls=dict(positive=1,corruptions=len(bad)),models_or_predictions=0,production_integrated=False,final_acceptance=False)
    (HERE/'verified.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(details));print('TERMINAL_WRAPPER_VERIFIED')
if __name__=='__main__':main()
