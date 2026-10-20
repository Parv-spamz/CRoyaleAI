"""Independently reproduce deck selection and every policy's initial native state."""
from common import *
def main():
    assert not (HERE/'verified.json').exists()
    p=check();stamp,S,runners=initialize();assert stamp==p['runtime']
    from pipeline.rl_royale import league_decks,deck_weights
    from pipeline.dataset_gen import card_key
    from pipeline.royale_env import UnsupportedDeck
    import numpy as np
    census=league_decks(CENSUS);w=deck_weights([x['sides'] for x in census],.5,.5)
    assert [(x['opp'],x['seed']) for x in p['scenarios']]==[(o,s) for o in ('gen','s1') for s in SEEDS]
    rejections=[]
    for spec in p['scenarios']:
        for j in range(spec['proposal']+1):
            d=census[int(np.random.default_rng([spec['seed']*1000+j,69]).choice(len(census),p=w))] if spec['opp']=='gen' else dict(name='icebow',engine=list(S.E.ICEBOW_ENGINE_DECK))
            proposal={k:v for k,v in spec.items() if k not in ('initial_state_sha256','loaded_forms')};proposal.update(opp_deck=d['engine'],deck_name=d['name'],proposal=j)
            try:
                if spec['opp']=='gen' and any(card_key(n) not in runners['r1e'].opps['gen'][0].gid for n in d['engine']):reason='opponent vocabulary'
                else:
                    m=runners['r1e'].setup(spec['opp'],spec['seed'],d['engine'],tag=spec['tag'])
                    reason='ValueError: Unsupported original deck form' if m.env.form_fallbacks else None
            except (UnsupportedDeck,KeyError,ValueError) as ex:reason=type(ex).__name__+': '+str(ex)
            if j<spec['proposal']:
                assert reason;rejections.append(dict(**proposal,reason=reason))
            else:assert reason is None and d['engine']==spec['opp_deck'] and d['name']==spec['deck_name']
        for arm,run in runners.items():
            m=run.setup(spec['opp'],spec['seed'],spec['opp_deck'],tag=spec['tag'])
            assert m.learner.side==spec['side'] and not m.env.form_fallbacks
            assert blobsha(m.env.core.save_state())==spec['initial_state_sha256'],(arm,spec['tag'])
            assert {str(k):v for k,v in m.env.loaded_forms.items()}==spec['loaded_forms']
    assert rejections==p['rejected_proposals'];check()
    write(HERE/'verified.json',dict(complete=True,prepared_sha256=sha(HERE/'prepared.json'),scenarios=64,policy_setups=192,policy_predictions=0,optimizer_updates=0))
    print('GAMEPLAY_SCENARIOS_INDEPENDENT')
if __name__=='__main__':main()
