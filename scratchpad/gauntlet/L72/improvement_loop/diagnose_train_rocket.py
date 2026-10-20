"""CPU-only Rocket failure decomposition on split-zero rows, never held-out data."""
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
from pipeline.eval_gen import GenRows
from pipeline.expert_context import probabilities
from pipeline.model_gen import load_model
from pipeline.opp_elixir_count import card_cost
from pipeline.rocket_teaching import sha
from pipeline.train_rocket_curriculum import load_subset

SOURCE = ROOT / 'icebow/data/pipeline/gen_dataset_v31_public.npz'
CONTEXTS = ROOT / 'icebow/data/bench/context_teaching_20261005'
HERE = Path(__file__).resolve().parent
CHECKPOINTS = {
    'r1e': 'icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt',
    'ordinary_il': 'icebow/data/bench/expert_context_20261005/v4_uniform/candidate.pt',
    'rocket_il': 'icebow/data/bench/expert_context_20261005/v4_rocket/candidate.pt',
}


def main():
    torch.set_num_threads(1)
    out = HERE / 'train_rocket_diagnosis.json'
    if out.exists():
        raise ValueError('Fresh diagnosis output required')
    with np.load(SOURCE) as z, np.load(CONTEXTS / 'cohorts.npz') as c:
        meta = json.loads(str(z['meta']))
        split, card, gate, rep, tags = [z[k] for k in ('split', 'y_card', 'y_gate', 'rep', 'tags')]
        cohorts = {k: c[k] for k in c.files}
    rocket = meta['card_vocab'].index('rocket')
    tornado = meta['card_vocab'].index('tornado')
    train = cohorts['pool'] & (split == 0)
    is_rocket = (gate == 1) & (card == rocket)
    masks = dict(finish=train & cohorts['finish'] & is_rocket,
                 combo_rocket=train & cohorts['combo'] & is_rocket,
                 combo_tornado=train & cohorts['combo'] & (gate == 1) & (card == tornado),
                 ordinary_rocket=train & is_rocket & ~cohorts['finish'] & ~cohorts['combo'])
    rng = np.random.default_rng(20261005)
    selected = {k: np.flatnonzero(v) if k == 'finish' else
                np.sort(rng.choice(np.flatnonzero(v), min(int(v.sum()), 256), replace=False))
                for k, v in masks.items()}
    ids = np.unique(np.concatenate(list(selected.values())))
    if np.any(split[ids] != 0):
        raise ValueError('Refusing any non-training row')
    print('TRAIN_ONLY_ROWS_SELECTED', len(ids), flush=True)
    sampled_mass = {arm: {k: float(probabilities(cohorts, split, arm)[m].sum())
                          for k, m in masks.items()} for arm in ('uniform', 'rocket')}
    sub, meta = load_subset(SOURCE, ids)
    rows = GenRows(sub, np.arange(len(ids)), 'cpu')
    costs = np.array([card_cost(k.replace('-', '_')) or 0 for k in meta['card_vocab']])
    legal = (sub['hand_card'] > 0) & (costs[sub['hand_card']] <= np.floor(sub['sc'][:, 3] * 10 + 1e-3)[:, None])
    summaries, predictions, hashes = {}, {}, {}
    for name, relative in CHECKPOINTS.items():
        path = ROOT / relative
        model, state = load_model(path, 'cpu')
        if state['args']['grid'] != 'lattice' or model.feature_version != 4:
            raise ValueError('This diagnosis requires original v4 lattice models')
        model.eval()
        result = []
        with torch.no_grad():
            for lo in range(0, len(ids), 64):
                ix = np.arange(lo, min(lo + 64, len(ids)))
                b = rows.batch(ix)
                enc = model.encode_gen(b)
                h = model.heads_gen(enc, b)
                logits = h['card'].masked_fill(~torch.as_tensor(legal[ix]), -torch.inf)
                cp = logits.softmax(-1).numpy()
                cells = model.cell_logits_gen(enc, b['card'], b['form'])
                predicted = cells.argmax(-1).numpy()
                xy = np.c_[predicted % 36 / 36, predicted // 36 / 64]
                distance = np.linalg.norm((xy - sub['y_xy'][ix]) * [18, 32], axis=1)
                called = h['gate'].sigmoid().numpy()
                chosen = sub['hand_card'][ix, logits.argmax(-1).numpy()]
                for j, i in enumerate(ix):
                    result.append(dict(row=int(ids[i]), tag=str(tags[rep[ids[i]]]),
                        tick=int(sub['tick'][i]), side=int(sub['side'][i]),
                        expert_card=meta['card_vocab'][int(sub['y_card'][i])],
                        chosen_card=meta['card_vocab'][int(chosen[j])],
                        gate=float(called[j]), legal=bool(legal[i].any()),
                        rocket_probability=float(cp[j][sub['hand_card'][i] == rocket].sum()),
                        expert_xy=sub['y_xy'][i].tolist(), predicted_xy=xy[j].tolist(),
                        aim_distance_tiles=float(distance[j]),
                        card_correct=bool(chosen[j] == sub['y_card'][i]),
                        aim_within_two=bool(distance[j] <= 2),
                        gated_card=bool(called[j] > .35 and chosen[j] == sub['y_card'][i] and legal[i].any()),
                        gated_aim=bool(called[j] > .35 and chosen[j] == sub['y_card'][i] and distance[j] <= 2 and legal[i].any())))
        summaries[name] = {}
        for cohort, chosen_ids in selected.items():
            membership = set(map(int, chosen_ids))
            a = [r for r in result if r['row'] in membership]
            summaries[name][cohort] = dict(rows=len(a), replays=len({r['tag'] for r in a}),
                gate_pass=sum(r['gate'] > .35 for r in a),
                **{k: sum(r[k] for r in a) for k in ('card_correct', 'aim_within_two', 'gated_card', 'gated_aim')},
                mean_rocket_probability=float(np.mean([r['rocket_probability'] for r in a])))
        predictions[name] = result
        hashes[name] = sha(path)
        print(name, json.dumps(summaries[name]), flush=True)
    report = dict(schema=1, split='training_only', selected_row_ids=ids.tolist(),
        selection_seed=20261005, selected_ids_sha256=hashlib.sha256(ids.tobytes()).hexdigest(),
        source_sha256=sha(SOURCE), contexts_sha256=sha(CONTEXTS / 'cohorts.npz'),
        script_sha256=sha(__file__), checkpoints=hashes,
        full_training_counts={k: int(m.sum()) for k, m in masks.items()},
        sampling_probability_mass=sampled_mass,
        expected_exposures_in_128000_draws={arm: {k: v * 128000 for k, v in m.items()} for arm, m in sampled_mass.items()},
        summaries=summaries, predictions=predictions,
        limitations=['Training diagnosis only, not generalization or acceptance.',
                     'Aim is teacher-forced distance to the expert cast; not simulated impact.',
                     'Finish windows come from the original replay outcome annotation.'])
    out.write_text(json.dumps(report, indent=2, allow_nan=False))
    print('TRAIN_ROCKET_DIAGNOSIS_COMPLETE')


if __name__ == '__main__':
    main()
