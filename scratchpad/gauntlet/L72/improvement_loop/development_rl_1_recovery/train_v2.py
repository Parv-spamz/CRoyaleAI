from recovery import *
if __name__=='__main__':
    check_recovery()
    assert not list(OUT.rglob('*.*')),'Recovery only authorized before any candidate update'
    ns=dict(__name__='outcome_recovered_train',__file__=str(HERE/'train.py'),RECOVERY=RECOVERY,form_match=form_match)
    exec(compile(training_source(),str(HERE/'train.py'),'exec'),ns)
    ns['main']()
    check_recovery()
