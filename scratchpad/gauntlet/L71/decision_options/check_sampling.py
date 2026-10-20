"""R1e Q1/Q2 CPU diagnostics; follow with check_sampling_v2.py for old R1.

The historical first run also evaluated old R1 without vocabulary remapping.
That invalid arm has been removed; v2 is the only supported old-R1 evaluator.
"""
from __future__ import annotations
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pipeline.decision_options import DecisionOptions, filtered_probabilities, choose_cells, rocket_radius_tiles
from pipeline.eval_gen import GenRows
from pipeline.model_gen import load_model
from pipeline.opp_elixir_count import card_cost

DATA = ROOT / 'icebow/data/pipeline/gen_dataset_v31_public.npz'
LABELS = ROOT / '.foreman/codex_autopilot/runs/public_labels_full_reconstructed/labels.jsonl'
CHECKPOINTS = {
    'r1e': 'icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt',
}
CACHE = ROOT / 'icebow/data/bench/decision_options_20261004'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def take(zf, name, idx):
    """Streaming subset reader adapted from L71/rocket_diag; at most 16 MiB/chunk."""
    with zf.open(name + '.npy') as f:
        version = np.lib.format.read_magic(f)
        shape, fortran, dtype = (np.lib.format.read_array_header_1_0(f) if version == (1, 0)
                                 else np.lib.format.read_array_header_2_0(f))
        if fortran or dtype.hasobject:
            raise ValueError('unsupported source array layout')
        width = int(np.prod(shape[1:], dtype=np.int64)) * dtype.itemsize
        result = np.empty((len(idx),) + shape[1:], dtype)
        step = max(1, (16 << 20) // max(width, 1))
        for lo in range(0, shape[0], step):
            count = min(step, shape[0] - lo)
            buf = bytearray()
            while len(buf) < count * width:
                part = f.read(count * width - len(buf))
                if not part:
                    raise EOFError(name)
                buf += part
            a, b = np.searchsorted(idx, [lo, lo + count])
            if b > a:
                result[a:b] = np.frombuffer(buf, dtype).reshape((count,) + shape[1:])[idx[a:b] - lo]
        return result


def mean(values, mask):
    return float(np.asarray(values)[mask].mean()) if np.any(mask) else None


def metrics(prob, base, hand, rocket_id, allowed, gate, target_slot, yplay, masks):
    n = len(hand); row = np.arange(n)
    chosen = base.argmax(1)
    has = allowed.any(1)
    changed = 1 - prob[row, chosen]
    top = base.max(1)
    rocket = (prob * (hand == rocket_id)).sum(1)
    correct = prob[row, np.maximum(target_slot, 0)]
    valid = yplay & has & (target_slot >= 0)
    result = dict(agreement=mean(correct, valid), agreement_n=int(valid.sum()),
                  changed_probability=mean(changed, valid),
                  confident_override=mean(changed, valid & (top >= .6)),
                  confident_n=int((valid & (top >= .6)).sum()),
                  rocket_recall=mean(rocket, masks['pro_rocket']),
                  rocket_false_fire=mean(rocket, masks['other_pro_play']),
                  rocket_on_pro_wait=mean(rocket, ~yplay & has),
                  contexts={key: dict(n=int(mask.sum()), rocket_choice=mean(rocket, mask),
                                     gate_pass_035=mean(gate > .35, mask),
                                     rocket_gated_035=mean(rocket * (gate > .35), mask),
                                     rocket_gated_027=mean(rocket * (gate > .27), mask))
                            for key, mask in masks.items()})
    return result


def main():
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    try:
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    except AttributeError:
        pass
    started = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    def log(message):
        print(f'[{time.time()-started:.0f}s] {message}', flush=True)
    with np.load(DATA, allow_pickle=False) as z, zipfile.ZipFile(DATA) as zf:
        meta = json.loads(str(z['meta']))
        cv = meta['card_vocab']; rocket_id = cv.index('rocket')
        target_deck = sorted(cv.index(k) for k in ('ice-wizard', 'knight', 'rocket', 'skeletons',
                                                  'tesla', 'the-log', 'tornado', 'x-bow'))
        ids = np.flatnonzero((z['deck_id'] == 90) & (z['split'] == 1))
        keys = ['sc', 'hand_card', 'hand_form', 'next_card', 'next_form', 'deck_card', 'deck_form', 'past',
                'y_gate', 'y_card', 'y_hand_pos', 'y_xy', 'y_wait_card', 'y_crowns', 'tick', 'side', 'rep',
                'split', 'deck_id', 'opp_past', 'opp_cycle', 'projectiles', 'effects', 'own_ability', 'y_cell']
        sub = {k: take(zf, k, ids) for k in keys}
        assert (np.sort(sub['deck_card'], axis=1) == target_deck).all(), 'deck90 no longer icebow'
        offsets = z['off']; lengths = offsets[ids + 1] - offsets[ids]
        gather = np.concatenate([np.arange(offsets[i], offsets[i + 1]) for i in ids])
        sub['tok'] = take(zf, 'tok', gather); sub['unit_form'] = take(zf, 'unit_form', gather)
        sub['off'] = np.r_[0, np.cumsum(lengths)].astype(np.int64)
        tags = z['tags']
    n = len(ids); log(f'loaded {n} held-out icebow rows, threads=1, CPU only')
    yplay = sub['y_gate'] > .5; hand = sub['hand_card'].astype(int)
    costs = np.array([card_cost(k.replace('-', '_')) or 0.0 for k in cv])
    allowed = (hand > 0) & (costs[hand] <= np.floor(sub['sc'][:, 3] * 10 + 1e-3)[:, None] + 1e-6)
    rmask = yplay & (sub['y_card'] == rocket_id)
    ri = np.flatnonzero(rmask)
    wanted = {(str(tags[sub['rep'][r]]), int(sub['side'][r]), int(sub['tick'][r])): j for j, r in enumerate(ri)}
    tower = np.zeros(len(ri), bool); finish = tower.copy(); joined = tower.copy()
    with LABELS.open() as f:
        for line in f:
            label = json.loads(line)
            if label.get('card') != 'rocket':
                continue
            key = (label['tag'], int(label['side']), int(label['tick']))
            if key in wanted:
                j = wanted[key]; joined[j] = True; tower[j] = bool(label['tower_rocket'])
                finish[j] = any(hit.get('finish') for hit in label.get('tower_hits', []))
    assert joined.all(), 'Missing pro Rocket labels'
    masks = {'pro_rocket': rmask, 'other_pro_play': yplay & ~rmask}
    for name, values in [('pro_tower_rocket', tower), ('pro_finishing_rocket', finish)]:
        masks[name] = np.zeros(n, bool); masks[name][ri] = values
    masks['late_pro_tower_rocket'] = masks['pro_tower_rocket'] & (sub['sc'][:, 0] * 300 >= 120)
    report = {'dataset': str(DATA.relative_to(ROOT)), 'dataset_sha256': sha(DATA),
              'labels_sha256': sha(LABELS), 'rows': n, 'pro_plays': int(yplay.sum()),
              'pro_rockets': len(ri), 'replays': len(np.unique(sub['rep'])), 'split': 'validation (1)',
              'device': 'cpu', 'threads': 1, 'rocket_radius_tiles': rocket_radius_tiles(),
              'rule': 'reject agreement drop >0.01 or confident override >1e-12; four frozen settings only',
              'limits': 'Teacher-forced card/target agreement, not wins. Finishing subset is actual pro finishing Rocket plays, not all potential one/two-Rocket opportunities. No next-Rocket planning is measured.',
              'models': {}}
    rows = GenRows(sub, np.arange(n), torch.device('cpu'))
    for label, relative in CHECKPOINTS.items():
        model, state = load_model(ROOT / relative, torch.device('cpu')); model.eval()
        gates = np.empty(n, np.float32); cards = np.empty((n, 4), np.float32)
        cell_logits = np.empty((len(ri), 2304), np.float32)
        rocket_position = {int(r): j for j, r in enumerate(ri)}
        with torch.no_grad():
            for lo in range(0, n, 64):
                ix = np.arange(lo, min(n, lo + 64)); b = rows.batch(ix)
                enc = model.encode_gen(b); heads = model.heads_gen(enc, b)
                gates[ix] = heads['gate'].sigmoid().numpy(); cards[ix] = heads['card'].numpy()
                pos = [i for i, r in enumerate(ix) if int(r) in rocket_position]
                if pos:
                    cell_logits[[rocket_position[int(ix[i])] for i in pos]] = model.cell_logits_gen(
                        {k: v[pos] for k, v in enc.items()}, b['card'][pos], b['form'][pos]).numpy()
                if lo % 4096 == 0:
                    log(f'{label} forward {lo}/{n}')
        base = filtered_probabilities(cards, allowed, ratio=np.finfo(float).tiny, temperature=1)
        greedy = np.zeros_like(base); greedy[np.arange(n), base.argmax(1)] = allowed.any(1)
        baseline = metrics(greedy, base, hand, rocket_id, allowed, gates, sub['y_hand_pos'], yplay, masks)
        candidates = []
        for ratio in (.5, .7):
            for temperature in (.7, 1.0):
                prob = filtered_probabilities(cards, allowed, ratio, temperature)
                m = metrics(prob, base, hand, rocket_id, allowed, gates, sub['y_hand_pos'], yplay, masks)
                m.update(ratio=ratio, temperature=temperature,
                         agreement_delta_pp=100 * (m['agreement'] - baseline['agreement']))
                m['passes_offline'] = m['agreement_delta_pp'] >= -1 - 1e-10 and m['confident_override'] <= 1e-12
                candidates.append(m)
        logits = torch.from_numpy(cell_logits)
        old_cell = logits.argmax(-1).numpy()
        area_cell = choose_cells(logits, ['Rocket'] * len(ri), DecisionOptions(spell_aim='rocket_area')).numpy()
        targets = sub['y_xy'][ri] * [18, 32]
        def coverage(cells):
            coords = np.c_[cells % 36 / 2, cells // 36 / 2]
            return np.linalg.norm(coords - targets, axis=1) <= rocket_radius_tiles() + 1e-6
        aim = {}
        for name, mask in [('all_pro_rocket', np.ones(len(ri), bool)), ('tower', tower), ('finishing', finish)]:
            aim[name] = {'n': int(mask.sum()), 'argmax_target_coverage': mean(coverage(old_cell), mask),
                         'area_target_coverage': mean(coverage(area_cell), mask)}
        cache = CACHE / (label + '.npz')
        np.savez_compressed(cache, ids=ids, logits=cards, allowed=allowed, hand=hand, gate=gates,
                            y_slot=sub['y_hand_pos'], y_play=yplay, y_card=sub['y_card'], rocket_id=rocket_id,
                            rocket_rows=ri, cell_logits=cell_logits, pro_xy=sub['y_xy'][ri],
                            old_cell=old_cell, area_cell=area_cell, rep=sub['rep'],
                            **{'mask_' + k: v for k, v in masks.items()})
        report['models'][label] = dict(checkpoint=relative, checkpoint_sha256=sha(ROOT / relative),
                                       feature_version=state['args'].get('feature_version', 1),
                                       cache=str(cache.relative_to(ROOT)), cache_sha256=sha(cache),
                                       baseline=baseline, candidates=candidates, aim=aim)
        (OUT/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
        log(f'{label}: diagnostics saved')
    report['elapsed_seconds'] = time.time() - started
    (OUT/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    log('SAMPLING_AND_AIM_CHECKS_COMPLETE')


if __name__ == '__main__':
    main()
