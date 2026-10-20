"""Isolated source-reconstruction loader; original production module untouched."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
LOOP=HERE.parent
sys.path[:0]=[str(LOOP),str(LOOP/'deal_recovery'),str(ROOT)]

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def load():
    from native_catalog_overlay import activate
    _,catalog_proof=activate()
    proof=json.loads((HERE/'verified.json').read_bytes())
    assert proof['complete'] and proof['native_costs']==[5,3,5] and proof['repeat_equal']
    assert proof['probe_sha256']==sha(HERE/'probe.json') and proof['audit_sha256']==sha(HERE/'audit.json')
    assert proof['script_sha256']==sha(HERE/'verify.py') and proof['correction_sha256']==sha(HERE/'ORACLE_CORRECTION.md')
    probe=json.loads((HERE/'probe.json').read_bytes())
    for p,h in probe['sources'].items():assert sha(ROOT/p)==h,p
    receipt=ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-void-native-independent.json'
    r=json.loads(receipt.read_bytes());assert r['exit_code']==0 and r['matched']
    assert hashlib.sha256(receipt.with_suffix('.out').read_text().encode()).hexdigest()==r['output_sha256']
    from driver_patch_v3 import load as opening_loader
    module=opening_loader()
    assert module.UNVERIFIED=={'void'} and module.SLUG_ALIASES['void']=='DarkMagic'
    assert module.card_for_slug('void')==28000023 and module.card_cost(28000023)==5
    module.UNVERIFIED=module.UNVERIFIED-{'void'}
    module.patch_provenance.update(verified_slug='void',identity_proof_sha256=sha(HERE/'verified.json'),
        unverified_before=['void'],unverified_after=[],original_module_unchanged=True)
    return module,catalog_proof

def controls(module):
    from research.sandbox_tools import replay_drive as original
    from native_core.card_catalog import validate_deck
    assert original.UNVERIFIED=={'void'} and module.UNVERIFIED==set()
    deck=[28000023,26000000,26000010,26000030,26000031,26000084,26000049,26000019]
    assert validate_deck(deck)[0]['card_id']==28000023
    negatives=[]
    for form in ('evolution','hero','invalid'):
        bad=[dict(card_id=c) for c in deck];bad[0]['form']=form
        try:validate_deck(bad)
        except ValueError:negatives.append(form)
        else:raise AssertionError('Unsupported Void form accepted')
    return dict(positive_checks=2,rejected_forms=negatives,original_unverified_unchanged=True)
