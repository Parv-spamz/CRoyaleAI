import native_targets as m

def fixture():
    return dict(tag='sample',final_decks={'0':['ArcherQueen'],'1':[]},
        log=[dict(card='archer-queen',accepted=True,side=0,tick=10,play_index=0),
             dict(card='archer-queen',ability=True,accepted=True,side=0,tick=50,entity_id=12)],
        frames=[dict(tick=20,entities=[[0,0,0,'ArcherQueen',100,100,0,26000072,12]])])

def test_exact_controller_delay_and_no_opponent_private_dependency():
    r=fixture();ds,c=m.extract(r,{'archer-queen':{26000072}})
    assert ds[0]['status']=='LINKED' and ds[0]['delay_s']==2
    r['players']=[{'hand':['PRIVATE'],'elixir':999}]*2
    assert m.extract(r,{'archer-queen':{26000072}})==(ds,c)

def test_overlapping_deployments_are_unknown_not_negative():
    r=fixture();r['log'].insert(1,dict(card='archer-queen',accepted=True,side=0,tick=15,play_index=1))
    ds,c=m.extract(r,{'archer-queen':{26000072}})
    assert all(d['status']=='AMBIGUOUS_CONTROLLER_LINK' for d in ds)
    assert c['accepted_press_without_unique_deployment']==1
    assert m.describe(ds)['pressed_share'] is None

def test_same_card_wrong_entity_is_not_assigned():
    r=fixture();r['log'][1]['entity_id']=99
    ds,c=m.extract(r,{'archer-queen':{26000072}})
    assert c['accepted_press_without_unique_deployment']==1
    assert ds[0]['press_ticks']==[]
    assert m.describe(ds)['pressed_share'] is None

def test_composite_card_sibling_is_not_the_ability_controller():
    from phase2_build import CONTROLLER_BASE_HP,LEVEL_PCT
    r=fixture();r['final_decks']['0']=['Goblinstein']
    r['log'][0]['card']=r['log'][1]['card']='goblinstein'
    hp=int(CONTROLLER_BASE_HP['goblinstein']*LEVEL_PCT[10]/100)
    r['frames'][0]['entities']=[[0,0,0,'Goblinstein',hp,hp,0,26000099,12],
        [0,0,0,'Goblinstein',hp+500,hp+500,0,26000099,13]]
    ds,c=m.extract(r,{'goblinstein':{26000099}})
    assert ds[0]['status']=='LINKED' and ds[0]['entities']==[12]
    assert ds[0]['delay_s']==2
