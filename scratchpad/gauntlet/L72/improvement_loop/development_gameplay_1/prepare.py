"""Select fixed native-loadable scenarios without policy predictions."""
from common import *
def main():
    assert not (HERE/'prepared.json').exists() and not OUT.exists()
    OUT.mkdir();bound=sources();stamp,S,runners=initialize()
    from pipeline.rl_royale import league_decks
    from pipeline.dataset_gen import card_key
    from pipeline.royale_env import UnsupportedDeck
    census=league_decks(CENSUS);scenarios=[];rejected=[]
    for opp in ('gen','s1'):
        for seed in SEEDS:
            found=False
            for j in range(50 if opp=='gen' else 1):
                d=S.opp_deck_for(seed*1000+j,census) if opp=='gen' else dict(name='icebow',engine=list(S.E.ICEBOW_ENGINE_DECK))
                spec=dict(opp=opp,seed=seed,side=seed%2,tag=f'l72-development-gameplay1:{opp}:{seed}',opp_deck=d['engine'],deck_name=d['name'],proposal=j)
                if opp=='gen' and any(card_key(n) not in runners['r1e'].opps['gen'][0].gid for n in d['engine']):
                    rejected.append(dict(**spec,reason='opponent vocabulary'));continue
                try:
                    m=setup(runners['r1e'],spec)
                except (UnsupportedDeck,KeyError,ValueError) as ex:
                    rejected.append(dict(**spec,reason=type(ex).__name__+': '+str(ex)));continue
                spec['initial_state_sha256']=blobsha(m.env.core.save_state())
                spec['loaded_forms']={str(k):v for k,v in m.env.loaded_forms.items()}
                scenarios.append(spec);found=True;break
            assert found,(opp,seed)
    from royalegym.protocol import Winner
    assert sources()==bound
    write(HERE/'prepared.json',dict(complete=True,sources=bound,runtime=stamp,winner_codes=dict(blue=int(Winner.BLUE),red=int(Winner.RED)),scenarios=scenarios,rejected_proposals=rejected,policy_predictions=0,optimizer_updates=0))
    print('GAMEPLAY_SCENARIOS_PREPARED')
if __name__=='__main__':main()
