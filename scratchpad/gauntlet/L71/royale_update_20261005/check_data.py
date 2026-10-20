"""Independently compare staged tables and preserve concise evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
OLD = ROOT / 'research/ext/Royale/RoyaleSim/data'
NEW = ROOT / 'research/ext/Royale-20261005/RoyaleSim/data'
CHANGES = []


def compare(a, b, path):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(a.keys() | b.keys()):
            if k not in a:
                CHANGES.append(dict(path=path+'/'+k, added=b[k]))
            elif k not in b:
                CHANGES.append(dict(path=path+'/'+k, removed=a[k]))
            else:
                compare(a[k], b[k], path+'/'+k)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            compare(x, y, path+'/'+str(i))
    elif a != b:
        CHANGES.append(dict(path=path, old=a, new=b))


def main():
    inventory = json.loads((HERE/'inventory.json').read_text())
    for name in ['calibration.json', 'derived/cards.json', 'derived/arena.json', 'derived/globals.json']:
        expected = inventory['old_runtime_data'][str(Path('data')/name)]
        assert hashlib.sha256((OLD/name).read_bytes()).hexdigest() == expected, name
        compare(json.loads((OLD/name).read_text()), json.loads((NEW/name).read_text()), name)
    card = [x for x in CHANGES if x['path'].startswith('derived/cards.json/')]
    assert len(card) == 8 and all('added' in x for x in card), card
    for field in ('OVERTIME_S', 'MANA_REGEN_MS_1X', 'MANA_REGEN_MS_2X', 'MANA_REGEN_MS_OVERTIME'):
        a = json.loads((OLD/'calibration.json').read_text())['match'][field]['value']
        b = json.loads((NEW/'calibration.json').read_text())['match'][field]['value']
        assert a == b, (field, a, b)
    out = dict(old_data_unchanged=True, card_only_eight_new_flags=True,
               match_duration_regen_unchanged=True, changes=CHANGES)
    (HERE/'data_verified.json').write_text(json.dumps(out, indent=2))
    print('DATA_VERIFIED', len(CHANGES), 'leaf changes;', len(card), 'new card flags')
    print(json.dumps(card, indent=2))


if __name__ == '__main__':
    main()
