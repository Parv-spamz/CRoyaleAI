"""Independent raw-log and native-frame recount for the owner's coverage query."""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from pipeline.body_identity import resolve
from pipeline import vocab

FAMILIES=('goblin_barrel','witch','night_witch','furnace')
LIMITS=(500,1000,1400,1500)


def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def decode_live(events):
    by_tick={}
    for e in events:
        if e.get('event')=='frame' and 'ents' in e and e.get('my_side') is not None:
            bodies=[(int(b[0]),b[1],b[2],int(b[3]),b[4],b[5],int(b[6])) for b in e['ents'] if len(b)>=7]
            by_tick[int(e['tick'])]=(int(e['my_side']),bodies,[],None,'legacy_public_frame')
    for e in events:
        if e.get('event')!='decision' or not e.get('public'):continue
        p=e['public'];bodies=[(int(b['side']),b['x'],b['y'],int(b.get('card_id',-1)),b.get('hp'),b.get('max_hp'),int(b.get('kind',-1))) for b in p.get('raw_bodies',[])]
        known=p.get('own_hand') is not None and p.get('own_elixir_raw') is not None
        ready=(float(p['own_elixir_raw'])>=6 and any(vocab.engine_key(c.get('name') or '')=='rocket' for c in p['own_hand'])) if known else None
        shots=[(int(s['side']),int(s.get('card_id',-1))) for s in p.get('raw_projectiles',[]) or [] if isinstance(s,dict)]
        by_tick[int(p['raw_tick'])]=(int(p['observer_side']),bodies,shots,ready,'decision_public')
    return [(t,*by_tick[t]) for t in sorted(by_tick)]


def decode_pro(rec,side):
    by_tick={}
    for f in rec['frames']+rec.get('play_frames',[]):
        bodies=[(int(e[0]),e[1],e[2],int(e[-2]),e[4],e[5],int(e[6])) for e in f.get('entities',[]) if len(e)>=9 and e[6] not in (12,13)]
        bodies += [(int(t[0]),t[3],t[4],-1,t[5],t[6],13 if t[1]=='princess' else 12) for t in f['towers']]
        shots=[(int(s['side']),int(s.get('card_id',-1))) for s in f.get('public_objects',{}).get('projectiles',[]) or [] if isinstance(s,dict)]
        by_tick[int(f['tick'])]=(side,bodies,shots,None,'native_public')
    return [(t,*by_tick[t]) for t in sorted(by_tick)]


def recount(identifier,frames,mapping):
    evidence={k:dict(first_tick=None,frames=0,parent_frames=0,child_frames=0,
                    uncertain_body_frames=0,projectile_frames=0) for k in FAMILIES}
    history=defaultdict(list)
    for tick,side,bodies,shots,ready,mode in frames:
        enemy=[b for b in bodies if b[0]!=side]
        for family in FAMILIES:
            matches=[b for b in enemy if b[4] is not None and b[4]>0 and b[3] in mapping and mapping[b[3]][0]==family]
            projectile=any(s!=side and card in mapping and mapping[card][0]==family for s,card in shots)
            reasons=set()
            for b in matches:
                _,name,form=mapping[b[3]]
                identity=resolve(name,b[5],form).reason if family!='goblin_barrel' else 'uncertain_body'
                reasons.add(identity if identity in ('parent','child') else 'uncertain_body')
            row=evidence[family]
            if matches or projectile:
                if row['first_tick'] is None:row['first_tick']=tick
                row['frames']+=1
            for reason in ('parent','child','uncertain_body'):row[reason+'_frames']+=int(reason in reasons)
            row['projectile_frames']+=int(projectile)
        for b in enemy:
            if b[6]==13 and b[4] is not None and b[4]>=0:
                history[(b[0],b[1],b[2])].append((tick,float(b[4]),ready))
    output=[]
    for identity,rows in sorted(history.items()):
        selected=[r for r in rows if r[1]>0 and r[1]<=1500]
        if not selected:continue
        first=min(r[0] for r in selected)
        selected.sort()
        endticks=[r[0] for r in rows if r[0]>first and r[1]==0]
        ready_ticks=[r[0] for r in selected if r[2] is True]
        thresholds={}
        for limit in LIMITS:
            times=[r[0] for r in rows if r[1]>0 and r[1]<=limit]
            thresholds[str(limit)]=dict(samples=len(times),first_tick=min(times) if times else None)
        output.append(dict(identity=list(identity),first_tick=first,first_hp=selected[0][1],
            minimum_positive_hp=min(r[1] for r in selected),last_qualifying_tick=selected[-1][0],
            qualifying_samples=len(selected),later_zero_tick=min(endticks) if endticks else None,
            max_qualifying_sample_gap_ticks=max([selected[i][0]-selected[i-1][0] for i in range(1,len(selected))] or [0]),
            ready_samples=len(ready_ticks),readiness_unknown_samples=sum(r[2] is None for r in selected),
            first_ready_tick=min(ready_ticks) if ready_ticks else None,thresholds=thresholds,
            hp_bands={str(high):sum(high-500<r[1]<=high for r in rows) for high in (500,1000,1500)}))
    return dict(id=identifier,public_samples=len(frames),sample_modes=dict(Counter(f[-1] for f in frames)),encounters=evidence,towers=output)


def totals(rows):
    groups={k:set() for k in FAMILIES};parents={k:set() for k in FAMILIES};shots={k:set() for k in FAMILIES}
    thresholds={str(t):dict(records=set(),towers=set()) for t in LIMITS};ready_records=set();ready_towers=set()
    for i,r in enumerate(rows):
        for family in FAMILIES:
            if r['encounters'][family]['frames']:groups[family].add(i)
            if r['encounters'][family]['parent_frames']:parents[family].add(i)
            if r['encounters'][family]['projectile_frames']:shots[family].add(i)
        for j,t in enumerate(r['towers']):
            for bound in thresholds:
                if t['thresholds'][bound]['samples']:
                    thresholds[bound]['records'].add(i);thresholds[bound]['towers'].add((i,j))
            if t['ready_samples']:ready_records.add(i);ready_towers.add((i,j))
    return dict(records=len(rows),with_public_observations=sum(r['public_samples']>0 for r in rows),
        no_public_observations=sum(r['public_samples']==0 for r in rows),
        encounters={k:dict(records=len(groups[k]),confirmed_parent_records=len(parents[k]),projectile_records=len(shots[k])) for k in FAMILIES},
        thresholds={k:{field:len(values) for field,values in row.items()} for k,row in thresholds.items()},
        rocket_ready_records=len(ready_records),rocket_ready_towers=len(ready_towers))


def compare(actual,expected):
    for key in ('id','public_samples','sample_modes','encounters','towers'):assert actual[key]==expected[key],(actual.get('id'),key)


def controls(mapping):
    body=lambda side,hp:(side,3500,25500,-1,hp,4000,13)
    fixture=[(10,0,[body(1,1500),body(0,25)],[],True,'test'),
             (11,0,[body(1,1400)],[],False,'test'),(12,0,[body(1,1000)],[],None,'test'),
             (13,0,[body(1,500)],[],False,'test'),(14,0,[body(1,0)],[],False,'test')]
    expected=recount('fixture',fixture,mapping);tower=expected['towers'][0]
    assert len(expected['towers'])==1 and tower['qualifying_samples']==4 and tower['later_zero_tick']==14
    assert tower['thresholds']=={'500':{'samples':1,'first_tick':13},'1000':{'samples':2,'first_tick':12},'1400':{'samples':3,'first_tick':11},'1500':{'samples':4,'first_tick':10}}
    assert tower['ready_samples']==1 and tower['readiness_unknown_samples']==1
    compare(expected,expected)
    corruptions=[]
    for k,value in [('first_tick',0),('first_hp',1501),('qualifying_samples',5),('ready_samples',2),('later_zero_tick',None)]:
        changed=deepcopy(expected);changed['towers'][0][k]=value;corruptions.append(changed)
    changed=deepcopy(expected);changed['towers'][0]['identity'][0]=0;corruptions.append(changed)
    changed=deepcopy(expected);changed['towers'][0]['thresholds']['1400']['samples']=4;corruptions.append(changed)
    changed=deepcopy(expected);changed['encounters']['witch']['frames']=1;corruptions.append(changed)
    changed=deepcopy(expected);changed['public_samples']=0;corruptions.append(changed)
    for changed in corruptions:
        try:compare(changed,expected)
        except AssertionError:pass
        else:raise AssertionError('Corruption accepted')
    assert not recount('zero',[(0,0,[body(1,0),body(0,300)],[],None,'test')],mapping)['towers']
    return dict(positive=2,negative=len(corruptions))


def main():
    assert not (HERE/'verified.json').exists()
    started=read(HERE/'started.json');report=read(HERE/'report.json');details=read(HERE/'details.json')
    assert report['started_sha256']==sha(HERE/'started.json') and report['details_sha256']==sha(HERE/'details.json')
    assert report['policy_predictions']==report['optimizer_updates']==0 and not report['trained']
    for p,h in started['sources'].items():assert sha(ROOT/p)==h,p
    cat=read(ROOT/'research/ext/cr-native-sandbox/native_core/data/live_card_catalog.json')
    names={'Witch':'witch','DarkWitch':'night_witch','FirespiritHut':'furnace','GoblinBarrel':'goblin_barrel'}
    mapping={int(c[field]):(names[c['display_name']],c['display_name'],form) for c in cat['cards'] if c['display_name'] in names
             for field,form in (('card_id',0),('evolution_form_id',1),('hero_form_id',2)) if c.get(field) is not None}
    assert {str(k):list(v) for k,v in mapping.items()}==started['family_map']
    candidates=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'scratchpad/gauntlet/L68/live_reader').glob('live_play_*.jsonl')
        if 'live_play_20261004_210000'<=p.stem<'live_play_20261005_124400')
    selected=[m['path'] for m in started['live']+started['excluded_unclosed']]
    assert len(selected)==len(set(selected)) and sorted(selected)==candidates
    assert report['excluded_unclosed']==len(started['excluded_unclosed'])
    result=[]
    for m in started['live']:
        p=ROOT/m['path'];assert sha(p)==m['sha256'];events=[json.loads(line) for line in p.open()]
        assert any(e.get('event')=='end' for e in events)
        expected=recount(p.name,decode_live(events),mapping)
        rows=[r for r in details['live'] if r['id']==p.name];assert len(rows)==1;actual=rows[0]
        compare(actual,expected)
        assert actual['rocket_attempts']==sum(e.get('event')=='play' and e.get('name')=='Rocket' for e in events)
        assert actual['rocket_confirmations']==sum(e.get('event')=='confirmed' and e.get('name')=='Rocket' for e in events)
        result.append(expected)
    assert len(result)==len(details['live']) and totals(result)==report['live']
    inventory=read(HERE.parent/'void_capacity/inventory.json');assert started['exact_sides']==inventory['exact_sides']
    tags={s['tag'] for s in inventory['exact_sides']}
    assert started['pro']==sorted([m for m in inventory['qualified'] if m['tag'] in tags],key=lambda r:r['tag'])
    pro=[]
    for m in started['pro']:
        assert sha(ROOT/m['path'])==m['sha256'];rec=read(ROOT/m['path'])
        for side in [s['side'] for s in started['exact_sides'] if s['tag']==m['tag']]:
            expected=recount(m['tag']+':'+str(side),decode_pro(rec,side),mapping)
            matches=[r for r in details['pro'] if r['id']==expected['id']];assert len(matches)==1
            compare(matches[0],expected);assert matches[0]['split']==m['split']=='confirmation';pro.append(expected)
    assert len(pro)==len(details['pro']) and totals(pro)==report['pro']
    assert report['live_rocket_attempts']==sum(r['rocket_attempts'] for r in details['live'])
    assert report['live_rocket_confirmations']==sum(r['rocket_confirmations'] for r in details['live'])
    fixture_counts=controls(mapping)
    result=dict(complete=True,report_sha256=sha(HERE/'report.json'),script_sha256=sha(__file__),
        details_sha256=sha(HERE/'details.json'),controls=fixture_counts,live=report['live'],pro=report['pro'])
    (HERE/'verified.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));print('OWNER_COVERAGE_RECHECK_INDEPENDENT_PASS')


if __name__=='__main__':main()
