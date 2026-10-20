"""Predeclared expert exposure ablations, strictly train-only."""
import numpy as np

MIXTURES = {
    'uniform': {'pool': 1.0},
    'rocket': {'pool': .8, 'opportunity': .1, 'sequence': .1},
    'rocket_xbow': {'pool': .75, 'opportunity': .1, 'sequence': .1, 'xbow': .05},
    'rocket_barrel': {'pool': .75, 'opportunity': .1, 'sequence': .1, 'barrel': .05},
    'rocket_both': {'pool': .7, 'opportunity': .1, 'sequence': .1, 'xbow': .05, 'barrel': .05},
}


def probabilities(cohorts, split, arm):
    if arm not in MIXTURES:
        raise ValueError('Unknown predeclared arm')
    split = np.asarray(split)
    pool = np.asarray(cohorts['pool'])
    if pool.dtype != bool or pool.shape != split.shape:
        raise ValueError('Invalid pool')
    probability = np.zeros(len(split), np.float64)
    for name, mass in MIXTURES[arm].items():
        mask = np.asarray(cohorts[name])
        if mask.dtype != bool or mask.shape != pool.shape or (mask & ~pool).any():
            raise ValueError('Invalid cohort ' + name)
        eligible = mask & pool & (split == 0)
        if not eligible.any():
            raise ValueError('Empty required train cohort ' + name)
        probability[eligible] += mass / eligible.sum()
    if abs(probability.sum()-1) > 1e-12 or probability[split != 0].sum() != 0:
        raise ValueError('Invalid training distribution')
    return probability
