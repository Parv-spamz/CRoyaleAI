"""Supplement exact source binding on Windows paths without repeating counters."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent/'rl_failure_audit'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    target=HERE/'bindings_verified.json';assert not target.exists()
    v=json.loads((HERE/'verified.json').read_text());paths=[]
    for path,digest in v['inputs'].items():
        if Path(path).parts[0]=='scratchpad':assert sha(ROOT/path)==digest;paths.append(path)
    assert len(paths)>=10
    target.write_text(json.dumps(dict(complete=True,source_paths=paths,verified_sha256=sha(HERE/'verified.json'),source_sha256=sha(Path(__file__)),reason='Outer review used a slash prefix on Windows relative paths; exact Path.parts supplement, no counter rerun'),indent=2)+'\n')
    print('RL_FAILURE_BINDINGS_VERIFIED')
if __name__=='__main__':main()
