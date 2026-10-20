"""Apply the additional declared controls and bind the existing independent recount."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
WORKTREE = Path('C:/Users/benpe/.codex/worktrees/learned-defence/ClashBot')
sys.path.insert(0, str(WORKTREE))
from scratchpad.gauntlet.L71.decision_options.score_q3 import summarize, read
HERE = Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    output = HERE/'frozen_supplement.json'
    if output.exists():
        raise ValueError('Fresh supplement required')
    report_path = HERE/'frozen_reconciled.json'
    report = json.loads(report_path.read_text())
    assert report['complete'] and not report['pending'] and len(report['receipts']) == 34
    recount_path = ROOT/'scratchpad/gauntlet/L71/context_teaching/all_predictions_verified.json'
    metrics_path = recount_path.with_name('heldout_metrics_verified.json')
    recount = json.loads(recount_path.read_text())
    metrics = json.loads(metrics_path.read_text())
    assert metrics['recount_sha256'] == sha(recount_path)
    metric_by = {r['heldout']:r for r in metrics['results']}
    bound = {}
    for r in recount['results']:
        folder = ROOT/r['heldout']
        assert r['matches'] and r['rows'] == 38317
        assert sha(folder/'report.json') == r['report_sha256']
        assert sha(folder/'predictions.npz') == r['predictions_sha256']
        m = metric_by[r['heldout']]
        assert m['report_sha256'] == r['report_sha256'] and m['predictions_sha256'] == r['predictions_sha256']
        name = 'r1e' if folder.name == 'r1e_heldout' else folder.parent.name
        bound[name] = m['metrics']
    assert len(bound) == 9
    exp = WORKTREE/'scratchpad/gauntlet/L71/context_teaching/experiments'
    baseline = dict(ghost=summarize(read(exp/'ghost_r1e.jsonl')),
                    reactive=summarize(read(exp/'reactive_r1e/matches.jsonl')))
    games = dict(r1e=baseline, **{k:dict(ghost=v['ghost'],reactive=v['reactive']) for k,v in report['verdicts'].items()})
    additions = {}
    for name, row in report['verdicts'].items():
        prior = row['primary_control']
        current, old = games[name]['ghost'], games[prior]['ghost']
        additional = {}
        if 'rocket' in name:
            additional = dict(primary_rocket_share_closer=abs(current['rocket_share']-.058)<abs(old['rocket_share']-.058),
                              primary_tower_rockets_increase=current['tower_rockets']>old['tower_rockets'])
        changes = {}
        for key in ('witch','night_witch','furnace','xbow'):
            a, b = bound[name]['contexts'][key]['action_agreement'], bound[prior]['contexts'][key]['action_agreement']
            assert a['denominator'] == b['denominator']
            changes[key] = dict(candidate=a, control=b, change_n=a['n']-b['n'])
        additions[name] = dict(primary_control=prior, extra_rocket_gates=additional,
            primary_action_comparisons=changes,
            failed_existing=[k for group in ('heldout_gates','gameplay_gates') for k,v in row[group].items() if not v],
            failed_extra=[k for k,v in additional.items() if not v],
            final_accept=False)
        assert not row['passes']
    result = dict(complete=True, accepted=[], final_verdict='REJECT ALL EIGHT; CONTINUE L72',
        scorer_sha256=sha(report_path), recount_sha256=sha(recount_path), metrics_sha256=sha(metrics_path),
        reviewer_sha256=sha(Path(__file__)), bound_prediction_rows=9*38317, baseline=baseline,
        additions=additions, metrics=bound,
        interpretation='Learning failures and same-code gameplay reject every arm. Added literal primary controls '
            'and isolated component deltas cannot rescue them. Historical old-runtime tests are not new-runtime '
            'confirmation, component mastery or live-landing evidence.')
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(accepted=[], verified_rows=9*38317,
                         extra_failures={n:v['failed_extra'] for n,v in additions.items()})))
    print('FROZEN_COMPONENT_SUPPLEMENT_VERIFIED')


if __name__ == '__main__':
    main()
