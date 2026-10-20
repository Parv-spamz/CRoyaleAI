"""Closeout: preserve failed fixture receipt, bind successful evidence and details."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'icebow/data/bench/opponent_hand_reader_20261006'
sys.path.insert(0,str(ROOT))
from pipeline.dataset_gen import card_key


def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    assert not (HERE/'reviewed.json').exists(),'Fresh closeout required'
    start=read(HERE/'started.json');c=read(HERE/'collected.json');v=read(HERE/'verified.json')
    assert v['complete'] and v['collected_sha256']==sha(HERE/'collected.json')
    assert c['started_sha256']==sha(HERE/'started.json')
    for p,h in start['bindings'].items():assert sha(ROOT/p)==h,p
    for p,h in c['outputs'].items():assert sha(OUT/p)==h,p
    receipts={}
    for name in ['tests','tests-v2','collect','independent']:
        p=ROOT/'scratchpad/gauntlet/L71/integration/checks'/('l72-opponent-hand-'+name+'.json')
        r=read(p)
        assert (r['exit_code'],r['matched'])==((1,False) if name=='tests' else (0,True))
        text=p.with_suffix('.out').read_text()
        assert hashlib.sha256(text.encode()).hexdigest()==r['output_sha256']
        receipts[name]=dict(path=str(p.relative_to(ROOT)),sha256=sha(p),seconds=r['seconds'],
                            exit_code=r['exit_code'],matched=r['matched'])
    counts=Counter();cards=defaultdict(Counter);bad_replays=set();examples=[]
    events={x['tag']:x for x in map(json.loads,(OUT/'events.jsonl').read_text().splitlines())}
    for row in map(json.loads,(OUT/'predictions.jsonl').read_text().splitlines()):
        if row['part']!='development':continue
        p=row['predictions']['public'];actual=set(row['truth'])
        counts['decisions']+=1
        counts['all_eight_revealed']+=len(p['revealed'])==8
        for card in p['in_hand']:
            cards[card]['in_claims']+=1;cards[card]['in_errors']+=card not in actual
        for card in p['out_of_hand']:
            cards[card]['out_claims']+=1;cards[card]['out_errors']+=card in actual
        if p['full_hand'] and set(p['in_hand'])!=actual:
            bad_replays.add(row['tag']);counts['full_errors_with_issue']+=bool(p['issues'])
            if len(examples)<3:
                ev=events[row['tag']];side=row['side'];tick=row['tick']
                examples.append(dict(tag=row['tag'],side=side,tick=tick,truth=row['truth'],
                    prediction=p['in_hand'],issues=p['issues'],
                    ideal_tail=[(e['tick'],card_key(e['card'])) for e in ev['ideal']
                                if e['side']==side and e['tick']<tick][-8:],
                    public_tail=[(e['tick'],card_key(e['card'])) for e in ev['public'][1-side]
                                 if e['tick']<tick][-8:]))
    counts['replays_with_full_error']=len(bad_replays)
    deck_coverage=Counter()
    for source in start['sources']:
        rec=read(ROOT/source['path'])
        for names in rec['final_decks'].values():
            for card in names:deck_coverage[card_key(card)]+=1
    details=dict(development_descriptive=dict(counts),per_card=dict(cards),
                 examples=examples,oracle_only_deck_coverage=dict(deck_coverage))
    (HERE/'details.json').write_text(json.dumps(details,indent=2))
    bindings={n:sha(HERE/n) for n in ['started.json','collected.json','verified.json',
        'details.json','README.md','REVIEW.md','review.py']}
    result=dict(complete=True,receipts=receipts,bindings=bindings,
        scope='Reader engineering only; conditional public estimates; policy unchanged',
        no_new_model=True,no_training=True,no_live_change=True)
    (HERE/'reviewed.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(counts=counts,mirror_deck_sides=deck_coverage['mirror'])))
    print('OPPONENT_HAND_REVIEWED')


if __name__=='__main__':main()
