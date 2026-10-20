import os
from shared import *
from pipeline.model_gen import GenModel

def main():
    cutoff();assert not (HERE/'started.json').exists();OUT.mkdir(exist_ok=False)
    c.setup();f.check();assert read(FIT/'reviewed_results.json')['complete']
    bound=sources()
    for path,h in bound.items():assert sha(ROOT/path)==h,path
    write(HERE/'started.json',dict(pid=os.getpid(),sources=bound))
    ids=arrays(f.OUT/'schedule.npz')['sample'];sub,meta=c.load_subset(c.DATA,ids)
    rows=c.GenRows(sub,np.arange(len(ids)),'cuda');model,state=model_code.load_local(CKPT,'cuda');model.eval()
    before={k:v.clone() for k,v in model.state_dict().items()};reports={};artifacts={}
    for mir in (False,True):
        orientation='mirrored' if mir else 'native';cache=arrays(f.OUT/('local_cell_final_'+orientation+'.npz'))
        chunks=[]
        with torch.inference_mode():
            for lo in range(0,1024,128):
                cutoff();ix=np.arange(lo,lo+128);b=c.augment(rows.batch(ix),mir)
                enc=model.encode_gen(b);heads=model.heads_gen(enc,b)
                q=model.query(torch.cat([enc['g'],model.emb(b['card'],b['form'])],-1))
                base=GenModel.cell_logits_gen(model,enc,b['card'],b['form'])
                scores=model.local_scores(enc['p'],q);res=scores[:,model.cell_patch,model.local_cell_offset]
                full=model.cell_logits_gen(enc,b['card'],b['form'])
                assert torch.equal(base+res,full)
                assert np.array_equal(full.argmax(-1).cpu().numpy(),cache['expert_cell'][ix])
                assert np.array_equal(heads['gate'].sigmoid().cpu().numpy()>.35,cache['gate'][ix]>.35)
                allowed=torch.as_tensor(cache['allowed'][ix],device='cuda')
                slots=heads['card'].masked_fill(~allowed,-torch.inf).argmax(-1).cpu().numpy()
                assert np.array_equal(sub['hand_card'][ix,slots],cache['chosen_card'][ix])
                play=sub['y_gate'][ix]==1;take=torch.as_tensor(play,device='cuda')
                chunk=dict(ids=ids[ix][play],rep=sub['rep'][ix][play],tick=sub['tick'][ix][play],card=sub['y_card'][ix][play],
                    xy=b['xy'][take].cpu().numpy(),form=b['form'][take].cpu().numpy(),anchor=cache['expert_cell'][ix][play])
                chunk.update({k:v[take].cpu().numpy() for k,v in dict(p=enc['p'],g=enc['g'],q=q,base=base,residual=res,full=full).items()})
                assert all(np.isfinite(v).all() for v in chunk.values())
                chunks.append(chunk)
        z={k:np.concatenate([chunk[k] for chunk in chunks]) for k in chunks[0]}
        assert len(z['ids'])==512;path=OUT/(orientation+'.npz');np.savez_compressed(path,**z)
        artifacts[path.name]=sha(path);reports[orientation]=summarize(z,meta['card_vocab'])
    assert all(torch.equal(v,model.state_dict()[k]) for k,v in before.items()) and sha(CKPT)==read(FIT/'trained.json')['checkpoint_sha256']
    assert sources()==bound
    logs=[json.loads(line) for line in (f.OUT/'train.jsonl').read_text().splitlines()]
    means={key:{part:float(np.mean([r['parts'][part] for r in rows])) for part in logs[0]['parts']} for key,rows in [('first256',logs[:256]),('last256',logs[-256:])]}
    write(OUT/'report.json',reports)
    write(HERE/'collected.json',dict(complete=True,artifacts=artifacts,report_sha256=sha(OUT/'report.json'),
        sources=bound,forward_views=2048,play_records=1024,weights_unchanged=True,optimizer_updates=0,backward=0,
        cache_choices_exact=True,full_decomposition_exact=True,loss_parts=means,accepted=False,deployed=False))
    print('LOCAL_CELL_CONTRIBUTION_COLLECTED')

if __name__=='__main__':main()
