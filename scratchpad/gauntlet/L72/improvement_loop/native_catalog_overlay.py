"""Load only the attested isolated package, without changing validators or originals."""
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def activate():
    if any(k=='native_core' or k.startswith('native_core.') for k in sys.modules):
        raise RuntimeError('Native package was imported before explicit isolated activation')
    manifest=HERE/'native_catalog_corrected.json'
    data=json.loads(manifest.read_text(encoding='utf-8'))
    assert data['complete'] and data['native_python_unchanged']
    for group in ('original_hashes','corrected_hashes','sources'):
        for path,digest in data[group].items():assert sha(ROOT/path)==digest,path
    package_root=Path(data['package_root']).resolve()
    assert package_root==ROOT/'icebow/data/bench/native_confirmation_20261005/catalog_corrected'
    sys.path.insert(0,str(package_root))
    module=importlib.import_module('native_core.card_catalog')
    assert Path(module.__file__).resolve()==package_root/'native_core/card_catalog.py'
    return module,data


if __name__=='__main__':
    m,data=activate()
    assert m.observed_card(13000043)==dict(base_card_id=26000043,card_form='evolution',form_name='AngryBarbarians_EV1')
    assert m.observed_card(26000043)['card_form']=='base'
    assert m.observed_card(13000000)['card_form']=='evolution'
    deck=[dict(card_id=x) for x in [26000043,26000000,26000010,26000030,26000031,26000084,26000049,26000019]]
    deck[0]['form']='evolution'
    assert m.replay_spells(deck)[0]==dict(d=26000043,l=10,el=1)
    rejected=0
    for form in ['hero','both','invalid']:
        deck[0]['form']=form
        try:m.validate_deck(deck)
        except ValueError:rejected+=1
        else:raise AssertionError('Unsupported form accepted')
    assert rejected==3
    print('NATIVE_CATALOG_ISOLATED_CONTROLS_PASS: base/known/evolved identity, preserved el flag, three rejected forms')
