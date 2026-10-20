"""Verify original compressed asset identity; never modify a catalog."""
import csv, hashlib, io, json, lzma, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
NATIVE=ROOT/'research/ext/cr-native-sandbox'

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def decode(b):return lzma.decompress(b[:9]+b'\0'*4+b[9:],format=lzma.FORMAT_ALONE).decode()

def main():
    out=HERE/'audit.json';assert not out.exists()
    manifest=ROOT/'icebow/data/bench/native_confirmation_20261005/runtime/manifest/runtime-manifest.json'
    m=json.loads(manifest.read_bytes());apk=NATIVE/'runtime/apks/split_install_time_asset_pack.apk'
    assert sha(apk)==next(x['sha256'] for x in m['apks'] if x['name']==apk.name)
    paths=['csv_logic/spells_other.csv','csv_client/texts.csv','csv_logic/characters/dark_magic.toml']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in [manifest,apk,HERE/'PLAN.md',Path(__file__),
        NATIVE/'native_core/data/live_card_catalog.json',ROOT/'research/sandbox_tools/replay_drive.py']}
    with zipfile.ZipFile(apk) as z:
        for name in paths:
            p=NATIVE/'runtime/extracted-assets'/name
            assert z.read('assets/'+name)==p.read_bytes(),name
            hashes[str(p.relative_to(ROOT))]=sha(p)
    rows=list(csv.DictReader(io.StringIO(decode((NATIVE/'runtime/extracted-assets'/paths[0]).read_bytes()))))
    spell=next(x for x in rows if x['Name']=='DarkMagic')
    texts=list(csv.DictReader(io.StringIO(decode((NATIVE/'runtime/extracted-assets'/paths[1]).read_bytes()))))
    text=next(x for x in texts if x['Name']==spell['TID'])
    cat=json.loads((NATIVE/'native_core/data/live_card_catalog.json').read_bytes())
    card=next(x for x in cat['cards'] if x['internal_name']==spell['Name'])
    assert text['EN']=='Void' and spell['TID']=='TID_SPELL_DARK_MAGIC'
    assert card['card_id']==28000023 and card['elixir']==int(spell['ManaCost'])==5
    report=dict(complete=True,sources=hashes,identity=dict(slug='void',internal_name=spell['Name'],
        text_key=spell['TID'],english=text['EN'],card_id=card['card_id'],catalog_elixir=card['elixir']),
        original_assets_match_apk=True,model_predictions=0,native_cost_measured=False,
        official_cost_revision_url='https://supercell.com/en/games/clashroyale/blog/news/final-august-balance-changes-826/')
    out.write_text(json.dumps(report,indent=2));print(json.dumps(report['identity']));print('VOID_PINNED_IDENTITY_VERIFIED')

if __name__=='__main__':main()
