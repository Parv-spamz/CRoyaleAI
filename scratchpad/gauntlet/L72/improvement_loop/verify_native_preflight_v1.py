"""Independent recount and pairwise lifetime-bijection audit of completed captures."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
DATA=ROOT/'icebow/data/bench/native_confirmation_20261005/preflight_v2'


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def compare_frames(left,right):
    assert len(left)==len(right)
    previous={kind:{} for kind in ('projectiles','area_effects')}
    for a,b in zip(left,right):
        assert {k:v for k,v in a.items() if k!='public_objects'}=={
            k:v for k,v in b.items() if k!='public_objects'}
        ap,bp=a['public_objects'],b['public_objects']
        assert {k:v for k,v in ap.items() if k not in previous}=={
            k:v for k,v in bp.items() if k not in previous}
        for kind,old in previous.items():
            backward={v:k for k,v in old.items()};current={};reverse={}
            assert len(ap[kind])==len(bp[kind])
            for x,y in zip(ap[kind],bp[kind]):
                assert {k:v for k,v in x.items() if k!='id'}=={
                    k:v for k,v in y.items() if k!='id'}
                xid=(x['id'],x.get('generation_key'),x.get('category'),x['card_id'])
                yid=(y['id'],y.get('generation_key'),y.get('category'),y['card_id'])
                assert xid not in current and yid not in reverse
                if xid in old:assert old[xid]==yid
                if yid in backward:assert backward[yid]==xid
                current[xid]=yid;reverse[yid]=xid
            previous[kind]=current


def main():
    process=ROOT/'scratchpad/gauntlet/L71/integration/checks/l72-native-capture-v2.json'
    receipt=json.loads(process.read_text())
    assert receipt['exit_code']==0 and receipt['matched'] is True
    assert hashlib.sha256(process.with_suffix('.out').read_text().encode()).hexdigest()==receipt['output_sha256']
    verified=json.loads((HERE/'native_capture_v2_verified.json').read_text())
    assert verified['complete'] and verified['negative_control_passed']
    for name in ('inputs','remote_hashes','fields','progress'):
        assert sha(HERE/f'native_capture_v2_{name}.json')==verified[name+'_sha256']
    frozen=json.loads((HERE/'native_capture_v2_inputs.json').read_text())
    for name,digest in frozen.items():assert sha(ROOT/name)==digest,name
    progress=json.loads((HERE/'native_capture_v2_progress.json').read_text())
    fields=json.loads((HERE/'native_capture_v2_fields.json').read_text())
    expected=json.loads((ROOT/'.foreman/codex_autopilot/native_redrive_2300/sample_jobs.json').read_text())
    assert len(progress)==20 and {r['tag'] for r in progress}=={r['tag'] for r in expected}
    count=Counter();grades=Counter();repeats=[];recordings={}
    for index,row in enumerate(progress):
        assert row['index']==index and row['ok'] is True
        file=DATA/f"replay_{row['tag']}.json"
        assert sha(file)==row['recording_sha256']
        rec=json.loads(file.read_text())
        old=json.loads((ROOT/'scratchpad/gauntlet/ext/public_preflight_remaining'/file.name).read_text())
        assert rec['log']==old['log'] and rec['grade']==old['grade']
        assert rec['final']['state_hash']==old['final']['state_hash']
        assert rec['record_every']==1 and rec['record_native'] and rec['drive_abilities']
        grades.update(source_commands=rec['grade']['plays_total'],driven_commands=rec['grade']['plays_driven'],
                      accepted_commands=rec['grade']['accepted'],skipped_commands=len(rec['grade']['skipped']))
        count['accepted_ability_events']+=sum(bool(e.get('ability') and e.get('accepted')) for e in rec['log'])
        for frame in rec['frames']:
            count['frames']+=1
            pub=frame['public_objects']
            assert isinstance(pub['projectiles'],list) and isinstance(pub['area_effects'],list)
            count['projectiles_rows']+=len(pub['projectiles'])
            count['area_effects_rows']+=len(pub['area_effects'])
            count['past_motion_tti_known']+=sum(p['past_motion_tti_ms'] is not None for p in pub['projectiles'])
        if index in (0,5,10,15):
            repeat=DATA/'repeats'/file.name
            assert sha(repeat)==row['repeat_sha256']
            other=json.loads(repeat.read_text())
            assert all(rec[k]==other[k] for k in ('final','log','grade'))
            compare_frames(rec['frames'],other['frames'])
            repeats.append(row['tag'])
        recordings[row['tag']]=sha(file)
    assert len(repeats)==4
    assert fields['status']=='PASS' and fields['errors']=={}
    for name,value in count.items():assert fields['coverage'][name]==value,(name,value)
    # Independent identity oracle must reject a mid-flight identity split.
    import copy
    fixture={'tick':1,'public_objects':{'projectiles':[dict(id='a',generation_key=1,card_id=2,x=3)],'area_effects':[]}}
    a=[fixture,dict(fixture,tick=2)]
    b=copy.deepcopy(a)
    for f in b:f['public_objects']['projectiles'][0]['id']='b'
    compare_frames(a,b)
    b[1]['public_objects']['projectiles'][0]['id']='c'
    try:compare_frames(a,b)
    except AssertionError:pass
    else:raise AssertionError('Independent lifetime negative control missed a split')
    report=dict(complete=True,replays=20,repeats=len(repeats),coverage=dict(count),commands=dict(grades),
        process_receipt_sha256=sha(process),producer_report_sha256=sha(HERE/'native_capture_v2_verified.json'),
        script_sha256=sha(__file__),recordings=recordings,repeat_tags=repeats,
        independent_lifetime_negative_control=True,model_predictions=0,
        limitations=['Historical skipped ability commands remain skipped, not verified successes.',
                    'These exposed mechanics fixtures are not fresh model confirmation.',
                    'TTI disappearance is not verified actual live landing truth.'])
    (HERE/'native_capture_independent.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('recordings','repeat_tags')}))
    print('NATIVE_PREFLIGHT_INDEPENDENTLY_VERIFIED')


if __name__=='__main__':main()
