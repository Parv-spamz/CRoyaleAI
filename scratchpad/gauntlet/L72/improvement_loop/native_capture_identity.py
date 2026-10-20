"""Compare captured object lifetimes without comparing allocator addresses."""
import copy


def canonical_frames(frames):
    result=copy.deepcopy(frames)
    active={kind:{} for kind in ('projectiles','area_effects')}
    count={kind:0 for kind in active}
    for frame in result:
        for kind,previous in active.items():
            current={}
            for row in frame['public_objects'][kind]:
                identity=(row['id'],row.get('generation_key'),row.get('category'),row['card_id'])
                if identity in current:
                    raise ValueError('Duplicate object identity in one frame')
                if identity in previous:
                    ordinal=previous[identity]
                else:
                    count[kind]+=1
                    ordinal=count[kind]
                current[identity]=ordinal
                row['id']=f'{kind}:{ordinal}'
            active[kind]=current
    return result


def verify():
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[4]
    folder=root/'icebow/data/bench/native_confirmation_20261005/preflight'
    first=next(folder.glob('replay_*.json'))
    a=json.loads(first.read_text());b=json.loads((folder/'repeats'/first.name).read_text())
    normalized=canonical_frames(a['frames'])
    assert a['frames'] != b['frames']
    assert normalized == canonical_frames(b['frames'])
    # These must still fail: geometry, time-to-impact, lifetime split, loss, duplication.
    index=next(i for i in range(1,len(a['frames']))
               if a['frames'][i]['public_objects']['projectiles'] and
               a['frames'][i-1]['public_objects']['projectiles'] and
               a['frames'][i]['public_objects']['projectiles'][0]['id'] ==
               a['frames'][i-1]['public_objects']['projectiles'][0]['id'])
    for kind in ('geometry','tti','identity_split','missing','duplicate'):
        altered=copy.deepcopy(b['frames'])
        rows=altered[index]['public_objects']['projectiles']
        if kind=='geometry':rows[0]['target_x']+=1
        elif kind=='tti':rows[0]['past_motion_tti_ms']=123456
        elif kind=='identity_split':rows[0]['id']='new-allocation-mid-flight'
        elif kind=='missing':rows.pop(0)
        else:rows.append(copy.deepcopy(rows[0]))
        try:
            assert normalized != canonical_frames(altered), kind
        except ValueError:
            assert kind=='duplicate'
    print('NATIVE_IDENTITY_ORACLE_PASS: original pair equivalent; five corruptions rejected')


if __name__=='__main__':verify()
