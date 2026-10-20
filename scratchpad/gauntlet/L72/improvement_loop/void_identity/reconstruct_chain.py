"""Single bounded native collection followed by its read-only verifier."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent

def main():
    with (HERE/'chain_started.json').open('x') as f:
        json.dump(dict(pid=os.getpid(),started=time.time(),jobs=['capture','independent_verify']),f)
    check=ROOT/'scratchpad/gauntlet/L71/integration/run_check.py'
    for name,script,token in [('l72-void-reconstruction-capture','reconstruct_collect.py','VOID_RECONSTRUCTION_CAPTURE_COMPLETE'),
                              ('l72-void-reconstruction-independent','reconstruct_verify.py','VOID_RECONSTRUCTION_INDEPENDENT_PASS')]:
        argv=[sys.executable,str(check),'--name',name,'--expect',token,'--',sys.executable,'-u',str(HERE/script)]
        r=subprocess.run(argv,cwd=ROOT)
        if r.returncode:return r.returncode
    print('VOID_RECONSTRUCTION_CHAIN_COMPLETE',flush=True);return 0

if __name__=='__main__':raise SystemExit(main())
