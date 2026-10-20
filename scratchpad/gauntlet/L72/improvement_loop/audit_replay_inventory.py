"""Read-only local replay/exposure inventory; never score a model or select by outcome."""
from collections import defaultdict
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

import numpy as np

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
TAG=re.compile(r'^(?:[0-9a-f]{32}|[a-z0-9]{12})$')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def tag(value):
    value=str(value).lower().removeprefix('replay_').removesuffix('.json')
    return value if TAG.fullmatch(value) else None


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--suffix',default='');a=ap.parse_args()
    if a.suffix and not re.fullmatch('[a-z0-9_]+',a.suffix):raise ValueError('Plain report suffix required')
    suffix=('_'+a.suffix) if a.suffix else ''
    dest=HERE/('replay_inventory'+suffix+'.json')
    if dest.exists():raise ValueError('Fresh inventory required')
    exposure=defaultdict(set);datasets=[];unknown=[]
    for deck in ('icebow','hogeq'):
        for path in sorted((ROOT/deck/'data/pipeline').glob('*dataset*.npz')):
            with np.load(path,allow_pickle=False) as z:
                if 'tags' not in z.files:
                    unknown.append(str(path.relative_to(ROOT)));continue
                values=[str(v) for v in z['tags'].tolist()]
            valid={tag(v) for v in values}-{None}
            source=str(path.relative_to(ROOT))
            for value in valid:exposure[value].add(source)
            datasets.append(dict(path=source,sha256=sha(path),tag_count=len(valid),
                                 invalid_tag_count=len(values)-sum(tag(v) is not None for v in values)))
    label_path=ROOT/'.foreman/codex_autopilot/runs/public_labels_full_reconstructed/manifest.json'
    label_manifest=json.loads(label_path.read_text())
    for record in label_manifest['sources']:
        value=tag(record['tag'])
        if value:exposure[value].add('public_labels_full_reconstructed')
    # Prior ghost evaluation is exposure even if a replay never trained a model.
    pins=[]
    for base in [ROOT/'icebow/data/ghost_pool',ROOT/'scratchpad/gauntlet/L68/generalist/lat26/screens']:
        for path in sorted(base.glob('*.jsonl')):
            values=set()
            with path.open(encoding='utf-8') as stream:
                for line in stream:
                    if not line.strip():continue
                    row=json.loads(line);value=tag(row.get('tag',''))
                    if value:values.add(value);exposure[value].add(str(path.relative_to(ROOT)))
            pins.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),tag_count=len(values)))
    roots=[p for p in (ROOT/'scratchpad/gauntlet/ext').iterdir()
           if p.is_dir() and (p.name.startswith('corpus_') or p.name in ('batch_v2','fetch_public_v1','public_preflight_remaining'))]
    paths=defaultdict(list);counts={}
    for base in sorted(roots):
        n=0
        for directory,dirs,files in os.walk(base,followlinks=False):
            dirs[:]=[d for d in dirs if not (Path(directory)/d).is_symlink() and not (Path(directory)/d).is_junction()]
            for name in files:
                if not name.startswith('replay_') or not name.endswith('.json'):continue
                value=tag(name)
                if value:
                    paths[value].append(str((Path(directory)/name).relative_to(ROOT)));n+=1
        counts[str(base.relative_to(ROOT))]=n
    candidates={value:files for value,files in sorted(paths.items()) if value not in exposure}
    candidate_records=[]
    for value,files in candidates.items():
        # Inventory only; no labels, model outputs or outcome filtering.
        candidate_records.append(dict(tag=value,paths=files))
    candidate_file=HERE/('local_candidate_replays'+suffix+'.json')
    if candidate_file.exists():raise ValueError('Candidate inventory exists')
    candidate_file.write_text(json.dumps(candidate_records,indent=2))
    excluded_file=HERE/('historical_exposure_tags'+suffix+'.json')
    if excluded_file.exists():raise ValueError('Exposure inventory exists')
    excluded_file.write_text(json.dumps({k:sorted(v) for k,v in sorted(exposure.items())},indent=2))
    report=dict(schema=1,datasets=datasets,dataset_files_without_tags=unknown,
        labels_manifest_sha256=sha(label_path),prior_evaluation_pins=pins,recording_counts=counts,
        recording_files=sum(counts.values()),unique_recorded_tags=len(paths),
        unique_historical_exposure_tags=len(exposure),candidate_unique_tags=len(candidates),
        candidate_file_sha256=sha(candidate_file),exposure_file_sha256=sha(excluded_file),
        script_sha256=sha(__file__),limitations=[
            'All historical train and validation IDs are excluded conservatively.',
            'Candidate IDs are discovery leads, not certified untouched confirmation.',
            'Need parent-model provenance, command-content deduplication, availability and label coverage audit.',
            'No model predictions, label outcomes, or confirmation thresholds inspected or changed.'])
    dest.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('datasets','prior_evaluation_pins')}))
    if unknown or any(d['invalid_tag_count'] for d in datasets):
        raise ValueError('Uncovered dataset tag format; inventory is incomplete')
    print('LOCAL_REPLAY_INVENTORY_COMPLETE')


if __name__=='__main__':main()
