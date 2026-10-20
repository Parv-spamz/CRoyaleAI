"""Complete the unchanged trial8 recount after an import-only failure."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / 'development_iteration_8'))
import experiment as e

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    checks = e.c.ROOT / 'scratchpad/gauntlet/L71/integration/checks'
    failed_path = checks / 'l72-development8-independent.json'
    failed = e.c.read(failed_path)
    output = failed_path.with_suffix('.out')
    assert failed['exit_code'] != 0 and not failed['matched']
    assert "ModuleNotFoundError: No module named 'extra_masks'" in output.read_text()
    assert hashlib.sha256(output.read_text().encode()).hexdigest() == failed['output_sha256']
    assert not (e.HERE / 'results_verified.json').exists()
    # The reused verifier imports these existing descriptor names from experiment.
    # They are the frozen iteration4 clock masks, not new model inputs or rules.
    e.PHASES = ('single_clock', 'double_regulation_clock', 'early_overtime_clock', 'late_overtime_clock')
    sys.path.append(str(BASE / 'development_iteration_7'))
    import extra_masks
    spec = importlib.util.spec_from_file_location('trial8_recount', e.HERE / 'recount.py')
    recount = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recount)
    assert Path(extra_masks.__file__).resolve() == BASE / 'development_iteration_7/extra_masks.py'
    assert Path(recount.__file__).resolve() == e.HERE / 'recount.py'
    second = checks / 'l72-development8-independent-v2.json'
    second_receipt = e.c.read(second)
    assert second_receipt['exit_code'] != 0 and not second_receipt['matched']
    assert 'AssertionError' in second.with_suffix('.out').read_text()
    assert hashlib.sha256(second.with_suffix('.out').read_text().encode()).hexdigest() == second_receipt['output_sha256']
    binding = {str(path.relative_to(e.c.ROOT)): sha(path) for path in (
        Path(__file__), e.HERE / 'recount.py', Path(extra_masks.__file__),
        e.HERE / 'RECOUNT_COMPLETION.md', e.HERE / 'RECOUNT_IMPORT_CORRECTION.md',
        BASE / 'recount_development8_v2.py', failed_path, output, second, second.with_suffix('.out'))}
    e.c.write(e.HERE / 'recount_v3_started.json', dict(sources=binding, prediction_or_optimization=False))
    recount.main()
    assert all(sha(e.c.ROOT / name) == digest for name, digest in binding.items())
    result = e.c.read(e.HERE / 'results_verified.json')
    result['recount_completion_binding'] = binding
    result['preserved_failed_receipt_sha256'] = sha(failed_path)
    e.c.write(e.HERE / 'results_verified.json', result)
    print('AIM_HEADS_RECOUNT_V3_COMPLETE')

if __name__ == '__main__':
    main()
