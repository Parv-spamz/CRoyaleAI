"""Recount the owner-started refreshed-entry match; no gameplay or model calls."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[4]
LOG = ROOT/'scratchpad/gauntlet/L68/live_reader/live_play_20261005_062759.jsonl'
OUT = Path(__file__).with_name('manual_match_verified.json')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    if OUT.exists():
        raise ValueError('Fresh verification output required')
    rows = [json.loads(line) for line in LOG.read_text().splitlines()]
    counts = Counter(row['event'] for row in rows)
    assert counts['start'] == counts['end'] == counts['stop'] == 1
    start = next(row for row in rows if row['event'] == 'start')
    end = next(row for row in rows if row['event'] == 'end')
    assert start['ckpt_sha256'] == sha(Path(start['ckpt']))
    assert start['device'] == 'cpu' and not start['anti_leak']
    assert start['public_audit'] and not start['dry_run']
    assert start['decision_options']['card_choice'] == 'argmax'
    assert start['decision_options']['spell_aim'] == 'argmax'
    assert counts['play'] == end['played']
    assert counts['confirmed'] == end['confirmed']
    assert counts['unconfirmed'] == end['fails']
    audits = [row for row in rows if row['event'] == 'decision']
    forbidden = {'opp_elixir_true_EVAL_ONLY', 'opponent_hand', 'opp_hand',
                 'opponent_next_card', 'opponent_ability_ready'}

    def check_keys(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for child in value.values():
                check_keys(child)
        elif isinstance(value, list):
            for child in value:
                check_keys(child)

    for row in audits:
        assert not row['forced'] and row['public']['schema'] == 1
        assert row['public']['source'] == 'public_reader_and_actual_model_batch'
        check_keys(row['public'])
        json.dumps(row, allow_nan=False)
    assert sum(row['decision']['play'] for row in audits) == counts['play']
    delays = sorted(row['decide_ms'] for row in audits)
    result = dict(log=str(LOG.relative_to(ROOT)), log_sha256=sha(LOG),
        verifier_sha256=sha(Path(__file__)), start=start, events=dict(counts), end=end,
        unresolved_attempts=end['played']-end['confirmed']-end['fails'],
        decision_ms=dict(median=statistics.median(delays),
                         p95=delays[int(.95*(len(delays)-1))], maximum=max(delays)),
        stops=[row for row in rows if row['event'] == 'stop'],
        unconfirmed=[row for row in rows if row['event'] == 'unconfirmed'],
        interpretation='Owner manual R1e entry evidence only; no new-model acceptance. '
          'Audit schema/key check is not a replacement for existing public-input privacy tests. '
          'Frame telemetry has separate EVAL_ONLY values; these are excluded from public decision audits.')
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(events=counts, unresolved_attempts=result['unresolved_attempts'],
                         decision_ms=result['decision_ms'])))
    print('OWNER_MANUAL_MATCH_RECOUNTED')


if __name__ == '__main__':
    main()
