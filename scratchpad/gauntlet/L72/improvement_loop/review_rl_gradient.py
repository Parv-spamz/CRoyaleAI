"""Close out gradient diagnostics without inference, backward passes or optimization."""
import copy, hashlib, json, statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'rl_gradient_audit'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def membership(rows):
    assert len(rows)==27 and [r['update'] for r in rows]==list(range(6,33))
    assert all(r['pre_checkpoint_update']==r['update']-1 and r['sample_rows']==256 for r in rows)
def main():
    assert not (HERE/'reviewed.json').exists()
    r=read(HERE/'report.json');v=read(HERE/'verified.json')
    assert r['complete'] and v['complete'] and read(HERE/'chain_complete.json')['complete']
    assert v['report_sha256']==sha(HERE/'report.json') and v['source_sha256']==sha(HERE/'verify.py')
    assert v['updates']==27 and v['rows']==6912 and v['controls']==dict(positive=3,negative=8)
    assert r['optimizer_updates']==r['development_predictions']==v['optimizer_updates']==0
    assert not r['new_checkpoint'] and not v['new_checkpoint'] and not v['accepted']
    membership(r['updates'])
    corrupt=[copy.deepcopy(r['updates']) for _ in range(4)]
    corrupt[0].pop();corrupt[1][-1]=copy.deepcopy(corrupt[1][0]);corrupt[2][0]['update']=5;corrupt[3][0]['pre_checkpoint_update']=6
    for rows in corrupt:
        try:membership(rows)
        except AssertionError:pass
        else:raise AssertionError('Corrupt update membership accepted')
    for p,h in r['source_binding'].items():assert sha(ROOT/p)==h
    logs=[json.loads(line) for line in (ROOT/'icebow/data/bench/development_rl_1_20261005/train.jsonl').read_text().splitlines()]
    for row,summary in zip(r['updates'],v['summaries']):
        assert row['update']==summary['update'] and row['weights_unchanged'] and row['optimizer_updates']==0
        assert row['beta']==logs[row['update']-2]['beta_next']
        assert row['cohort_rows']==logs[row['update']-1]['rows']
        assert sha(ROOT/row['gradient_file'])==row['gradient_sha256']
        for p,h in row['inputs'].items():assert sha(ROOT/p)==h
        for key in ('pg_norm','vf_norm','dot','cosine','vf_share'):
            assert abs(row['metrics'][key]-summary[key])<=1e-10*max(1.,abs(summary[key]))
    receipts={}
    for name,token in [('l72-rl-gradient-collection','RL_GRADIENT_COLLECTED'),('l72-rl-gradient-independent','RL_GRADIENT_VERIFIED')]:
        p=CHECKS/(name+'.json');e=read(p);out=p.with_suffix('.out');text=out.read_text(encoding='utf-8')
        assert e['exit_code']==0 and e['matched'] and token in text and hashlib.sha256(text.encode()).hexdigest()==e['output_sha256']
        receipts[name]=dict(receipt_sha256=sha(p),output_sha256=sha(out),seconds=e['seconds'])
    shares=[x['vf_share'] for x in v['summaries']];cosines=[x['cosine'] for x in v['summaries']]
    result=dict(complete=True,report_sha256=sha(HERE/'report.json'),verified_sha256=sha(HERE/'verified.json'),source_sha256=sha(Path(__file__)),receipts=receipts,updates=27,rows=6912,membership_controls=dict(positive=1,negative=4),critic_larger=sum(x['critic_larger'] for x in v['summaries']),opposed=sum(x['opposed'] for x in v['summaries']),vf_share=dict(min=min(shares),median=statistics.median(shares),max=max(shares)),cosine=dict(min=min(cosines),median=statistics.median(cosines),max=max(cosines)),optimizer_updates=0,new_checkpoint=False,accepted=False,causal_performance_claim=False)
    (HERE/'reviewed.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('RL_GRADIENT_REVIEWED')
if __name__=='__main__':main()
