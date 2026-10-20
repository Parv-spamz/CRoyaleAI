"""Owner-requested source/coverage correction, without policy predictions."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pipeline import vocab
from pipeline.body_identity import resolve

FAMILIES = ('goblin_barrel', 'witch', 'night_witch', 'furnace')
LIMITS = (500, 1000, 1400, 1500)
CAT = ROOT / 'research/ext/cr-native-sandbox/native_core/data/live_card_catalog.json'


def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def read(p): return json.loads(Path(p).read_bytes())
def save(p, obj): p.write_text(json.dumps(obj, indent=2) + '\n')


def family_map():
    result, done = {}, set()
    for c in read(CAT)['cards']:
        family = vocab.engine_key(c['display_name'])
        if family not in FAMILIES or family in done: continue
        done.add(family)
        for field, form in (('card_id', 0), ('evolution_form_id', 1), ('hero_form_id', 2)):
            if c.get(field) is not None:
                result[int(c[field])] = (family, c['display_name'], form)
    assert done == set(FAMILIES)
    return result


def live_frames(events):
    result = {}
    for e in events:
        if e.get('event') != 'frame' or 'ents' not in e or e.get('my_side') is None: continue
        bodies = [dict(side=b[0], x=b[1], y=b[2], card_id=b[3], hp=b[4], max_hp=b[5], kind=b[6])
                  for b in e['ents'] if len(b) >= 7]
        result[int(e['tick'])] = dict(tick=int(e['tick']), observer=int(e['my_side']), bodies=bodies,
            projectiles=[], ready=None, mode='legacy_public_frame')
    for e in events:
        if e.get('event') != 'decision' or not e.get('public'): continue
        p = e['public']; tick = int(p['raw_tick'])
        hand, elixir = p.get('own_hand'), p.get('own_elixir_raw')
        ready = None if hand is None or elixir is None else (
            any(vocab.engine_key(c.get('name') or '') == 'rocket' for c in hand) and float(elixir) >= 6)
        result[tick] = dict(tick=tick, observer=int(p['observer_side']), bodies=p.get('raw_bodies', []),
            projectiles=p.get('raw_projectiles', []), ready=ready, mode='decision_public')
    return [result[t] for t in sorted(result)]


def native_frames(rec, side):
    result = {}
    for f in rec['frames'] + rec.get('play_frames', []):
        bodies = [dict(side=b[0], x=b[1], y=b[2], hp=b[4], max_hp=b[5], kind=b[6], card_id=b[-2])
                  for b in f.get('entities', []) if len(b) >= 9 and b[6] not in (12, 13)]
        bodies.extend(dict(side=t[0], x=t[3], y=t[4], hp=t[5], max_hp=t[6],
                           kind=13 if t[1] == 'princess' else 12, card_id=-1) for t in f.get('towers', []))
        result[int(f['tick'])] = dict(tick=int(f['tick']), observer=side, bodies=bodies,
            projectiles=f.get('public_objects', {}).get('projectiles', []), ready=None, mode='native_public')
    return [result[t] for t in sorted(result)]


def analyze(identifier, frames, mapping):
    evidence = {k: dict(first_tick=None, frames=0, parent_frames=0, child_frames=0,
                        uncertain_body_frames=0, projectile_frames=0) for k in FAMILIES}
    towers = {}
    for f in frames:
        observed = {k: set() for k in FAMILIES}
        for b in f['bodies']:
            if int(b['side']) == f['observer'] or not isinstance(b.get('hp'), (int, float)) or b['hp'] <= 0: continue
            match = mapping.get(int(b.get('card_id', -1)))
            if match:
                family, name, form = match
                if family == 'goblin_barrel': reason = 'uncertain_body'
                else:
                    reason = resolve(name, b.get('max_hp'), form).reason
                    if reason not in ('parent', 'child'): reason = 'uncertain_body'
                observed[family].add(reason)
            if int(b.get('kind', -1)) != 13 or int(b.get('card_id', -1)) != -1: continue
            identity = (int(b['side']), b['x'], b['y'])
            if identity not in towers:
                towers[identity] = dict(identity=list(identity), observations=[])
            hp = float(b['hp'])
            if not math.isfinite(hp): continue
            towers[identity]['observations'].append((f['tick'], hp, f['ready']))
        # Dead towers remain useful follow-through, but never enter denominators.
        for b in f['bodies']:
            if int(b['side']) != f['observer'] and int(b.get('kind', -1)) == 13 and int(b.get('card_id', -1)) == -1 and b.get('hp') == 0:
                identity = (int(b['side']), b['x'], b['y'])
                towers.setdefault(identity, dict(identity=list(identity), observations=[]))['observations'].append((f['tick'], 0, f['ready']))
        for p in f['projectiles'] or []:
            if isinstance(p, dict) and int(p['side']) != f['observer'] and int(p.get('card_id', -1)) in mapping:
                observed[mapping[int(p['card_id'])][0]].add('projectile')
        for family, reasons in observed.items():
            if not reasons: continue
            row = evidence[family]
            if row['first_tick'] is None: row['first_tick'] = f['tick']
            row['frames'] += 1
            for reason in reasons: row[reason + '_frames'] += 1
    candidates = []
    for t in towers.values():
        observations = sorted(t.pop('observations'))
        qualifies = [(tick, hp, ready) for tick, hp, ready in observations if 0 < hp <= 1500]
        if not qualifies: continue
        row = dict(t, first_tick=qualifies[0][0], first_hp=qualifies[0][1],
                   minimum_positive_hp=min(hp for _, hp, _ in qualifies),
                   last_qualifying_tick=qualifies[-1][0], qualifying_samples=len(qualifies),
                   later_zero_tick=next((tick for tick, hp, _ in observations if hp == 0 and tick > qualifies[0][0]), None),
                   max_qualifying_sample_gap_ticks=max([b[0]-a[0] for a,b in zip(qualifies, qualifies[1:])] or [0]),
                   ready_samples=sum(ready is True for _, _, ready in qualifies),
                   readiness_unknown_samples=sum(ready is None for _, _, ready in qualifies),
                   first_ready_tick=next((tick for tick, _, ready in qualifies if ready is True), None),
                   thresholds={str(limit): dict(samples=sum(0 < hp <= limit for _, hp, _ in observations),
                       first_tick=next((tick for tick, hp, _ in observations if 0 < hp <= limit), None)) for limit in LIMITS},
                   hp_bands={str(high): sum(high-500 < hp <= high for _, hp, _ in observations) for high in (500,1000,1500)})
        candidates.append(row)
    return dict(id=identifier, public_samples=len(frames), sample_modes=dict(Counter(f['mode'] for f in frames)),
                encounters=evidence, towers=sorted(candidates, key=lambda r: r['identity']))


def aggregate(rows):
    return dict(records=len(rows), with_public_observations=sum(r['public_samples'] > 0 for r in rows),
        no_public_observations=sum(r['public_samples'] == 0 for r in rows),
        encounters={k: dict(records=sum(r['encounters'][k]['frames'] > 0 for r in rows),
                            confirmed_parent_records=sum(r['encounters'][k]['parent_frames'] > 0 for r in rows),
                            projectile_records=sum(r['encounters'][k]['projectile_frames'] > 0 for r in rows)) for k in FAMILIES},
        thresholds={str(limit): dict(records=sum(any(t['thresholds'][str(limit)]['samples'] for t in r['towers']) for r in rows),
                     towers=sum(t['thresholds'][str(limit)]['samples'] > 0 for r in rows for t in r['towers'])) for limit in LIMITS},
        rocket_ready_records=sum(any(t['ready_samples'] for t in r['towers']) for r in rows),
        rocket_ready_towers=sum(t['ready_samples'] > 0 for r in rows for t in r['towers']))


def main():
    assert not (HERE / 'started_v2.json').exists()
    inventory_path = HERE.parent / 'void_capacity/inventory.json'
    inventory = read(inventory_path); tags = {s['tag'] for s in inventory['exact_sides']}
    members = sorted([m for m in inventory['qualified'] if m['tag'] in tags], key=lambda r:r['tag'])
    live, excluded = [], []
    for p in sorted((ROOT/'scratchpad/gauntlet/L68/live_reader').glob('live_play_*.jsonl')):
        if not 'live_play_20261004_210000' <= p.stem < 'live_play_20261005_124400': continue
        events = [json.loads(line) for line in p.open()]
        target = live if any(e.get('event') == 'end' for e in events) else excluded
        target.append(dict(path=str(p.relative_to(ROOT)), sha256=sha(p)))
    sources = {str(inventory_path.relative_to(ROOT)):sha(inventory_path)}
    for p in [Path(__file__), HERE/'verify_v2.py', HERE/'CORRECTION.md', HERE/'PLAN.md', CAT,
              ROOT/'pipeline/body_identity.py', ROOT/'pipeline/vocab.py', ROOT/'pipeline/obs_contract.py',
              ROOT/'research/ext/Royale/RoyaleSim/data/derived/cards.json',
              ROOT/'research/ext/Royale/RoyaleSim/data/calibration.json']:
        sources[str(p.relative_to(ROOT))] = sha(p)
    for m in members: assert sha(ROOT/m['path']) == m['sha256']
    mapping = family_map()
    save(HERE/'started_v2.json',dict(live=live, excluded_unclosed=excluded, pro=members,
        exact_sides=inventory['exact_sides'], sources=sources, family_map=mapping, predictions=0))
    live_rows=[];native_rows=[]
    for m in live:
        p=ROOT/m['path'];assert sha(p)==m['sha256'];events=[json.loads(line) for line in p.open()]
        row=analyze(p.name,live_frames(events),mapping)
        start=next(e for e in events if e['event']=='start')
        row['checkpoint']=start.get('ckpt_sha256',start.get('ckpt'))
        row['anti_leak']=start.get('anti_leak','unlogged')
        row['rocket_attempts']=sum(e.get('event')=='play' and e.get('name')=='Rocket' for e in events)
        row['rocket_confirmations']=sum(e.get('event')=='confirmed' and e.get('name')=='Rocket' for e in events)
        live_rows.append(row)
    for m in members:
        rec=read(ROOT/m['path'])
        for side in [s['side'] for s in inventory['exact_sides'] if s['tag']==m['tag']]:
            row=analyze(m['tag']+':'+str(side),native_frames(rec,side),mapping)
            row['split']=m['split'];row['recorded_level']=rec['level'];native_rows.append(row)
    for p,h in sources.items(): assert sha(ROOT/p)==h
    save(HERE/'details_v2.json',dict(live=live_rows,pro=native_rows))
    result=dict(complete=True,policy_predictions=0,optimizer_updates=0,trained=False,
        started_sha256=sha(HERE/'started_v2.json'),details_sha256=sha(HERE/'details_v2.json'),
        live=aggregate(live_rows),pro=aggregate(native_rows),
        live_rocket_attempts=sum(r['rocket_attempts'] for r in live_rows),
        live_rocket_confirmations=sum(r['rocket_confirmations'] for r in live_rows),
        excluded_unclosed=len(excluded))
    save(HERE/'report_v2.json',result);print(json.dumps(result));print('OWNER_COVERAGE_RECHECK_COMPLETE')


if __name__=='__main__': main()
