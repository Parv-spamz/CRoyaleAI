"""Bounded synthetic probe on the isolated idle native service only."""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
NATIVE = ROOT/'research/ext/cr-native-sandbox'
HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(NATIVE))
from native_core.card_catalog import CATALOG_PATH, card_cost
from native_core.decks import build_replay
from native_core.env import NativeRoyaleEnv


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    output = HERE/'native_elite_form_probe_v2.json'
    if output.exists():
        raise ValueError('Fresh output required')
    template_path=NATIVE/'examples/eight-card-bootstrap.json'
    template=json.loads(template_path.read_text(encoding='utf-8-sig'))
    assets=NATIVE/'runtime/extracted-assets/csv_logic'
    bound=[Path(__file__),HERE/'NATIVE_FORM_PROBE_PLAN.md',CATALOG_PATH,template_path,
           NATIVE/'native_core/env.py',NATIVE/'native_core/decks.py',
           NATIVE/'android_probe/native/jni_bridge.cpp',
           assets/'spells_characters.csv',assets/'spells_evolved.csv',
           assets/'characters/angry_barbarian_evo.toml']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in bound}
    expected=json.loads((HERE/'native_worker_rebuild.json').read_bytes())
    assert hashes[str((NATIVE/'android_probe/native/jni_bridge.cpp').relative_to(ROOT))]==expected['source_sha256']
    report=dict(started_at=time.strftime('%Y-%m-%dT%H:%M:%S'),port=37031,
        synthetic_only=True,model_calls=0,production_changes=False,source_hashes=hashes,
        seed=42,arms={},complete=False)
    def save():
        output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    save()
    try:
        with NativeRoyaleEnv(port=37031,timeout=20) as env:
            for name,target,flag in [('elite_base',26000043,0),('elite_evolution',26000043,1),
                                      ('knight_evolution_control',26000000,1)]:
                fillers=['Goblins','Skeletons','IceSpirits','FireSpirits','ElectroSpirit','Bats','SpearGoblins']
                deck=[fillers[0],fillers[1],{'card_id':target},*fillers[2:]]
                opponent=['Knight','Archer','Giant','Skeletons','Musketeer','HogRider','Cannon','Arrows']
                replay=build_replay(template,deck,opponent,seed=42)
                replay['battle']['deck0']['sp'][2]['el']=flag
                arm=dict(target=target,requested_form_flag=flag,replay=replay,plays=[],target_plays=[])
                report['arms'][name]=arm
                state=env.reset(replay,warmup_steps=100)
                arm['initial_state']=state
                for _ in range(60):
                    state=env.observe()
                    if state.get('tick',0)>=5000 or state.get('episode',{}).get('terminated'):
                        break
                    player=next(p for p in state['players'] if int(p['side'])==0)
                    hand=sorted(player['hand'],key=lambda c:(c['deck_index']!=2,card_cost(c['card_id']),c['deck_index']))
                    if not hand:
                        env.step(20)
                        continue
                    selected=hand[0]
                    cost=card_cost(selected['card_id'])
                    waits=0
                    while player['elixir']+1e-6<cost and waits<80 and state['tick']<5000:
                        env.step(10);state=env.observe()
                        player=next(p for p in state['players'] if int(p['side'])==0)
                        waits+=1
                    if state['tick']>=5000 or state.get('episode',{}).get('terminated'):
                        break
                    grid=env.probe_grid(side=0,deck_index=selected['deck_index'])
                    cells=[(abs(x-9)+abs(y-3),x,y) for y,row in enumerate(grid['rows'])
                           for x,v in enumerate(row) if v=='1']
                    if not cells:
                        raise ValueError('Empty native mask')
                    _,column,row=min(cells)
                    x=int((column+.5)*int(grid['cell_size']))
                    y=int((row+.5)*int(grid['cell_size']))
                    dry_run=env.probe(side=0,deck_index=selected['deck_index'],x=x,y=y)
                    if not dry_run.get('accepted'):
                        arm['failed_exact_probe']=dict(x=x,y=y,result=dry_run)
                        raise ValueError('Native grid/exact placement disagreement')
                    before_tick=int(state['tick'])
                    result=env.act(side=0,deck_index=selected['deck_index'],
                                   x=x,y=y)
                    entry=dict(tick=before_tick,deck_index=selected['deck_index'],card_id=selected['card_id'],
                               x=x,y=y,dry_run=dry_run,result=result)
                    arm['plays'].append(entry)
                    if not result.get('accepted'):
                        raise ValueError('Validated native action rejected')
                    env.step(1)
                    if selected['deck_index']==2 and result.get('accepted'):
                        after=env.observe()
                        entry['entities_after']=[e for e in after['entities'] if e.get('side')==0]
                        arm['target_plays'].append(entry)
                    save()
                    if len(arm['target_plays'])>=3:
                        break
                    env.step(20)
                arm['final_state']=env.observe()
                arm['resolved_sequence']=[p['result'].get('resolved_data_id') for p in arm['target_plays']]
                assert len(arm['target_plays'])==3, name+' incomplete target cycles'
                print(name,arm['resolved_sequence'],flush=True)
                save()
        assert report['arms']['elite_base']['resolved_sequence']==[26000043]*3
        assert report['arms']['knight_evolution_control']['resolved_sequence']==[26000000,26000000,13000000]
        report['elite_distinct_evolution_observed']=any(
            x!=26000043 for x in report['arms']['elite_evolution']['resolved_sequence'])
        assert all(sha(ROOT/p)==h for p,h in hashes.items()),'Source modified during probe'
        report['complete']=True
        save()
        print('NATIVE_ELITE_FORM_PROBE_V2_COMPLETE')
    except Exception as error:
        report['error']=repr(error)
        save()
        raise


if __name__=='__main__':
    main()
