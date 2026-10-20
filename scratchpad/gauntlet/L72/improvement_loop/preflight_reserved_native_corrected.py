"""Outcome-blind native card/form compatibility for immutable reserved groups."""
from collections import Counter,defaultdict
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from native_catalog_overlay import activate
activate()
from research.sandbox_tools.replay_drive import card_for_slug,split_slug,UNVERIFIED
from native_core.card_catalog import validate_deck,CATALOG_PATH

HERE=Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


@lru_cache(None)
def check_deck(deck):
    try:
        parsed=[]
        for token in deck:
            slug,form=split_slug(token)
            if slug in UNVERIFIED:raise ValueError('Unverified native card mapping: '+slug)
            parsed.append(dict(card_id=card_for_slug(slug),form=form,level=11))
        validate_deck(parsed)
        return None
    except (ValueError,KeyError) as error:return str(error)


def main():
    report=HERE/'native_compatibility_corrected.json'
    reservation=json.loads((HERE/'replay_reservation.json').read_text())
    inventory=json.loads((HERE/'unused_hf_inventory.json').read_text())
    source=Path(inventory['candidates']);split_file=Path(reservation['reservation_file'])
    output=source.with_name('native_compatible_groups_corrected.jsonl')
    if report.exists() or output.exists():raise ValueError('Fresh compatibility output required')
    if sha(source)!=reservation['candidate_commands_sha256'] or sha(split_file)!=reservation['reservation_sha256']:
        raise ValueError('Reservation sources changed')
    with split_file.open() as f:splits={r['tag']:r for line in f if (r:=json.loads(line))}
    counts=Counter();errors=Counter();strata=defaultdict(Counter);exact=[]
    with source.open() as f,output.open('x') as out:
        for line in f:
            row=json.loads(line);bound=splits[row['tag']]
            if bound['signature']!=row['signature']:raise ValueError('Command group mismatch')
            problems=sorted({e for deck in row['decks'] if (e:=check_deck(tuple(sorted(deck))))})
            counts['checked']+=1
            if problems:
                counts['incompatible']+=1;errors.update(problems)
            else:
                counts['compatible']+=1;strata[bound['split']].update(row['strata'])
                out.write(json.dumps(dict(row,split=bound['split']))+'\n')
            if 'exact_icebow' in row['strata']:
                assert bound['split']=='confirmation'
                exact.append(dict(tag=row['tag'],compatible=not problems,errors=problems,strata=row['strata']))
    assert counts['checked']==len(splits)
    control=('knight','skeletons','tesla','ice-wizard','the-log','tornado','rocket','x-bow')
    assert check_deck(control) is None
    assert check_deck(('elite-barbarians-ev1',)+control[1:]) is None
    assert check_deck(('void',)+control[1:]) is not None
    result=dict(counts=dict(counts),errors=dict(errors),strata={k:dict(v) for k,v in strata.items()},
        exact_icebow=exact,compatible_file=str(output),compatible_sha256=sha(output),
        catalog_sha256=sha(CATALOG_PATH),replay_driver_sha256=sha(ROOT/'research/sandbox_tools/replay_drive.py'),
        reservation_manifest_sha256=sha(HERE/'replay_reservation.json'),script_sha256=sha(__file__),
        negative_controls=1,positive_controls=2,isolated_catalog_manifest_sha256=sha(HERE/'native_catalog_corrected.json'),confirmation_qualified=False,
        limitations=['Card/form availability only, not command/reconstruction/public-object parity.',
                    'No source forms, replay assignments or model inputs changed.'])
    report.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='exact_icebow'}))
    print('RESERVED_NATIVE_CORRECTED_FORMS_PREFLIGHT_COMPLETE')


if __name__=='__main__':main()
