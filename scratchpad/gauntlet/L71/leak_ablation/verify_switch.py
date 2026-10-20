"""CPU-only replay of the live dispatch block, without importing/tapping the game."""
import argparse
import ast
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
PLAYER = ROOT / 'scratchpad/gauntlet/L68/live_reader/live_play.py'


def parser(tree):
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    statements = [main.body[0]]
    for n in main.body:
        if (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == 'add_argument'
                and n.value.args[0].value in ('--leak', '--no-anti-leak')):
            statements.append(n)
    scope = {'argparse': argparse}
    exec(compile(ast.Module(body=statements, type_ignores=[]), str(PLAYER), 'exec'), scope)
    return scope['ap']


def dispatch(tree, args, cases):
    # Execute the actual assignment and following early-continue branch. The
    # baseline comes from Git, so a broken flag cannot certify itself.
    force = next(n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'forced' for t in n.targets))
    block = next(n for n in ast.walk(tree) if isinstance(n, ast.If) and n.lineno == force.end_lineno + 1)
    loop = ast.parse('for d, el in cases:\n    pass\n').body[0]
    loop.body = [force, block, ast.parse('result.append((d, el, forced))').body[0]]
    module = ast.fix_missing_locations(ast.Module(body=[loop], type_ignores=[]))
    scope = {'a': args, 'cases': cases, 'result': []}
    exec(compile(module, str(PLAYER), 'exec'), scope)
    return scope['result']


def main():
    source = PLAYER.read_text(encoding='utf-8')
    compile(source, str(PLAYER), 'exec')
    current = ast.parse(source)
    baseline = ast.parse(subprocess.check_output(
        ['git', 'show', 'f11419b:scratchpad/gauntlet/L68/live_reader/live_play.py'], cwd=ROOT, text=True))
    p = parser(current)
    default, disabled = p.parse_args([]), p.parse_args(['--no-anti-leak'])
    assert default.no_anti_leak is False and disabled.no_anti_leak is True
    assert default.leak == disabled.leak == 9.5
    cases = []
    logs = ROOT / 'scratchpad/gauntlet/L68/live_reader'
    for path in sorted(logs.glob('live_play_20261004_*.jsonl')):
        # Freeze the cohort before the owner-requested deployment.
        if path.name > 'live_play_20261004_213607.jsonl':
            continue
        events = [json.loads(line) for line in path.read_text().splitlines()]
        if (Path(events[0].get('ckpt', '')).name != 'rseries_r1e31_u0155.pt'
                or events[0].get('dry_run') or not any(e.get('event') == 'end' for e in events)):
            continue
        cases.extend(({'play': not e['forced'], 'card': 1}, e['elixir'])
                     for e in events if e.get('event') == 'play')
    assert cases, 'Missing historical positive controls'
    old = dispatch(baseline, argparse.Namespace(leak=9.5), cases)
    assert dispatch(current, default, cases) == old, 'Default dispatch changed'
    new = dispatch(current, disabled, cases)
    assert new == [entry for entry in old if not entry[2]]
    assert len(new) < len(old), 'No recorded forced-play positive control'
    # A capped WAIT must remain WAIT, including when no card is affordable;
    # learned PLAY decisions must still dispatch above and below the cap.
    probes = [({'play': play, 'card': card}, el)
              for play in (False, True) for card in (0, 1) for el in (0, 9.49, 9.5, 10)]
    assert dispatch(current, default, probes) == dispatch(baseline, argparse.Namespace(leak=9.5), probes)
    assert all(not forced and d['play'] for d, _, forced in dispatch(current, disabled, probes))
    assert len(dispatch(current, disabled, probes)) == sum(d['play'] for d, _ in probes)
    print(f'Historical dispatches: {len(old)}; disabled: {len(new)}; forced suppressed: {len(old)-len(new)}')
    print('ANTI_LEAK_SWITCH_VERIFIED')


if __name__ == '__main__':
    main()
