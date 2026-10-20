"""Pro baseline for pre-emptive Log vs Goblin/Skeleton Barrel, bot-telemetry definition
(pipeline/public_outcomes.py summarize, lines 158-168). CPU only, single process."""
import sys, json, glob, random, ctypes, bisect
from pathlib import Path
from collections import Counter
ROOT = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(ROOT))
from pipeline.public_outcomes import normalize, summarize
from pipeline.dataset_gen import card_key
try: ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)  # below normal
except Exception: pass
OUT = Path(__file__).parent
CORPUS = ROOT / 'scratchpad/gauntlet/ext/corpus_v6/icebow_public_v1'
DECK = {'xbow', 'skeletons', 'log', 'knight', 'tesla', 'tornado', 'icewizard', 'rocket'}
BARRELS = ('goblin-barrel', 'skeleton-barrel')
def deck_set(d): return {c.split('@')[0].lower() for c in d}

def measure(rec, side, check_summary=False):
    """Per-barrel rows for one side, same loop as summarize(); extra frames only for the conditional."""
    plays = sorted([dict(p, card=card_key(p['card']), tick=int(p.get('engine_tick', p['tick']))) for p in rec['log']
                    if p.get('accepted') is True and not p.get('skipped') and not p.get('ability') and p.get('card')],
                   key=lambda p: p['tick'])
    barrels = [p for p in plays if p['side'] != side and p['card'] in BARRELS]
    mine = [p for p in plays if p['side'] == side]
    log_ticks = [p['tick'] for p in mine if p['card'] == 'the-log']
    ticks = max((f['tick'] for f in rec['frames']), default=0)
    frames = [normalize(f) for f in rec['frames']]  # exactly what summarize() uses
    # elixir/hand evidence for the conditional (measurement only)
    ex = {f['tick']: f['elixir'][side] for f in rec['frames'] + rec.get('play_frames', []) if f.get('elixir')}
    ex_ticks = sorted(ex)
    # own-hand timeline: hand is constant between own plays, so hand at t == hand_before of the next own play;
    # after the last own play use play_frames' players block (opponent plays) if any.
    nxt = sorted((p['tick'], [card_key(c) for c in p['hand_before']]) for p in rec['log']
                 if p['side'] == side and p.get('accepted') is True and not p.get('skipped') and not p.get('ability') and p.get('hand_before'))
    nxt_t = [t for t, _ in nxt]
    pfh = sorted((f['tick'], [card_key(c) for c in pl['hand']]) for f in rec.get('play_frames', [])
                 for pl in f.get('players', []) if pl['side'] == side and pl.get('hand'))
    pfh_t = [t for t, _ in pfh]
    def hand_at(t):
        i = bisect.bisect_left(nxt_t, t)
        if i < len(nxt): return nxt[i][1]
        j = bisect.bisect_right(pfh_t, t) - 1  # after our last play: latest recorded block at/before t
        if j >= 0 and (not nxt or pfh_t[j] > nxt_t[-1]): return pfh[j][1]
        return None  # unknown
    rows = []
    for b in barrels:
        end = min([p['tick'] for p in barrels if p['card'] == b['card'] and p['tick'] > b['tick']] + [ticks + 1])
        ts = [f['tick'] for f in frames if b['tick'] <= f['tick'] < end and
              (any(q['card'] == b['card'] and q['side'] != side for q in f['projectiles']) or
               (b['card'] == 'skeleton-barrel' and any(e['card'] == 'skeleton-barrel' and e['side'] != side and e['hp'] > 0 for e in f['bodies'])))]
        row = dict(card=b['card'], tick=b['tick'], observed=bool(ts), preempt=False, playable=None, unknown_hand=False)
        if ts:
            lo, hi = min(ts), max(ts) + 10
            row['window'] = [lo, hi]
            row['preempt'] = any(lo <= t <= hi for t in log_ticks)
            ok, unk = False, False
            for t in ex_ticks[bisect.bisect_left(ex_ticks, lo):bisect.bisect_right(ex_ticks, hi)]:
                h = hand_at(t)
                if h is None: unk = True
                elif 'the-log' in h and ex[t] >= 2: ok = True; break
            row['playable'] = ok; row['unknown_hand'] = unk and not ok
        rows.append(row)
    if check_summary:
        s = summarize(rec, side)
        got = (sum(r['preempt'] for r in rows), len(rows), sum(r['observed'] for r in rows))
        want = (s['preemptive_log']['n'], s['preemptive_log']['denominator'], s['barrels_with_observed_flight'])
        assert got == want, (rec['tag'], side, got, want)
    return rows

def main():
    files = sorted(glob.glob(str(CORPUS / 'j*/replay_*.json')))
    n_check = int(sys.argv[1]) if len(sys.argv) > 1 else 40  # cross-check against summarize() on the first N sides
    per = []; decks = Counter(); sides_used = 0; checked = 0
    for fp in files:
        rec = json.load(open(fp))
        sides = [int(s) for s, d in rec['final_decks'].items() if deck_set(d) == DECK]
        decks[len(sides)] += 1
        for s in sides:
            rows = measure(rec, s, check_summary=checked < n_check); checked += 1; sides_used += 1
            per.append(dict(tag=rec['tag'], side=s, rows=rows))
    json.dump(per, open(OUT / 'per_barrel.json', 'w'))
    def agg(sel, kinds):
        a = Counter()
        for r in sel:
            for b in r['rows']:
                if b['card'] not in kinds: continue
                a['all'] += 1; a['observed'] += b['observed']; a['preempt'] += b['preempt']
                if b['observed']:
                    a['playable'] += bool(b['playable']); a['cond_preempt'] += bool(b['preempt'] and b['playable'])
                    a['preempt_not_playable'] += bool(b['preempt'] and not b['playable']); a['unknown_hand'] += b['unknown_hand']
        return a
    def stats(a):
        d = lambda n, m: n / m if m else None
        return dict(counts=dict(a), uncond=dict(n=a['preempt'], den=a['all'], rate=d(a['preempt'], a['all'])),
                    uncond_observed_only=dict(n=a['preempt'], den=a['observed'], rate=d(a['preempt'], a['observed'])),
                    cond=dict(n=a['cond_preempt'], den=a['playable'], rate=d(a['cond_preempt'], a['playable'])),
                    log_playable_share=dict(n=a['playable'], den=a['all'], rate=d(a['playable'], a['all'])),
                    log_playable_share_of_observed=dict(n=a['playable'], den=a['observed'], rate=d(a['playable'], a['observed'])))
    groups = {'all': BARRELS, 'goblin': ('goblin-barrel',), 'skeleton': ('skeleton-barrel',)}
    point = {g: stats(agg(per, k)) for g, k in groups.items()}
    rng = random.Random(0); B = 2000
    # replay-cluster bootstrap: resample replays (tags); a mirror replay keeps both sides together
    by_tag = {}
    for r in per: by_tag.setdefault(r['tag'], []).append(r)
    tags = list(by_tag); cnt = {g: {t: agg(by_tag[t], k) for t in tags} for g, k in groups.items()}
    boots = {g: {m: [] for m in ('uncond', 'uncond_observed_only', 'cond', 'log_playable_share')} for g in groups}
    for _ in range(B):
        samp = Counter(rng.choices(tags, k=len(tags)))
        for g in groups:
            a = Counter()
            for t, m in samp.items():
                for k, v in cnt[g][t].items(): a[k] += v * m
            s = stats(a)
            for m in boots[g]: boots[g][m].append(s[m]['rate'])
    for g in groups:
        for m in boots[g]:
            v = sorted(x for x in boots[g][m] if x is not None)
            point[g][m]['ci95'] = [v[int(.025 * len(v))], v[int(.975 * len(v)) - 1]] if v else None
    res = dict(replays=len(files), replays_by_n_icebow_sides=dict(decks), icebow_sides=sides_used, resamples=B,
               summarize_crosscheck_sides=min(n_check, checked), bot_reference=dict(n=64, den=272, rate=64 / 272),
               results=point)
    json.dump(res, open(OUT / 'results.json', 'w'), indent=1)
    print(json.dumps({g: {m: point[g][m] for m in ('uncond', 'cond', 'log_playable_share')} for g in groups}, indent=1))
    print(res['replays_by_n_icebow_sides'], sides_used)
if __name__ == '__main__': main()
