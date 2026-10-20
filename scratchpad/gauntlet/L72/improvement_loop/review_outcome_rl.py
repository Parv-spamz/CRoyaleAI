"""Review final-only outcome RL evidence and separately bind once-only delivery.

Runs only after the original independent recount. No inference or optimization.
This file is outside both frozen driver directories.
"""
import argparse,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
BASE=Path(__file__).resolve().parent
HERE=BASE/'development_rl_1'
RECOVERY=BASE/'development_rl_1_recovery'
OUT=ROOT/'icebow/data/bench/development_rl_1_20261005'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
ARM='outcome_rl_v5'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def receipt(name,success=True):
    p=CHECKS/(name+'.json');r=read(p);out=p.with_suffix('.out')
    assert (r['exit_code']==0 and r['matched']) if success else (r['exit_code']!=0 and not r['matched'])
    assert hashlib.sha256(out.read_text(encoding='utf-8').encode()).hexdigest()==r['output_sha256']
    return dict(receipt_sha256=sha(p),output_file_sha256=sha(out),exit_code=r['exit_code'])
def main(phase):
    if phase=='delivery':
        assert not (HERE/'reviewed_results.json').exists()
        e=read(HERE/'reviewed_evidence.json');assert e['complete']
        assert sha(HERE/'results_verified.json')==e['results_sha256'] and sha(HERE/'report_model.txt')==e['report_message_sha256']
        delivery=receipt('l72-outcome-rl-discord');review=receipt('l72-outcome-rl-reviewed-evidence')
        out=(CHECKS/'l72-outcome-rl-discord.out').read_text(encoding='utf-8');chunks=out.count('HTTP 204')
        expected=max(1,math.ceil(len((HERE/'report_model.txt').read_text(encoding='utf-8').strip())/1900));assert chunks==expected
        assert sha(ROOT/'scratchpad/gauntlet/L69/discord/post.py')==e['sender_source_sha256']
        write(HERE/'reviewed_results.json',dict(e,evidence_sha256=sha(HERE/'reviewed_evidence.json'),evidence_review_receipt=review,delivery=delivery,delivery_chunks=chunks,developmental_only=True,deployment_accepted=False))
        print('OUTCOME_RL_DELIVERY_REVIEWED');return
    assert not (HERE/'reviewed_evidence.json').exists() and not (CHECKS/'l72-outcome-rl-discord.json').exists()
    r=read(HERE/'results_verified.json');t=read(HERE/'trained.json');p=read(HERE/'prepared.json');v=read(RECOVERY/'verified.json')
    assert r['complete'] and r['rows']==54723 and r['continuation_passed']==all(r['filters'].values()) and not r['deployment_accepted']
    assert t['complete'] and t['updates']==32 and t['games']==256
    completed_chain=(RECOVERY/'chain_complete.json').exists()
    if completed_chain:assert read(RECOVERY/'chain_complete.json')['complete']
    else:
        assert read(RECOVERY/'chain_failed.json')['job']=='independent'
        assert not r['original_probability_summary_exact'] and not r['continuation_passed']
        assert sha(CHECKS/'l72-outcome-rl-independent.json')==r['preserved_independent_failure_sha256']
        for path,digest in r['recount_completion_binding'].items():assert sha(ROOT/path)==digest
    assert sha(ROOT/t['checkpoint'])==t['checkpoint_sha256']==r['checkpoint_sha256'] and sha(OUT/'train.jsonl')==t['train_log_sha256']
    for path,digest in {**p['sources'],**v['sources'],**v['original_failure']}.items():assert sha(ROOT/path)==digest
    assert sha(OUT/'paired_replay_counts.json')==r['paired_sha256'] and sha(OUT/'all_replay_counts.json')==r['replay_counts_sha256']
    logs=[json.loads(x) for x in (OUT/'train.jsonl').read_text().splitlines()]
    assert [x['update'] for x in logs]==list(range(1,33)) and len(r['updates'])==32
    for i,(log,count) in enumerate(zip(logs,r['updates'])):
        assert log['games']==count['games']==8 and log['total_games']==(i+1)*8 and log['rows']==count['rows']
        assert log['critic_warmup']==(i<5) and log['ppo']['nonfinite'] is None and not log['stop']
        assert math.isfinite(log['on_policy_maxdev']) and log['on_policy_maxdev']<1e-4
        assert all(math.isfinite(log['ppo'][k]) for k in ('l_pg','l_v','grad_norm_mean','ratio_mean'))
    stages=('prepare','setup-recovery','train-v2','eval')+(('independent',) if completed_chain else ('recount-diagnosis','independent-v2'))
    receipts={name:receipt('l72-outcome-rl-'+name) for name in stages}
    failed=receipt('l72-outcome-rl-train',False)
    independent_failure=None if completed_chain else receipt('l72-outcome-rl-independent',False)
    paired=read(OUT/'paired_replay_counts.json');summary={}
    for control,groups in paired.items():
        summary[control]={}
        for group,replays in groups.items():
            summary[control][group]={}
            for metric in ('action','card','aim1','log_correct','log_wrong'):
                vals=[x[metric] for x in replays.values()]
                assert sum(vals)==r['counts'][ARM][group][metric]-r['counts'][control][group][metric]
                summary[control][group][metric]=dict(net_rows=sum(vals),more=sum(x>0 for x in vals),less=sum(x<0 for x in vals),same=sum(x==0 for x in vals))
    arms=('r1e_corrected','ordinary_v5',ARM);c=r['counts']
    def nums(group,metric):return '/'.join(str(c[a][group][metric]) for a in arms)
    def total(group):return c[ARM][group]['rows']
    failed_filters=[k for k,x in r['filters'].items() if not x]
    verdict='DEVELOPMENT FILTERS PASS; new matched gameplay still required' if r['continuation_passed'] else 'REJECTED for development continuation'
    msg=(f'ClashBot NEW model outcome_rl_v5: {verdict}. NOT ACCEPTED / NOT DEPLOYED.\n'
      'Outcome-only PPO:32 updates/256 fresh training games (5 critic-only+27 policy), final checkpoint only. No new tactical rules or spell-frequency reward.\n'
      'Fixed internal-development counts below: corrected-input R1e / ordinary_v5 control / candidate. Parent exposure disclosed; these are not untouched or physical-hit results.\n'
      f'Rocket forced aim <=1 tile: {nums("rocket","aim1")}/{total("rocket")}; full expert actions {nums("rocket","action")}/{total("rocket")}; late Rocket actions {nums("rocket_late_overtime_clock","action")}/{total("rocket_late_overtime_clock")}.\n'
      f'Barrel correct {nums("barrel_pro","log_correct")}, wrong {nums("barrel_pro","log_wrong")}, not-fired {nums("barrel_pro","log_not_fired")}, of {total("barrel_pro")}.\n'
      f'Full actions Witch {nums("witch","action")}/{total("witch")}; Night Witch {nums("night_witch","action")}/{total("night_witch")}; Furnace {nums("furnace","action")}/{total("furnace")}; defense {nums("defensive_sequence","action")}/{total("defensive_sequence")}.\n'
      f'Late all actions {nums("phase_late_overtime_clock","action")}/{total("phase_late_overtime_clock")}; general card {nums("all","card")}/{c[ARM]["all"]["play"]}.\n'
      f'Failed fixed filters: {", ".join(failed_filters) if failed_filters else "none"}. All54723 rows and paired replay counts independently reconciled.\n'
      +('Original verifier exact summary comparison failed (max difference1.7e-21); retained as FALSE. Every per-row original1e-4 probability bound passes. Separate recount completed, no tolerance waiver.\n' if not completed_chain else '')+
      'No new gameplay superiority, safe Rocket cycling/finishing or adaptation proof. All final component/statistical/untouched/gameplay gates remain. Owner STOP intact. Initial setup failure and verified JSON-key recovery preserved; no completed training rerun.\n')
    assert len(msg)<3900
    (HERE/'report_model.txt').write_text(msg,encoding='utf-8')
    write(HERE/'reviewed_evidence.json',dict(complete=True,results_sha256=sha(HERE/'results_verified.json'),checkpoint_sha256=t['checkpoint_sha256'],receipts=receipts,original_failure=failed,independent_failure=independent_failure,finite_updates=32,games=256,paired=summary,report_message_sha256=sha(HERE/'report_model.txt'),continuation_passed=r['continuation_passed'],deployment_accepted=False,source_sha256=sha(Path(__file__)),sender_source_sha256=sha(ROOT/'scratchpad/gauntlet/L69/discord/post.py')))
    print(json.dumps(dict(verdict=verdict,failed_filters=failed_filters,message_characters=len(msg))));print('OUTCOME_RL_EVIDENCE_REVIEWED')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('evidence','delivery'),required=True);main(parser.parse_args().phase)
