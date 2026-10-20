"""Schema-only audit of a bounded, pinned public archive sample. No predictions."""
from collections import Counter
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, parse_qs

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Nodes(HTMLParser):
    def __init__(self):
        super().__init__();self.nodes=[]
    def handle_starttag(self,tag,attrs):
        self.nodes.append((tag,dict(attrs)))


def main():
    discovery=read(HERE/'additional_source_discovery.json')
    assert sha(ROOT/discovery['api_path'])==discovery['api_sha256']
    api=read(ROOT/discovery['api_path'])
    assert api['sha']==discovery['revision'] and not api['private'] and not api['gated']
    metadata=read(HERE/'additional_source_metadata.json')
    for name,row in metadata['metadata'].items():
        assert sha(ROOT/row['path'])==row['sha256']
        assert (ROOT/row['path']).stat().st_size==row['bytes']
    matches=[json.loads(s) for s in (ROOT/metadata['metadata']['matches.jsonl']['path']).read_text(encoding='utf-8').splitlines()]
    events=[json.loads(s) for s in (ROOT/metadata['metadata']['events.jsonl']['path']).read_text(encoding='utf-8').splitlines()]
    cards=[c for m in matches for d in m['decks'].values() for c in d]
    icebow={'tornado','tesla','ice-wizard','x-bow','rocket','knight','the-log','skeletons'}
    exact=[m['battle_id'] for m in matches if any(set(d)==icebow for d in m['decks'].values())]
    sample=read(HERE/'additional_raw_schema_download.json')
    raw_paths=[r['rfilename'] for r in api['siblings'] if r['rfilename'].startswith('raw/') and r['rfilename'].endswith('.json')]
    expected=sorted(raw_paths,key=lambda p:hashlib.sha256((sample['selection_salt']+p).encode()).hexdigest())[:6]
    assert sample['revision']==api['sha'] and [f['remote_path'] for f in sample['files']]==expected
    rows=[]
    for source in sample['files']:
        p=ROOT/source['path']; assert sha(p)==source['sha256']
        r=read(p);html=r['payload']['html'];parsed=Nodes();parsed.feed(html)
        markers=[a for tag,a in parsed.nodes if 'data-x' in a]
        timeline=[a for tag,a in parsed.nodes if 'data-card' in a and 'data-t' in a]
        form_tokens=re.findall(r'[a-z-]+(?:-ev\d+|-hero)(?=[.\"\s/?<])',html)
        query=parse_qs(urlsplit(r['request_url']).query)
        rows.append(dict(tag=p.stem,sha256=source['sha256'],success=r['payload']['success'],
                         markers=len(markers),timeline_events=len(timeline),explicit_form_tokens=sorted(set(form_tokens)),
                         positioned_markers=sum(a.get('data-x','').lstrip('-').isdigit() and a.get('data-y','').lstrip('-').isdigit() for a in markers),
                         orientation_markers=sum('data-i' in a for a in markers),
                         query_keys=sorted(query),html_data_attributes=sorted({k for _,a in parsed.nodes for k in a if k.startswith('data-')}),
                         original_deck_forms_certified=False))
    report=dict(revision=api['sha'],cleaned_matches=len(matches),cleaned_events=len(events),
                cleaned_event_types=dict(Counter(e['event_type'] for e in events)),
                cleaned_form_markers=sum(bool(re.search(r'-(ev\d+|hero)$',c)) for c in cards),
                cleaned_exact_icebow_ids=exact,cleaned_exact_raw_path_matches=[t for t in exact if any(Path(p).stem==t for p in raw_paths)],
                raw_schema_sample=rows,model_predictions=0,source_qualified_for_native_reconstruction=False,
                script_sha256=sha(__file__),inputs={name:sha(HERE/name) for name in ('additional_source_discovery.json','additional_source_metadata.json','additional_raw_schema_download.json')},
                limitations=['Sampled raw action HTML and query fields do not certify complete original deck forms.',
                             'Cleaned legacy metadata has no original form suffixes; no form substitution is allowed.',
                             'Filename freshness has not established command-signature separation.',
                             'No conclusion about every unsampled raw file; no bulk acquisition authorized by this audit.'])
    output=HERE/'additional_source_schema.json';assert not output.exists()
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('cleaned_matches','cleaned_events','cleaned_form_markers','cleaned_exact_icebow_ids','source_qualified_for_native_reconstruction')}))
    print('ADDITIONAL_SOURCE_SCHEMA_AUDIT_COMPLETE')


if __name__=='__main__': main()
