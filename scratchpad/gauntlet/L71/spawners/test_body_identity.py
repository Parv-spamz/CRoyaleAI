import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from body_identity import resolve, tables, CATALOG
from pipeline import vocab
from pipeline.rocket_teaching import scaled_stat


@pytest.mark.parametrize('parent,child', [('witch', 'skeletons'), ('night-witch', 'bats'),
    ('furnace', 'fire-spirit'), ('goblin-hut', 'spear-goblins'),
    ('barbarian-hut', 'barbarians'), ('tombstone', 'skeletons')])
def test_all_public_levels(parent, child):
    name = parent.replace('-', '_')
    # Engine canonical keys accept underscores only when already lower case.
    for level in range(9, 17):
        result = resolve(name, scaled_stat(child, 'hitpoints', level))
        assert result.cls == vocab.unit_id(child.replace('-', '_'))
        assert result.form == 0 and result.reason == 'child'
        result = resolve(name, scaled_stat(parent, 'hitpoints', level))
        assert result.cls == vocab.unit_id(name) and result.reason == 'parent'


@pytest.mark.parametrize('name,form,child', [('Witch', 1, 'skeletons'),
    ('FirespiritHut', 1, 'fire_spirit'), ('Tombstone', 2, 'skeletons')])
def test_child_does_not_inherit_parent_form(name, form, child):
    hp = scaled_stat(child.replace('_', '-'), 'hitpoints', 11)
    assert resolve(name, hp, form).cls == vocab.unit_id(child)
    assert resolve(name, hp, form).form == 0
    parent_hp = scaled_stat(vocab.engine_key(name).replace('_', '-'), 'hitpoints', 11)
    assert resolve(name, parent_hp, form).form == form


def test_unknown_and_ambiguous_are_conservative():
    for hp in (None, 0, -1, 81.1, 1, float('nan'), 99999):
        result = resolve('DarkWitch', hp, 0)
        assert result.cls == vocab.unit_id('night_witch') and result.reason == 'unknown_hp'
    result = resolve('DarkWitch', 81, 2)  # unsupported form
    assert result.cls == vocab.unit_id('night_witch') and result.form == 2
    original = tables()['witch', 0][81].copy()
    try:
        tables()['witch', 0][81].add((vocab.unit_id('witch'), 0, 'parent'))
        assert resolve('Witch', 81).reason == 'ambiguous_hp'
        assert resolve('Witch', 81).cls == vocab.unit_id('witch')
    finally:
        tables()['witch', 0][81] = original


def test_parent_and_direct_child_paths_agree():
    assert resolve('DarkWitch', 81).cls == resolve('Bat', 81).cls == vocab.unit_id('bats')
    assert resolve('Witch', 81).cls == resolve('Skeleton', 81).cls == vocab.unit_id('skeletons')
    assert resolve('FirespiritHut', 217).cls == resolve('FireSpirits', 217).cls
    # SIM's named FireSpirit calibration is 215, still unambiguously named.
    assert resolve('FireSpirits', 215).cls == vocab.unit_id('fire_spirit')


def test_unrelated_legacy_mapping_unchanged():
    for name, hp in [('Knight', 1666), ('Golem', 1039), ('GoblinBarrel', 202), ('Log', 0)]:
        for form in (0, 1, 2):
            assert resolve(name, hp, form).cls == vocab.engine_unit_id(name, hp)
            assert resolve(name, hp, form).form == form


def test_catalog_derived_relationships():
    catalog = json.loads(CATALOG.read_text())
    nw = next(c for c in catalog['cards'] if c['name'] == 'DarkWitch')
    assert nw['spawner']['character'] == nw['death_spawn']['character'] == 'Bat'
    # All level-11 native witnesses (six per family) must resolve to the
    # independently audited class, including Night Witch's bats.
    report = json.loads((Path(__file__).parent/'audit.json').read_text())
    for examples in report['examples'].values():
        for example in examples:
            entity = example['entity']
            assert vocab.UNIT_VOCAB[resolve(entity[3], entity[5]).cls] == example['expected']
