"""Bounded synthetic identity/cost probe; no expert replay or model invocation."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
LOOP=HERE.parent
NATIVE=ROOT/'research/ext/cr-native-sandbox'
sys.path[:0]=[str(LOOP),str(ROOT)]
from native_catalog_overlay import activate
activate()
from native_core.env import NativeRoyaleEnv
from native_core.decks import build_replay
from native_core.card_catalog import card_cost
from research.sandbox_tools.replay_drive import public_object_evidence
from native_capture_identity import canonical_frames

def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def player(s):return next(p for p in s['players'] if p['side']==0)
def frame(s):return dict(tick=s['tick'],players=s['players'],entities=s['entities'],public_objects=public_object_evidence(s))

def main():
    out=HERE/'probe.json';assert not out.exists()
    audit=read(HERE/'audit.json');assert audit['complete']
    hashes={**audit['sources'],**{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'audit.json',
        LOOP/'native_catalog_overlay.py',LOOP/'native_catalog_corrected.json',LOOP/'native_capture_identity.py',
        NATIVE/'native_core/env.py',NATIVE/'native_core/decks.py',NATIVE/'examples/eight-card-bootstrap.json']}}
    remote=read(LOOP/'native_capture_v2_remote_hashes.json')
    def attest():
        r=subprocess.run(['C:/Android/Sdk/platform-tools/adb.exe','-s','emulator-5560','shell','sha256sum',*remote],text=True,capture_output=True,check=True)
        assert {x.split()[1]:x.split()[0] for x in r.stdout.splitlines()}==remote
        for p,h in hashes.items():assert sha(ROOT/p)==h,p
    attest()
    result=dict(complete=False,sources=hashes,guest_hashes=remote,arms={},synthetic_only=True,model_predictions=0)
    def save():out.write_text(json.dumps(result,indent=2))
    save()
    try:
        template=json.loads((NATIVE/'examples/eight-card-bootstrap.json').read_text(encoding='utf-8-sig'))
        with NativeRoyaleEnv(port=38031,timeout=20) as env:
            for name,target in [('void',28000023),('arrows_control',28000001),('void_repeat',28000023)]:
                deck=['Goblins','Skeletons',target,'IceSpirits','FireSpirits','ElectroSpirit','Bats','SpearGoblins']
                replay=build_replay(template,deck,['Knight','Archer','Giant','Skeletons','Musketeer','HogRider','Cannon','Arrows'],seed=42)
                arm=dict(target=target,replay=replay,plays=[]);result['arms'][name]=arm
                state=env.reset(replay,warmup_steps=100);arm['initial']=frame(state)
                for _ in range(9):
                    assert state['tick']<1000 and not state['episode']['terminated']
                    selected=min(player(state)['hand'],key=lambda c:(c['card_id']!=target,card_cost(c['card_id']),c['deck_index']))
                    while player(state)['elixir']<card_cost(selected['card_id']):
                        assert state['tick']<990;env.step(10);state=env.observe()
                    grid=env.probe_grid(side=0,deck_index=selected['deck_index'])
                    _,x,y=min((abs(x-9)+abs(y-(22 if selected['card_id']==target else 3)),x,y)
                        for y,row in enumerate(grid['rows']) for x,v in enumerate(row) if v=='1')
                    x=int((x+.5)*grid['cell_size']);y=int((y+.5)*grid['cell_size'])
                    assert env.probe(side=0,deck_index=selected['deck_index'],x=x,y=y)['accepted']
                    before=env.observe();played=env.act(side=0,deck_index=selected['deck_index'],x=x,y=y);after=env.observe()
                    entry=dict(card_id=selected['card_id'],deck_index=selected['deck_index'],x=x,y=y,
                        before=frame(before),after=frame(after),result=played)
                    arm['plays'].append(entry);save()
                    assert played['accepted'] and before['tick']==after['tick']
                    entry['measured_cost']=player(before)['elixir']-player(after)['elixir']
                    if selected['card_id']==target:
                        arm['target_play']=entry;arm['frames']=[frame(after)]
                        for _ in range(10):env.step(10);arm['frames'].append(frame(env.observe()))
                        break
                    env.step(4);state=env.observe()
                assert 'target_play' in arm and len(arm['plays'])<=9
                assert arm['target_play']['result']['resolved_data_id']==target
                assert abs(arm['target_play']['measured_cost']-card_cost(target))<1e-6
                save()
        a=result['arms']['void'];b=result['arms']['void_repeat']
        assert [(p['card_id'],p['x'],p['y'],p['before']['tick'],p['measured_cost']) for p in a['plays']]==[(p['card_id'],p['x'],p['y'],p['before']['tick'],p['measured_cost']) for p in b['plays']]
        assert canonical_frames(a['frames'])==canonical_frames(b['frames'])
        attest();result['complete']=True;save();print('VOID_NATIVE_COST_CAPTURE_COMPLETE')
    except BaseException as e:
        result['error']=repr(e);save();raise

if __name__=='__main__':main()
