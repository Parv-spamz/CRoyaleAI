import unittest
import torch

from pipeline.tests.test_search_s0 import runner,to_root,HOGEQ
from scratchpad.gauntlet.L71.xbow_support.counterfactual import branch_pair,plain_todo


def test_actual_forks_keep_opponent_and_root_and_charge_followups(tmp_path):
    torch.set_num_threads(1)
    run=runner(tail_cap=1200,horizon_s=12,rollout_self='policy')
    m,ds,p,enc,heads,allowed=to_root(unittest.TestCase(),run,'gen',HOGEQ,3,after=200)
    todo=plain_todo(ds)
    # A real affordable root action, independent of the random model's gate.
    for i,(s,p,d) in enumerate(todo):
        if s is m.learner:
            candidate=run.learner
            from pipeline.search_s0 import shortlist
            todo[i]=(s,p,shortlist(candidate,enc,heads,allowed,1,1)[0])
    result=branch_pair(run,m,ds,todo,tmp_path/'root')
    assert result['root_tick']>=200
    assert len(result['branches'])==2
    assert all(b['end_tick']<=result['root_tick']+240 for b in result['branches'])
    assert all(b['all_elixir_spent']>=0 for b in result['branches'])
    assert (tmp_path/'root/root.bin').stat().st_size>0
