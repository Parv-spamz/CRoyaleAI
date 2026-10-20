"""Check exact stopped-chain receipts and metadata-only wrapper differences."""
import ast
import common as c
from recovery_common import NAMES


def main():
    dest=c.HERE/'recovery_bound.json'
    if dest.exists():raise ValueError('Preserve existing binding')
    c.check_prepared();c.check_frozen()
    assert c.read(c.HERE/'chain_failed.json')=={'job':'v5-eval','returncode':1}
    folder=c.ROOT/'scratchpad/gauntlet/L71/integration/checks'
    names=('r1e-eval','v5-train','v5-eval','v5-portable');evidence={}
    for name in names:
        path=folder/('l72-development1-'+name+'.json');r=c.read(path)
        output=path.with_suffix('.out');text=output.read_text()
        # run_check hashes combined captured text, whose Windows newlines are normalized here.
        assert c.hashlib.sha256(text.encode()).hexdigest()==r['output_sha256']
        if name=='v5-eval':
            assert r['exit_code']==1 and not r['matched'] and 'TorchVersion' in text
        else:assert r['exit_code']==0 and r['matched'] and r['expected'] in text
        evidence[str(path.relative_to(c.ROOT))]=c.sha(path)
        evidence[str(output.relative_to(c.ROOT))]=c.sha(output)
    proof=c.read(c.HERE/'ordinary_v5_portable.json')
    for file,key in [('candidate.pt','source_sha256'),('candidate_portable.pt','portable_sha256')]:
        path=c.OUT/'ordinary_v5'/file;assert c.sha(path)==proof[key]
        evidence[str(path.relative_to(c.ROOT))]=c.sha(path)
    for path in (c.HERE/'prelaunch.json',c.HERE/'chain_failed.json',c.HERE/'ordinary_v5_portable.json',
                 c.OUT/'ordinary_v5'/'result.json',c.OUT/'ordinary_v5'/'train.jsonl',
                 c.OUT/'r1e_corrected_eval'/'report.json',c.OUT/'r1e_corrected_eval'/'predictions.npz'):
        evidence[str(path.relative_to(c.ROOT))]=c.sha(path)
    for file in ('evaluate_v2.py','recount_v2.py'):
        ast.parse((c.HERE/file).read_text())
    # Prediction and metric functions are inherited unchanged; only loader/destination bindings differ.
    def functions(path):
        tree=ast.parse(path.read_text())
        return {x.name:ast.dump(x,include_attributes=False) for x in tree.body if isinstance(x,ast.FunctionDef)}
    a,b=functions(c.HERE/'recount.py'),functions(c.HERE/'recount_v2.py')
    for name in ('independent_masks','independently_count','controls'):assert a[name]==b[name]
    c.write(dest,dict(complete=True,skip_completed=['r1e-eval','v5-train','v5-portable'],
        no_extra_optimization=True,original_recipe_unchanged=True,
        sources={str((c.HERE/n).relative_to(c.ROOT)):c.sha(c.HERE/n) for n in NAMES},completed_evidence=evidence))
    print('DEVELOPMENT_1_RECOVERY_BOUND')


if __name__=='__main__':main()
