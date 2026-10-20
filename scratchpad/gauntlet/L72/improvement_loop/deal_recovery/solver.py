"""Generic offline deal fitting using measured tick-zero positions, never tactics."""
import copy
import itertools
import json

MAX_RESETS=64

class UnresolvedDeal(ValueError):
    def __init__(self,history):
        super().__init__('No source-consistent native opening within fixed reset budget')
        self.history=history

def legal(hand,queue,sequence):
    if len(hand)!=4 or len(queue)!=4 or len(set(hand+queue))!=8:return False
    current=set(hand); pending=list(queue)
    for card in sequence:
        if card not in current:return False
        current.remove(card);current.add(pending.pop(0));pending.append(card)
    return True

def infer(sequence,cards):
    return [(list(h),list(q)) for h in itertools.combinations(cards,4)
            for q in itertools.permutations([c for c in cards if c not in h]) if legal(list(h),list(q),sequence)]

def validate_order(original,order):
    assert set(original)==set(order)=={0,1}
    for side in (0,1):
        a={v['card_id']:v for v in original[side]};b={v['card_id']:v for v in order[side]}
        assert len(a)==len(b)==len(original[side])==len(order[side])==8
        assert a==b,'Deck identity/form/level changed'

def measure(order,positions,sequences):
    measured={}
    for side in (0,1):
        h,q=positions[side]['hand'],positions[side]['queue']
        assert sorted(h+q)==list(range(8)) and len(h)==len(q)==4
        hand=[order[side][i]['card_id'] for i in h]
        queue=[order[side][i]['card_id'] for i in q]
        measured[side]=dict(hand_positions=h,queue_positions=q,hand=hand,queue=queue,
                            sequence_legal=legal(hand,queue,sequences[side]))
    return measured

def resolve(original,sequences,reset,max_resets=MAX_RESETS):
    assert 1<=max_resets<=MAX_RESETS
    validate_order(original,original)
    deals={s:infer(sequences[s],[v['card_id'] for v in original[s]]) for s in (0,1)}
    assert all(deals.values()),'No legal abstract deal for source sequence'
    order=copy.deepcopy(original);history=[];seen=set();cursor={0:0,1:0}
    for attempt in range(max_resets):
        validate_order(original,order)
        key=tuple(tuple(v['card_id'] for v in order[s]) for s in (0,1))
        assert key not in seen,'Repeated permutation reached reset'
        seen.add(key)
        state,positions=reset(order)
        m=measure(order,positions,sequences)
        history.append(dict(attempt=attempt,orders={s:[v['card_id'] for v in order[s]] for s in (0,1)},measured=m))
        if all(m[s]['sequence_legal'] for s in (0,1)):
            return order,state,dict(resets=len(history),budget=max_resets,history=history)
        # Two fits per inferred assignment allow a position change to settle.
        # Move on deterministically when an arrangement repeats or stays invalid.
        proposed=None
        for _ in range(2*max(len(v) for v in deals.values())):
            candidate=copy.deepcopy(order)
            exhausted=False
            for s in (0,1):
                if m[s]['sequence_legal']:continue
                deal_index=cursor[s]//2;cursor[s]+=1
                if deal_index>=len(deals[s]):exhausted=True;break
                hand,queue=deals[s][deal_index]
                by_id={v['card_id']:v for v in original[s]}
                for position,card in zip(m[s]['hand_positions']+m[s]['queue_positions'],hand+queue):
                    candidate[s][position]=by_id[card]
            if exhausted:break
            candidate_key=tuple(tuple(v['card_id'] for v in candidate[s]) for s in (0,1))
            if candidate_key not in seen:proposed=candidate;break
        if proposed is None:break
        order=proposed
    raise UnresolvedDeal(history)

def self_test():
    original={s:[dict(card_id=i+s*10,form='evolution' if i==0 else 'base') for i in range(8)] for s in (0,1)}
    seq={s:[i+s*10 for i in [7,6,5,4,3,2,1,0]] for s in (0,1)}
    calls=[]
    def fixed(order):
        calls.append(copy.deepcopy(order))
        return {},{s:dict(hand=[0,1,2,3],queue=[4,5,6,7]) for s in (0,1)}
    final,_,r=resolve(original,seq,fixed)
    assert r['resets']<=64 and len(calls)==r['resets'];validate_order(original,final)
    # Both sides' positions can depend on a changed deck. The final measured
    # opening, rather than an assumed position map, decides whether to accept.
    def coupled(order):
        shift=order[0][0]['card_id']%2
        p=[(i+shift)%8 for i in range(8)]
        return {},{s:dict(hand=p[:4],queue=p[4:]) for s in (0,1)}
    final,_,r2=resolve(original,seq,coupled)
    assert all(x['sequence_legal'] for x in r2['history'][-1]['measured'].values())
    negatives=[]
    def reject(name,fn):
        try:fn()
        except (AssertionError,ValueError):negatives.append(name)
        else:raise AssertionError('Corruption accepted: '+name)
    bad=copy.deepcopy(original);bad[0][0]['form']='base'
    reject('changed_form',lambda:validate_order(original,bad))
    bad2=copy.deepcopy(original);bad2[0][0]['card_id']=9
    reject('changed_card',lambda:validate_order(original,bad2))
    reject('illegal_sequence',lambda:resolve(original,{0:[7,7],1:seq[1]},fixed))
    reject('bad_positions',lambda:resolve(original,seq,lambda o:({}, {s:dict(hand=[0]*4,queue=[4,5,6,7]) for s in (0,1)})))
    reject('budget_escalation',lambda:resolve(original,seq,fixed,65))
    attempts=[]
    def impossible(order):
        attempts.append(order)
        # Native fixture always keeps the first requested card outside hand.
        pos={}
        for s in (0,1):
            target=next(i for i,v in enumerate(order[s]) if v['card_id']==seq[s][0])
            rest=[i for i in range(8) if i!=target]
            pos[s]=dict(hand=rest[:4],queue=[target]+rest[4:])
        return {},pos
    try:resolve(original,seq,impossible,3)
    except UnresolvedDeal as e:
        assert len(e.history)==len(attempts)==3
        assert len({json.dumps(h['orders'],sort_keys=True) for h in e.history})==3
        negatives.append('unachievable_bounded_no_repeats')
    else:raise AssertionError('Unachievable deal accepted')
    print(json.dumps(dict(positive_checks=2,rejected=negatives,reset_counts=[r['resets'],r2['resets']])))
    print('DEAL_RECOVERY_SOLVER_CONTROLS_PASS')

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--self-test',action='store_true')
    if ap.parse_args().self_test:self_test()
