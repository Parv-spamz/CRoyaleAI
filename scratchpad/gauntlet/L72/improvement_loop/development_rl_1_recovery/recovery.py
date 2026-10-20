import ast,datetime,sys
from pathlib import Path
RECOVERY=Path(__file__).resolve().parent
ORIGINAL=RECOVERY.parent/'development_rl_1'
sys.path.insert(0,str(ORIGINAL))
from shared import *

def form_match(actual,expected):
    assert type(actual) is dict and set(actual)=={0,1}
    assert type(expected) is dict and set(expected)=={'0','1'}
    assert all(type(v) is list and len(v)==8 and all(type(f) is int and f in (0,1,2) for f in v) for v in actual.values())
    assert all(type(v) is list and len(v)==8 and all(type(f) is int and f in (0,1,2) for f in v) for v in expected.values())
    return {str(k):v for k,v in actual.items()}==expected

def failure_inputs():
    paths=[HERE/'prepared.json',HERE/'training_started.json',HERE/'chain_failed.json',ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-outcome-rl-train.json',ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-outcome-rl-train.out']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}

def binding():
    return {str(p.relative_to(ROOT)):sha(p) for p in list(RECOVERY.glob('*.py'))+[RECOVERY/'PLAN.md']}

def check_recovery():
    check();v=read(RECOVERY/'verified.json')
    assert v['complete'] and v['sources']==binding() and v['original_failure']==failure_inputs()
    r=read(ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-outcome-rl-setup-recovery.json')
    assert r['exit_code']==0 and r['matched']
    return v

def training_source():
    src=(HERE/'train.py').read_text(encoding='utf-8')
    old="self.env.loaded_forms==expected['forms']"
    assert src.count(old)==1 and src.count("HERE/'training_started.json'")==2
    src=src.replace(old,"form_match(self.env.loaded_forms,expected['forms'])")
    src=src.replace("HERE/'training_started.json'","RECOVERY/'training_started.json'")
    return src

def verification_source():
    src=(HERE/'verify.py').read_text(encoding='utf-8')
    old="for stage in ('prepare','train','eval'):"
    assert src.count(old)==1
    return src.replace(old,"for stage in ('prepare','train-v2','eval'):")
