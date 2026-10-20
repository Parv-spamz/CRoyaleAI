"""Short, excluded CPU control for telemetry neutrality and accounting failures."""
import copy
from common import *
from accounting import validate
def main():
    assert not (HERE/'prelaunch.json').exists()
    p=check();v=read(HERE/'verified.json');assert v['complete'] and v['prepared_sha256']==sha(HERE/'prepared.json')
    stamp,S,runners=initialize();run=runners['ordinary_v6']
    spec=dict(opp='s1',seed=2026100499,side=1,opp_deck=list(S.E.ICEBOW_ENGINE_DECK),tag='l72-gameplay1-smoke-excluded')
    traces=[]
    for enabled in (False,True):
        run.lcfg['behaviour_telemetry']=enabled
        m=setup(run,spec);m.env.tail_cap=300
        r=run.play('plain',m)
        traces.append(dict(final=blobsha(m.env.core.save_state()),accepted=m.learner.accepted,opp_accepted=m.opp.accepted,plays=m.learner.plays,opp_plays=m.opp.plays,end_tick=r['end_tick']))
    assert traces[0]==traces[1],'Telemetry altered short control'
    fixture=dict(model='m',tag='t',initial_state_sha256='h',match=dict(opp='s1',seed=2,learner_side=0,opp_deck=['d'],wall_truncated=False,form_fallbacks=[],end_tick=6000,crowns_for=1,crowns_against=0,outcome='win',plays_attempted=1,plays_accepted=1),raw=dict(terminated=True,core_game_over=True,end_tick=6000,crowns=[1,0],winner_side=0),full_result=dict(outcome='win',plays_attempted=1,plays_accepted=1))
    fs=[dict(tag='t',initial_state_sha256='h',opp='s1',seed=2,side=0,opp_deck=['d'])]
    assert validate([fixture],fs,['m']);bad=[]
    bad += [[],[fixture,fixture]]
    for path,value in [(('tag',),'other'),(('match','outcome'),'loss'),(('match','crowns_for'),2),(('match','wall_truncated'),True),(('match','opp_deck'),['wrong']),(('raw','terminated'),False),(('initial_state_sha256',),'changed')]:
        q=copy.deepcopy(fixture);at=q
        for k in path[:-1]:at=at[k]
        at[path[-1]]=value;bad.append([q])
    for rows in bad:
        try:validate(rows,fs,['m'])
        except (AssertionError,KeyError):pass
        else:raise AssertionError('Corruption accepted')
    check();write(HERE/'prelaunch.json',dict(complete=True,prepared_sha256=sha(HERE/'prepared.json'),verified_sha256=sha(HERE/'verified.json'),runtime=stamp,telemetry_neutral=True,smoke_seed=spec['seed'],smoke_cap=300,smoke_full_games=0,controls=dict(positive=1,negative=len(bad)),collection_allowed=True,optimizer_updates=0,deployment_accepted=False))
    print('GAMEPLAY_PREFLIGHT_COMPLETE')
if __name__=='__main__':main()
