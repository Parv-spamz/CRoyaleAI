"""Run an explicitly supplied inspected command and save process evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[4]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--name',required=True)
    ap.add_argument('--expect',required=True)
    ap.add_argument('command',nargs=argparse.REMAINDER)
    a=ap.parse_args()
    command=a.command[1:] if a.command and a.command[0]=='--' else a.command
    if not command or Path(a.name).name!=a.name:
        raise ValueError('Need command and a plain receipt name')
    out=Path(__file__).parent/'checks'
    out.mkdir(parents=True,exist_ok=True)
    receipt=out/(a.name+'.json')
    if receipt.exists():
        raise ValueError('Fresh check receipt required')
    start=time.time()
    p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    output=p.stdout+p.stderr
    (out/(a.name+'.out')).write_text(output)
    result=dict(command=command,cwd=str(ROOT),shell='none; subprocess argument vector',
        exit_code=p.returncode,expected=a.expect,matched=a.expect in output,
        output_sha256=hashlib.sha256(output.encode()).hexdigest(),seconds=time.time()-start)
    receipt.write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
    if p.returncode or not result['matched']:
        raise SystemExit(1)
    print('INSPECTED_CHECK_PASS')


if __name__=='__main__':
    main()
