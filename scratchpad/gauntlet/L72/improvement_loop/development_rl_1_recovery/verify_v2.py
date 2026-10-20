from recovery import *
if __name__=='__main__':
    check_recovery()
    ns=dict(__name__='outcome_recovered_verify',__file__=str(HERE/'verify.py'))
    exec(compile(verification_source(),str(HERE/'verify.py'),'exec'),ns)
    ns['main']()
    check_recovery()
