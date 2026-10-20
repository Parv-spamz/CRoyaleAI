"""Independent complete-membership and seed-cluster outcome recount."""
import gzip,json
import numpy as np
from common import ROOT,HERE,OUT,ARMS,SEEDS,CKPTS,read,write,sha,check
from accounting import validate
def main():
    assert not (HERE/'results_verified.json').exists()
    p=check();done=read(HERE/'collection_complete.json');assert done['complete'] and done['matches']==192
    assert sha(OUT/'matches.jsonl')==done['index_sha256']
    index=[json.loads(line) for line in (OUT/'matches.jsonl').read_text().splitlines()]
    records=[];aggregate={a:{} for a in ARMS};behaviour={a:[] for a in ARMS}
    for row in index:
        path=ROOT/row['path'];assert sha(path)==row['sha256']
        with gzip.open(path,'rt',encoding='utf-8') as f:r=json.load(f)
        assert (r['model'],r['tag'],r['match']['outcome'])==(row['model'],row['tag'],row['outcome'])
        assert r['runtime']==p['runtime'] and r['checkpoint_sha256']==p['sources'][str(CKPTS[r['model']].relative_to(ROOT))]
        assert r['raw']['winner_side']=={p['winner_codes']['blue']:0,p['winner_codes']['red']:1}.get(r['raw']['core_winner'],-1)
        records.append({k:v for k,v in r.items() if k not in ('frames','accepted_plays')})
        side=r['match']['learner_side'];accepted=[x for x in r['accepted_plays'] if x['side']==side and not x.get('ability')]
        assert len(accepted)==r['match']['plays_accepted']
        assert len(r['accepted_plays'])==len([x for x in r['accepted_plays'] if x.get('accepted')])
        behaviour[r['model']].append(r['match']['behaviour'])
    validate(records,p['scenarios'],ARMS)
    for arm in ARMS:
        for opp in ('gen','s1','all'):
            rows=[r for r in records if r['model']==arm and (opp=='all' or r['match']['opp']==opp)]
            aggregate[arm][opp]=dict(games=len(rows),**{o:sum(r['match']['outcome']==o for r in rows) for o in ('win','loss','draw')},accepted=sum(r['match']['plays_accepted'] for r in rows),attempted=sum(r['match']['plays_attempted'] for r in rows),unlanded=sum(r['full_result']['plays_unlanded'] for r in rows),refused=sum(sum(v for k,v in r['full_result']['refuse_reasons'].items() if k!='match_over_before_landing') for r in rows))
    lookup={(r['model'],r['match']['opp'],r['match']['seed']):r for r in records};paired={}
    draw=np.random.default_rng(2026100507).integers(0,32,size=(10000,32))
    for control in ('r1e','ordinary_v5'):
        diffs=np.array([sum(int(lookup[('ordinary_v6',o,s)]['match']['outcome']=='win')-int(lookup[(control,o,s)]['match']['outcome']=='win') for o in ('gen','s1'))/2 for s in SEEDS])
        boot=diffs[draw].mean(1);paired[control]=dict(win_delta=float(diffs.mean()),ci95=np.quantile(boot,[.025,.975]).tolist(),seed_clusters=32,bootstrap_draws=10000)
    filters=dict(all192_complete=True,gen_vs_v5=aggregate['ordinary_v6']['gen']['win']>=aggregate['ordinary_v5']['gen']['win'],s1_vs_v5=aggregate['ordinary_v6']['s1']['win']>=aggregate['ordinary_v5']['s1']['win'],overall_vs_r1e=aggregate['ordinary_v6']['all']['win']>=aggregate['r1e']['all']['win'],no_new_refusals=aggregate['ordinary_v6']['all']['refused']<=aggregate['ordinary_v5']['all']['refused'])
    check();write(HERE/'results_verified.json',dict(complete=True,index_sha256=done['index_sha256'],aggregate=aggregate,paired=paired,filters=filters,continuation_passed=all(filters.values()),behaviour=behaviour,developmental_only=True,deployment_accepted=False))
    print('DEVELOPMENT_GAMEPLAY_INDEPENDENT_COMPLETE')
if __name__=='__main__':main()
