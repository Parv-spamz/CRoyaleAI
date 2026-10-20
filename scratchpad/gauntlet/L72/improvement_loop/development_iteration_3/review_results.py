"""Review existing completed evidence only; no training, inference or delivery."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'icebow/data/bench/development_iteration_3_20261005'
CHECKS = ROOT / 'scratchpad/gauntlet/L71/integration/checks'


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    dest = HERE / 'reviewed_results.json'
    if dest.exists():
        raise ValueError('Preserve completed review')
    r = read(HERE / 'results_verified.json')
    assert r['complete'] and r['rows'] == 54723
    assert not r['continuation_point_filter_passed'] and not r['deployment_accepted']
    assert sha(OUT / 'paired_replay_counts.json') == r['paired_sha256']
    assert sha(OUT / 'all_replay_counts.json') == r['replay_counts_sha256']
    logs = [json.loads(x) for x in (OUT / 'rocket_aim3_v6/train.jsonl').read_text().splitlines()]
    assert [x['step'] for x in logs] == list(range(1, 1001))
    assert all(math.isfinite(x['loss']) and all(math.isfinite(v) for v in x['parts'].values()) for x in logs)
    assert sha(OUT / 'rocket_aim3_v6/candidate.pt') == r['hashes']['rocket_aim3_v6']['checkpoint']
    receipts = {}
    for name in ('preflight', 'train', 'eval', 'independent', 'discord'):
        p = CHECKS / ('l72-development3-' + name + '.json')
        v = read(p)
        output = p.with_suffix('.out')
        logical_output = output.read_text()
        assert v['exit_code'] == 0 and v['matched']
        assert hashlib.sha256(logical_output.encode()).hexdigest() == v['output_sha256']
        receipts[p.name] = dict(sha256=sha(p), output_file_sha256=sha(output), exit_code=0)
    delivery = CHECKS / 'l72-development3-discord.out'
    assert delivery.read_text().count('HTTP 204') == 1
    paired = read(OUT / 'paired_replay_counts.json')
    summaries = {}
    for control, groups in paired.items():
        summaries[control] = {}
        for group, replays in groups.items():
            summaries[control][group] = {
                metric: dict(net_rows=sum(x[metric] for x in replays.values()),
                    replays_more=sum(x[metric] > 0 for x in replays.values()),
                    replays_less=sum(x[metric] < 0 for x in replays.values()),
                    replays_same=sum(x[metric] == 0 for x in replays.values()))
                for metric in ('action', 'card', 'aim1', 'log_correct', 'log_wrong')}
            for metric, summary in summaries[control][group].items():
                assert summary['net_rows'] == r['counts']['rocket_aim3_v6'][group][metric] - r['counts'][control][group][metric]
    result = dict(complete=True, results_sha256=sha(HERE / 'results_verified.json'),
        receipts=receipts, finite_updates=1000, paired=summaries,
        report_message_sha256=sha(HERE / 'report_model.txt'), delivery_chunks=1,
        rejected=True, developmental_only=True, deployment_accepted=False)
    dest.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({g: summaries['ordinary_v6'][g] for g in ('rocket', 'furnace', 'barrel_pro')}))
    print('ROCKET_AIM_REVIEW_COMPLETE')


if __name__ == '__main__':
    main()
