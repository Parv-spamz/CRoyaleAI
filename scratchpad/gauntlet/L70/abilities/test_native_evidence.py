import copy
import unittest
import native_evidence as N


class NativeEvidenceTest(unittest.TestCase):
    def sample(self):
        return dict(record_native=True,frames=[dict(tick=10,entities=[[0,1000,1000,'Queen',100,100,99,500001]])],
            log=[dict(ability=True,card='archer-queen',side=0,tick=20,engine_tick=20,entity_id=500001,accepted=True)])

    def test_controller_uses_correct_side_identity_and_past_frame(self):
        r=self.sample();out=N.replay_evidence(r)['archer-queen']
        self.assertEqual(out['counts']['accepted_controller_confirmed'],1)
        self.assertEqual(out['ages'],[.5])
        for change in ('future','wrong_side','stale'):
            x=copy.deepcopy(r)
            if change=='future':x['frames'][0]['tick']=21
            elif change=='wrong_side':x['frames'][0]['entities'][0][0]=1
            else:x['log'][0]['tick']=x['log'][0]['engine_tick']=40
            self.assertEqual(N.replay_evidence(x)['archer-queen']['counts']['accepted_controller_confirmed'],0)

    def test_duplicate_disagreement_and_private_mutations(self):
        r=self.sample();base=N.replay_evidence(r)
        r['players']=[dict(hand=['private'],elixir=100)]
        r['frames'][0]['elixir']=[100,100]
        self.assertEqual(N.replay_evidence(r),base)
        r['frames'].append(dict(tick=10,entities=[]))
        self.assertEqual(N.replay_evidence(r)['archer-queen']['counts']['accepted_controller_unconfirmed'],1)

    def test_skipped_and_rejected_presses_are_not_accepted_activations(self):
        r=self.sample();r['log']=[dict(r['log'][0],accepted=False,result_name='not_ready'),
                                dict(r['log'][0],accepted=False,skipped='no_controller')]
        c=N.replay_evidence(r)['archer-queen']['counts']
        self.assertEqual((c['accepted'],c['rejected'],c['skipped']),(0,1,1))


if __name__=='__main__':unittest.main()
