import copy
from audit_v2 import distinct_frames,join_frame
from controls import frame
from io_utils import *

def main():
    a,b=frame(10),frame(20)
    assert distinct_frames([a,b,copy.deepcopy(b)])==[a,b]
    rec={'frames':[a,b,copy.deepcopy(b)]}
    assert join_frame(rec,{'y_gate':0,'tick':20},[])[1]==dict(kind='frames',index=1)
    bad=copy.deepcopy(b);bad['towers'][0][5]-=1
    negatives=0
    for fs in ([a,b,bad],[b,a]):
        try:distinct_frames(fs)
        except AssertionError:negatives+=1
        else:raise AssertionError('Corrupt duplicate/order accepted')
    assert negatives==2
    write(HERE/'duplicate_controls.json',dict(positive=2,negative=2,sources={p.name:sha(p) for p in
        (HERE/'audit_v2.py',HERE/'duplicate_controls.py',HERE/'DUPLICATE_FRAME_CORRECTION.md')}))
    print('MATCH_DUPLICATE_CONTROLS_PASS')

if __name__=='__main__':main()
