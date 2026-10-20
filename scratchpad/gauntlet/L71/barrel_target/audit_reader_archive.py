"""Inventory saved reader flights; no new live play or access to private players."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from pipeline.projectile_observation import objects, tokens_from_objects
from pipeline.rocket_teaching import sha


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args()
    folder=a.root/'scratchpad/gauntlet/L70/reader'
    paths=sorted(folder.glob('decoded_*.jsonl'))+sorted((folder/'sidebyside').glob('re_v2*.jsonl'))
    sources=[];examples=[];counts=Counter()
    for path in paths:
        n=Counter()
        for line in path.open():
            if not line.strip():continue
            f=json.loads(line);n['frames']+=1
            if not f.get('coherent'):continue
            n['coherent_frames']+=1
            observed=objects(f,source='reader')
            n['projectiles']+=len(observed['projectiles'])
            for q in observed['projectiles']:
                if q[0]!='goblin-barrel':continue
                n['barrel_observations']+=1
                normalized={str(s):tokens_from_objects(dict(projectiles=[q],effects=[]),s,{'goblin-barrel':1})['projectiles'][0].tolist() for s in (0,1)}
                if len(examples)<12:
                    examples.append(dict(file=str(path.relative_to(a.root)),tick=f['game_tick'],public_shot=q,normalized=normalized))
        counts.update(n)
        sources.append(dict(path=str(path.relative_to(a.root)),sha256=sha(path),counts=dict(n)))
    out=dict(counts=dict(counts),sources=sources,examples=examples,
        limitations=['Reader archive coverage is an inventory, not verified in-game landing evidence.',
                    'No opponent player fields are read. Zero Barrel observations means unavailable evidence.'])
    (Path(__file__).parent/'reader_archive.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out['counts']));print('BARREL_READER_ARCHIVE_AUDITED')


if __name__=='__main__':main()
