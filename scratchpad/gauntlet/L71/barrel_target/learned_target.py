"""Compatibility wrapper for the integrated version-6 learned target residual.

No card-specific action rule: all public known targets use the same trainable
projection. Zero initialization preserves every legacy output before learning.
"""
from pipeline.model_gen import GenModel


class SpatialGenModel(GenModel):
    def __init__(self, *, d=128, layers=4, d_c=64, n_cards=124, feature_version=6, **kwargs):
        if feature_version != 6:
            raise ValueError('Prototype requires explicit version6')
        super().__init__(d=d, layers=layers, d_c=d_c, n_cards=n_cards, feature_version=feature_version, **kwargs)


def from_checkpoint_state(state):
    if not state.get('gen') or int(state['args'].get('feature_version', 1)) not in (4, 5):
        raise ValueError('Explicit public v4/v5 source checkpoint required')
    args = state['args']
    model = SpatialGenModel(d=int(args['d']), layers=int(args['layers']), d_c=int(state['d_c']),
                            n_cards=len(state['card_vocab']))
    result = model.load_state_dict(state['model'], strict=False)
    expected = {'projectile_target_in.0.weight', 'projectile_target_in.0.bias',
                'projectile_target_in.2.weight', 'projectile_target_in.2.bias',
                'projectile_target_spread.weight'}
    if set(result.missing_keys) != expected or result.unexpected_keys:
        raise ValueError('Unexpected checkpoint migration: ' + str(result))
    return model
