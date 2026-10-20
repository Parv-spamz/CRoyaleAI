"""Review completed fixed evidence and delivery; no fitting or message sending."""
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'development_iteration_5'
OUT=ROOT/'icebow/data/bench/development_iteration_5_20261005'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
ARM='tower_spatial_v7'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    assert not (HERE/'reviewed_results.json').exists()
    r=read(HERE/'results_verified.json');assert r['complete'] and r['rows']==54723
    assert not r['continuation_point_filter_passed'] and not r['deployment_accepted']
    assert read(HERE/'chain_complete.json')['complete']
    assert sha(OUT/'paired_replay_counts.json')==r['paired_sha256']
    assert sha(OUT/'all_replay_counts.json')==r['replay_counts_sha256']
    logs=[json.loads(line) for line in (OUT/ARM/'train.jsonl').read_text().splitlines()]
    assert [v['step'] for v in logs]==list(range(1,1001))
    assert all(math.isfinite(v['loss']) and all(math.isfinite(x) for x in v['parts'].values()) for v in logs)
    assert sha(OUT/ARM/'candidate.pt')==r['hashes'][ARM]['checkpoint']
    receipts={}
    for name in ('preflight','train','eval','independent','discord'):
        path=CHECKS/('l72-development5-'+name+'.json');v=read(path);output=path.with_suffix('.out')
        assert v['exit_code']==0 and v['matched']
        assert hashlib.sha256(output.read_text().encode()).hexdigest()==v['output_sha256']
        receipts[path.name]=dict(sha256=sha(path),output_file_sha256=sha(output),exit_code=0)
    delivery=CHECKS/'l72-development5-discord.out';assert delivery.read_text().count('HTTP 204')==1
    paired=read(OUT/'paired_replay_counts.json');summary={}
    for control,groups in paired.items():
        summary[control]={}
        for group,replays in groups.items():
            summary[control][group]={}
            for metric in ('action','card','aim1','log_correct','log_wrong'):
                vals=[v[metric] for v in replays.values()]
                totals=dict(net_rows=sum(vals),replays_more=sum(x>0 for x in vals),replays_less=sum(x<0 for x in vals),replays_same=sum(x==0 for x in vals))
                assert totals['net_rows']==r['counts'][ARM][group][metric]-r['counts'][control][group][metric]
                summary[control][group][metric]=totals
    result=dict(complete=True,results_sha256=sha(HERE/'results_verified.json'),receipts=receipts,
        finite_updates=1000,paired=summary,report_message_sha256=sha(HERE/'report_model.txt'),delivery_chunks=1,
        rejected=True,developmental_only=True,deployment_accepted=False)
    (HERE/'reviewed_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({g:summary['ordinary_v6'][g]['action'] for g in ('phase_late_overtime_clock','rocket_late_overtime_clock','rocket','defensive_sequence')}))
    print('TOWER_REVIEW_COMPLETE')
if __name__=='__main__':main()
