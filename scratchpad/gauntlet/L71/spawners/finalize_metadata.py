"""Refresh form-share metadata after the verified body correction; arrays unchanged.

Writes a new artifact, preserving the full reconstruction and its evidence.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from pipeline.rocket_teaching import sha


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists():
        raise ValueError('Fresh output required')
    source=args.source/'gen_dataset_v5_public.npz'
    manifest=json.loads((args.source/'manifest.json').read_text())
    assert manifest['trainable'] and sha(source)==manifest['output_sha256']
    with np.load(source) as z:
        meta=json.loads(str(z['meta']))
        forms=z['unit_form']
    original_stats=meta['new_features'].copy()
    meta['new_features']['evo_share']=float(np.mean(forms==1))
    meta['new_features']['hero_share']=float(np.mean(forms==2))
    meta['body_identity_refinement']=dict(source_archive_sha256=sha(source),
        source_manifest_sha256=sha(args.source/'manifest.json'), script_sha256=sha(__file__),
        previous_form_statistics=original_stats, arrays_changed=False)
    args.out.mkdir(parents=True)
    target=args.out/'gen_dataset_v5_public.npz'
    with ZipFile(source) as src,ZipFile(target,'w',compression=ZIP_DEFLATED,compresslevel=3,allowZip64=True) as dst:
        for info in src.infolist():
            with dst.open(info.filename,'w',force_zip64=True) as output:
                if info.filename=='meta.npy':
                    np.lib.format.write_array(output,np.asarray(json.dumps(meta)),allow_pickle=False)
                else:
                    with src.open(info) as data:
                        shutil.copyfileobj(data,output,16<<20)
    shutil.copyfile(args.source/'changed_rows.npy',args.out/'changed_rows.npy')
    manifest.update(output=str(target),output_sha256=sha(target),metadata_refinement=meta['body_identity_refinement'])
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(dict(evo_share=meta['new_features']['evo_share'],hero_share=meta['new_features']['hero_share'])))
    print('SPAWNER_METADATA_FINALIZED')


if __name__=='__main__':
    main()
