"""Construct a source-bound research driver with only opening-deal changes."""
import hashlib
from pathlib import Path
import types

from solver import resolve,measure,validate_order

ROOT=Path(__file__).resolve().parents[5]
SOURCE=ROOT/'research/sandbox_tools/replay_drive.py'
EXPECTED='802b11a9ed975ae22b86e5fff91fb280a65bfb965cbf359b8ae426fdf60b6a53'
BEFORE='''    else:
        final = order_a
        out["deal_strategy"] = "NOT position-based: playing canonical order, expect card_not_in_hand rejections"
'''
AFTER='''    else:
        final, recovered_state, repair = _recover_deals(env, template, decks, plays, seed, level, out["tick_after_reset"])
        out["deal_strategy"] = "verified native opening permutation supporting original card sequence"
        out["deal_recovery"] = repair
'''
ANCHOR='''    out["opening_hand"] = {side: [item["name"] for item in player(state, side)["hand"]] for side in (0, 1)}'''

def load():
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED,'Original driver changed'
    text=raw.decode('utf-8').replace('\r\n','\n')
    assert text.count(BEFORE)==text.count(ANCHOR)==1
    changed=text.replace(BEFORE,AFTER).replace(ANCHOR,'    out["opening_deal_verified"] = _verify_opening(final, state, plays, out["tick_after_reset"])\n'+ANCHOR)
    # Exact inverse confirms all command-driving/grading/public capture code unchanged.
    assert changed.replace(AFTER,BEFORE).replace('    out["opening_deal_verified"] = _verify_opening(final, state, plays, out["tick_after_reset"])\n','')==text
    module=types.ModuleType('isolated_replay_deals');module.__file__=str(SOURCE)
    exec(compile(changed,str(SOURCE), 'exec'),module.__dict__)
    def sequence(decks,plays):
        return {s:[next(v['card_id'] for v in decks[s] if v['slug']==p['attr_card'])
                   for p in plays if p['side']==s and not p['ability']] for s in (0,1)}
    def positions(state,expected_tick):
        assert int(state['tick'])==expected_tick==10, 'Native bootstrap tick changed'
        result={}
        for s in (0,1):
            player=module.player(state,s)
            result[s]=dict(hand=list(player['hand_deck_indices']),queue=list(player['cycle_deck_indices']))
            assert player['next_deck_index']==result[s]['queue'][0]
        return result
    def verify_opening(order,state,plays,expected_tick):
        measured=measure(order,positions(state,expected_tick),sequence(order,plays))
        assert all(v['sequence_legal'] for v in measured.values()),'Final reset does not reproduce inferred opening'
        return measured
    def recover(env,template,decks,plays,seed,level,expected_tick):
        def reset(order):
            validate_order(decks,order)
            replay=module.build_replay(template,module.deck_spec(order[0],level),module.deck_spec(order[1],level),seed=seed)
            state=env.reset(replay,warmup_steps=0)
            return state,positions(state,expected_tick)
        return resolve(decks,sequence(decks,plays),reset,max_resets=61)
    module._recover_deals=recover;module._verify_opening=verify_opening
    module.patch_provenance=dict(original_sha256=EXPECTED,generated_source_sha256=hashlib.sha256(changed.encode()).hexdigest(),
        replacement_count=1,insertion_count=1,command_loop_unchanged=True)
    return module
