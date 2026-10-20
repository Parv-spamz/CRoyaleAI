"""Recount the completed Rust log without running blocked executables."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def main():
    path = HERE / 'sim_rust.out'
    contents = path.read_bytes()
    receipt = json.loads((HERE / 'sim_rust.json').read_text())
    digest = hashlib.sha256(contents).hexdigest()
    if digest != receipt['output_sha256']:
        raise ValueError('Rust log changed after its process receipt')
    log = contents.decode('utf-8')
    rows = re.findall(r'test result: (\w+)\. (\d+) passed; (\d+) failed; '
                      r'(\d+) ignored; (\d+) measured; (\d+) filtered out', log)
    blocked = re.findall(r'could not execute process `([^`]+)` \(never executed\)'
                         r'\s*Caused by:\s*An Application Control policy has blocked '
                         r'this file\. \(os error 4551\)', log)
    failures = re.findall(r'^error: test failed, to rerun pass `--test ([^`]+)`', log, re.M)
    blocked_names = [Path(p).stem.rsplit('-', 1)[0] for p in blocked]
    if len(failures) != 16 or set(failures) != set(blocked_names) or len(blocked) != 16:
        raise ValueError('The failure summary has an unexplained target')
    totals = {key: sum(int(row[i + 1]) for row in rows)
              for i, key in enumerate(('passed', 'failed', 'ignored', 'measured', 'filtered'))}
    if not rows or any(row[0] != 'ok' for row in rows) or totals['failed']:
        raise ValueError('An executed target has a failed test')
    report = dict(schema=1, exit_code=receipt['exit_code'], output_sha256=digest,
                  runtime_manifest_sha256=receipt['runtime_manifest_sha256'],
                  parsed_test_summaries=len(rows), executed_test_totals=totals,
                  blocked_targets=failures, blocked_target_count=len(blocked),
                  blocked_reason='Windows Application Control, OS error 4551; never executed',
                  ignored_test_lines=re.findall(r'^test (?!result:).* \.\.\. ignored.*$', log, re.M),
                  all_tests_passed=False, runtime_acceptance_complete=False,
                  security_policy_changed=False, blocked_binaries_reexecuted=False)
    (HERE / 'rust_adjudication.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(executed=totals, blocked_targets=len(blocked), acceptance_complete=False)))


if __name__ == '__main__':
    main()
