"""Fixed synthetic controls for new descriptive state/history functions."""
import copy
from audit import tower_state,phase,lifetimes,bow_history,outcomes
from io_utils import *

def frame(t,bow=False,hp=3052,eid=7):
    towers=[[s,k,l,x,y,h,m] for s,y in ((0,6500),(1,25500))
        for k,l,x,h,m in [('king',None,9000,4824,4824),('princess','left',3500,hp if s==0 else 3052,3052),('princess','right',14500,3052,3052)]]
    return dict(tick=t,towers=towers,entities=[[1,15500,19500,'Xbow',1600,1600,13,27000008,eid]] if bow else [],elixir=[5,6])

def main():
    positive=negative=0
    f=frame(10);assert tower_state(f,0)['margin']==0;positive+=1
    f['towers'][0][5:]=[2000,10000];f['towers'][1][5:]=[1000,2000]
    f['towers'][3][5:]=[2000,4000];f['towers'][4][5:]=[900,1000]
    st=tower_state(f,0);assert st['margin']==100 and st['fraction_margin']<0;positive+=1
    bad=copy.deepcopy(f);bad['towers'].append(bad['towers'][0]);assert tower_state(bad,0) is None;negative+=1
    bad=copy.deepcopy(f);bad['towers'].pop();assert tower_state(bad,0) is None;negative+=1
    bad=copy.deepcopy(f);bad['towers'][1][1]='building';assert tower_state(bad,0) is None;negative+=1
    bad=copy.deepcopy(f);bad['towers'][1][5]=None;assert tower_state(bad,0) is None;negative+=1
    bad=copy.deepcopy(f);bad['towers'][1][6]=0;assert tower_state(bad,0) is None;negative+=1
    bad=copy.deepcopy(f);bad['towers'][1][5]=0
    assert tower_state(bad,0)['margin']!=st['margin'] and tower_state(bad,0)['crowns']==[0,1];negative+=1
    assert [phase(t) for t in (2399,2400,3599,3600,4799,4800)]==[
        'single_clock','double_regulation_clock','double_regulation_clock','early_overtime_clock','early_overtime_clock','late_overtime_clock'];positive+=1
    frames=[frame(10),frame(20,True),frame(30,True),frame(40,hp=2800),frame(50,hp=2800)]
    commands=[dict(tick=11,side=1,card='x-bow',x=15500,y=19500,cost=6)]
    labels={(1,11):{'offensive_xbow':True}};ticks=[f['tick'] for f in frames]
    h=lambda fs,t:bow_history(commands,labels,lifetimes(fs),fs,[f['tick'] for f in fs],1,t)
    assert h(frames,11)['status']=='none' and h(frames,25)['status']=='ongoing';positive+=1
    assert h(frames,45)['status']=='ended_enemy_princess_hp_drop';positive+=1
    changed=copy.deepcopy(frames);changed[3]['towers'][1][5]=100;changed[4]['towers'][1][5]=100
    assert h(changed,25)==h(frames,25);negative+=1
    changed=copy.deepcopy(frames);changed[2]['entities'][0][8]=99
    assert h(changed,45)['status']!='ended_enemy_princess_hp_drop';negative+=1
    changed=[frames[0],frames[1],frames[3],frames[4]]
    assert h(changed,45)['status']=='unknown';negative+=1
    reused=frames+[frame(60,True,eid=7),frame(70,hp=2800)]
    assert len(lifetimes(reused))==2 and h(reused,45)==h(frames,45);positive+=1
    assert not outcomes({},frames[0],tower_state(frames[0],1),1,10,frames,ticks,commands)['10']['covered'];negative+=1
    out=dict(complete=True,positive=positive,negative=negative,sources={p.name:sha(p) for p in (HERE/'controls.py',HERE/'audit.py',HERE/'METRICS.md')})
    assert not (HERE/'controls.json').exists();write(HERE/'controls.json',out);print(json.dumps(out));print('MATCH_ADAPTATION_CONTROLS_PASS')

if __name__=='__main__':main()
