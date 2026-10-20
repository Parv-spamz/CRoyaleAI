"""Independent cost arithmetic and stable native-identity repeat comparison."""
import copy,csv,hashlib,io,json,lzma,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
LOOP=HERE.parent
sys.path.insert(0,str(LOOP))
from native_capture_identity import canonical_frames

def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def normalize(frames):
    result=copy.deepcopy(frames)
    for frame in result:
        bodies=frame['entities'];mapping={r['id']:r['entity_id'] for r in bodies}
        assert len(mapping)==len(bodies)==len({r['entity_id'] for r in bodies})
        for r in bodies:
            target=r['target'];assert target in mapping or target in ('0x0',None,0)
            r['id']='entity:'+str(r['entity_id'])
            r['target']='entity:'+str(mapping[target]) if target in mapping else None
    return canonical_frames(result)

def check(report):
    expected={'void':(28000023,5),'arrows_control':(28000001,3),'void_repeat':(28000023,5)}
    assert set(report['arms'])==set(expected)
    for name,(card,cost) in expected.items():
        a=report['arms'][name];p=a['target_play'];b=p['before'];z=p['after']
        assert a['target']==p['card_id']==p['result']['resolved_data_id']==card
        assert p['result']['accepted'] and p['result']['result_code']==0
        assert b['tick']==z['tick']==p['result']['tick']
        one=next(x for x in b['players'] if x['side']==0);two=next(x for x in z['players'] if x['side']==0)
        for key in ('elixir','elixir_exact'):
            if key in one:assert abs(one[key]-two[key]-cost)<1e-6
        assert p['measured_cost']==cost
        assert any(h['card_id']==card and h['deck_index']==p['deck_index'] for h in one['hand'])
        assert all(x['result']['accepted'] for x in a['plays']) and len(a['plays'])<=9
        assert a['frames'][-1]['tick']<1000
    a=report['arms']['void'];b=report['arms']['void_repeat']
    assert a['replay']==b['replay']
    assert normalize(a['frames'])==normalize(b['frames'])
    for pa,pb in zip(a['plays'],b['plays']):
        assert (pa['card_id'],pa['deck_index'],pa['x'],pa['y'],pa['measured_cost'])==(pb['card_id'],pb['deck_index'],pb['x'],pb['y'],pb['measured_cost'])
        assert normalize([pa['before'],pa['after']])==normalize([pb['before'],pb['after']])
    assert len(a['plays'])==len(b['plays'])
    assert any(f['public_objects']['area_effects'] for f in a['frames'])

def main():
    output=HERE/'verified.json';assert not output.exists()
    audit=read(HERE/'audit.json');report=read(HERE/'probe.json')
    assert audit['complete'] and report['error']=='AssertionError()' and report['complete'] is False
    for p,h in report['sources'].items():assert sha(ROOT/p)==h,p
    identity=audit['identity']
    assert identity==dict(slug='void',internal_name='DarkMagic',text_key='TID_SPELL_DARK_MAGIC',english='Void',card_id=28000023,catalog_elixir=5)
    # Independent localization/card-table join, without importing the producer.
    assets=ROOT/'research/ext/cr-native-sandbox/runtime/extracted-assets'
    def table(relative):
        b=(assets/relative).read_bytes();s=lzma.decompress(b[:9]+b'\0'*4+b[9:],format=lzma.FORMAT_ALONE).decode()
        return list(csv.DictReader(io.StringIO(s)))
    spell=next(x for x in table('csv_logic/spells_other.csv') if x['Name']=='DarkMagic')
    text=next(x for x in table('csv_client/texts.csv') if x['Name']==spell['TID'])
    assert text['EN']=='Void' and int(spell['ManaCost'])==5
    check(report);negatives=[]
    def reject(name,mutate):
        bad=copy.deepcopy(report);mutate(bad)
        try:check(bad)
        except (AssertionError,KeyError):negatives.append(name)
        else:raise AssertionError('Corruption accepted: '+name)
    reject('wrong_resolved_card',lambda r:r['arms']['void']['target_play']['result'].update(resolved_data_id=28000001))
    reject('wrong_cost',lambda r:r['arms']['void']['target_play'].update(measured_cost=3))
    reject('failed_control',lambda r:r['arms']['arrows_control']['target_play']['result'].update(accepted=False))
    reject('changed_geometry',lambda r:r['arms']['void_repeat']['frames'][1]['entities'][0].update(x=0))
    reject('changed_health',lambda r:r['arms']['void_repeat']['frames'][1]['entities'][0].update(hp=1))
    reject('unknown_target',lambda r:r['arms']['void_repeat']['frames'][1]['entities'][0].update(target='unknown'))
    reject('changed_area_timer',lambda r:r['arms']['void_repeat']['frames'][1]['public_objects']['area_effects'][0].update(source_remaining_ms=99999))
    remote=report['guest_hashes']
    r=subprocess.run(['C:/Android/Sdk/platform-tools/adb.exe','-s','emulator-5560','shell','sha256sum',*remote],text=True,capture_output=True,check=True)
    assert {x.split()[1]:x.split()[0] for x in r.stdout.splitlines()}==remote
    proof=dict(complete=True,audit_sha256=sha(HERE/'audit.json'),probe_sha256=sha(HERE/'probe.json'),
        script_sha256=sha(__file__),correction_sha256=sha(HERE/'ORACLE_CORRECTION.md'),native_costs=[5,3,5],
        resolved_ids=[28000023,28000001,28000023],repeat_equal=True,positive_checks=1,negative_checks=negatives,
        producer_final_comparison_failed=True,producer_failure_preserved=True,final_guest_attestation=True,
        model_predictions=0,production_changed=False,full_mechanics_parity=False)
    output.write_text(json.dumps(proof,indent=2));print(json.dumps(proof));print('VOID_NATIVE_COST_INDEPENDENT_PASS')

if __name__=='__main__':main()
