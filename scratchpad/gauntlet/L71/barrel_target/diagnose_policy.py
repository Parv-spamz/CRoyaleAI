"""Held-out Log aiming and public Barrel-target sensitivity; CPU only.

The forced-Log head is diagnostic, never an inference override. Perturbing only
the target isolates model sensitivity; it is not a valid gameplay simulation.
"""
import argparse
import ctypes
import json
from pathlib import Path
import sys
import time
from zipfile import ZipFile

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline.eval_gen import GenRows
from pipeline.model_gen import load_model
from pipeline.opp_elixir_count import card_cost
from pipeline.train_rocket_curriculum import take, load_subset
from pipeline.rocket_teaching import ICEBOW, sha

DATA = ROOT/'icebow/data/pipeline/gen_dataset_v31_public.npz'
CKPT = ROOT/'icebow/data/bench/rl_royale/rseries_r1e31/rseries_r1e31_u0155.pt'
HERE = Path(__file__).parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ckpt', type=Path, default=CKPT)
    ap.add_argument('--name', default='r1e')
    args = ap.parse_args()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    try:
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    except AttributeError:
        pass
    start = time.time()
    with np.load(DATA) as z, ZipFile(DATA) as archive:
        meta = json.loads(str(z['meta']))
        cv = meta['card_vocab']
        barrel_id, log_id = cv.index('goblin-barrel'), cv.index('the-log')
        decks = [d['id'] for d in meta['decks'] if set(d['cards']) == ICEBOW]
        ids = np.flatnonzero(np.isin(z['deck_id'], decks) & (z['split'] == 1))
        projectiles = take(archive, 'projectiles', ids)
        barrel = (projectiles[..., 0] == barrel_id) & (projectiles[..., 1] == 1)
        use = barrel.any(1)
        ids = ids[use]
        tags = z['tags']
    print(f'[{time.time()-start:.0f}s] {len(ids)} held-out rows with a visible enemy Goblin Barrel', flush=True)
    sub, meta = load_subset(DATA, ids)
    model, st = load_model(args.ckpt, 'cpu')
    assert st['card_vocab'] == cv and model.feature_version >= 4
    model.eval()
    rows = GenRows(sub, np.arange(len(ids)), 'cpu')
    values = []
    with torch.no_grad():
        for lo in range(0, len(ids), 32):
            ix = np.arange(lo, min(lo+32, len(ids)))
            batch = rows.batch(ix)
            out = model(batch, card=torch.full((len(ix),), log_id), form=torch.zeros(len(ix), dtype=torch.long))
            cell = out['cell'].argmax(-1).numpy()
            gate = out['gate'].sigmoid().numpy()
            hand = sub['hand_card'][ix]
            costs = np.asarray([card_cost(k.replace('-', '_')) or 0 for k in cv])
            allowed = (hand > 0) & (costs[hand] <= np.floor(sub['sc'][ix, 3]*10+1e-3)[:, None])
            choice = out['card'].masked_fill(~torch.from_numpy(allowed), -torch.inf).argmax(-1).numpy()
            chosen_card = hand[np.arange(len(ix)), choice]
            perturbed = dict(batch)
            pp = batch['projectiles'].clone()
            mask = (pp[..., 0] == barrel_id) & (pp[..., 1] == 1) & (pp[..., 4] >= 0)
            pp[..., 4] = torch.where(mask, 1-pp[..., 4], pp[..., 4])
            perturbed['projectiles'] = pp
            flipped = model(perturbed, card=torch.full((len(ix),), log_id), form=torch.zeros(len(ix), dtype=torch.long))['cell'].argmax(-1).numpy()
            for j, row in enumerate(ix):
                shots = sub['projectiles'][row]
                shots = shots[(shots[:, 0] == barrel_id) & (shots[:, 1] == 1)]
                tx = float(shots[0, 4]) if len(shots) == 1 else None
                ty = float(shots[0, 5]) if len(shots) == 1 else None
                # Only unambiguous own-half targets well clear of the centre line.
                certain = tx is not None and 0 <= tx <= 1 and ty >= .5 and (tx < .4 or tx > .6)
                px, py = int(cell[j]) % 36 / 36, int(cell[j]) // 36 / 64
                fx = int(flipped[j]) % 36 / 36
                expert_log = sub['y_gate'][row] == 1 and sub['y_card'][row] == log_id
                values.append(dict(row_id=int(ids[row]), tag=str(tags[sub['rep'][row]]), tick=int(sub['tick'][row]),
                    side=int(sub['side'][row]), target_x=tx, target_y=ty, unambiguous_target=certain,
                    target_tti_s=float(shots[0, 6]) if len(shots) == 1 else None,
                    pro_log=bool(expert_log), pro_xy=sub['y_xy'][row].tolist() if expert_log else None,
                    log_available=bool(((hand[j] == log_id) & allowed[j]).any()),
                    chose_log=bool(allowed[j].any() and chosen_card[j] == log_id), gate=float(gate[j]),
                    log_xy=[px, py], swapped_target_log_x=fx,
                    original_lane_correct=bool(certain and (px < .5) == (tx < .5)),
                    swapped_lane_correct=bool(certain and (fx < .5) != (tx < .5)),
                    changed_lane_with_target=bool((px < .5) != (fx < .5))))
    def metrics(items):
        return dict(n=len(items), log_choices=sum(v['chose_log'] for v in items),
                    gated_log_choices=sum(v['chose_log'] and v['gate'] > .35 for v in items),
                    forced_log_same_lane=sum(v['original_lane_correct'] for v in items),
                    forced_log_swapped_lane=sum(v['swapped_lane_correct'] for v in items),
                    changed_lane_with_target=sum(v['changed_lane_with_target'] for v in items))
    known = [v for v in values if v['unambiguous_target'] and v['log_available']]
    pro = [v for v in known if v['pro_log']]
    pro_same = [v for v in pro if (v['pro_xy'][0] < .5) == (v['target_x'] < .5)]
    report = dict(checkpoint=str(args.ckpt), checkpoint_sha256=sha(args.ckpt), dataset_sha256=sha(DATA),
        total_visible_barrel_rows=len(values), known_playable=metrics(known), pro_log=metrics(pro),
        pro_log_same_lane=metrics(pro_same), rows=values, seconds=time.time()-start,
        limitations=['Held-out teacher-forced states; no gameplay outcome or live-target validation.',
                    'Forced Log aim separates the placement head from learned card/gate decisions.',
                    'Changing only the target measures feature sensitivity, not a physically valid counterfactual.',
                    'Other threats can make a different-lane Log correct; the pro same-lane subset reduces that ambiguity.'])
    (HERE/(args.name+'_policy.json')).write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ('total_visible_barrel_rows','known_playable','pro_log','pro_log_same_lane','seconds')}))
    print('BARREL_POLICY_DIAGNOSTIC_COMPLETE')


if __name__ == '__main__':
    main()
