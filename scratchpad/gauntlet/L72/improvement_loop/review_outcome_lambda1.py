"""Bind completed lambda1 results and once-only model delivery; no model jobs."""
import argparse, hashlib, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
HERE = BASE / 'development_rl_2'
OUT = ROOT / 'icebow/data/bench/development_rl_2_20261005'
CHECKS = ROOT / 'scratchpad/gauntlet/L71/integration/checks'
PREFIX = 'l72-outcome-lambda1-'
ARM = 'outcome_lambda1_v5'
SENDER = ROOT / 'scratchpad/gauntlet/L69/discord/post.py'

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def write(p, x): p.write_text(json.dumps(x, indent=2, allow_nan=False)+'\n', encoding='utf-8')
def receipt(stage):
    p = CHECKS / (PREFIX+stage+'.json'); x = read(p); out = p.with_suffix('.out')
    assert x['exit_code'] == 0 and x['matched']
    assert hashlib.sha256(out.read_text(encoding='utf-8').encode()).hexdigest() == x['output_sha256']
    return dict(receipt_sha256=sha(p), output_file_sha256=sha(out), seconds=x['seconds'])

def main(phase):
    if phase == 'delivery':
        assert not (HERE/'reviewed_results.json').exists()
        e = read(HERE/'reviewed_evidence.json')
        assert e['complete'] and sha(HERE/'results_verified.json') == e['results_sha256']
        assert sha(HERE/'report_model.txt') == e['report_message_sha256'] and sha(SENDER) == e['sender_source_sha256']
        delivery = receipt('discord'); review = receipt('reviewed-evidence')
        chunks = (CHECKS/(PREFIX+'discord.out')).read_text(encoding='utf-8').count('HTTP 204')
        assert chunks == max(1, math.ceil(len((HERE/'report_model.txt').read_text(encoding='utf-8').strip())/1900))
        write(HERE/'reviewed_results.json', dict(e, evidence_sha256=sha(HERE/'reviewed_evidence.json'), evidence_review_receipt=review, delivery=delivery, delivery_chunks=chunks))
        print('OUTCOME_LAMBDA1_DELIVERY_REVIEWED'); return
    assert not (HERE/'reviewed_evidence.json').exists() and not (CHECKS/(PREFIX+'discord.json')).exists()
    r=read(HERE/'results_verified.json'); t=read(HERE/'trained.json'); p=read(HERE/'prepared.json')
    assert r['complete'] and r['rows']==54723 and r['continuation_passed']==all(r['filters'].values())
    assert not r['deployment_accepted'] and read(HERE/'chain_complete.json')['complete']
    assert t['complete'] and t['updates']==32 and t['games']==256
    assert sha(ROOT/t['checkpoint']) == t['checkpoint_sha256'] == r['checkpoint_sha256']
    assert sha(OUT/'train.jsonl') == t['train_log_sha256'] and sha(HERE/'prepared.json') == t['prepared_sha256']
    for path, digest in p['sources'].items(): assert sha(ROOT/path)==digest, path
    assert sha(OUT/'paired_replay_counts.json')==r['paired_sha256']
    assert sha(OUT/'all_replay_counts.json')==r['replay_counts_sha256']
    logs=[json.loads(z) for z in (OUT/'train.jsonl').read_text().splitlines()]
    assert [x['update'] for x in logs]==list(range(1,33)) and len(r['updates'])==32
    for i,(log,count) in enumerate(zip(logs,r['updates'])):
        assert log['games']==count['games']==8 and log['total_games']==(i+1)*8 and log['rows']==count['rows']
        assert log['critic_warmup']==(i<5) and log['ppo']['nonfinite'] is None and not log['stop']
        assert log['on_policy_maxdev']==count['ratio_maxdev']
        assert all(math.isfinite(log[k]) and log[k]<1e-4 for k in ('on_policy_maxdev','on_policy_torch_maxdev'))
        assert all(math.isfinite(log['ppo'][k]) for k in ('l_pg','l_v','grad_norm_mean','ratio_mean'))
    receipts={stage:receipt(stage) for stage in ('prepare','train','eval','independent')}
    paired=read(OUT/'paired_replay_counts.json'); summary={}
    for control,groups in paired.items():
        summary[control]={}
        for group,replays in groups.items():
            summary[control][group]={}
            for metric in ('action','card','aim1','log_correct','log_wrong'):
                vals=[x[metric] for x in replays.values()]
                assert sum(vals)==r['counts'][ARM][group][metric]-r['counts'][control][group][metric]
                summary[control][group][metric]=dict(net_rows=sum(vals),more=sum(x>0 for x in vals),less=sum(x<0 for x in vals),same=sum(x==0 for x in vals))
    old=read(BASE/'development_rl_1/results_verified.json')
    assert not old['continuation_passed'] and read(BASE/'development_rl_1/reviewed_results.json')['delivery_chunks']==1
    c=dict(r['counts'],outcome_rl_v5=old['counts']['outcome_rl_v5'])
    arms=('r1e_corrected','ordinary_v5','outcome_rl_v5',ARM)
    def nums(g,k): return '/'.join(str(c[a][g][k]) for a in arms)
    failed=[k for k,v in r['filters'].items() if not v]
    verdict='DEVELOPMENT FILTERS PASS' if r['continuation_passed'] else 'REJECTED for continuation'
    msg=(f'ClashBot NEW model outcome_lambda1_v5: {verdict}. NOT ACCEPTED / NOT DEPLOYED.\n'
         'Only learning change: GAE lambda .95->1, original ordinary_v5 parent. All32 updates/256 training games complete; final checkpoint only; finite/no guard stop.\n'
         'Fixed development counts: corrected-input R1e / ordinary_v5 / previous outcome_rl_v5 / new candidate. Parent exposure disclosed; these are agreement counts, not physical hits or untouched evidence.\n'
         f'Rocket aim <=1tile {nums("rocket","aim1")}/955; full Rocket {nums("rocket","action")}/955; late Rocket {nums("rocket_late_overtime_clock","action")}/320.\n'
         f'Barrel correct {nums("barrel_pro","log_correct")}, wrong {nums("barrel_pro","log_wrong")}, nonfired {nums("barrel_pro","log_not_fired")}, of63.\n'
         f'Witch {nums("witch","action")}/726; Night Witch {nums("night_witch","action")}/373; Furnace {nums("furnace","action")}/1174; defense {nums("defensive_sequence","action")}/8183.\n'
         f'Late all {nums("phase_late_overtime_clock","action")}/6422; general card {nums("all","card")}/17192; all action {nums("all","action")}/54723. PLAY/WAIT aggregates do not prove physical defensive value.\n'
         'Fails all3 Rocket material floors and Barrel/Witch/Night Witch/Furnace/defense protections; general-card and late-all protections pass.\n'
         'All71003 training rows/outcomes/returns/probabilities and54723 development predictions independently reconcile; exact canonical probability summary passes. Original RL1 failure remains preserved.\n'
         'No gameplay superiority, cycling/finishing/adaptation proof or deployment. All final material/component/statistical/untouched/gameplay/Q4/Q5 gates stay open. Owner STOP intact.\n')
    assert not r['continuation_passed'] and len(msg)<1900
    (HERE/'report_model.txt').write_text(msg,encoding='utf-8')
    write(HERE/'reviewed_evidence.json',dict(complete=True,results_sha256=sha(HERE/'results_verified.json'),checkpoint_sha256=t['checkpoint_sha256'],receipts=receipts,finite_updates=32,games=256,training_rows=sum(x['rows'] for x in r['updates']),paired=summary,previous_results_sha256=sha(BASE/'development_rl_1/results_verified.json'),previous_delivery_review_sha256=sha(BASE/'development_rl_1/reviewed_results.json'),report_message_sha256=sha(HERE/'report_model.txt'),continuation_passed=r['continuation_passed'],deployment_accepted=False,source_sha256=sha(Path(__file__)),sender_source_sha256=sha(SENDER)))
    print(json.dumps(dict(verdict=verdict,failed_filters=failed,message_characters=len(msg))));print('OUTCOME_LAMBDA1_EVIDENCE_REVIEWED')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('evidence','delivery'),required=True);main(parser.parse_args().phase)
