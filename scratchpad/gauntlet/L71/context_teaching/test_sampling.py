from pathlib import Path
import sys
import numpy as np
import pytest
sys.path.insert(0, str(Path(__file__).parent))
from sampling import MIXTURES, probabilities


def cohorts():
    split = np.array([0]*10 + [1]*10)
    c = dict(pool=np.ones(20, bool))
    for name, rows in [('opportunity',[1,11]), ('sequence',[2,12]), ('xbow',[3,13]), ('barrel',[4,14])]:
        c[name] = np.isin(np.arange(20), rows)
    return c, split


@pytest.mark.parametrize('arm', list(MIXTURES))
def test_declared_masses_never_touch_validation(arm):
    c, split = cohorts()
    p = probabilities(c, split, arm)
    assert np.isclose(p.sum(), 1) and (p[10:] == 0).all()
    ordinary = MIXTURES[arm]['pool'] / 10
    for name, row in [('opportunity',1), ('sequence',2), ('xbow',3), ('barrel',4)]:
        assert np.isclose(p[row], ordinary + MIXTURES[arm].get(name,0))
    draws = np.random.default_rng(7).choice(20, 10000, p=p)
    assert (split[draws] == 0).all()


def test_missing_bucket_is_not_silently_replaced():
    c, split = cohorts()
    c['barrel'][:10] = False
    with pytest.raises(ValueError, match='Empty required'):
        probabilities(c, split, 'rocket_barrel')
    c, split = cohorts()
    c['pool'][3] = False
    with pytest.raises(ValueError, match='Invalid cohort'):
        probabilities(c, split, 'rocket_xbow')
