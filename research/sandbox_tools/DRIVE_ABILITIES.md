# Driving recorded ability presses

These are operator commands for a later run. **None were run during implementation.**
The worker commands start Android/emulator services and use adb; run them only when
that is allowed alongside the live MuMu bot. No GPU is needed. Commands below use
PowerShell from `C:\Users\benpe\ClashBot` unless stated otherwise.

`--drive-abilities` is opt-in on both drivers. Without it, the old log is unchanged.
With it, presses have `kind="ability"`, `ability=true`, an attributed base `card`
(null if ambiguous), `entity_id`, native `accepted`/`result_code`, `delay_ticks`, and
an explanatory `skipped` when undrivable. No-command skips have null result/ID.
An elixir retry that loses its entity retains the last attempted ID/native result.
`tick` is the pro's tick; `engine_tick` is the actual attempt tick. As with card
plays, earlier elixir delays can make later commands late. Only code 1050 is
retried, bounded by `--elixir-slack`; 1014 is recorded without retry.

Attribution follows phase 1 (`mine_abilities.py`'s champion/hero candidate rule and
single/unique-plausible resolution), substituting **current live units** for its
statistical age windows. Legacy crawl CSVs omit candidate lists: candidates are
reconstructed from that side's deck. Optional `ability_source_candidates` lists
(or JSON CSV cells) are honored, including an explicitly empty list. With multiple
candidates, exactly one must have a live unit on that side; otherwise skip. The
newest eligible entity of that card wins (`creation_ordinal`, else the documented
generation-key ordinal). Every retry observes again and retains the attributed card.
Ability events go in `log`, not `play_frames`; grade command totals include attempted
abilities. Filter `ability` when calculating card-only acceptance rates.

## Offline tests

```powershell
icebow/.venv/Scripts/python.exe -B -m unittest discover -s research/sandbox_tools/tests -v
```

Tests use a mock environment, frozen real crawl events with a pre-change expected
log, and saved observation fixtures. They never connect to an engine.

## Start and ping one slot

Exact local recipe from `icebow/Instructions.txt`, Stage 5:

```powershell
Set-Location C:\Users\benpe\ClashBot\research\ext\cr-native-sandbox
. .\runtime.env.ps1
.\.venv\Scripts\python.exe -m native_core.worker start --workers 1 --base-port 37031 --transport adb --avd-name royale_worker_api31
.\.venv\Scripts\python.exe -m native_core.client --port 37031 ping
```

For two slots, use `--workers 2` **instead of** the one-slot start, with the same
base port/transport/AVD arguments, then ping both 37031 and 37032. Do not start a
second overlapping pool. Keep this window open.

## Paired validation on exactly 50 replays

In a repo-root PowerShell window, use identical tags/settings and separate fresh
outputs. The HF crawl has complete positioned events and includes ability presses.
Choose a new `$Trial` for another experiment; never mix enabled/disabled outputs.

```powershell
$Py = '.\research\ext\cr-native-sandbox\.venv\Scripts\python.exe'
$Crawl = 'scratchpad\gauntlet\ext\crawl_hf_icebow'
$Trial = 'scratchpad\gauntlet\ext\ability_validation_50'
if (Test-Path $Trial) { throw 'Choose a fresh Trial directory' }
& $Py -B research/sandbox_tools/replay_batch.py --crawl $Crawl --tags "$Crawl\tags.json" --limit 50 --out "${Trial}\off" --port 37031 --seed 424242 --level 11 --elixir-slack 40 --tail-cap 7200 --record-every 20 --record-plays --determinism-every 0
& $Py -B research/sandbox_tools/replay_batch.py --crawl $Crawl --tags "$Crawl\tags.json" --limit 50 --out "${Trial}\on_abil" --port 37031 --seed 424242 --level 11 --elixir-slack 40 --tail-cap 7200 --record-every 20 --record-plays --determinism-every 0 --drive-abilities
@'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
def read(mode):
    return {p.stem: json.loads(p.read_text()) for p in (root/mode).glob('replay_*.json')}
a, b = read('off'), read('on_abil')
assert len(a) == len(b) == 50 and a.keys() == b.keys(), 'Require 50 paired successes; inspect summary.jsonl failures'
for tag in a:
    assert a[tag]['expected'] == b[tag]['expected'], tag
scores = {}
for label, records in [('off', a), ('on_abil', b)]:
    crowns = winner = accepted = skipped = 0
    for r in records.values():
        exp = [int(r['expected']['crowns_by_side'][str(s)]) for s in (0, 1)]
        want = None if exp[0] == exp[1] else int(exp[1] > exp[0])
        f = r['final']
        crowns += f['crowns'] == exp
        winner += bool(f['terminated']) and f['winner'] == want
        accepted += sum(bool(e.get('ability') and e.get('accepted')) for e in r['log'])
        skipped += sum('ability' in str(e.get('skipped', '')) for e in r['log'])
    scores[label] = (crowns / 50, winner / 50)
    print(label, 'crowns/winner match:', scores[label], 'accepted presses:', accepted, 'skipped presses:', skipped)
print('on minus off (percentage points):', [100*(y-x) for x,y in zip(scores['off'], scores['on_abil'])])
'@ | & $Py -B - $Trial
```

Require complete paired results; inspect skips, 1014/1050 rejections and delays
before scaling. A measured improvement is **not yet established** by mock tests.
The comparator uses `expected.crowns_by_side` to derive the expected winner
(side 1 is the crawl team); nonterminal runs do not count as winner matches.

## Re-drive the six configured corpora into new outputs

Current inputs in `icebow/data/pipeline/gen_dataset_v2.json["corpora"]`:

| Input | New output | Crawl source |
|---|---|---|
| `scratchpad/gauntlet/ext/corpus_v6/icebow` | same path + `_abil` | icebow crawl2 + crawl_hf_icebow |
| `scratchpad/gauntlet/ext/corpus_v6/hogeq` | same path + `_abil` | hogeq crawl2 + crawl_hf_hogeq |
| `scratchpad/gauntlet/ext/corpus_gen_pilot/s0` | same path + `_abil` | generalist pilot crawl chunks |
| `scratchpad/gauntlet/ext/corpus_gen_pilot/s1` | same path + `_abil` | generalist pilot crawl chunks |
| `scratchpad/gauntlet/ext/corpus_gen_pilot/s2` | same path + `_abil` | generalist pilot crawl chunks |
| `scratchpad/gauntlet/ext/corpus_gen_pilot/s3` | same path + `_abil` | generalist pilot crawl chunks |

First prepare small tag manifests from the **existing recorded corpus membership**.
This avoids adding unrecorded tags or losing the corrected `attr_i` seat rotation.
The script prefers fully positioned `plays_ext_i1.csv`, then `plays_ext.csv`.
It fails if any source event set is missing/incomplete. It does not invoke an engine.

```powershell
$Py = '.\research\ext\cr-native-sandbox\.venv\Scripts\python.exe'
@'
import csv, json
from collections import defaultdict
from pathlib import Path
manifest = Path('scratchpad/gauntlet/ext/ability_redrive_manifests')
assert not manifest.exists(), 'Use fresh manifests or inspect the existing jobs before resuming'
corpora = json.loads(Path('icebow/data/pipeline/gen_dataset_v2.json').read_text())['corpora']
jobs, tag_files = [], {}
for slot_group, original in enumerate(corpora):
    corpus = Path(original)
    output = Path(str(corpus) + '_abil')
    assert not output.exists(), f'Output must be NEW: {output}'
    remaining = {p.stem[7:] for p in corpus.glob('replay_*.json')}
    assert remaining, corpus
    if corpus.parent.name == 'corpus_v6':
        deck = corpus.name
        sources = [(Path(deck)/'data/royaleapi/crawl2', n) for n in ('plays_ext_i1.csv', 'plays_ext.csv')]
        sources += [(Path(f'scratchpad/gauntlet/ext/crawl_hf_{deck}'), 'plays_ext.csv')]
    else:
        sources = [(p, 'plays_ext.csv') for p in sorted(Path('scratchpad/gauntlet/L68/generalist/pilot/crawl').glob('chunk_*'))]
    for crawl, plays_file in sources:
        with (crawl/'battles.csv').open(encoding='utf-8', newline='') as f:
            counts = {r['replay_tag']: int(r['plays']) for r in csv.DictReader(f)}
        events = defaultdict(list)
        with (crawl/plays_file).open(encoding='utf-8', newline='') as f:
            for r in csv.DictReader(f):
                if r['replay_tag'] in remaining:
                    events[r['replay_tag']].append(r)
        selected = sorted(t for t, rows in events.items() if len(rows) == counts.get(t)
            and all(r['attr_ability'] == '1' or all(r[k] not in ('', 'None') for k in ('x_units', 'y_units')) for r in rows))
        if selected:
            tags = manifest/f'tags_{len(jobs):03d}.json'
            tag_files[tags] = selected
            jobs.append(dict(group=slot_group, crawl=str(crawl), plays_file=plays_file, tags=str(tags), out=str(output)))
            remaining.difference_update(selected)
    assert not remaining, (corpus, 'missing source tags', sorted(remaining)[:10])
manifest.mkdir(parents=True)
for path, tags in tag_files.items():
    path.write_text(json.dumps(tags), encoding='utf-8')
(manifest/'jobs.json').write_text(json.dumps(jobs, indent=2), encoding='utf-8')
print('Prepared', len(jobs), 'jobs for', len(corpora), 'corpora;', sum(map(len, tag_files.values())), 'recordings')
'@ | & $Py -B -
```

Run this loop with `$Slots=1; $Slot=0` for one slot. For two slots, run it in
**two repo-root windows**, both with `$Slots=2`, one with `$Slot=0` and the other
with `$Slot=1`. A whole output corpus belongs to one window, so summaries cannot race.
The batch runner resumes its own completed tags; do not use `--redo` or change flags
mid-resume. Check failures in every `summary.jsonl` (batch exit 0 alone is insufficient).

```powershell
$Slots = 1
$Slot = 0
$Port = 37031 + $Slot
$Py = '.\research\ext\cr-native-sandbox\.venv\Scripts\python.exe'
$Jobs = Get-Content scratchpad/gauntlet/ext/ability_redrive_manifests/jobs.json -Raw | ConvertFrom-Json
foreach ($Job in $Jobs) {
    if (($Job.group % $Slots) -ne $Slot) { continue }
    & $Py -B research/sandbox_tools/replay_batch.py --crawl $Job.crawl --plays-file $Job.plays_file --tags $Job.tags --out $Job.out --port $Port --seed 424242 --level 11 --elixir-slack 40 --tail-cap 7200 --drive-abilities --record-every 20 --record-plays --determinism-every 0
    if ($LASTEXITCODE -ne 0) { throw "Batch failed: $($Job.tags)" }
}
```

Each batch invocation's `aggregate.json` covers that invocation's tag list only;
use all `replay_*.json`/`summary.jsonl` entries for a whole-corpus assessment. Verify
old/new filename sets match and every new record has `drive_abilities=true` before
using the new corpus. Existing dataset metadata is not modified by this recipe.

## Downstream compatibility

`pipeline/dataset.py` excludes `ability` before building accepted plays, waits,
and history. `dataset_gen.py:99` already excludes it from public play history and
uses the guarded S1 builder for row creation. Legacy rows retain their semantics.

**Known scope issue:** `e1_pool.py:266-282` imports old ability skips by matching
the `skipped` string; it does not recognize accepted ability log entries. Those
would reach its card/coordinate parser. Its later filters (`:316`, `:536`) and
`royale_env.py:188,198` do exclude commands already marked `ability`, but cannot
repair that importer gap. Do not feed `_abil` recordings to that importer until
it gets a minimal explicit-ability guard. That file was outside the requested write set.

## Lead addendum (2026-10-03): record exact forms and projectiles in the gen_v3.1 re-drive

Add `--record-full --record-native` to every full re-drive command above (with `--drive-abilities`):
- `--record-full`: every recorded frame carries entity `kind`, `projectiles` (side, x, y, target_x, target_y, card)
  and spell `effects` -- spells and barrels in flight, with their landing target.
- `--record-native`: every entity row ends with `[native card_id, entity_id]`. The native card_id IS the
  evolution / hero FORM id for evolved / hero bodies (catalog `evolution_form_id` / `hero_form_id`), so gen_v3.1's
  per-unit form labels can be read directly instead of reconstructed from the evolution cycle (the reconstruction
  under-tags ambiguous bodies and its cycle table disagrees with the live catalog for 23/41 cards). Verify on the
  50-replay validation that form ids actually appear before the full run.
