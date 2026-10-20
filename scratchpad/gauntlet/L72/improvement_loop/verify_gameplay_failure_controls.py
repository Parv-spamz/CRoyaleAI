"""Exercise the exact independent refusal-accounting fragment without rerunning records."""
import collections,copy,hashlib,json,textwrap
from pathlib import Path
HERE=Path(__file__).resolve().parent/'gameplay_failure_audit'
p=HERE/'verify_v2.py';source=p.read_text()
fragment=textwrap.dedent(source[source.index('        refused='):source.index('        for tick,name')])
code=compile(fragment,str(p)+':refusal-fragment','exec')
plays=[dict(tick=5980,land_tick=6006,reason='game_over',card='Log',accepted=False),dict(tick=6000,land_tick=6026,reason='game_over',card='Log',accepted=False)]
base=dict(fr={'plays':plays,'refuse_reasons':{'game_over':2}},m={'end_tick':6100,'outcome':'loss'},d={'accepted_plays':[{'tick':5999}]},
    q={'rejected':[{k:v for k,v in x.items() if k!='accepted'} for x in plays],'reasons':{'game_over':2},'end_tick':6100,'outcome':'loss','game_over_decided_before':1,'game_over_decided_after':1})
def run(env):exec(code,dict(collections=collections),env)
run(copy.deepcopy(base));bad=[]
for key,value in [('end_tick',6099),('outcome','win'),('game_over_decided_before',2),('game_over_decided_after',0)]:
    v=copy.deepcopy(base);v['q'][key]=value;bad.append(v)
v=copy.deepcopy(base);v['fr']['refuse_reasons']={'out_of_territory':2};bad.append(v)
v=copy.deepcopy(base);v['d']['accepted_plays'][0]['tick']=6000;bad.append(v)
v=copy.deepcopy(base);v['fr']['plays'][0]['land_tick']=5999;v['q']['rejected'][0]['land_tick']=5999;bad.append(v)
for env in bad:
    try:run(env)
    except AssertionError:pass
    else:raise AssertionError('corrupt refusal accounting accepted')
target=HERE/'accounting_controls.json';assert not target.exists()
target.write_text(json.dumps(dict(complete=True,positive=1,negative=len(bad),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),fragment_sha256=hashlib.sha256(fragment.encode()).hexdigest()),indent=2)+'\n')
print('GAMEPLAY_FAILURE_ACCOUNTING_CONTROLS_COMPLETE')
