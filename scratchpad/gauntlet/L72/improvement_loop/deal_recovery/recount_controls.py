"""Exercise the independent opening/command oracle against archived training captures."""
import copy
import json
from pathlib import Path
from verify_v4 import read,csv_rows,recount,opening,ROOT,HERE

def main():
    audit=read(HERE/'audit.json');result=read(HERE/'complete_v3.json')
    by_tag={i['tag']:i for i in audit['training_trials']}
    choices=[r for r in result['rows'] if r['attempts'][0]['status']=='captured']
    failures=[];positives=0
    def validate(rec,item):
        folder=ROOT/item['job']['crawl'];commands=csv_rows(folder/'plays_ext.csv')
        recount(rec,commands,csv_rows(folder/'battles.csv')[0]);opening(rec,commands,item['job'])
    first=choices[0];item=by_tag[first['tag']];rec=read(ROOT/first['attempts'][0]['path'])
    validate(rec,item);positives+=1
    good=next(r for r in choices if r['usable']);gi=by_tag[good['tag']]
    validate(read(ROOT/good['attempts'][0]['path']),gi);positives+=1
    def reject(name,fn):
        bad=copy.deepcopy(rec);fn(bad)
        try:validate(bad,item)
        except (AssertionError,KeyError,ValueError,IndexError):failures.append(name)
        else:raise AssertionError('Accepted corruption: '+name)
    reject('missing_card_frame',lambda r:r['play_frames'].pop())
    reject('wrong_frame_tick',lambda r:r['play_frames'][0].__setitem__('tick',-1))
    reject('changed_command',lambda r:r['log'][0].__setitem__('card','fake-card'))
    reject('dropped_ability',lambda r:r['log'].pop(next(i for i,x in enumerate(r['log']) if x.get('ability'))))
    reject('wrong_opening_position',lambda r:r['opening_deal_verified']['0']['hand_positions'].__setitem__(0,99))
    reject('wrong_opening_card',lambda r:r['opening_deal_verified']['0']['hand'].__setitem__(0,999))
    reject('changed_form',lambda r:r['final_decks']['0'].__setitem__(0,r['final_decks']['0'][0]+'@invalid'))
    print(json.dumps(dict(positive_checks=positives,rejected=failures)))
    print('DEAL_RECOUNT_CONTROLS_PASS')

if __name__=='__main__':main()
