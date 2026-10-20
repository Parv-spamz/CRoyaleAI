import copy,gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def validate(rows):
    expected={f'{i}_{a}_{m}' for i in range(8) for a in ('r1e','ordinary_v5') for m in ('disabled','enabled')}
    ix={r['key']:r for r in rows};assert len(rows)==len(ix)==32 and set(ix)==expected
    pairs=[]
    for i in range(8):
        for arm in ('r1e','ordinary_v5'):
            a,b=[ix[f'{i}_{arm}_{m}'] for m in ('disabled','enabled')]
            for key in ('initial','accepted','native','runtime','checkpoint','tag','seed','opp','boundary'):assert a[key]==b[key],(i,arm,key)
            for m,r in [('disabled',a),('enabled',b)]:
                assert r['mode']==m and r['arm']==arm and r['scenario']==i
                assert r['seed']==2026100580+i//2 and r['opp']==('gen' if i%2==0 else 's1')
                assert r['native']['game_over'] and r['native']['terminated'] and not r['result']['wall_truncated']
                assert r['result']['form_fallbacks']==[] and r['result']['outcome']==a['result']['outcome']
            boundary=a['boundary'];assert boundary==6000
            assert [d for d in a['decisions'] if d['tick']<boundary]==b['decisions']
            assert all(d['tick']<boundary for d in b['decisions'])
            assert [f for f in a['frames'] if f['tick']<boundary]==[f for f in b['frames'] if f['tick']<boundary]
            for side in ('0','1'):assert [p for p in a['plays'][side] if p['tick']<boundary]==b['plays'][side]
            pairs.append(dict(scenario=i,arm=arm,fulltime=a['native']['tick']>=boundary,removed_decisions=len(a['decisions'])-len(b['decisions']),outcome=a['result']['outcome'],end_tick=a['native']['tick']))
    return pairs
def main():
    assert not (HERE/'verified.json').exists();r=read(HERE/'report.json');assert r['complete']
    receipt=read(ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-terminal-policy-collection.json');assert receipt['exit_code']==0 and receipt['matched']
    for p,h in r['sources'].items():assert sha(ROOT/p)==h
    rows=[]
    for item in r['records']:
        p=ROOT/item['path'];assert sha(p)==item['sha256']
        with gzip.open(p,'rt',encoding='utf-8') as f:x=json.load(f)
        assert x['key']==item['key'] and x['runtime']==r['runtime'];rows.append(x)
    pairs=validate(rows);bad=[rows[:-1],rows+[rows[0]]]
    pos=next(i for i,x in enumerate(rows) if x['mode']=='enabled')
    for key,value in [('accepted',[]),('native',{}),('initial',{}),('seed',0),('decisions',[dict(tick=6000,side=0)])]:
        test=copy.deepcopy(rows);test[pos][key]=value;bad.append(test)
    for test in bad:
        try:validate(test)
        except (AssertionError,KeyError):pass
        else:raise AssertionError('Corrupt policy record accepted')
    out=dict(complete=True,pairs=pairs,fulltime_pairs=sum(p['fulltime'] for p in pairs),removed_decisions=sum(p['removed_decisions'] for p in pairs),native_neutral=True,controls=dict(positive=1,negative=len(bad)),report_sha256=sha(HERE/'report.json'),policy_deployment_accepted=False,production_changed=False)
    (HERE/'verified.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));print('TERMINAL_POLICY_VERIFIED')
if __name__=='__main__':main()
