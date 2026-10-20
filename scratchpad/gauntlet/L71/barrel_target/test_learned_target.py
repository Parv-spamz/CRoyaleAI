from pathlib import Path
import sys

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from learned_target import SpatialGenModel, from_checkpoint_state
from pipeline.model_gen import GenModel
from pipeline.model_v3 import PATCH_X, PATCH_Y, cell_index
from pipeline.eval_gen import GenRows
from pipeline.tests.test_model_gen import toy


def sample():
    arrays = toy(n=4)['gen']
    arrays['unit_form'] = np.zeros(len(arrays['tok']), np.int8)
    arrays['opp_past'] = np.zeros((4, 3, 5), np.float32)
    arrays['opp_cycle'] = np.zeros((4, 8, 4), np.float32)
    arrays['projectiles'] = np.zeros((4, 64, 8), np.float32)
    arrays['effects'] = np.zeros((4, 32, 6), np.float32)
    arrays['own_ability'] = np.zeros((4, 2, 7), np.float32)
    arrays['projectiles'][:, 0] = [2, 1, .5, .5, .2, .8, 1, 1]
    # GenModel's ability pool accepts any object count; no latent hidden state.
    return GenRows(arrays, np.arange(4), 'cpu').batch(np.arange(4))


def test_zero_adapter_preserves_all_base_outputs():
    torch.set_num_threads(1)
    torch.manual_seed(10)
    base = GenModel(d=32, layers=1, d_c=16, n_cards=124, feature_version=5).eval()
    state = dict(gen=True, args=dict(d=32, layers=1, feature_version=5), d_c=16,
                 card_vocab=list(range(124)), model=base.state_dict())
    new = from_checkpoint_state(state).eval()
    batch = sample()
    with torch.no_grad():
        a = base(batch, card=batch['card'], form=batch['form'])
        b = new(batch, card=batch['card'], form=batch['form'])
    assert set(a) == set(b)
    for key in a:
        assert torch.equal(a[key], b[key]), key


def test_known_target_geometry_and_padding():
    model = SpatialGenModel(d=32, layers=1, d_c=16)
    batch = sample()
    with torch.no_grad():
        model.projectile_target_in[-1].weight.zero_()
        model.projectile_target_in[-1].bias.fill_(1)
        model.projectile_target_spread.weight[:, 0, 1, 1] = 1
    before = model.target_patches(batch)
    index = cell_index(torch.tensor([[.2, .8]]), PATCH_X, PATCH_Y).item()
    assert (before[:, index] == 1).all() and (before.sum(1) == 1).all()
    batch['projectiles'][:, 0, 4] = .8
    after = model.target_patches(batch)
    other = cell_index(torch.tensor([[.8, .8]]), PATCH_X, PATCH_Y).item()
    assert other != index and (after[:, other] == 1).all() and (after[:, index] == 0).all()
    batch['projectiles'][:, 0, 4:6] = -1
    assert (model.target_patches(batch) == 0).all()
    batch['projectiles'][:, 0, 4] = float('nan')
    assert (model.target_patches(batch) == 0).all()


def test_two_flights_both_remain_visible_and_order_invariant():
    model = SpatialGenModel(d=32, layers=1, d_c=16)
    batch = sample()
    with torch.no_grad():
        model.projectile_target_in[-1].weight.zero_()
        model.projectile_target_in[-1].bias.fill_(1)
        model.projectile_target_spread.weight[:, 0, 1, 1] = 1
    batch['projectiles'][:, 1] = batch['projectiles'][:, 0]
    batch['projectiles'][:, 1, 4] = .8
    a = model.target_patches(batch)
    batch['projectiles'] = batch['projectiles'].flip(1)
    assert torch.equal(a, model.target_patches(batch))
    assert (a.sum(1) == 2).all()


def test_expert_cell_loss_trains_residual_without_action_rule():
    torch.set_num_threads(1)
    model = SpatialGenModel(d=32, layers=1, d_c=16).eval()
    batch = sample()
    logits = model(batch, card=batch['card'], form=batch['form'])['cell']
    torch.nn.functional.cross_entropy(logits, torch.tensor([50*36+28]*4)).backward()
    grad = model.projectile_target_spread.weight.grad
    assert torch.isfinite(grad).all() and grad.abs().sum() > 0


def test_migration_refuses_wrong_shape_or_nonpublic_checkpoint():
    with pytest.raises(ValueError):
        from_checkpoint_state(dict(gen=True, args=dict(feature_version=1)))
    with pytest.raises(ValueError):
        SpatialGenModel(feature_version=4)
