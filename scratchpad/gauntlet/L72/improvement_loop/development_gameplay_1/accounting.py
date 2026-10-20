"""Independent record membership and native-terminal outcome checks."""
def validate(records,specs,arms):
    expected={(a,s['tag']):s for s in specs for a in arms}
    assert len(records)==len(expected)
    seen=set()
    for row in records:
        key=(row['model'],row['tag']);assert key in expected and key not in seen;seen.add(key)
        spec=expected[key];r=row['match'];raw=row['raw']
        assert row['initial_state_sha256']==spec['initial_state_sha256']
        assert (r['opp'],r['seed'],r['learner_side'],r['opp_deck'])==(spec['opp'],spec['seed'],spec['side'],spec['opp_deck'])
        assert not r['wall_truncated'] and not r['form_fallbacks'] and raw['terminated']
        assert raw['core_game_over'] and raw['end_tick']==r['end_tick']
        side=spec['side'];own,enemy=raw['crowns'][side],raw['crowns'][1-side]
        assert (r['crowns_for'],r['crowns_against'])==(own,enemy)
        winner=raw['winner_side'];outcome=('draw' if own==enemy else 'win' if own>enemy else 'loss') if winner<0 else ('win' if winner==side else 'loss')
        assert r['outcome']==outcome
        assert row['full_result']['outcome']==outcome
        assert row['full_result']['plays_attempted']==r['plays_attempted']
        assert row['full_result']['plays_accepted']==r['plays_accepted']
    return True
