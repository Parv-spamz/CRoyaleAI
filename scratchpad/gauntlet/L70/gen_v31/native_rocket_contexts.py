"""Describe verified native Rocket audit rows without inferring hits or intent."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from mine_rockets import describe

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows):
    targets=[t for r in rows for t in r['targets']]
    ends={(r['tag'],r['side']):r['final_tower_hp_margin'] for r in rows}
    return dict(rockets=len(rows),replay_sides=len(ends),tower_targets=len(targets),
        hp_before=describe(t['hp_before'] for t in targets),
        own_elixir_before=describe(r['own_elixir_before'] for r in rows),
        phases=dict(Counter(r['phase'] for r in rows)),
        phase_seconds_left=describe(r['phase_seconds_left'] for r in rows),
        match_limit_seconds_left=describe(r['match_limit_seconds_left'] for r in rows),
        crowns_before=dict(Counter(':'.join(map(str,r['crowns_before'])) for r in rows if 'crowns_before' in r)),
        total_tower_hp_margin_before=describe(r.get('total_tower_hp_margin_before') for r in rows),
        prior_candidates=describe(t['prior_rocket_candidates'] for t in targets),
        gap_seconds=describe(t['gap_s'] for t in targets),
        final_recorded_hp_margin_per_replay_side=describe(ends.values()),
        context_age_seconds=describe((r['tick']-r['context_tick'])*.05 for r in rows if r['context_tick'] is not None))


def main():
    source=HERE/'native_mining_1552'
    inputs={str((source/p).relative_to(ROOT)):sha(source/p) for p in ('report.json','manifest.json','rockets.jsonl')}
    rows=[json.loads(s) for s in (source/'rockets.jsonl').read_text().splitlines()]
    report=json.loads((source/'report.json').read_text())
    assert len(rows)==report['counts']['accepted_rockets']
    candidates=[r for r in rows if r['targets']]
    assert len(candidates)==report['tower_candidates']['rockets']
    assert all(r['context_tick'] is None or r['context_tick']<=r['tick'] for r in rows)
    groups={'all_rockets':rows,'tower_candidates':candidates}
    for label,value in (('native_tiebreak',True),('other_end',False),('end_unknown',None)):
        group=[r for r in candidates if r['tiebreaker'] is value]
        groups['tower_candidates_'+label]=group
        for hp,low in (('le497',True),('gt497',False)):
            groups['tower_candidates_'+label+'_'+hp]=[
                r for r in group if any((t['hp_before']<=497)==low for t in r['targets'])]
    result=dict(status='DESCRIPTIVE_NATIVE_REDRIVE_CONTEXTS_NOT_HIT_OR_INTENT_TRUTH',inputs=inputs,
        source_counts=report['counts'],groups={k:summarize(v) for k,v in groups.items()},
        tiebreak_evidence=dict(Counter(r['tiebreaker_evidence'] for r in rows)),
        sequence_lengths=report['tower_candidates']['sequence_lengths'],
        limitations=[
            'Targeting candidates use the original 3.5-tile audit envelope; hit attribution remains unknown.',
            'A native tiebreak outcome is a reconstructed match outcome, not proof of original human intent.',
            'The 497-HP split is the requested live diagnostic; native level11 Rocket damage is different.',
            'Final HP margins use the final recorded towers, including any tiebreak drain, once per replay/side.',
            'Context distributions weight accepted Rockets; replay-side end margins have a different denominator.',
            'Mixed decks and both replay sides: pooled Rocket share is not the S1 Icebow5.8% reference.',
            'Descriptive census of selected recordings; no policy comparison, causal effect or acceptance claim.'])
    assert all(sha(ROOT/p)==v for p,v in inputs.items())
    output=HERE/'native_rocket_contexts_1839.json'
    with output.open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({k:dict(rockets=v['rockets'],hp_median=v['hp_before']['median'],
        elixir_median=v['own_elixir_before']['median']) for k,v in result['groups'].items()},indent=2))


if __name__=='__main__':main()
