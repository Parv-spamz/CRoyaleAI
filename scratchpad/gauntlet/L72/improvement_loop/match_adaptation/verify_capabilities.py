"""Independent native-schema and recorded-result provenance inventory."""
from collections import Counter
from io_utils import *

def crown_pair(record):
    expected=record.get('expected',{}).get('crowns_by_side',{})
    actual=record.get('final',{}).get('crowns')
    if set(expected)!={'0','1'} or not isinstance(actual,list) or len(actual)!=2:return None
    if any(not isinstance(x,int) for x in actual+list(expected.values())):return None
    return actual==[expected['0'],expected['1']]

def main():
    assert not (HERE/'capabilities_verified.json').exists()
    report=read(HERE/'report_v2.json');binding=check_binding();c=Counter();grades=Counter();different=[]
    assert crown_pair(dict(expected={'crowns_by_side':{'0':1,'1':2}},final={'crowns':[1,2]})) is True
    assert crown_pair(dict(expected={'crowns_by_side':{'0':1,'1':2}},final={'crowns':[2,1]})) is False
    assert crown_pair(dict(expected={'crowns_by_side':{'0':1}},final={'crowns':[1,2]})) is None
    for tag,source in binding['sources'].items():
        path=ROOT/source['path'];assert sha(path)==source['sha256'];r=read(path)
        c['replays']+=1;c['native_crowns_mismatch']+=not r.get('grade',{}).get('crowns_match',False)
        previous=None
        for f in r['frames']:
            if previous is not None and f['tick']==previous['tick']:
                assert f==previous;c['byte_equal_duplicate_frames']+=1;continue
            if previous is not None:assert f['tick']>previous['tick']
            previous=f;c['frames']+=1
            c['frames_observed_multiplier']+=any(k in f for k in ['elixir_rate','elixir_multiplier'])
            c['frames_causal_hits']+=f.get('public_objects',{}).get('causal_hit_events') is not None
            c['entity_rows_with_target_column']+=len([e for e in f.get('entities',[]) if len(e)>9])
        actual=crown_pair(r);grades[str(actual)]+=1
        if actual!=r.get('grade',{}).get('crowns_match'):different.append(tag)
    assert dict(c)==report['capabilities']
    write(HERE/'capabilities_verified.json',dict(complete=True,report_sha256=sha(HERE/'report_v2.json'),
        sources=len(binding['sources']),counts=dict(c),raw_expected_vs_native_final_crowns=dict(grades),
        grade_flag_disagrees_with_raw=different,controls=dict(positive=1,negative=1,missing=1),
        verifier_sha256=sha(__file__),no_model_calls=True))
    print(json.dumps(dict(counts=dict(c),raw_crowns=dict(grades),grade_disagreements=len(different))))
    print('MATCH_CAPABILITIES_INDEPENDENT_COMPLETE')

if __name__=='__main__':main()
