"""Review completed game evidence and receipts without inference or replaying games."""
import argparse, collections, gzip, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent/'development_gameplay_1'
OUT=ROOT/'icebow/data/bench/development_gameplay_1_20261005'
CHECKS=ROOT/'scratchpad/gauntlet/L71/integration/checks'
sys.path.insert(0,str(HERE))
from common import check

def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def receipt(name,success=True):
    p=CHECKS/f'l72-development-gameplay1-{name}.json';r=read(p);o=p.with_suffix('.out')
    assert hashlib.sha256(o.read_text().encode()).hexdigest()==r['output_sha256']
    assert (r['exit_code']==0 and r['matched'])==success
    if not success:assert r['exit_code']!=0
    return dict(sha256=sha(p),output_sha256=sha(o),exit_code=r['exit_code'],matched=r['matched'],seconds=r['seconds'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--delivery',action='store_true');args=ap.parse_args()
    p=check();r=read(HERE/'results_verified.json')
    assert r['complete'] and read(HERE/'chain_complete.json')['complete'] and not r['deployment_accepted']
    assert r['continuation_passed']==all(r['filters'].values())
    assert sha(OUT/'matches.jsonl')==r['index_sha256']
    if args.delivery:
        target=HERE/'reviewed_results.json';assert not target.exists()
        s=read(HERE/'reviewed_stats.json');assert s['results_sha256']==sha(HERE/'results_verified.json')
        d=receipt('discord');assert (CHECKS/'l72-development-gameplay1-discord.out').read_text().count('HTTP 204')==1
        s.update(report_message_sha256=sha(HERE/'report_gameplay_addendum.txt'),delivery=d,delivery_chunks=1)
        target.write_text(json.dumps(s,indent=2)+'\n');print('GAMEPLAY_DELIVERY_REVIEW_COMPLETE');return
    target=HERE/'reviewed_stats.json';assert not target.exists()
    receipts={n:receipt(n) for n in ('prepared-v2','setup-independent','preflight-v2','collection','independent')}
    failures={n:receipt(n,False) for n in ('prepared','preflight')}
    rows=[json.loads(x) for x in (OUT/'matches.jsonl').read_text().splitlines()];assert len(rows)==192
    reasons={a:collections.Counter() for a in r['aggregate']};mix={a:collections.Counter() for a in reasons}
    behaviour={a:collections.Counter() for a in reasons};games={};members=[]
    for row in rows:
        path=ROOT/row['path'];assert sha(path)==row['sha256']
        with gzip.open(path,'rt') as f:d=json.load(f)
        a=d['model'];fr=d['full_result'];plays=fr['plays'];key=(a,d['match']['opp'],d['match']['seed'])
        assert key not in games;games[key]=int(d['match']['outcome']=='win')
        actual=collections.Counter(x['reason'] for x in plays if not x['accepted'])
        assert actual==collections.Counter(fr['refuse_reasons'])
        assert len(plays)==fr['plays_attempted'] and sum(x['accepted'] for x in plays)==fr['plays_accepted']
        assert actual['match_over_before_landing']==fr['plays_unlanded']
        reasons[a].update(actual);mix[a].update(fr['card_mix_accepted'])
        b=d['match']['behaviour'];behaviour[a]['accepted']+=b['accepted_plays']
        for k in ('rocket_share','tower_rocket_share','tower_hit_hp_confirmation','preemptive_log'):
            behaviour[a][k+'_n']+=b[k]['n'];behaviour[a][k+'_denominator']+=b[k]['denominator']
        for k in ('finish_offs','multi_rocket_cycles','defensive_rockets','rocket_then_tornado','tornado_then_rocket','defensive_xbows','unknown_rocket_impacts'):
            behaviour[a][k]+=b[k]
        members.append(dict(model=a,tag=d['tag'],outcome=d['match']['outcome'],checkpoint=d['checkpoint_sha256'],record_sha256=row['sha256']))
    paired={}
    for control in ('r1e','ordinary_v5'):
        paired[control]={}
        for opp in ('gen','s1','all'):
            vals=[v-games[(control,o,s)] for (a,o,s),v in games.items() if a=='ordinary_v6' and (opp=='all' or o==opp)]
            paired[control][opp]=dict(better=sum(x>0 for x in vals),worse=sum(x<0 for x in vals),same=sum(x==0 for x in vals),net=sum(vals))
            assert sum(vals)==r['aggregate']['ordinary_v6'][opp]['win']-r['aggregate'][control][opp]['win']
    for a in reasons:
        agg=r['aggregate'][a]['all'];assert sum(mix[a].values())==agg['accepted']==behaviour[a]['accepted']
        assert sum(reasons[a].values())+agg['accepted']==agg['attempted']
        assert sum(v for k,v in reasons[a].items() if k!='match_over_before_landing')==agg['refused']
    result=dict(complete=True,results_sha256=sha(HERE/'results_verified.json'),index_sha256=sha(OUT/'matches.jsonl'),
        sources=p['sources'],runtime=p['runtime'],receipts=receipts,preserved_failures=failures,members=members,
        aggregate=r['aggregate'],paired=r['paired'],paired_games=paired,filters=r['filters'],refusal_reasons=reasons,
        accepted_card_mix=mix,behaviour_descriptive=behaviour,continuation_passed=r['continuation_passed'],
        refusal_limit='Frozen count excludes only match_over_before_landing; game_over is retained and is not ordinary legality failure.',
        developmental_only=True,deployment_accepted=False)
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('paired_games','refusal_reasons','behaviour_descriptive')},indent=2))
    print('GAMEPLAY_REVIEW_COMPLETE')
if __name__=='__main__':main()
