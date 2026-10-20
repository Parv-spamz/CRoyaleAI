"""Build an isolated, evidence-bound catalog correction; leave originals intact."""
import csv
import hashlib
import io
import json
import lzma
from pathlib import Path
import shutil
import tomllib

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
NATIVE=ROOT/'research/ext/cr-native-sandbox'
OUT=ROOT/'icebow/data/bench/native_confirmation_20261005/catalog_corrected'


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def asset(path):
    b=path.read_bytes()
    return lzma.decompress(b[:9]+b'\0'*4+b[9:],format=lzma.FORMAT_ALONE).decode('utf-8')


def main():
    assert not OUT.exists(),'Fresh isolated output required'
    probe=HERE/'native_elite_form_probe_v3.json'
    p=json.loads(probe.read_text(encoding='utf-8'))
    assert p['complete'] and p['model_calls']==0
    # The registered probe plan was bound before execution and remains fixed.
    for name,h in p['source_hashes'].items():assert sha(ROOT/name)==h,name
    arms=p['arms']
    assert arms['elite_base']['resolved_sequence']==[26000043]*3
    assert arms['elite_evolution']['resolved_sequence']==[26000043,13000043,26000043]
    assert arms['knight_evolution_control']['resolved_sequence']==[26000000,26000000,13000000]
    evolved=[e for e in arms['elite_evolution']['target_plays'][1]['entities_after']
             if e.get('native_card_id')==13000043]
    assert len(evolved)==2 and all(e['hp']==e['max_hp']==1341 for e in evolved)
    assets=NATIVE/'runtime/extracted-assets/csv_logic'
    overlay=assets/'characters/angry_barbarian_evo.toml'
    base_asset=assets/'spells_characters.csv'
    form='AngryBarbarians_EV1'
    assert tomllib.loads(asset(overlay))['SPELL_EVOLVED'][form]['SummonCharactersList']==[
        'AngryBarbarian_EV1','AngryBarbarian_EV1_2']
    row=next(r for r in csv.DictReader(io.StringIO(asset(base_asset))) if r['Name']=='AngryBarbarians')
    assert row['EvolvedSpells']==form
    source=NATIVE/'native_core'
    catalog_path=source/'data/live_card_catalog.json'
    original=json.loads(catalog_path.read_text(encoding='utf-8'))
    corrected=json.loads(json.dumps(original))
    target=next(r for r in corrected['cards'] if r['card_id']==26000043)
    changes={'evolution_form':form,'evolution_form_id':13000043,'evolution_cycles':2}
    assert all(target[k] is None for k in changes)
    target.update(changes)
    corrected['counts']['evolutions']+=1
    restored=json.loads(json.dumps(corrected))
    reverted=next(r for r in restored['cards'] if r['card_id']==26000043)
    reverted.update({k:None for k in changes});restored['counts']['evolutions']-=1
    assert restored==original,'Unexpected catalog changes'
    package=OUT/'native_core';(package/'data').mkdir(parents=True)
    original_hashes={}
    corrected_hashes={}
    for path in sorted(source.glob('*.py')):
        shutil.copyfile(path,package/path.name)
        original_hashes[str(path.relative_to(ROOT))]=sha(path)
        corrected_hashes[str((package/path.name).relative_to(ROOT))]=sha(package/path.name)
        assert sha(path)==sha(package/path.name)
    dest=package/'data/live_card_catalog.json'
    dest.write_text(json.dumps(corrected,indent=2)+'\n',encoding='utf-8')
    original_hashes[str(catalog_path.relative_to(ROOT))]=sha(catalog_path)
    corrected_hashes[str(dest.relative_to(ROOT))]=sha(dest)
    report=dict(complete=True,package_root=str(OUT),native_python_unchanged=True,
        original_hashes=original_hashes,corrected_hashes=corrected_hashes,
        changes={'card_id':26000043,**changes,'evolution_count':[41,42]},
        sources={str(x.relative_to(ROOT)):sha(x) for x in [Path(__file__),probe,overlay,base_asset,
            HERE/'NATIVE_CATALOG_CORRECTION_PLAN.md']},
        model_predictions=0,production_catalog_changed=False,confirmation_qualified=False)
    (HERE/'native_catalog_corrected.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('NATIVE_CATALOG_ISOLATED_PREPARED')


if __name__=='__main__':main()
